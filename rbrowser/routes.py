"""
Flask route registration for rBrowser.

All web endpoints are defined here to keep the entrypoint lightweight. The
routes expect an instance of `NomadNetWebBrowser` to perform the underlying
operations.
"""

from __future__ import annotations

import io
import mimetypes
import os
import re
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
import json
import RNS
from flask import jsonify, render_template, request, send_file, send_from_directory , Response, stream_with_context
import time
import uuid
import threading

# Global storage for download progress
download_progress = {}
download_results = {}

def register_routes(app, browser) -> None:
    """Attach all routes to the provided Flask application."""

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/style.css")
    def serve_css():
        return send_from_directory("templates", "style.css", mimetype="text/css")

    @app.route("/api/nodes")
    def api_nodes():
        nodes = browser.get_nodes()
        for node in nodes:
            path_info = browser.get_node_path_info(node["hash"])
            node["hops"] = path_info["hops"]
            node["next_hop_interface"] = path_info["next_hop_interface"]
        return jsonify(nodes)

    @app.route("/api/status")
    def api_status():
        return jsonify(
            {
                "running": browser.running,
                "total_announces": browser.announce_count,
                "unique_nodes": len(browser.nomadnet_nodes),
                "identity_hash": RNS.prettyhexrep(browser.identity.hash)
                if browser.identity
                else None,
            }
        )

    @app.route("/api/fetch/<node_hash>", methods=["GET", "POST"])
    def api_fetch_page(node_hash):
        page_path = request.args.get("path", "/page/index.mu")
        form_data = request.get_json() if request.method == "POST" else None

        print(f"🌐 API Request: Fetching {page_path} from {node_hash[:16]}...")
        if form_data:
            print(f"📝 Form data: {form_data}")

        response = browser.fetch_page(node_hash, page_path, form_data)

        if response["status"] == "success":
            content_length = len(response.get("content", ""))
            print(f"✅ API Response: Successfully fetched {content_length} characters")
        else:
            print(f"❌ API Response: Failed - {response.get('error', 'Unknown error')}")

        return jsonify(response)

    @app.route("/script/purify.min.js")
    def serve_purify():
        script_path = os.path.join("script", "purify.min.js")
        if os.path.exists(script_path):
            print(f"✅ Serving DOMPurify from: {script_path}")
            return send_from_directory("script", "purify.min.js", mimetype="application/javascript")
        print(f"❌ DOMPurify not found at: {script_path}")
        return "console.error('DOMPurify file not found');", 404

    @app.route("/script/micron-parser_original.js")
    def serve_micron_parser():
        script_path = os.path.join("script", "micron-parser_original.js")
        if os.path.exists(script_path):
            print(f"✅ Serving micron parser from: {script_path}")
            return send_from_directory("script", "micron-parser_original.js", mimetype="application/javascript")
        print(f"❌ Micron parser not found at: {script_path}")
        return "console.error('Micron parser file not found');", 404

    @app.route("/api/download/<node_hash>")
    def api_download_file(node_hash):
        file_path = request.args.get("path", "/file/")
        if not file_path.startswith("/file/"):
            return jsonify({"error": "Invalid file path"}), 400
        
        # Generate unique download ID
        download_id = str(uuid.uuid4())
        
        # Return download ID to client immediately
        return jsonify({"download_id": download_id, "status": "started"})
        
    @app.route("/api/download/<node_hash>/stream")
    def api_download_file_stream(node_hash):
        """Stream file download with Server-Sent Events for progress."""
        file_path = request.args.get("path", "/file/")
        download_id = request.args.get("download_id")
        
        if not file_path.startswith("/file/"):
            return jsonify({"error": "Invalid file path"}), 400
        
        def generate():
            # Track progress
            download_progress[download_id] = {"progress": 0, "status": "downloading"}
            
            def progress_callback(progress):
                download_progress[download_id]["progress"] = progress * 100
                # Send progress update via SSE
                yield f"data: {json.dumps({'progress': progress * 100, 'status': 'downloading'})}\n\n"
            
            # Download file with progress tracking
            response = browser.fetch_file(node_hash, file_path, progress_callback)
            
            if response["status"] == "error":
                yield f"data: {json.dumps({'error': response.get('error'), 'status': 'error'})}\n\n"
                return
            
            file_data = response["content"]
            filename = file_path.split("/")[-1] or "download"
            
            # Send completion with file data
            import base64
            file_b64 = base64.b64encode(file_data).decode('utf-8')
            yield f"data: {json.dumps({'progress': 100, 'status': 'complete', 'filename': filename, 'file_data': file_b64})}\n\n"
            
            # Cleanup
            if download_id in download_progress:
                del download_progress[download_id]
        
        return Response(generate(), mimetype='text/event-stream')

    @app.route("/api/download/<node_hash>/start")
    def api_start_download(node_hash):
        """Start a download and return a download ID."""
        file_path = request.args.get("path", "/file/")
        if not file_path.startswith("/file/"):
            return jsonify({"error": "Invalid file path"}), 400
        
        # Generate unique download ID
        download_id = str(uuid.uuid4())
        download_progress[download_id] = {"progress": 0, "status": "starting"}
        
        # Removed the print statement here - it's now in nomadnet.py
        
        def do_download():
            def progress_callback(progress):
                download_progress[download_id] = {
                    "progress": progress * 100,
                    "status": "downloading"
                }
                # Removed: print statement here
            
            response = browser.fetch_file(node_hash, file_path, progress_callback)
            
            if response["status"] == "success":
                download_results[download_id] = {
                    "status": "complete",
                    "content": response["content"],
                    "filename": file_path.split("/")[-1] or "download"
                }
                download_progress[download_id] = {"progress": 100, "status": "complete"}
            else:
                download_results[download_id] = {
                    "status": "error",
                    "error": response.get("error", "Unknown error")
                }
                download_progress[download_id] = {"progress": 0, "status": "error"}
        
        # Start download in background thread
        thread = threading.Thread(target=do_download)
        thread.daemon = True
        thread.start()
        
        return jsonify({"download_id": download_id, "status": "started"})

    @app.route("/api/download/progress/<download_id>")
    def api_download_progress(download_id):
        """Get current download progress."""
        progress_data = download_progress.get(download_id, {"progress": 0, "status": "unknown"})
        return jsonify(progress_data)

    @app.route("/api/download/result/<download_id>")
    def api_download_result(download_id):
        """Get the downloaded file once complete."""
        result = download_results.get(download_id)
        
        if not result:
            return jsonify({"error": "Download not found"}), 404
        
        if result["status"] == "error":
            return jsonify({"error": result.get("error", "Download failed")}), 500
        
        file_data = result["content"]
        filename = result["filename"]
        
        # Cleanup
        if download_id in download_progress:
            del download_progress[download_id]
        if download_id in download_results:
            del download_results[download_id]
        
        if not isinstance(file_data, bytes):
            if isinstance(file_data, str):
                file_data = file_data.encode("latin1")
            else:
                file_data = str(file_data).encode("latin1")
        
        mime_type, _ = mimetypes.guess_type(filename)
        if not mime_type:
            mime_type = "application/octet-stream"
        
        print(f"✅ Serving file: {filename} ({len(file_data)} bytes)")
        
        file_obj = io.BytesIO(file_data)
        return send_file(
            file_obj,
            mimetype=mime_type,
            as_attachment=True,
            download_name=filename
        )

    @app.route("/favicon.svg")
    def favicon():
        return "", 204

    @app.route("/api/fingerprint/<node_hash>", methods=["POST"])
    def api_send_fingerprint(node_hash):
        print(f"API Request: Sending identity fingerprint to {node_hash[:16]}...")
        response = browser.send_fingerprint(node_hash)
        if response["status"] == "success":
            print("API Response: Identity fingerprint sent successfully")
        else:
            print(f"API Response: Identity fingerprint failed - {response.get('error', 'Unknown error')}")
        return jsonify(response)

    @app.route("/api/connection-status")
    def api_connection_status():
        try:
            status_data = browser.get_cached_status()
        except Exception as exc:
            print(f"Error in connection status: {exc}")
            return jsonify({"status": "connerror", "message": "Status check failed", "color": "red"})

        app_uptime = status_data["app_uptime"]
        has_nodes = status_data["has_nodes"]
        time_since_last_announce = status_data["time_since_last_announce"]
        connection_state = status_data["connection_state"]
        reticulum_ready = status_data["reticulum_ready"]

        if not reticulum_ready:
            return jsonify({"status": "connerror", "message": "Reticulum initialization failed", "color": "red"})

        if connection_state == "failed":
            return jsonify({"status": "connerror", "message": "Connection failed during startup", "color": "red"})

        if connection_state == "initializing":
            return jsonify({"status": "waiting", "message": "Initializing Reticulum...", "color": "yellow"})

        if connection_state == "connecting":
            return jsonify({"status": "waiting", "message": "Connecting to Reticulum...", "color": "yellow"})

        if connection_state == "connected":
            if app_uptime < 60:
                return jsonify(
                    {
                        "status": "waiting",
                        "message": "Connected! <span style='color: #FFC107;'>Waiting for announces...</span> ",
                        "color": "green",
                    }
                )
            if app_uptime < 120:
                return jsonify({"status": "waiting", "message": "Waiting for network activity...", "color": "yellow"})
            return jsonify(
                {"status": "waiting", "message": "Connected but no network activity", "color": "yellow"}
            )

        if connection_state == "active":
            if has_nodes:
                if time_since_last_announce and time_since_last_announce > 300:
                    return jsonify(
                        {"status": "waiting", "message": "No recent announces, waiting...", "color": "yellow"}
                    )
                return jsonify({"status": "online", "message": "Online. Reticulum Connected!", "color": "green"})
            return jsonify(
                {"status": "waiting", "message": "Connection active but no nodes found", "color": "yellow"}
            )

        return jsonify(
            {"status": "connerror", "message": f"Unknown connection state: {connection_state}", "color": "red"}
        )

    @app.route("/api/search-cache")
    def api_search_cache():
        query = request.args.get("q", "").lower().strip()
        if not query:
            return jsonify([])

        results: List[Dict[str, Any]] = []
        search_limit = int(browser.cache_settings.get("search_limit", 50))

        try:
            for node_dir in _iter_cache_dirs(browser.cache_dir):
                node_result = _search_node_cache(node_dir, query, search_limit, results)
                if node_result is not None:
                    results.extend(node_result)
                if len(results) >= search_limit:
                    break
            return jsonify(results)

        except Exception as exc:
            print(f"Search error: {exc}")
            import traceback

            traceback.print_exc()
            return jsonify({"error": str(exc)}), 500

    @app.route("/api/refresh-node-cache/<node_hash>", methods=["POST"])
    def api_refresh_node_cache(node_hash):
        try:
            print(f"=== Refresh request received for: {node_hash} ===")
            node_name = _resolve_node_name(browser, node_hash)
            print(f"Queuing {node_name} for refresh...")
            browser.cache.enqueue_cache(node_hash, node_name)
            print("Successfully queued!")
            return jsonify(
                {
                    "status": "success",
                    "message": f"Queued {node_name} for cache refresh",
                    "node_name": node_name,
                    "node_hash": node_hash,
                }
            )
        except Exception as exc:
            print(f"ERROR in refresh endpoint: {exc}")
            import traceback

            traceback.print_exc()
            return jsonify({"status": "error", "message": str(exc)}), 500

    @app.route("/api/check-cache-status/<node_hash>")
    def api_check_cache_status(node_hash):
        try:
            cache_dir = browser.cache_dir / node_hash
            cached_at_file = cache_dir / "cached_at.txt"
            if not cached_at_file.exists():
                return jsonify({"updated": False})

            cached_datetime = datetime.fromisoformat(cached_at_file.read_text().strip())
            cached_at = cached_datetime.strftime("%Y-%m-%d %H:%M:%S")
            time_since_cache = (datetime.now() - cached_datetime).total_seconds()
            updated = time_since_cache < 10

            cache_status = _calculate_cache_status(time_since_cache)

            return jsonify({"updated": updated, "cache_status": cache_status, "cached_at": cached_at})

        except Exception as exc:
            print(f"Error checking cache status: {exc}")
            return jsonify({"updated": False})

    @app.route("/templates/go.png")
    def serve_go_icon():
        return _serve_template_asset("go.png")

    @app.route("/templates/search.png")
    def serve_search_icon():
        return _serve_template_asset("search.png")

    @app.route("/templates/star.png")
    def serve_star_icon():
        return _serve_template_asset("star.png")

    @app.route("/templates/ping.png")
    def serve_ping_icon():
        return _serve_template_asset("ping.png")

    @app.route("/templates/fingerprint.png")
    def serve_fingerprint_icon():
        return _serve_template_asset("fingerprint.png")
    
    @app.route('/templates/<path:filename>')
    def serve_template_file(filename):
        """Serve static files from templates directory (icons, images, etc.)"""
        return send_from_directory('templates', filename)

    @app.route("/api/cache-settings", methods=["GET", "POST"])
    def api_cache_settings():
        if request.method == "GET":
            return jsonify(browser.cache_settings)

        data = request.json or {}
        action = data.get("action")

        if action == "toggle_auto_cache":
            browser.cache_settings["auto_cache_enabled"] = data.get("enabled", True)
        elif action == "update_size_limit":
            browser.cache_settings["size_limit_mb"] = data.get("value", 100)
        elif action == "update_expiry":
            browser.cache_settings["expiry_days"] = data.get("value", 30)
        elif action == "update_search_limit":
            browser.cache_settings["search_limit"] = data.get("value", 50)
        elif action == "toggle_additional_pages":
            browser.cache_settings["cache_additional"] = data.get("enabled", False)
        elif action == "clear_cache":
            try:
                browser.cache.clear_cache()
                return jsonify({"message": "Cache cleared successfully", "status": "success"})
            except Exception as exc:
                return jsonify({"message": f"Error clearing cache: {exc}", "status": "error"})
        elif action == "refresh_cache":
            count = 0
            for node_data in browser.nomadnet_nodes.values():
                browser.cache.enqueue_cache(node_data["hash"], node_data["name"])
                count += 1
            return jsonify({"message": f"Queued {count} nodes for refresh", "status": "success"})
        elif action == "cache_additional_all":
            if not browser.cache_settings.get("cache_additional", False):
                return jsonify({"message": "Additional page caching is disabled", "status": "error"})

            count = 0
            for node_dir in _iter_cache_dirs(browser.cache_dir):
                node_hash = node_dir.name
                name_file = node_dir / "node_name.txt"
                node_name = name_file.read_text(encoding="utf-8") if name_file.exists() else "Unknown"
                browser.cache.enqueue_additional(node_hash, node_name)
                count += 1

            return jsonify({"message": f"Queued {count} nodes for additional page caching", "status": "success"})

        browser.save_cache_settings()
        return jsonify({"status": "success"})

    @app.route("/api/export-cache")
    def api_export_cache():
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            for node_dir in _iter_cache_dirs(browser.cache_dir):
                for file in node_dir.rglob("*"):
                    if file.is_file():
                        archive.write(file, file.relative_to(browser.cache_dir))

        zip_buffer.seek(0)
        return send_file(
            io.BytesIO(zip_buffer.read()),
            mimetype="application/zip",
            as_attachment=True,
            download_name="nomadnet_cache_export.zip",
        )

    @app.route("/api/cache-stats")
    def api_cache_stats():
        node_count = 0
        page_count = 0
        valid_page_count = 0
        total_size = 0

        for node_dir in _iter_cache_dirs(browser.cache_dir):
            node_count += 1
            for file in node_dir.rglob("*.mu"):
                if file.is_file():
                    page_count += 1
                    total_size += file.stat().st_size
                    try:
                        content = file.read_text(encoding="utf-8", errors="ignore")
                        if "Request failed" not in content:
                            valid_page_count += 1
                    except Exception as exc:
                        print(f"Error reading {file}: {exc}")

        cache_size = _format_cache_size(total_size)
        return jsonify(
            {
                "node_count": node_count,
                "page_count": page_count,
                "valid_page_count": valid_page_count,
                "cache_size": cache_size,
            }
        )

    @app.route("/api/ping/<node_hash>", methods=["POST"])
    def api_ping_node(node_hash):
        print(f"API Request: Pinging node {node_hash[:16]}...")
        response = browser.ping_node(node_hash)
        if response["status"] == "success":
            print(f"API Response: Ping successful - RTT: {response.get('rtt', 0):.2f}s")
        else:
            print(f"API Response: Ping failed - {response.get('error', 'Unknown error')}")
        return jsonify(response)
    
    @app.route('/api/favorites', methods=['GET'])
    def get_favorites():
        try:
            favorites_file = 'settings/favorites.json'
            if os.path.exists(favorites_file):
                with open(favorites_file, 'r') as f:
                    favorites = json.load(f)
                return jsonify({'status': 'success', 'favorites': favorites})
            else:
                return jsonify({'status': 'success', 'favorites': []})
        except Exception as e:
            return jsonify({'status': 'error', 'error': str(e)})

    @app.route('/api/favorites', methods=['POST'])
    def save_favorites():
        try:
            favorites = request.json.get('favorites', [])
            favorites_file = 'settings/favorites.json'
            
            # Create settings directory if it doesn't exist
            os.makedirs('settings', exist_ok=True)
            
            with open(favorites_file, 'w') as f:
                json.dump(favorites, f, indent=2)
            
            return jsonify({'status': 'success', 'message': 'Favorites saved'})
        except Exception as e:
            return jsonify({'status': 'error', 'error': str(e)})


# ---------------------------------------------------------------------- #
# Helper utilities (kept module-private)                                 #
# ---------------------------------------------------------------------- #


def _iter_cache_dirs(cache_root: Path) -> Iterable[Path]:
    if not cache_root.exists():
        return []
    return (node_dir for node_dir in cache_root.iterdir() if node_dir.is_dir())


def _search_node_cache(
    node_dir: Path,
    query: str,
    search_limit: int,
    results: List[Dict[str, Any]],
) -> Optional[List[Dict[str, Any]]]:
    node_results: List[Dict[str, Any]] = []
    name_file = node_dir / "node_name.txt"
    node_name = name_file.read_text(encoding="utf-8") if name_file.exists() else "Unknown Node"

    cached_at_file = node_dir / "cached_at.txt"
    cached_at = "Unknown"
    cache_age_days: Optional[float] = None
    cache_status = "unknown"

    if cached_at_file.exists():
        try:
            cached_datetime = datetime.fromisoformat(cached_at_file.read_text().strip())
            cached_at = cached_datetime.strftime("%Y-%m-%d %H:%M:%S")
            cache_age = datetime.now() - cached_datetime
            cache_age_days = cache_age.total_seconds() / 86400
            cache_status = _calculate_cache_status(cache_age.total_seconds())
        except Exception as exc:
            print(f"Error parsing cache date: {exc}")

    index_file = node_dir / "index.mu"
    if index_file.exists():
        node_results.extend(
            _match_content(
                index_file,
                node_dir.name,
                node_name,
                query,
                cached_at,
                cache_status,
                cache_age_days,
                search_limit,
                results,
            )
        )

    pages_dir = node_dir / "pages"
    if pages_dir.exists():
        for page_file in pages_dir.glob("*.mu"):
            if len(results) + len(node_results) >= search_limit:
                break
            node_results.extend(
                _match_content(
                    page_file,
                    node_dir.name,
                    node_name,
                    query,
                    cached_at,
                    cache_status,
                    cache_age_days,
                    search_limit,
                    results,
                )
            )

    return node_results


def _match_content(
    file_path: Path,
    node_hash: str,
    node_name: str,
    query: str,
    cached_at: str,
    cache_status: str,
    cache_age_days: Optional[float],
    search_limit: int,
    results: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    matches: List[Dict[str, Any]] = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as exc:
        print(f"Error reading cache file {file_path}: {exc}")
        return matches

    if query not in content.lower() and query not in node_name.lower():
        return matches

    snippet = extract_snippet(content, query)
    if query in node_name.lower():
        snippet = f"Node name match: {node_name}\n\n" + snippet

    page_name = file_path.name
    page_path = "/page/index.mu" if page_name == "index.mu" else f"/page/{page_name}"

    matches.append(
        {
            "node_hash": node_hash,
            "node_name": node_name,
            "snippet": snippet,
            "url": f"{node_hash}:{page_path}",
            "page_name": page_name,
            "page_path": page_path,
            "cached_at": cached_at,
            "cache_status": cache_status,
            "cache_age_days": cache_age_days,
        }
    )
    return matches


def _calculate_cache_status(time_since_cache_seconds: float) -> str:
    cache_age_days = time_since_cache_seconds / 86400
    if cache_age_days <= 3:
        return "fresh"
    if cache_age_days <= 10:
        return "good"
    if cache_age_days <= 20:
        return "moderate"
    return "old"


def _resolve_node_name(browser, node_hash: str) -> str:
    for node_data in browser.nomadnet_nodes.values():
        if node_data.get("hash") == node_hash:
            return node_data.get("name", "Unknown")

    cache_dir = browser.cache_dir / node_hash
    name_file = cache_dir / "node_name.txt"
    if name_file.exists():
        return name_file.read_text(encoding="utf-8", errors="ignore").strip()

    return "Unknown"


def _serve_template_asset(filename: str):
    try:
        return send_from_directory("templates", filename, mimetype="image/png")
    except Exception as exc:
        print(f"❌ Error serving {filename}: {exc}")
        return "", 404


def _format_cache_size(total_size: int) -> str:
    if total_size < 1024:
        return f"{total_size} B"
    if total_size < 1024 * 1024:
        return f"{total_size / 1024:.1f} KB"
    return f"{total_size / (1024 * 1024):.1f} MB"


def extract_snippet(content: str, query: str, context_length: int = 150) -> str:
    """Extract text snippet around search term with highlighting."""
    lower_content = content.lower()
    query_pos = lower_content.find(query.lower())

    if query_pos == -1:
        return content[:context_length] + ("..." if len(content) > context_length else "")

    start = max(0, query_pos - context_length // 2)
    end = min(len(content), query_pos + len(query) + context_length // 2)

    snippet = content[start:end]
    if start > 0:
        snippet = "..." + snippet
    if end < len(content):
        snippet = snippet + "..."

    import re

    highlighted = re.sub(f"({re.escape(query)})", r"<mark>\\1</mark>", snippet, flags=re.IGNORECASE)
    return highlighted


__all__ = ["register_routes", "extract_snippet"]
