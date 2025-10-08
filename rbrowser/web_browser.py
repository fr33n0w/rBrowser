"""
High level management for the rBrowser NomadNet client.

`NomadNetWebBrowser` coordinates the Reticulum connection, caches announce
information about nodes, and exposes helpers used by the Flask API.
"""

from __future__ import annotations

import os
import sys
import threading
import time
from datetime import datetime
from typing import Any, Dict, Optional

import RNS
import RNS.vendor.umsgpack as msgpack

from .cache import CacheManager
from .nomadnet import NomadNetAnnounceHandler, NomadNetBrowser, NomadNetFileBrowser, _clean_hash


class NomadNetWebBrowser:
    """Main controller for rBrowser runtime state."""

    def __init__(self) -> None:
        self.reticulum: Optional[RNS.Reticulum] = None
        self.identity: Optional[RNS.Identity] = None
        self.nomadnet_nodes: Dict[str, Dict[str, Any]] = {}
        self.running = False
        self.announce_count = 0
        self.start_time = time.time()
        self.last_announce_time: Optional[float] = None
        self.connection_state = "initializing"
        self.reticulum_ready = False

        self._status_cache: Optional[Dict[str, Any]] = None
        self._status_cache_time: Optional[float] = None
        self._cache_lock = threading.Lock()
        self.cache_duration = 1.0

        self.nomadnet_cached_links: Dict[bytes, RNS.Link] = {}

        # Cache manager handles all caching concerns and background work.
        self.cache = CacheManager(self)

        print("=" * 90)
        print("🌐 rBrowser v1.0 - Standalone Nomadnet Browser - https://github.com/fr33n0w/rBrowser")
        print("=" * 90)
        print("⚡ Initializing rBrowser v1.0 NomadNet Web Browser...")
        print("📋 RNS LOG LEVEL SET TO: CRITICAL")
        print("🔗 Connecting to Reticulum...")
        print("=" * 90)

        self.init_reticulum()

    # ------------------------------------------------------------------ #
    # Convenience properties                                             #
    # ------------------------------------------------------------------ #

    @property
    def cache_settings(self) -> Dict[str, Any]:
        return self.cache.settings

    @property
    def cache_dir(self):
        return self.cache.cache_dir

    def save_cache_settings(self) -> None:
        self.cache.save_settings()

    # ------------------------------------------------------------------ #
    # Reticulum initialisation                                           #
    # ------------------------------------------------------------------ #

    def init_reticulum(self) -> None:
        """Initialise Reticulum and register announce handlers."""
        try:
            self.connection_state = "connecting"
            print("🔗 Connecting to Reticulum...")
            RNS.loglevel = RNS.LOG_CRITICAL

            self.reticulum = self._ensure_reticulum_instance()

            identity_path = "nomadnet_browser_identity"
            if os.path.exists(identity_path):
                self.identity = RNS.Identity.from_file(identity_path)
            else:
                self.identity = RNS.Identity()
                self.identity.to_file(identity_path)

            self.nomadnet_handler = NomadNetAnnounceHandler(self)
            RNS.Transport.register_announce_handler(self.nomadnet_handler)

            self.reticulum_ready = True
            self.connection_state = "connected"

            if self.identity:
                print(f"🟢 Reticulum Connected! 🔑 Browser identity: {RNS.prettyhexrep(self.identity.hash)}")
            else:
                print("🟢 Reticulum Connected! (no identity hash available)")
            print("=" * 90)

        except Exception as exc:
            self.reticulum_ready = False
            self.connection_state = "failed"
            print(f"Failed to initialise Reticulum: {exc}")
            sys.exit(1)

    def _ensure_reticulum_instance(self) -> RNS.Reticulum:
        """Obtain or create a Reticulum instance."""
        try:
            if hasattr(RNS.Reticulum, "get_instance"):
                instance = RNS.Reticulum.get_instance()
                if instance:
                    print("🔄 Using existing Reticulum instance")
                    return instance
            return RNS.Reticulum()
        except Exception as exc:
            if "reinitialise" in str(exc).lower() or "already running" in str(exc).lower():
                print("⚠️ Reticulum already running - attempting to use existing instance...")
                instance = getattr(RNS.Reticulum, "get_instance", lambda: None)()
                if not instance:
                    print("❌ Cannot access existing Reticulum instance")
                    print("   Try killing all Python processes first: sudo pkill python3")
                    sys.exit(1)
                print("✅ Connected to existing Reticulum instance")
                return instance

            print(f"❌ Reticulum initialization failed: {exc}")
            sys.exit(1)

    # ------------------------------------------------------------------ #
    # Announce handling                                                  #
    # ------------------------------------------------------------------ #

    def process_nomadnet_announce(
        self,
        destination_hash: bytes,
        announced_identity: RNS.Identity,
        app_data: Optional[bytes],
    ) -> None:
        """Process incoming announce messages from NomadNet nodes."""
        self.announce_count += 1
        self.last_announce_time = time.time()

        hash_str = RNS.prettyhexrep(destination_hash)
        clean_hash_str = hash_str.replace("<", "").replace(">", "").replace(":", "")

        node_name = self._decode_node_name(app_data, hash_str)

        if node_name.startswith("EmptyNode_") or node_name.startswith("BinaryNode_") or node_name == "UNKNOWN":
            print(f"Filtered test node: {hash_str[:16]} -> {node_name}")
            return

        node_entry = self.nomadnet_nodes.setdefault(
            hash_str,
            {
                "hash": clean_hash_str,
                "name": node_name,
                "last_seen": datetime.now().isoformat(),
                "announce_count": self.announce_count,
                "node_announce_count": 0,
                "app_data_length": len(app_data) if app_data else 0,
                "last_seen_relative": "Just now",
            },
        )

        node_entry["node_announce_count"] += 1
        node_entry["name"] = node_name
        node_entry["last_seen"] = datetime.now().isoformat()
        node_entry["app_data_length"] = len(app_data) if app_data else 0
        node_entry["last_seen_relative"] = "Just now"

        if self.connection_state == "connected":
            self.connection_state = "active"
            print("🟢 Connection state updated to ACTIVE (received first valid announce)")

        print(
            "🌐 NomadNet Announce #"
            f"{self.announce_count}: {clean_hash_str} -> {node_name} "
            f"(node announces: {node_entry['node_announce_count']})"
        )

        self.cache.schedule_node(clean_hash_str, node_name)

    @staticmethod
    def _decode_node_name(app_data: Optional[bytes], hash_str: str) -> str:
        if app_data:
            try:
                return app_data.decode("utf-8")
            except Exception:
                try:
                    decoded = msgpack.unpackb(app_data)
                    if isinstance(decoded, str):
                        return decoded
                    return f"Node_{hash_str[:8]}"
                except Exception:
                    return f"BinaryNode_{hash_str[:8]}"
        return f"EmptyNode_{hash_str[:8]}"

    # ------------------------------------------------------------------ #
    # Cache-aware helpers                                                #
    # ------------------------------------------------------------------ #

    def get_cached_status(self) -> Dict[str, Any]:
        """Return cached status information used by the status API."""
        with self._cache_lock:
            now = time.time()

            if (
                self._status_cache is not None
                and self._status_cache_time is not None
                and now - self._status_cache_time < self.cache_duration
            ):
                return self._status_cache

            app_uptime = now - self.start_time
            has_nodes = bool(self.nomadnet_nodes)
            time_since_last_announce = (
                now - self.last_announce_time if self.last_announce_time else None
            )

            self._status_cache = {
                "app_uptime": app_uptime,
                "has_nodes": has_nodes,
                "time_since_last_announce": time_since_last_announce,
                "node_count": len(self.nomadnet_nodes),
                "announce_count": self.announce_count,
                "connection_state": getattr(self, "connection_state", "connected"),
                "reticulum_ready": getattr(self, "reticulum_ready", False),
            }
            self._status_cache_time = now
            return self._status_cache

    def get_nodes(self):
        current_time = datetime.now()
        for node in self.nomadnet_nodes.values():
            last_seen = datetime.fromisoformat(node["last_seen"])
            diff = current_time - last_seen

            if diff.total_seconds() < 60:
                node["last_seen_relative"] = "Just now"
            elif diff.total_seconds() < 3600:
                minutes = int(diff.total_seconds() / 60)
                node["last_seen_relative"] = f"{minutes}m ago"
            else:
                hours = int(diff.total_seconds() / 3600)
                node["last_seen_relative"] = f"{hours}h ago"

        return list(self.nomadnet_nodes.values())

    # ------------------------------------------------------------------ #
    # Page & file access                                                 #
    # ------------------------------------------------------------------ #

    def fetch_file(self, node_hash: str, file_path: str) -> Dict[str, Any]:
        """Fetch a file from a NomadNet node."""
        try:
            print(f"📁 NomadNetWebBrowser.fetch_file called: {file_path} from {node_hash[:16]}...")
            browser = NomadNetFileBrowser(self, node_hash)
            return browser.fetch_file(file_path)
        except Exception as exc:
            print(f"❌ File fetch failed: {exc}")
            return {"error": f"File fetch failed: {exc}", "content": b"", "status": "error"}

    def fetch_page(
        self,
        node_hash: str,
        page_path: str = "/page/index.mu",
        form_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Fetch a NomadNet page, reusing cached links whenever possible."""
        try:
            print(f"Fetching {page_path} from {node_hash[:16]}...")
            destination_hash = _clean_hash(node_hash)

            cached_link = self.nomadnet_cached_links.get(destination_hash)
            if cached_link and cached_link.status == RNS.Link.ACTIVE:
                print("Using existing cached link for page request")
                return self._request_via_cached_link(cached_link, page_path, form_data)

            print("Creating new browser instance (no cached link available)")
            browser = NomadNetBrowser(self, node_hash)
            response = browser.fetch_page(page_path, form_data)

            if response["status"] == "success" and getattr(browser, "link", None):
                self.nomadnet_cached_links[destination_hash] = browser.link
                print("Stored new link in cache")

            return response

        except Exception as exc:
            print(f"Fetch failed: {exc}")
            return {"error": f"Fetch failed: {exc}", "content": "", "status": "error"}

    def _request_via_cached_link(
        self,
        link: RNS.Link,
        page_path: str,
        form_data: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        processed_form_data = self._prepare_form_data(form_data)
        final_form_data = dict(processed_form_data)

        if getattr(link, "fingerprint_data", None):
            final_form_data.update(link.fingerprint_data)
            print(f"Including fingerprint data (no field_ prefix): {link.fingerprint_data}")

        print(f"Final form data being sent: {final_form_data}")

        result = {"data": None, "received": False}
        response_event = threading.Event()

        def on_response(receipt):
            try:
                if receipt.response:
                    data = receipt.response
                    if isinstance(data, bytes):
                        result["data"] = data.decode("utf-8")
                    else:
                        result["data"] = str(data)
                else:
                    result["data"] = "Empty response"
                result["received"] = True
                response_event.set()
            except Exception as exc:
                result["data"] = f"Response error: {exc}"
                result["received"] = True
                response_event.set()

        def on_failed(_receipt):
            result["data"] = "Request failed"
            result["received"] = True
            response_event.set()

        link.request(
            page_path,
            data=final_form_data or None,
            response_callback=on_response,
            failed_callback=on_failed,
        )

        success = response_event.wait(timeout=30)
        if success and result["received"]:
            return {"content": result["data"] or "Empty response", "status": "success", "error": None}

        return {"error": "Timeout", "content": "Request timeout on cached link", "status": "error"}

    @staticmethod
    def _prepare_form_data(form_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not form_data:
            return {}

        processed: Dict[str, Any] = {}
        for key, value in form_data.items():
            if key.startswith("field_") or key.startswith("var_"):
                processed[key] = value
            else:
                processed[f"field_{key}"] = value
        print(f"Processed form data: {processed}")
        return processed

    # ------------------------------------------------------------------ #
    # Misc helpers                                                       #
    # ------------------------------------------------------------------ #

    def start_monitoring(self) -> None:
        self.running = True
        print("=" * 90)
        print("📡 Started NomadNet announce monitoring")
        print("=" * 90)

    def get_node_hops(self, destination_hash: str) -> Dict[str, Any]:
        """Get the number of hops to a destination."""
        try:
            dest_hash = _clean_hash(destination_hash) if isinstance(destination_hash, str) else destination_hash
            hops = RNS.Transport.hops_to(dest_hash)

            try:
                next_hop_hash = RNS.Transport.next_hop(dest_hash)
                if next_hop_hash:
                    next_hop_if = RNS.Transport.next_hop_interface(dest_hash)
                    if next_hop_if and hasattr(next_hop_if, "name"):
                        next_hop_info = f"via {next_hop_if.name}"
                    else:
                        next_hop_info = f"via {RNS.prettyhexrep(next_hop_hash)[:16]}..."
                else:
                    next_hop_info = "Unknown"
            except Exception as exc:
                print(f"Error using next_hop functions: {exc}")
                next_hop_info = "Unknown"

            if next_hop_info == "Unknown" and hasattr(RNS.Transport, "path_table"):
                path_entry = RNS.Transport.path_table.get(dest_hash)  # type: ignore[attr-defined]
                if path_entry:
                    for attr in ["next_hop", "via", "interface", "receiving_interface"]:
                        if hasattr(path_entry, attr):
                            value = getattr(path_entry, attr)
                            if value and hasattr(value, "name"):
                                next_hop_info = f"via {value.name}"
                                break
                            if isinstance(value, bytes):
                                next_hop_info = f"via {RNS.prettyhexrep(value)[:16]}..."
                                break

            return {"hops": hops if hops is not None else "Unknown", "next_hop_interface": next_hop_info}

        except Exception as exc:
            print(f"Error getting path info to {destination_hash}: {exc}")
            return {"hops": "Unknown", "next_hop_interface": "Unknown"}

    def get_node_path_info(self, destination_hash: str) -> Dict[str, Any]:
        """Backward compatible alias used by the API routes."""
        return self.get_node_hops(destination_hash)

    def send_fingerprint(self, node_hash: str) -> Dict[str, Any]:
        """Send identity fingerprint to a NomadNet node."""
        try:
            print(f"NomadNetWebBrowser.send_fingerprint called for {node_hash[:16]}...")
            browser = NomadNetBrowser(self, node_hash)
            return browser.send_fingerprint()
        except Exception as exc:
            print(f"Identity fingerprint send failed: {exc}")
            return {"error": f"Identity fingerprint send failed: {exc}", "message": "", "status": "error"}

    def ping_node(self, node_hash: str) -> Dict[str, Any]:
        """Ping a NomadNet node to check reachability."""
        try:
            print(f"Pinging node {node_hash[:16]}...")
            browser = NomadNetBrowser(self, node_hash)
            return browser.send_ping()
        except Exception as exc:
            print(f"Ping failed: {exc}")
            return {"error": f"Ping failed: {exc}", "message": "", "status": "error"}


__all__ = ["NomadNetWebBrowser"]
