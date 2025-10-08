"""
Cache management helpers for rBrowser.

The caching logic used to live inside the monolithic rBrowser module. It now
resides here so it can evolve independently from the Flask routes and NomadNet
communication stacks.
"""

from __future__ import annotations

import json
import queue
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple

from .nomadnet import NomadNetBrowser


CacheTask = Tuple[str, str, str]


class CacheManager:
    """Handle caching of NomadNet pages and related maintenance."""

    DEFAULT_SETTINGS = {
        "auto_cache_enabled": True,
        "size_limit_mb": 100,
        "expiry_days": 30,
        "search_limit": 50,
        "cache_additional": False,
    }

    ADDITIONAL_PAGES = [
        "/page/home.mu",
        "/page/about.mu",
        "/page/menu.mu",
        "/page/info.mu",
        "/page/contact.mu",
        "/page/help.mu",
        "/page/messageboard/messageboard.mu",
        "/page/messageboard.mu",
        "/page/links.mu",
        "/page/faq.mu",
        "/page/files.mu",
        "/page/boards.mu",
        "/page/nomadForum/index.mu",
        "/page/archive.mu",
    ]

    def __init__(self, browser: "NomadNetWebBrowser", cache_root: str = "cache/nodes") -> None:
        self.browser = browser
        self.cache_dir = Path(cache_root)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.settings: Dict[str, object] = dict(self.DEFAULT_SETTINGS)
        self.cache_queue: "queue.Queue[CacheTask]" = queue.Queue()
        self.additional_cache_queue: "queue.Queue[Tuple[str, str]]" = queue.Queue()

        self._load_settings()

        self.cache_worker_thread = threading.Thread(target=self._cache_worker, daemon=True)
        self.cache_worker_thread.start()

        self.additional_cache_worker_thread = threading.Thread(
            target=self._additional_cache_worker,
            daemon=True,
        )
        self.additional_cache_worker_thread.start()

        print("✅ Cache worker threads started")

    # ------------------------------------------------------------------ #
    # Public API                                                         #
    # ------------------------------------------------------------------ #

    def schedule_node(self, node_hash: str, node_name: str) -> None:
        """
        Inspect cache state and queue work if required.

        This mirrors the legacy behaviour from the monolithic script while
        making the decision process easier to test and extend.
        """
        cache_path = self.cache_dir / node_hash
        index_file = cache_path / "index.mu"

        should_cache = False
        should_cache_additional = False

        if not cache_path.exists():
            should_cache = True
            print(f"🔄 Queuing {node_name} for caching (new node)...")
        elif not index_file.exists():
            should_cache = True
            print(f"🔄 Queuing {node_name} for re-caching (missing index)...")
        else:
            try:
                content = index_file.read_text(encoding="utf-8", errors="ignore")
                if len(content.strip()) < 10:
                    should_cache = True
                    print(f"🔄 Queuing {node_name} for re-caching (empty content)...")
                elif self.settings.get("cache_additional", False):
                    pages_dir = cache_path / "pages"
                    mu_files = list(pages_dir.glob("*.mu")) if pages_dir.exists() else []
                    if not mu_files:
                        should_cache_additional = True
                        print(f"🔄 Queuing {node_name} for additional page caching...")
            except Exception:
                should_cache = True
                print(f"🔄 Queuing {node_name} for re-caching (read error)...")

        auto_enabled = bool(self.settings.get("auto_cache_enabled", True))

        if should_cache and auto_enabled:
            self.enqueue_cache(node_hash, node_name)
        elif should_cache_additional and auto_enabled:
            self.enqueue_additional(node_hash, node_name)
        elif should_cache:
            print(f"⏸️ Auto-caching disabled, skipping {node_name}")
        elif should_cache_additional:
            print(f"⏸️ Auto-caching disabled, skipping additional pages for {node_name}")
        else:
            print(f"📁 {node_name} already cached, skipping...")

    def enqueue_cache(self, node_hash: str, node_name: str, page_path: str = "/page/index.mu") -> None:
        """Queue a node for caching regardless of current state."""
        self.cache_queue.put((node_hash, node_name, page_path))

    def enqueue_additional(self, node_hash: str, node_name: str) -> None:
        """Queue a node for caching additional pages."""
        self.additional_cache_queue.put((node_hash, node_name))

    def save_settings(self) -> None:
        """Persist cache settings to disk."""
        settings_dir = Path("settings")
        settings_dir.mkdir(exist_ok=True)
        settings_file = settings_dir / "cache_settings.json"

        with settings_file.open("w") as handle:
            json.dump(self.settings, handle, indent=2)
        print(f"💾 Saved cache settings: {self.settings}")

    def clear_cache(self) -> None:
        """Remove the entire cache directory tree."""
        if self.cache_dir.exists():
            import shutil

            shutil.rmtree(self.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def iter_cached_nodes(self) -> Iterable[Path]:
        """Yield all node cache directories."""
        if not self.cache_dir.exists():
            return []
        return (item for item in self.cache_dir.iterdir() if item.is_dir())

    def enforce_size_limit(self) -> None:
        """Remove oldest cache entries if the size limit is exceeded."""
        size_limit_mb = int(self.settings.get("size_limit_mb", -1))
        if size_limit_mb == -1 or not self.cache_dir.exists():
            return

        total_size = 0
        cache_entries = []

        for node_dir in self.iter_cached_nodes():
            dir_size = sum(file.stat().st_size for file in node_dir.rglob("*") if file.is_file())
            cached_at_file = node_dir / "cached_at.txt"

            try:
                cache_time = datetime.fromisoformat(cached_at_file.read_text().strip())
            except Exception:
                cache_time = datetime.now()

            total_size += dir_size
            cache_entries.append({"path": node_dir, "size": dir_size, "time": cache_time})

        size_limit_bytes = size_limit_mb * 1024 * 1024
        if total_size <= size_limit_bytes:
            return

        cache_entries.sort(key=lambda item: item["time"])
        print(
            f"🗑️ Cache size {total_size // (1024 * 1024)}MB exceeds limit {size_limit_mb}MB, removing old entries..."
        )

        for entry in cache_entries:
            if total_size <= size_limit_bytes:
                break
            try:
                import shutil

                shutil.rmtree(entry["path"])
                total_size -= entry["size"]
                print(f"🗑️ Removed old cache: {entry['path'].name} ({entry['size'] // 1024} KB)")
            except Exception as exc:
                print(f"Error removing cache {entry['path']}: {exc}")

    def cleanup_expired_cache(self) -> None:
        """Remove cache entries older than the configured expiry."""
        expiry_days = int(self.settings.get("expiry_days", -1))
        if expiry_days == -1 or not self.cache_dir.exists():
            return

        cutoff_date = datetime.now() - timedelta(days=expiry_days)
        removed_count = 0

        for node_dir in self.iter_cached_nodes():
            cached_at_file = node_dir / "cached_at.txt"
            if not cached_at_file.exists():
                continue

            try:
                cache_time = datetime.fromisoformat(cached_at_file.read_text().strip())
            except Exception as exc:
                print(f"Error processing cache expiry for {node_dir}: {exc}")
                continue

            if cache_time < cutoff_date:
                try:
                    import shutil

                    shutil.rmtree(node_dir)
                    removed_count += 1
                    print(f"🗑️ Expired cache removed: {node_dir.name}")
                except Exception as exc:
                    print(f"Error removing cache {node_dir}: {exc}")

        if removed_count:
            print(f"🧹 Removed {removed_count} expired cache entries")

    def cache_additional_pages(self, node_hash: str, node_name: str) -> None:
        """Cache the extra set of pages for a node."""
        if not self.settings.get("cache_additional", False):
            print(f"DEBUG: Additional caching disabled, skipping {node_name}")
            return

        print(f"📑 Starting additional page caching for {node_name}...")
        cache_dir = self.cache_dir / node_hash
        cache_dir.mkdir(parents=True, exist_ok=True)

        for page_path in self.ADDITIONAL_PAGES:
            try:
                print(f"📄 Trying to cache: {page_path}")
                browser = NomadNetBrowser(self.browser, node_hash)
                response = browser.fetch_page(page_path)

                if response["status"] != "success" or not response["content"].strip():
                    print(f"⚠️ Additional page not found or empty: {page_path}")
                    continue

                pages_dir = cache_dir / "pages"
                pages_dir.mkdir(exist_ok=True)

                filename = page_path.replace("/page/", "").replace(".mu", "") + ".mu"
                page_file = pages_dir / filename
                page_file.write_text(response["content"], encoding="utf-8")
                print(f"📄 Cached additional page: {page_path}")

            except Exception as exc:
                print(f"❌ Failed to cache additional page {page_path}: {exc}")

    # ------------------------------------------------------------------ #
    # Internal helpers                                                   #
    # ------------------------------------------------------------------ #

    def _cache_worker(self) -> None:
        """Process the cache queue in the background."""
        while True:
            try:
                node_hash, node_name, page_path = self.cache_queue.get(timeout=5)
                self.cache_single_page(node_hash, node_name, page_path)
                self.cache_queue.task_done()
            except queue.Empty:
                continue
            except Exception as exc:
                print(f"Cache worker error: {exc}")

    def _additional_cache_worker(self) -> None:
        print("🔧 Additional cache worker started")
        while True:
            try:
                node_hash, node_name = self.additional_cache_queue.get(timeout=5)
                print(f"🔧 Additional cache worker processing: {node_name}")
                self.cache_additional_pages(node_hash, node_name)
                self.additional_cache_queue.task_done()
            except queue.Empty:
                continue
            except Exception as exc:
                print(f"❌ Additional cache worker error: {exc}")

    def cache_single_page(self, node_hash: str, node_name: str, page_path: str) -> None:
        """Download and persist a single page to the cache."""
        try:
            print(f"📥 Attempting to cache page from {node_name} ({node_hash[:16]}...)")
            print(f"🔧 Additional caching setting: {self.settings.get('cache_additional', False)}")
            print(f"🔧 Page path: {page_path}")

            browser = NomadNetBrowser(self.browser, node_hash)
            response = browser.fetch_page(page_path)
            print(f"📋 Response status: {response['status']}")

            if response["status"] != "success":
                print(f"❌ Failed to fetch page: {response.get('error', 'Unknown error')}")
                return

            cache_dir = self.cache_dir / node_hash
            cache_dir.mkdir(parents=True, exist_ok=True)
            print(f"📂 Created cache directory: {cache_dir}")

            self._write_cache_files(cache_dir, node_name, response["content"])
            print(f"📄 Saved {len(response['content'])} characters to {cache_dir / 'index.mu'}")
            print(f"✅ Successfully cached page from {node_name}")

            if (
                self.settings.get("cache_additional", False)
                and page_path == "/page/index.mu"
            ):
                print(f"📑 Triggering additional page caching for {node_name}")
                self.enqueue_additional(node_hash, node_name)

            self.enforce_size_limit()
            self.cleanup_expired_cache()

        except Exception as exc:
            print(f"❌ Exception caching page from {node_name}: {exc}")
            import traceback

            traceback.print_exc()

    def _write_cache_files(self, cache_dir: Path, node_name: str, content: str) -> None:
        """Persist the fetched content with sensible encoding fallbacks."""
        try:
            (cache_dir / "index.mu").write_text(content, encoding="utf-8")
            (cache_dir / "node_name.txt").write_text(node_name, encoding="utf-8")
            (cache_dir / "cached_at.txt").write_text(str(datetime.now()), encoding="utf-8")
        except UnicodeEncodeError:
            safe_content = content.encode("utf-8", errors="replace").decode("utf-8")
            safe_name = node_name.encode("utf-8", errors="replace").decode("utf-8")

            (cache_dir / "index.mu").write_text(safe_content, encoding="utf-8")
            (cache_dir / "node_name.txt").write_text(safe_name, encoding="utf-8")
            (cache_dir / "cached_at.txt").write_text(str(datetime.now()), encoding="utf-8")
            print(f"✅ Successfully cached page from {safe_name} (with character replacements)")

    def _load_settings(self) -> None:
        settings_dir = Path("settings")
        settings_dir.mkdir(exist_ok=True)
        settings_file = settings_dir / "cache_settings.json"

        if settings_file.exists():
            try:
                with settings_file.open("r") as handle:
                    saved_settings = json.load(handle)
                self.settings.update(saved_settings)
                print(f"📋 Loaded cache settings: {self.settings}")
            except Exception as exc:
                print(f"Error loading cache settings: {exc}")


from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from .web_browser import NomadNetWebBrowser
