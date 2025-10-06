#!/usr/bin/env python3

import os
import sys
import time
import threading
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_from_directory, Response, send_file
import mimetypes
import io
import RNS
import RNS.vendor.umsgpack as msgpack
import secrets
from pathlib import Path
import queue
import argparse

# Ensure UTF-8 output for Windows console
if sys.platform == "win32":
    try:
        # Try to set UTF-8 encoding for console output
        os.system('chcp 65001 >nul')  # Set Windows console to UTF-8
    except:
        pass

app = Flask(__name__)
app.secret_key = secrets.token_hex(16) # needed for flask sessions

class NomadNetBrowser:
    def __init__(self, main_browser, destination_hash):
        self.main_browser = main_browser
        clean_hash = destination_hash.replace("<", "").replace(">", "").replace(":", "")
        self.destination_hash = bytes.fromhex(clean_hash)
        
    def fetch_page(self, page_path="/page/index.mu", form_data=None, timeout=30):
        try:
            print(f"🔍 Checking path to {RNS.prettyhexrep(self.destination_hash)[:16]}...")
            
            if not RNS.Transport.has_path(self.destination_hash):
                print(f"📡 Requesting path to {RNS.prettyhexrep(self.destination_hash)[:16]}...")
                RNS.Transport.request_path(self.destination_hash)
                start_time = time.time()
                while not RNS.Transport.has_path(self.destination_hash):
                    if time.time() - start_time > 30:
                        return {"error": "No path", "content": "No path to destination", "status": "error"}
                    time.sleep(0.1)
            
            print(f"✅ Path found, establishing connection...")
            identity = RNS.Identity.recall(self.destination_hash)
            if not identity:
                return {"error": "No identity", "content": "Could not recall identity", "status": "error"}
            
            self.destination = RNS.Destination(identity, RNS.Destination.OUT, RNS.Destination.SINGLE, "nomadnetwork", "node")
            self.link = RNS.Link(self.destination)
            self.result = {"data": None, "received": False}
            self.response_event = threading.Event()
            self.page_path = page_path
            self.form_data = form_data  # Store form data for use in callback
            
            if form_data:
                print(f"🌐 Requesting page: {page_path} with form data: {form_data}")
            else:
                print(f"🌐 Requesting page: {page_path}")
            
            self.link.set_link_established_callback(self._on_link_established)
            success = self.response_event.wait(timeout=timeout)
            
            if success and self.result["received"]:
                return {"content": self.result["data"] or "Empty response", "status": "success", "error": None}
            else:
                return {"error": "Timeout", "content": "Request timeout", "status": "error"}
                
        except Exception as e:
            print(f"❌ Exception during fetch: {str(e)}")
            return {"error": str(e), "content": f"Exception: {str(e)}", "status": "error"}

    def _on_link_established(self, link):
        try:
            if hasattr(self, 'form_data') and self.form_data:
                print(f"🔗 Link established, requesting: {self.page_path} with field_data: {self.form_data}")
                
                # UPDATED: Handle both field_ and var_ prefixes
                # Some NomadNet applications expect variables with var_ prefix instead of field_
                prefixed_form_data = {}
                for key, value in self.form_data.items():
                    # Try both var_ and field_ prefixes
                    prefixed_form_data[f"var_{key}"] = str(value)
                    prefixed_form_data[f"field_{key}"] = str(value)
                
                print(f"📝 Prefixed form data: {prefixed_form_data}")
                
                # Send the prefixed form data as a dictionary
                link.request(self.page_path, data=prefixed_form_data, response_callback=self._on_response, failed_callback=self._on_request_failed)
                
            else:
                print(f"🔗 Link established, requesting: {self.page_path}")
                link.request(self.page_path, data=None, response_callback=self._on_response, failed_callback=self._on_request_failed)
                
        except Exception as e:
            print(f"❌ Request error: {str(e)}")
            self.result["data"] = f"Request error: {str(e)}"
            self.result["received"] = True
            self.response_event.set()

    def _on_response(self, receipt):
        try:
            if receipt.response:
                data = receipt.response
                if isinstance(data, bytes):
                    try:
                        self.result["data"] = data.decode("utf-8")
                        print(f"✅ Received {len(self.result['data'])} characters")
                    except UnicodeDecodeError:
                        self.result["data"] = f"Binary data: {data.hex()[:200]}..."
                        print(f"⚠️ Received binary data: {len(data)} bytes")
                else:
                    self.result["data"] = str(data)
                    print(f"✅ Received text data: {len(str(data))} characters")
            else:
                self.result["data"] = "Empty response"
                print("⚠️ Empty response received")
            self.result["received"] = True
            self.response_event.set()
        except Exception as e:
            print(f"❌ Response processing error: {str(e)}")
            self.result["data"] = f"Response error: {str(e)}"
            self.result["received"] = True
            self.response_event.set()
    
    def _on_request_failed(self, receipt):
        print("❌ Request failed")
        self.result["data"] = "Request failed"
        self.result["received"] = True
        self.response_event.set()

    def ping_node(self, node_hash):
        """Ping a NomadNet node to check reachability"""
        try:
            print(f"Pinging node {node_hash[:16]}...")
            browser = NomadNetBrowser(self, node_hash)
            response = browser.send_ping()
            return response
        except Exception as e:
            print(f"Ping failed: {str(e)}")
            return {"error": f"Ping failed: {str(e)}", "message": "", "status": "error"}
            
    def send_ping(self, timeout=15):
        """Send a ping to test node reachability"""
        try:
            print(f"Pinging {RNS.prettyhexrep(self.destination_hash)[:16]}...")
            
            if not RNS.Transport.has_path(self.destination_hash):
                print(f"📡 Requesting path for ping...")
                RNS.Transport.request_path(self.destination_hash)
                start_time = time.time()
                while not RNS.Transport.has_path(self.destination_hash):
                    if time.time() - start_time > 30:
                        return {"error": "No path", "message": "No path to destination", "status": "error"}
                    time.sleep(0.1)
            
            print(f"✅ Path found, measuring round-trip time...")
            ping_start = time.time()
            
            identity = RNS.Identity.recall(self.destination_hash)
            if not identity:
                return {"error": "No identity", "message": "Could not recall identity", "status": "error"}
            
            self.destination = RNS.Destination(identity, RNS.Destination.OUT, RNS.Destination.SINGLE, "nomadnetwork", "node")
            self.link = RNS.Link(self.destination)
            self.result = {"data": None, "received": False, "rtt": None}
            self.response_event = threading.Event()
            self.ping_start_time = ping_start
            
            self.link.set_link_established_callback(self._on_ping_link_established)
            success = self.response_event.wait(timeout=timeout)
            
            if success and self.result["received"]:
                rtt = self.result.get("rtt", 0)
                return {
                    "message": f"Pong received! Round-trip time: {rtt:.2f}s",
                    "rtt": rtt,
                    "status": "success",
                    "error": None
                }
            else:
                return {"error": "Timeout", "message": "Ping timeout", "status": "error"}
                
        except Exception as e:
            print(f"❌ Exception during ping: {str(e)}")
            return {"error": str(e), "message": f"Exception: {str(e)}", "status": "error"}

    def _on_ping_link_established(self, link):
        try:
            print(f"🔗 Ping link established, sending ping request...")
            # Simple ping - just request the index page but measure RTT
            link.request("/page/index.mu", data=None, 
                        response_callback=self._on_ping_response, 
                        failed_callback=self._on_ping_failed)
        except Exception as e:
            print(f"❌ Ping request error: {str(e)}")
            self.result["received"] = True
            self.response_event.set()

    def _on_ping_response(self, receipt):
        try:
            rtt = time.time() - self.ping_start_time
            self.result["rtt"] = rtt
            self.result["received"] = True
            print(f"✅ Pong! RTT: {rtt:.2f}s")
            self.response_event.set()
        except Exception as e:
            print(f"❌ Ping response error: {str(e)}")
            self.result["received"] = True
            self.response_event.set()

    def _on_ping_failed(self, receipt):
        print("❌ Ping failed")
        self.result["received"] = True
        self.response_event.set()

    def send_fingerprint(self, timeout=30):
        """Send fingerprint using RNS link.identify() like MeshChat does"""
        try:
            print(f"Sending fingerprint to {RNS.prettyhexrep(self.destination_hash)[:16]}...")
            
            # Get or create cached link
            if hasattr(self.main_browser, 'nomadnet_cached_links') and self.destination_hash in self.main_browser.nomadnet_cached_links:
                existing_link = self.main_browser.nomadnet_cached_links[self.destination_hash]
                if existing_link.status == RNS.Link.ACTIVE:
                    print("Using existing cached link for identity establishment")
                    # Use RNS protocol-level identity establishment
                    existing_link.identify(self.main_browser.identity)
                    
                    # Also store LXMF destination for 'dest' variable
                    lxmf_dest_hash = RNS.Destination.hash(self.main_browser.identity, "lxmf", "delivery")
                    existing_link.fingerprint_data = {"dest": lxmf_dest_hash.hex()}
                    
                    print(f"Identity established on link: {RNS.prettyhexrep(self.main_browser.identity.hash)}")
                    print(f"LXMF dest stored: {lxmf_dest_hash.hex()}")
                    
                    return {"message": "Identity established on existing link", "status": "success", "error": None}
            
            # If no existing link, we need to create one first by making a page request
            # Then establish identity on that link
            response = self.main_browser.fetch_page(self.destination_hash.hex(), "/page/index.mu")
            
            if response["status"] == "success":
                # Now identify on the newly created cached link
                if self.destination_hash in self.main_browser.nomadnet_cached_links:
                    link = self.main_browser.nomadnet_cached_links[self.destination_hash]
                    link.identify(self.main_browser.identity)
                    
                    lxmf_dest_hash = RNS.Destination.hash(self.main_browser.identity, "lxmf", "delivery")
                    link.fingerprint_data = {"dest": lxmf_dest_hash.hex()}
                    
                    print(f"Identity established on new link: {RNS.prettyhexrep(self.main_browser.identity.hash)}")
                    
                    return {"message": "Identity established on new link", "status": "success", "error": None}
            
            return {"error": "Failed to establish link", "message": "Could not create or identify on link", "status": "error"}
                
        except Exception as e:
            print(f"Exception during fingerprint send: {str(e)}")
            return {"error": str(e), "message": f"Exception: {str(e)}", "status": "error"}
        
class NomadNetFileBrowser:
    def __init__(self, main_browser, destination_hash):
        self.main_browser = main_browser
        clean_hash = destination_hash.replace("<", "").replace(">", "").replace(":", "")
        self.destination_hash = bytes.fromhex(clean_hash)
        
    def fetch_file(self, file_path, timeout=60):  # Longer timeout for files
        try:
            print(f"🔍 Checking path to {RNS.prettyhexrep(self.destination_hash)[:16]} for file...")
            
            if not RNS.Transport.has_path(self.destination_hash):
                print(f"📡 Requesting path to {RNS.prettyhexrep(self.destination_hash)[:16]}...")
                RNS.Transport.request_path(self.destination_hash)
                start_time = time.time()
                while not RNS.Transport.has_path(self.destination_hash):
                    if time.time() - start_time > 30:
                        return {"error": "No path", "content": b"", "status": "error"}
                    time.sleep(0.1)
            
            print(f"✅ Path found, establishing connection for file transfer...")
            identity = RNS.Identity.recall(self.destination_hash)
            if not identity:
                return {"error": "No identity", "content": b"", "status": "error"}
            
            self.destination = RNS.Destination(identity, RNS.Destination.OUT, RNS.Destination.SINGLE, "nomadnetwork", "node")
            self.link = RNS.Link(self.destination)
            self.result = {"data": None, "received": False}
            self.response_event = threading.Event()
            self.file_path = file_path
            
            print(f"📁 Requesting file: {file_path}")
            self.link.set_link_established_callback(self._on_link_established)
            success = self.response_event.wait(timeout=timeout)
            
            if success and self.result["received"]:
                return {"content": self.result["data"] or b"", "status": "success", "error": None}
            else:
                return {"error": "Timeout", "content": b"", "status": "error"}
                
        except Exception as e:
            print(f"❌ Exception during file fetch: {str(e)}")
            return {"error": str(e), "content": b"", "status": "error"}
    
    def _on_link_established(self, link):
        try:
            print(f"🔗 Link established, requesting file: {self.file_path}")
            link.request(self.file_path, data=None, response_callback=self._on_response, failed_callback=self._on_request_failed)
        except Exception as e:
            print(f"❌ File request error: {str(e)}")
            self.result["data"] = b""
            self.result["received"] = True
            self.response_event.set()

    def _on_response(self, receipt):
        try:
            if receipt.response:
                data = receipt.response
                print(f"📁 Received response type: {type(data)}")
                # Don't print the actual data content for binary files to avoid terminal corruption
                
                if isinstance(data, bytes):
                    self.result["data"] = data
                    print(f"✅ Received file data: {len(data)} bytes")
                elif isinstance(data, str):
                    # For text files, encode to UTF-8
                    self.result["data"] = data.encode('utf-8')
                    print(f"✅ Received text file: {len(data)} characters")
                elif isinstance(data, list):
                    # Handle list response - this is likely where the corruption happens
                    try:
                        # Check if it's a list of bytes
                        if all(isinstance(item, bytes) for item in data):
                            self.result["data"] = b''.join(data)
                            print(f"✅ Joined {len(data)} byte chunks: {len(self.result['data'])} total bytes")
                        else:
                            # This might be the problem - don't convert to string for binary files
                            print(f"❌ Unexpected list content types: {[type(item) for item in data[:3]]}")
                            # Try to handle mixed content more carefully
                            binary_parts = []
                            for item in data:
                                if isinstance(item, bytes):
                                    binary_parts.append(item)
                                elif isinstance(item, str):
                                    # This might corrupt binary data - be very careful
                                    binary_parts.append(item.encode('latin1'))  # Use latin1 to preserve byte values
                                else:
                                    print(f"⚠️ Unexpected item type: {type(item)}")
                            
                            self.result["data"] = b''.join(binary_parts)
                            print(f"✅ Processed mixed list: {len(self.result['data'])} total bytes")
                            
                    except Exception as list_error:
                        print(f"❌ Error processing list data: {list_error}")
                        self.result["data"] = b""
                elif hasattr(data, 'read'):
                    # Handle file objects
                    try:
                        if hasattr(data, 'seek'):
                            data.seek(0)
                        file_content = data.read()
                        
                        if isinstance(file_content, bytes):
                            self.result["data"] = file_content
                        else:
                            self.result["data"] = file_content.encode('latin1')  # Preserve binary data
                        
                        print(f"✅ Successfully read file: {len(self.result['data'])} bytes")
                        
                        if hasattr(data, 'close'):
                            data.close()
                    except Exception as read_error:
                        print(f"❌ Error reading file object: {read_error}")
                        self.result["data"] = b""
                else:
                    print(f"❌ Unknown data type: {type(data)}")
                    self.result["data"] = b""
            else:
                self.result["data"] = b""
                print("⚠️ Empty file response received")
                
            self.result["received"] = True
            self.response_event.set()
        except Exception as e:
            print(f"❌ File response processing error: {str(e)}")
            self.result["data"] = b""
            self.result["received"] = True
            self.response_event.set()    

    def _on_request_failed(self, receipt):
        print("❌ File request failed")
        self.result["data"] = b""
        self.result["received"] = True
        self.response_event.set()


class NomadNetAnnounceHandler:
    def __init__(self, browser):
        self.browser = browser
        self.aspect_filter = "nomadnetwork.node"
        
    def received_announce(self, destination_hash, announced_identity, app_data):
        self.browser.process_nomadnet_announce(destination_hash, announced_identity, app_data)

class NomadNetWebBrowser:
    def __init__(self):
        self.reticulum = None
        self.identity = None
        self.nomadnet_nodes = {}
        self.running = False
        self.announce_count = 0
        self.start_time = time.time()
        self._status_cache = None
        self._status_cache_time = None  
        self._nodes_cache = None
        self._nodes_cache_time = None
        self._cache_lock = threading.Lock()
        self.cache_duration = 1.0
        self.connection_state = "initializing"
        self.last_announce_time = None
        self.reticulum_ready = False
        self.start_time = time.time()
        self.nomadnet_cached_links = {}
        self.cache_queue = queue.Queue()
        self.cache_dir = Path("cache/nodes")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        # search engine system page cache
        self.cache_worker_thread = threading.Thread(target=self.background_cache_worker, daemon=True)
        self.cache_worker_thread.start()
        # search engine system cache settings
        self.cache_settings = {
            'auto_cache_enabled': True,
            'size_limit_mb': 100,
            'expiry_days': 30,
            'search_limit': 50,
            'cache_additional': False
        }
        self.load_cache_settings()
        self.additional_cache_queue = queue.Queue()
        self.additional_cache_worker_thread = threading.Thread(target=self.additional_cache_worker, daemon=True)
        self.additional_cache_worker_thread.start()
        print("✅ Cache worker threads started")    
        
        print("=" * 90)
        print("🌐 rBrowser v1.0 - Standalone Nomadnet Browser - https://github.com/fr33n0w/rBrowser")
        print("=" * 90)
        print("⚡ Initializing rBrowser v1.0 NomadNet Web Browser...")
        print("📋 RNS LOG LEVEL SET TO: CRITICAL")
        print("🔗 Connecting to Reticulum...")
        print("=" * 90)
        self.init_reticulum()

    def additional_cache_worker(self):
        """Worker thread specifically for caching additional pages"""
        print("🔧 Additional cache worker started")
        while True:
            try:
                node_hash, node_name = self.additional_cache_queue.get(timeout=5)
                print(f"🔧 Additional cache worker processing: {node_name}")
                self.cache_additional_pages(node_hash, node_name)
                self.additional_cache_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"❌ Additional cache worker error: {e}")
                    
    def load_cache_settings(self):
        """Load settings from file"""
        settings_dir = Path("settings")
        settings_dir.mkdir(exist_ok=True)  # Create settings folder if it doesn't exist
        settings_file = settings_dir / "cache_settings.json"
        
        if settings_file.exists():
            try:
                import json
                with open(settings_file, 'r') as f:
                    saved_settings = json.load(f)
                    self.cache_settings.update(saved_settings)
                    print(f"📋 Loaded cache settings: {self.cache_settings}")
            except Exception as e:
                print(f"Error loading cache settings: {e}")

    def save_cache_settings(self):
        """Save settings to file"""
        try:
            import json
            settings_dir = Path("settings")
            settings_dir.mkdir(exist_ok=True)  # Create settings folder if it doesn't exist
            settings_file = settings_dir / "cache_settings.json"
            
            with open(settings_file, 'w') as f:
                json.dump(self.cache_settings, f, indent=2)
            print(f"💾 Saved cache settings: {self.cache_settings}")
        except Exception as e:
            print(f"Error saving cache settings: {e}")
            
    def enforce_cache_size_limit(self):
        """Remove oldest cache entries if size limit is exceeded"""
        size_limit_mb = self.cache_settings.get('size_limit_mb', -1)
        if size_limit_mb == -1:  # Unlimited
            return
        
        if not self.cache_dir.exists():
            return
        
        # Calculate current cache size
        total_size = 0
        cache_entries = []
        
        for node_dir in self.cache_dir.iterdir():
            if node_dir.is_dir():
                dir_size = 0
                cached_at_file = node_dir / "cached_at.txt"
                
                # Get directory size
                for file in node_dir.rglob('*'):
                    if file.is_file():
                        dir_size += file.stat().st_size
                
                total_size += dir_size
                
                # Get cache timestamp
                cache_time = datetime.now()  # Default to now if no timestamp
                if cached_at_file.exists():
                    try:
                        cache_time = datetime.fromisoformat(cached_at_file.read_text().strip())
                    except:
                        pass
                
                cache_entries.append({
                    'path': node_dir,
                    'size': dir_size,
                    'time': cache_time
                })
        
        # Check if we exceed the limit
        size_limit_bytes = size_limit_mb * 1024 * 1024
        if total_size <= size_limit_bytes:
            return
        
        # Remove oldest entries until under limit
        cache_entries.sort(key=lambda x: x['time'])  # Oldest first
        
        for entry in cache_entries:
            if total_size <= size_limit_bytes:
                break
            
            try:
                import shutil
                shutil.rmtree(entry['path'])
                total_size -= entry['size']
                print(f"🗑️ Removed old cache: {entry['path'].name} ({entry['size'] // 1024} KB)")
            except Exception as e:
                print(f"Error removing cache {entry['path']}: {e}")

    def cleanup_expired_cache(self):
        """Remove cache entries older than expiry setting"""
        expiry_days = self.cache_settings.get('expiry_days', -1)
        if expiry_days == -1:  # Never expire
            return
        
        if not self.cache_dir.exists():
            return
        
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=expiry_days)
        removed_count = 0
        
        for node_dir in self.cache_dir.iterdir():
            if node_dir.is_dir():
                cached_at_file = node_dir / "cached_at.txt"
                
                if cached_at_file.exists():
                    try:
                        cache_time = datetime.fromisoformat(cached_at_file.read_text().strip())
                        if cache_time < cutoff_date:
                            import shutil
                            shutil.rmtree(node_dir)
                            removed_count += 1
                            print(f"🗑️ Expired cache removed: {node_dir.name}")
                    except Exception as e:
                        print(f"Error processing cache expiry for {node_dir}: {e}")
        
        if removed_count > 0:
            print(f"🧹 Removed {removed_count} expired cache entries")

    def cache_single_page(self, node_hash, node_name, page_path):
        try:
            print(f"📥 Attempting to cache page from {node_name} ({node_hash[:16]}...)")
            print(f"🔧 Additional caching setting: {self.cache_settings.get('cache_additional', False)}")
            print(f"🔧 Page path: {page_path}")
            
            browser = NomadNetBrowser(self, node_hash)
            response = browser.fetch_page(page_path)
            
            print(f"📋 Response status: {response['status']}")
            if response["status"] == "success":
                cache_dir = self.cache_dir / node_hash
                cache_dir.mkdir(parents=True, exist_ok=True)
                print(f"📂 Created cache directory: {cache_dir}")
                
                # Save files with explicit UTF-8 encoding
                try:
                    (cache_dir / "index.mu").write_text(response["content"], encoding='utf-8')
                    (cache_dir / "node_name.txt").write_text(node_name, encoding='utf-8')
                    (cache_dir / "cached_at.txt").write_text(str(datetime.now()), encoding='utf-8')
                    
                    print(f"📄 Saved {len(response['content'])} characters to {cache_dir / 'index.mu'}")
                    print(f"✅ Successfully cached page from {node_name}")
                    
                    # Check if we should cache additional pages
                    should_cache_additional = (
                        self.cache_settings.get('cache_additional', False) and 
                        page_path == "/page/index.mu"
                    )
                    print(f"🔧 Should cache additional: {should_cache_additional}")
                    
                    if should_cache_additional:
                        print(f"📑 Triggering additional page caching for {node_name}")
                        self.cache_additional_pages(node_hash, node_name)
                    
                    # Run cache maintenance after successful caching
                    self.enforce_cache_size_limit()
                    self.cleanup_expired_cache()
                    
                except UnicodeEncodeError as e:
                    # Fallback: save with error handling for problematic characters
                    safe_content = response["content"].encode('utf-8', errors='replace').decode('utf-8')
                    safe_node_name = node_name.encode('utf-8', errors='replace').decode('utf-8')
                    
                    (cache_dir / "index.mu").write_text(safe_content, encoding='utf-8')
                    (cache_dir / "node_name.txt").write_text(safe_node_name, encoding='utf-8')
                    (cache_dir / "cached_at.txt").write_text(str(datetime.now()), encoding='utf-8')
                    
                    print(f"✅ Successfully cached page from {safe_node_name} (with character replacements)")
                    
                    # Check if we should cache additional pages
                    should_cache_additional = (
                        self.cache_settings.get('cache_additional', False) and 
                        page_path == "/page/index.mu"
                    )
                    print(f"🔧 Should cache additional: {should_cache_additional}")
                    
                    if should_cache_additional:
                        print(f"📑 Triggering additional page caching for {safe_node_name}")
                        self.cache_additional_pages(node_hash, safe_node_name)
                    
                    # Run cache maintenance after successful caching
                    self.enforce_cache_size_limit()
                    self.cleanup_expired_cache()
                    
            else:
                print(f"❌ Failed to fetch page: {response.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Exception caching page from {node_name}: {e}")
            import traceback
            traceback.print_exc()



    def cache_additional_pages(self, node_hash, node_name):
        """Cache common additional pages from a node"""
        
        if not self.cache_settings.get('cache_additional', False):
            print(f"DEBUG: Additional caching disabled, skipping {node_name}")
            return
        
        additional_pages = [
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
            "/page/archive.mu"
        ]
        
        print(f"📑 Starting additional page caching for {node_name}...")
        cache_dir = self.cache_dir / node_hash
        
        for page_path in additional_pages:
            try:
                print(f"📄 Trying to cache: {page_path}")
                browser = NomadNetBrowser(self, node_hash)
                response = browser.fetch_page(page_path)
                
                if response["status"] == "success" and response["content"].strip():
                    # Create pages subdirectory
                    pages_dir = cache_dir / "pages"
                    pages_dir.mkdir(exist_ok=True)
                    
                    # Save the page (remove /page/ prefix and .mu extension for filename)
                    filename = page_path.replace("/page/", "").replace(".mu", "") + ".mu"
                    page_file = pages_dir / filename
                    
                    page_file.write_text(response["content"], encoding='utf-8')
                    print(f"📄 Cached additional page: {page_path}")
                else:
                    print(f"⚠️ Additional page not found or empty: {page_path}")
                    
            except Exception as e:
                print(f"❌ Failed to cache additional page {page_path}: {e}")

                    
    def init_reticulum(self):
        try:
            # Set initial connecting state
            self.connection_state = "connecting"
            
            print("🔗 Connecting to Reticulum...")
            RNS.loglevel = RNS.LOG_CRITICAL
            
            # Check if Reticulum is already initialized
            try:
                # Try to get existing instance first
                if hasattr(RNS.Reticulum, 'get_instance'):
                    self.reticulum = RNS.Reticulum.get_instance()
                    if self.reticulum:
                        print("🔄 Using existing Reticulum instance")
                    else:
                        # Create new instance if none exists
                        self.reticulum = RNS.Reticulum()
                else:
                    # Fallback for older RNS versions
                    self.reticulum = RNS.Reticulum()
                    
            except Exception as e:
                # If get_instance fails or doesn't exist, handle the reinitialize error
                if "reinitialise" in str(e).lower() or "already running" in str(e).lower():
                    print("⚠️ Reticulum already running - attempting to use existing instance...")
                    # Try to work with the existing instance
                    try:
                        self.reticulum = RNS.Reticulum.get_instance()
                        if not self.reticulum:
                            print("❌ Cannot access existing Reticulum instance")
                            print("   Try killing all Python processes first: sudo pkill python3")
                            sys.exit(1)
                        print("✅ Connected to existing Reticulum instance")
                    except:
                        print("❌ Failed to connect to existing Reticulum instance")
                        print("   Please restart the Pi or kill existing Reticulum processes")
                        sys.exit(1)
                else:
                    print(f"❌ Reticulum initialization failed: {e}")
                    sys.exit(1)
            
            identity_path = "nomadnet_browser_identity"
            if os.path.exists(identity_path):
                self.identity = RNS.Identity.from_file(identity_path)
            else:
                self.identity = RNS.Identity()
                self.identity.to_file(identity_path)
            
            self.nomadnet_handler = NomadNetAnnounceHandler(self)
            RNS.Transport.register_announce_handler(self.nomadnet_handler)
            
            # Mark Reticulum as successfully initialized
            self.reticulum_ready = True
            self.connection_state = "connected"
            
            print(f"🟢 Reticulum Connected! 🔑 Browser identity: {RNS.prettyhexrep(self.identity.hash)}")
            print("=" * 90)
            
        except Exception as e:
            # Mark initialization as failed
            self.reticulum_ready = False
            self.connection_state = "failed"
            print(f"Failed to initialize: {e}")
            sys.exit(1)
            
    def process_nomadnet_announce(self, destination_hash, announced_identity, app_data):
        self.announce_count += 1
        self.last_announce_time = time.time()  # Track when we last received an announce
    
        hash_str = RNS.prettyhexrep(destination_hash)
        clean_hash_str = hash_str.replace("<", "").replace(">", "").replace(":", "")
    
        node_name = "UNKNOWN"
        if app_data:
            try:
                node_name = app_data.decode('utf-8')
            except:
                try:
                    decoded = msgpack.unpackb(app_data)
                    node_name = str(decoded) if isinstance(decoded, str) else f"Node_{hash_str[:8]}"
                except:
                    node_name = f"BinaryNode_{hash_str[:8]}"
        else:
            node_name = f"EmptyNode_{hash_str[:8]}"
    
        # Filter out test nodes
        if node_name.startswith("EmptyNode_") or node_name.startswith("BinaryNode_") or node_name == "UNKNOWN":
            print(f"Filtered test node: {hash_str[:16]} -> {node_name}")
            return
    
        # Track per-node announce count
        if hash_str in self.nomadnet_nodes:
            # Increment this node's announce count
            self.nomadnet_nodes[hash_str]["node_announce_count"] += 1
        else:
            # First announce from this node
            self.nomadnet_nodes[hash_str] = {
                "hash": clean_hash_str,
                "name": node_name,
                "last_seen": datetime.now().isoformat(),
                "announce_count": self.announce_count,  # Global sequence number
                "node_announce_count": 1,  # This node's announce count
                "app_data_length": len(app_data) if app_data else 0,
                "last_seen_relative": "Just now"
            }
    
        # Update other fields for existing nodes
        self.nomadnet_nodes[hash_str]["name"] = node_name
        self.nomadnet_nodes[hash_str]["last_seen"] = datetime.now().isoformat()
        self.nomadnet_nodes[hash_str]["app_data_length"] = len(app_data) if app_data else 0
        self.nomadnet_nodes[hash_str]["last_seen_relative"] = "Just now"
    
        if self.connection_state == "connected":
            self.connection_state = "active"
            print(f"🟢 Connection state updated to ACTIVE (received first valid announce)")
    
        print(f"🌐 NomadNet Announce #{self.announce_count}: {clean_hash_str} -> {node_name} (node announces: {self.nomadnet_nodes[hash_str]['node_announce_count']})")
        
        # search engine cache system #
        cache_path = self.cache_dir / clean_hash_str
        index_file = cache_path / "index.mu"
    
        # Check if cache exists AND has content
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
                content = index_file.read_text(encoding='utf-8', errors='ignore')
                if len(content.strip()) < 10:  # Less than 10 characters = probably empty/failed
                    should_cache = True
                    print(f"🔄 Queuing {node_name} for re-caching (empty content)...")
                else:
                    # Check if we need additional pages for existing good cache
                    if self.cache_settings.get('cache_additional', False):
                        pages_dir = cache_path / "pages"
                        if not pages_dir.exists() or len(list(pages_dir.glob("*.mu"))) == 0:
                            should_cache_additional = True
                            print(f"🔄 Queuing {node_name} for additional page caching...")
            except:
                should_cache = True
                print(f"🔄 Queuing {node_name} for re-caching (read error)...")
    
        if should_cache and self.cache_settings.get('auto_cache_enabled', True):
            self.cache_queue.put((clean_hash_str, node_name))
        elif should_cache_additional and self.cache_settings.get('auto_cache_enabled', True):
            # Queue just for additional pages, not full caching
            self.additional_cache_queue.put((clean_hash_str, node_name))
        elif should_cache:
            print(f"⏸️ Auto-caching disabled, skipping {node_name}")
        elif should_cache_additional:
            print(f"⏸️ Auto-caching disabled, skipping additional pages for {node_name}")
        else:
            print(f"📁 {node_name} already cached, skipping...")
            
    def background_cache_worker(self):
        """Runs in separate thread"""
        while True:
            try:
                hash_str, node_name = self.cache_queue.get(timeout=5)
                self.cache_single_page(hash_str, node_name, "/page/index.mu")
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Cache worker error: {e}")

    def cache_single_page(self, node_hash, node_name, page_path):
        try:
            print(f"📥 Attempting to cache page from {node_name} ({node_hash[:16]}...)")
            
            browser = NomadNetBrowser(self, node_hash)
            response = browser.fetch_page(page_path)
            
            print(f"📋 Response status: {response['status']}")
            if response["status"] == "success":
                cache_dir = self.cache_dir / node_hash
                cache_dir.mkdir(parents=True, exist_ok=True)
                print(f"📂 Created cache directory: {cache_dir}")
                
                # Save files with explicit UTF-8 encoding
                try:
                    (cache_dir / "index.mu").write_text(response["content"], encoding='utf-8')
                    (cache_dir / "node_name.txt").write_text(node_name, encoding='utf-8')
                    (cache_dir / "cached_at.txt").write_text(str(datetime.now()), encoding='utf-8')
                    
                    print(f"📄 Saved {len(response['content'])} characters to {cache_dir / 'index.mu'}")
                    print(f"✅ Successfully cached page from {node_name}")
                    
                    # Run cache maintenance after successful caching
                    self.enforce_cache_size_limit()
                    self.cleanup_expired_cache()
                    
                except UnicodeEncodeError as e:
                    # Fallback: save with error handling for problematic characters
                    safe_content = response["content"].encode('utf-8', errors='replace').decode('utf-8')
                    safe_node_name = node_name.encode('utf-8', errors='replace').decode('utf-8')
                    
                    (cache_dir / "index.mu").write_text(safe_content, encoding='utf-8')
                    (cache_dir / "node_name.txt").write_text(safe_node_name, encoding='utf-8')
                    (cache_dir / "cached_at.txt").write_text(str(datetime.now()), encoding='utf-8')
                    
                    print(f"✅ Successfully cached page from {safe_node_name} (with character replacements)")
                    
                    # Run cache maintenance after successful caching
                    self.enforce_cache_size_limit()
                    self.cleanup_expired_cache()
                    
            else:
                print(f"❌ Failed to fetch page: {response.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ Exception caching page from {node_name}: {e}")
            import traceback
            traceback.print_exc()

    def enforce_cache_size_limit(self):
        """Remove oldest cache entries if size limit is exceeded"""
        size_limit_mb = self.cache_settings.get('size_limit_mb', -1)
        if size_limit_mb == -1:  # Unlimited
            return
        
        if not self.cache_dir.exists():
            return
        
        # Calculate current cache size
        total_size = 0
        cache_entries = []
        
        for node_dir in self.cache_dir.iterdir():
            if node_dir.is_dir():
                dir_size = 0
                cached_at_file = node_dir / "cached_at.txt"
                
                # Get directory size
                for file in node_dir.rglob('*'):
                    if file.is_file():
                        dir_size += file.stat().st_size
                
                total_size += dir_size
                
                # Get cache timestamp
                cache_time = datetime.now()  # Default to now if no timestamp
                if cached_at_file.exists():
                    try:
                        cache_time = datetime.fromisoformat(cached_at_file.read_text().strip())
                    except:
                        pass
                
                cache_entries.append({
                    'path': node_dir,
                    'size': dir_size,
                    'time': cache_time
                })
        
        # Check if we exceed the limit
        size_limit_bytes = size_limit_mb * 1024 * 1024
        if total_size <= size_limit_bytes:
            return
        
        # Remove oldest entries until under limit
        cache_entries.sort(key=lambda x: x['time'])  # Oldest first
        
        print(f"🗑️ Cache size {total_size // (1024*1024)}MB exceeds limit {size_limit_mb}MB, removing old entries...")
        
        for entry in cache_entries:
            if total_size <= size_limit_bytes:
                break
            
            try:
                import shutil
                shutil.rmtree(entry['path'])
                total_size -= entry['size']
                print(f"🗑️ Removed old cache: {entry['path'].name} ({entry['size'] // 1024} KB)")
            except Exception as e:
                print(f"Error removing cache {entry['path']}: {e}")

    def cleanup_expired_cache(self):
        """Remove cache entries older than expiry setting"""
        expiry_days = self.cache_settings.get('expiry_days', -1)
        if expiry_days == -1:  # Never expire
            return
        
        if not self.cache_dir.exists():
            return
        
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=expiry_days)
        removed_count = 0
        
        for node_dir in self.cache_dir.iterdir():
            if node_dir.is_dir():
                cached_at_file = node_dir / "cached_at.txt"
                
                if cached_at_file.exists():
                    try:
                        cache_time = datetime.fromisoformat(cached_at_file.read_text().strip())
                        if cache_time < cutoff_date:
                            import shutil
                            shutil.rmtree(node_dir)
                            removed_count += 1
                            print(f"🗑️ Expired cache removed: {node_dir.name}")
                    except Exception as e:
                        print(f"Error processing cache expiry for {node_dir}: {e}")
        
        if removed_count > 0:
            print(f"🧹 Removed {removed_count} expired cache entries")


    def get_cached_status(self):
        """Get cached connection status to avoid repeated expensive operations"""
        with self._cache_lock:
            now = time.time()
            if (self._status_cache is not None and 
                self._status_cache_time is not None and 
                now - self._status_cache_time < self.cache_duration):
                return self._status_cache
            
            # Calculate fresh status
            current_time = time.time()
            app_uptime = current_time - self.start_time if hasattr(self, 'start_time') else 0
            has_nodes = len(self.nomadnet_nodes) > 0
            time_since_last_announce = current_time - self.last_announce_time if self.last_announce_time else None
            
            # Store in cache
            self._status_cache = {
                'app_uptime': app_uptime,
                'has_nodes': has_nodes,
                'time_since_last_announce': time_since_last_announce,
                'node_count': len(self.nomadnet_nodes),
                'announce_count': self.announce_count,
                'connection_state': getattr(self, 'connection_state', 'connected'),  # Default to connected if not set
                'reticulum_ready': getattr(self, 'reticulum_ready', False)
            }
            self._status_cache_time = now
            return self._status_cache
        
    def get_nodes(self):
        current_time = datetime.now()
        for node in self.nomadnet_nodes.values():
            last_seen = datetime.fromisoformat(node['last_seen'])
            diff = current_time - last_seen
            
            if diff.total_seconds() < 60:
                node['last_seen_relative'] = "Just now"
            elif diff.total_seconds() < 3600:
                minutes = int(diff.total_seconds() / 60)
                node['last_seen_relative'] = f"{minutes}m ago"
            else:
                hours = int(diff.total_seconds() / 3600)
                node['last_seen_relative'] = f"{hours}h ago"
        
        return list(self.nomadnet_nodes.values())
    
    def fetch_file(self, node_hash, file_path):
        """Fetch a file from a NomadNet node"""
        try:
            print(f"📁 NomadNetWebBrowser.fetch_file called: {file_path} from {node_hash[:16]}...")
            print(f"📁 Creating NomadNetFileBrowser instance...")
            browser = NomadNetFileBrowser(self, node_hash)
            response = browser.fetch_file(file_path)
            return response
        except Exception as e:
            print(f"❌ File fetch failed: {str(e)}")
            return {"error": f"File fetch failed: {str(e)}", "content": b"", "status": "error"}

    def fetch_page(self, node_hash, page_path="/page/index.mu", form_data=None):
        try:
            print(f"Fetching {page_path} from {node_hash[:16]}...")
            
            destination_hash = bytes.fromhex(node_hash.replace("<", "").replace(">", "").replace(":", ""))
            
            # Check for existing cached link first (like MeshChat does)
            if hasattr(self, 'nomadnet_cached_links') and destination_hash in self.nomadnet_cached_links:
                existing_link = self.nomadnet_cached_links[destination_hash]
                if existing_link.status == RNS.Link.ACTIVE:
                    print("Using existing cached link for page request")
                    
                    # Convert form data to field_ prefixed format (like NomadNetBrowser does)
                    processed_form_data = {}
                    if form_data:
                        for key, value in form_data.items():
                            # Add field_ prefix if not already present
                            if not key.startswith("field_") and not key.startswith("var_"):
                                processed_form_data[f"field_{key}"] = value
                            else:
                                processed_form_data[key] = value
                        print(f"Processed form data: {processed_form_data}")
                    
                    # Start with processed form data
                    final_form_data = processed_form_data.copy() if processed_form_data else {}
                    
                    # Add fingerprint data WITHOUT field_ prefix (special handling)
                    if hasattr(existing_link, 'fingerprint_data') and existing_link.fingerprint_data:
                        final_form_data.update(existing_link.fingerprint_data)
                        print(f"Including fingerprint data (no field_ prefix): {existing_link.fingerprint_data}")
                    
                    print(f"Final form data being sent: {final_form_data}")
                    
                    # Actually make the request on the existing link
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
                        except Exception as e:
                            result["data"] = f"Response error: {str(e)}"
                            result["received"] = True
                            response_event.set()
                    
                    def on_failed(receipt):
                        result["data"] = "Request failed"
                        result["received"] = True
                        response_event.set()
                    
                    # Make the actual request on the cached link with combined data
                    existing_link.request(page_path, data=final_form_data if final_form_data else None, 
                                        response_callback=on_response, 
                                        failed_callback=on_failed)
                    
                    # Wait for response
                    success = response_event.wait(timeout=30)
                    if success and result["received"]:
                        return {"content": result["data"] or "Empty response", "status": "success", "error": None}
                    else:
                        return {"error": "Timeout", "content": "Request timeout on cached link", "status": "error"}
            
            # Only create new browser/link if no cached link exists
            print("Creating new browser instance (no cached link available)")
            browser = NomadNetBrowser(self, node_hash)
            response = browser.fetch_page(page_path, form_data)
            
            # Store the link in cache after successful creation
            if response["status"] == "success" and hasattr(browser, 'link'):
                if not hasattr(self, 'nomadnet_cached_links'):
                    self.nomadnet_cached_links = {}
                self.nomadnet_cached_links[destination_hash] = browser.link
                print("Stored new link in cache")
            
            return response
            
        except Exception as e:
            print(f"Fetch failed: {str(e)}")
            return {"error": f"Fetch failed: {str(e)}", "content": "", "status": "error"}

    def start_monitoring(self):
        self.running = True
        print("=" * 90)
        print("📡 Started NomadNet announce monitoring")
        print("=" * 90)

    def get_node_hops(self, destination_hash):
        """Get the number of hops to a destination"""
        try:
            # Convert hash string to bytes if needed
            if isinstance(destination_hash, str):
                dest_hash = bytes.fromhex(destination_hash.replace("<", "").replace(">", "").replace(":", ""))
            else:
                dest_hash = destination_hash
                
            # Use RNS Transport to get hop count
            hops = RNS.Transport.hops_to(dest_hash)
            return hops if hops is not None else "Unknown"
        except Exception as e:
            print(f"Error getting hops to {destination_hash}: {e}")
            return "Unknown"
            
    def get_node_path_info(self, destination_hash):
        """Get hop count and next hop information"""
        try:
            if isinstance(destination_hash, str):
                dest_hash = bytes.fromhex(destination_hash.replace("<", "").replace(">", "").replace(":", ""))
            else:
                dest_hash = destination_hash
                
            hops = RNS.Transport.hops_to(dest_hash)
            next_hop_info = "Unknown"
            
            # Try using the next_hop and next_hop_interface functions directly
            try:
                next_hop_hash = RNS.Transport.next_hop(dest_hash)
                if next_hop_hash:
                    # Try to get interface info
                    next_hop_if = RNS.Transport.next_hop_interface(dest_hash)
                    if next_hop_if and hasattr(next_hop_if, 'name'):
                        next_hop_info = f"via {next_hop_if.name}"
                    else:
                        # Show the next hop hash if no interface name
                        next_hop_info = f"via {RNS.prettyhexrep(next_hop_hash)[:16]}..."
                        
            except Exception as e:
                print(f"Error using next_hop functions: {e}")
                
            # Fallback: Check the path_table directly
            if next_hop_info == "Unknown" and hasattr(RNS.Transport, 'path_table'):
                if dest_hash in RNS.Transport.path_table:
                    path_entry = RNS.Transport.path_table[dest_hash]
                    print(f"Path table entry type: {type(path_entry)}")
                    print(f"Path table entry attributes: {[attr for attr in dir(path_entry) if not attr.startswith('_')]}")
                    
                    # Try to extract next hop from path entry
                    for attr in ['next_hop', 'via', 'interface', 'receiving_interface']:
                        if hasattr(path_entry, attr):
                            value = getattr(path_entry, attr)
                            print(f"  {attr}: {value}")
                            if value and hasattr(value, 'name'):
                                next_hop_info = f"via {value.name}"
                            elif isinstance(value, bytes):
                                next_hop_info = f"via {RNS.prettyhexrep(value)[:16]}..."
                                          
            return {
                'hops': hops if hops is not None else "Unknown",
                'next_hop_interface': next_hop_info
            }
            
        except Exception as e:
            print(f"Error getting path info to {destination_hash}: {e}")
            return {'hops': "Unknown", 'next_hop_interface': "Unknown"}

    def send_fingerprint(self, node_hash):
        """Send identity fingerprint to a NomadNet node"""
        try:
            print(f"NomadNetWebBrowser.send_fingerprint called for {node_hash[:16]}...")
            browser = NomadNetBrowser(self, node_hash)
            response = browser.send_fingerprint()
            return response
        except Exception as e:
            print(f"Identity fingerprint send failed: {str(e)}")
            return {"error": f"Identity fingerprint send failed: {str(e)}", "message": "", "status": "error"}
        
    def ping_node(self, node_hash):
        """Ping a NomadNet node to check reachability"""
        try:
            print(f"Pinging node {node_hash[:16]}...")
            browser = NomadNetBrowser(self, node_hash)
            response = browser.send_ping()
            return response
        except Exception as e:
            print(f"Ping failed: {str(e)}")
            return {"error": f"Ping failed: {str(e)}", "message": "", "status": "error"}

# Initialize the browser
browser = NomadNetWebBrowser()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/style.css')
def serve_css():
    return send_from_directory('templates', 'style.css', mimetype='text/css')

@app.route('/api/nodes')
def api_nodes():
    nodes = browser.get_nodes()
    
    # Add path information to each node
    for node in nodes:
        path_info = browser.get_node_path_info(node['hash'])
        node['hops'] = path_info['hops']
        node['next_hop_interface'] = path_info['next_hop_interface']
    
    return jsonify(nodes)

@app.route('/api/status')
def api_status():
    return jsonify({
        "running": browser.running,
        "total_announces": browser.announce_count,
        "unique_nodes": len(browser.nomadnet_nodes),
        "identity_hash": RNS.prettyhexrep(browser.identity.hash) if browser.identity else None
    })

@app.route('/api/fetch/<node_hash>', methods=['GET', 'POST'])
def api_fetch_page(node_hash):
    page_path = request.args.get('path', '/page/index.mu')
    
    form_data = None
    if request.method == 'POST':
        form_data = request.get_json() or {}
    
    print(f"🌐 API Request: Fetching {page_path} from {node_hash[:16]}...")
    if form_data:
        print(f"📝 Form data: {form_data}")
    
    # Pass form_data as third parameter
    response = browser.fetch_page(node_hash, page_path, form_data)
    
    if response["status"] == "success":
        content_length = len(response.get('content', ''))
        print(f"✅ API Response: Successfully fetched {content_length} characters")
    else:
        print(f"❌ API Response: Failed - {response.get('error', 'Unknown error')}")
    
    return jsonify(response)

@app.route('/script/purify.min.js')
def serve_purify():
    """Serve the DOMPurify library"""
    try:
        script_path = os.path.join('script', 'purify.min.js')
        if os.path.exists(script_path):
            print(f"✅ Serving DOMPurify from: {script_path}")
            return send_from_directory('script', 'purify.min.js', mimetype='application/javascript')
        else:
            print(f"❌ DOMPurify not found at: {script_path}")
            return "console.error('DOMPurify file not found');", 404
    except Exception as e:
        print(f"❌ Error serving DOMPurify: {e}")
        return f"console.error('Error loading DOMPurify: {str(e)}');", 500

@app.route('/script/micron-parser_original.js')
def serve_micron_parser():
    """Serve the modified micron parser script"""
    try:
        script_path = os.path.join('script', 'micron-parser_original.js')
        if os.path.exists(script_path):
            print(f"✅ Serving micron parser from: {script_path}")
            return send_from_directory('script', 'micron-parser_original.js', mimetype='application/javascript')
        else:
            print(f"❌ Micron parser not found at: {script_path}")
            return "console.error('Micron parser file not found');", 404
    except Exception as e:
        print(f"❌ Error serving micron parser: {e}")
        return f"console.error('Error loading micron parser: {str(e)}');", 500
    
@app.route('/api/download/<node_hash>')
def api_download_file(node_hash):
    """Download a file from a NomadNet node"""
    file_path = request.args.get('path', '/file/')
    
    if not file_path.startswith('/file/'):
        return jsonify({"error": "Invalid file path"}), 400
    
    print(f"📁 Download Request: {file_path} from {node_hash[:16]}...")
    
    try:
        response = browser.fetch_file(node_hash, file_path)
        
        if response["status"] == "error":
            print(f"❌ Download failed: {response.get('error', 'Unknown error')}")
            return jsonify(response), 404
        
        file_data = response["content"]
        filename = file_path.split('/')[-1] or "download"
        
        # Ensure file_data is bytes - this is critical for binary files
        if not isinstance(file_data, bytes):
            print(f"⚠️ File data is not bytes, it's {type(file_data)}")
            if isinstance(file_data, str):
                # Don't encode strings as UTF-8 for binary files - this corrupts them
                file_data = file_data.encode('latin1')  # Preserve byte values
            else:
                file_data = str(file_data).encode('latin1')
        
        if not file_data:
            print(f"❌ No file data received")
            return jsonify({"error": "No file data received"}), 404
            
        mime_type, _ = mimetypes.guess_type(filename)
        if not mime_type:
            mime_type = 'application/octet-stream'
        
        print(f"✅ Serving file: {filename} ({len(file_data)} bytes, {mime_type})")
        
        file_obj = io.BytesIO(file_data)
        
        return send_file(
            file_obj,
            mimetype=mime_type,
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"❌ Download exception: {str(e)}")
        return jsonify({"error": f"Download failed: {str(e)}"}), 500

@app.route('/favicon.svg')
def favicon():
    return '', 204  # No content response

@app.route('/api/fingerprint/<node_hash>', methods=['POST'])
def api_send_fingerprint(node_hash):
    """Send identity fingerprint to a NomadNet node"""
    print(f"API Request: Sending identity fingerprint to {node_hash[:16]}...")
    
    response = browser.send_fingerprint(node_hash)
    
    if response["status"] == "success":
        print(f"API Response: Identity fingerprint sent successfully")
    else:
        print(f"API Response: Identity fingerprint failed - {response.get('error', 'Unknown error')}")
    
    return jsonify(response)

@app.route('/api/connection-status')
def api_connection_status():
    try:
        status_data = browser.get_cached_status()
        
        # Use cached data to determine status
        app_uptime = status_data['app_uptime']
        has_nodes = status_data['has_nodes']
        time_since_last_announce = status_data['time_since_last_announce']
        connection_state = status_data['connection_state']
        reticulum_ready = status_data['reticulum_ready']
        
        
        # Check for various failure states first
        if not reticulum_ready:
            return jsonify({
                "status": "connerror",
                "message": "Reticulum initialization failed",
                "color": "red"
            })
        
        if connection_state == "failed":
            return jsonify({
                "status": "connerror", 
                "message": "Connection failed during startup",
                "color": "red"
            })
        
        # Handle different connection states
        if connection_state == "initializing":
            return jsonify({
                "status": "waiting",
                "message": "Initializing Reticulum...",
                "color": "yellow"
            })
        
        elif connection_state == "connecting":
            return jsonify({
                "status": "waiting",
                "message": "Connecting to Reticulum...", 
                "color": "yellow"
            })
        
        elif connection_state == "connected":
            # Still waiting for first announces
            if app_uptime < 60:
                return jsonify({
                    "status": "waiting", 
                    "message": "Connected! <span style='color: #FFC107;'>Waiting for announces...</span> ",
                    "color": "green"
                })
            elif app_uptime < 120:
                return jsonify({
                    "status": "waiting",
                    "message": "Waiting for network activity...",
                    "color": "yellow"
                })
            else:
                return jsonify({
                    "status": "waiting",
                    "message": "Connected but no network activity",
                    "color": "yellow"
                })
        
        elif connection_state == "active":
            # We're receiving announces
            if has_nodes:
                if time_since_last_announce and time_since_last_announce > 300:  # 5 minutes
                    return jsonify({
                        "status": "waiting",
                        "message": "No recent announces, waiting...",
                        "color": "yellow"
                    })
                else:
                    return jsonify({
                        "status": "online",
                        "message": "Online. Reticulum Connected!",
                        "color": "green"
                    })
            else:
                # This shouldn't happen - active state but no nodes
                return jsonify({
                    "status": "waiting",
                    "message": "Connection active but no nodes found",
                    "color": "yellow"
                })
        
        else:
            return jsonify({
                "status": "connerror",
                "message": f"Unknown connection state: {connection_state}",
                "color": "red"
            })
            
    except Exception as e:
        print(f"Error in connection status: {e}")
        return jsonify({
            "status": "connerror",
            "message": "Status check failed", 
            "color": "red"
        })

@app.route('/api/search-cache')
def api_search_cache():
    query = request.args.get('q', '').lower().strip()
    if not query:
        return jsonify([])
    
    results = []
    cache_dir = browser.cache_dir
    search_limit = browser.cache_settings.get('search_limit', 50)
    
    try:
        if cache_dir.exists():
            for node_dir in cache_dir.iterdir():
                if node_dir.is_dir():
                    name_file = node_dir / "node_name.txt"
                    node_name = name_file.read_text(encoding='utf-8') if name_file.exists() else "Unknown Node"
                    
                    # Get cached timestamp and calculate freshness
                    cached_at_file = node_dir / "cached_at.txt"
                    cached_at = "Unknown"
                    cache_age_days = None
                    cache_status = "unknown"
                    
                    if cached_at_file.exists():
                        try:
                            cached_datetime = datetime.fromisoformat(cached_at_file.read_text().strip())
                            cached_at = cached_datetime.strftime("%Y-%m-%d %H:%M:%S")
                            
                            # Calculate cache age in days
                            cache_age = datetime.now() - cached_datetime
                            cache_age_days = cache_age.total_seconds() / 86400
                            
                            # Determine status
                            if cache_age_days <= 3:
                                cache_status = "fresh"
                            elif cache_age_days <= 10:
                                cache_status = "good"
                            elif cache_age_days <= 20:
                                cache_status = "moderate"
                            else:
                                cache_status = "old"
                                
                        except Exception as e:
                            print(f"Error parsing cache date: {e}")
                            cached_at = "Unknown"
                    
                    # Search index.mu
                    index_file = node_dir / "index.mu"
                    if index_file.exists():
                        try:
                            content = index_file.read_text(encoding='utf-8', errors='ignore')
                            if query in content.lower() or query in node_name.lower():
                                snippet = extract_snippet(content, query)
                                if query in node_name.lower():
                                    snippet = f"Node name match: {node_name}\n\n" + snippet
                                
                                results.append({
                                    'node_hash': node_dir.name,
                                    'node_name': node_name,
                                    'snippet': snippet,
                                    'url': f"{node_dir.name}:/page/index.mu",
                                    'page_name': 'index.mu',
                                    'page_path': '/page/index.mu',
                                    'cached_at': cached_at,
                                    'cache_status': cache_status,
                                    'cache_age_days': cache_age_days
                                })
                                
                                if len(results) >= search_limit:
                                    break
                        except Exception as e:
                            print(f"Error reading cache file {index_file}: {e}")
                    
                    # Search additional pages
                    pages_dir = node_dir / "pages"
                    if pages_dir.exists():
                        for page_file in pages_dir.glob("*.mu"):
                            if len(results) >= search_limit:
                                break
                            try:
                                content = page_file.read_text(encoding='utf-8', errors='ignore')
                                if query in content.lower():
                                    page_name = page_file.name
                                    snippet = extract_snippet(content, query)
                                    
                                    results.append({
                                        'node_hash': node_dir.name,
                                        'node_name': node_name,
                                        'snippet': snippet,
                                        'url': f"{node_dir.name}:/page/{page_name}",
                                        'page_name': page_name,
                                        'page_path': f'/page/{page_name}',
                                        'cached_at': cached_at,
                                        'cache_status': cache_status,
                                        'cache_age_days': cache_age_days
                                    })
                            except Exception as e:
                                print(f"Error reading additional page {page_file}: {e}")
        
        return jsonify(results)
        
    except Exception as e:
        print(f"Search error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/refresh-node-cache/<node_hash>', methods=['POST'])
def api_refresh_node_cache(node_hash):
    """Refresh cache for a specific node"""
    try:
        print(f"=== Refresh request received for: {node_hash} ===")
        
        # Find node name
        node_name = "Unknown"
        
        # First check active nodes
        for hash_key, node_data in browser.nomadnet_nodes.items():
            if node_data.get('hash') == node_hash:
                node_name = node_data.get('name', 'Unknown')
                print(f"Found in active nodes: {node_name}")
                break
        
        # If not found, check cache
        if node_name == "Unknown":
            cache_dir = browser.cache_dir / node_hash
            name_file = cache_dir / "node_name.txt"
            if name_file.exists():
                node_name = name_file.read_text(encoding='utf-8', errors='ignore').strip()
                print(f"Found in cache: {node_name}")
        
        print(f"Queuing {node_name} for refresh...")
        browser.cache_queue.put((node_hash, node_name))
        print(f"Successfully queued!")
        
        return jsonify({
            'status': 'success',
            'message': f'Queued {node_name} for cache refresh',
            'node_name': node_name,
            'node_hash': node_hash
        })
        
    except Exception as e:
        print(f"ERROR in refresh endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
    
@app.route('/api/check-cache-status/<node_hash>')
def api_check_cache_status(node_hash):
    """Check if cache has been updated recently"""
    try:
        cache_dir = browser.cache_dir / node_hash
        cached_at_file = cache_dir / "cached_at.txt"
        
        if cached_at_file.exists():
            cached_datetime = datetime.fromisoformat(cached_at_file.read_text().strip())
            cached_at = cached_datetime.strftime("%Y-%m-%d %H:%M:%S")
            
            # Check if updated in last 10 seconds
            time_since_cache = (datetime.now() - cached_datetime).total_seconds()
            updated = time_since_cache < 10
            
            # Calculate freshness
            cache_age_days = time_since_cache / 86400
            if cache_age_days <= 3:
                cache_status = "fresh"
            elif cache_age_days <= 10:
                cache_status = "good"
            elif cache_age_days <= 20:
                cache_status = "moderate"
            else:
                cache_status = "old"
            
            return jsonify({
                'updated': updated,
                'cache_status': cache_status,
                'cached_at': cached_at
            })
        
        return jsonify({'updated': False})
        
    except Exception as e:
        print(f"Error checking cache status: {e}")
        return jsonify({'updated': False})
    
@app.route('/templates/go.png')
def serve_go_icon():
    """Serve the go icon"""
    try:
        template_path = get_resource_path('templates') if 'get_resource_path' in globals() else 'templates'
        return send_from_directory(template_path, 'go.png', mimetype='image/png')
    except Exception as e:
        print(f"❌ Error serving star icon: {e}")
        return "", 404

@app.route('/templates/search.png')
def serve_search_icon():
    """Serve the search icon"""
    try:
        template_path = get_resource_path('templates') if 'get_resource_path' in globals() else 'templates'
        return send_from_directory(template_path, 'search.png', mimetype='image/png')
    except Exception as e:
        print(f"❌ Error serving search icon: {e}")
        return "", 404

@app.route('/templates/star.png')
def serve_star_icon():
    """Serve the star icon"""
    try:
        template_path = get_resource_path('templates') if 'get_resource_path' in globals() else 'templates'
        return send_from_directory(template_path, 'star.png', mimetype='image/png')
    except Exception as e:
        print(f"❌ Error serving star icon: {e}")
        return "", 404

@app.route('/templates/ping.png')
def serve_ping_icon():
    """Serve the ping icon"""
    try:
        template_path = get_resource_path('templates') if 'get_resource_path' in globals() else 'templates'
        return send_from_directory(template_path, 'ping.png', mimetype='image/png')
    except Exception as e:
        print(f"❌ Error serving ping icon: {e}")
        return "", 404

@app.route('/templates/fingerprint.png')
def serve_fingerprint_icon():
    """Serve the fingerprint icon"""
    try:
        template_path = get_resource_path('templates') if 'get_resource_path' in globals() else 'templates'
        return send_from_directory(template_path, 'fingerprint.png', mimetype='image/png')
    except Exception as e:
        print(f"❌ Error serving fingerprint icon: {e}")
        return "", 404

@app.route('/api/cache-settings', methods=['GET', 'POST'])
def api_cache_settings():
    if request.method == 'GET':
        return jsonify(browser.cache_settings)
    
    data = request.json
    action = data.get('action')
    
    if action == 'toggle_auto_cache':
        browser.cache_settings['auto_cache_enabled'] = data.get('enabled', True)
        
    elif action == 'update_size_limit':
        browser.cache_settings['size_limit_mb'] = data.get('value', 100)
        
    elif action == 'update_expiry':
        browser.cache_settings['expiry_days'] = data.get('value', 30)
        
    elif action == 'update_search_limit':
        browser.cache_settings['search_limit'] = data.get('value', 50)
        
    elif action == 'toggle_additional_pages':
        browser.cache_settings['cache_additional'] = data.get('enabled', False)
        
    elif action == 'clear_cache':
        import shutil
        try:
            if browser.cache_dir.exists():
                shutil.rmtree(browser.cache_dir)
                browser.cache_dir.mkdir(parents=True, exist_ok=True)
            return jsonify({'message': 'Cache cleared successfully', 'status': 'success'})
        except Exception as e:
            return jsonify({'message': f'Error clearing cache: {e}', 'status': 'error'})
    
    elif action == 'refresh_cache':
        count = 0
        for node_data in browser.nomadnet_nodes.values():
            browser.cache_queue.put((node_data['hash'], node_data['name']))
            count += 1
        return jsonify({'message': f'Queued {count} nodes for refresh', 'status': 'success'})
    
    elif action == 'cache_additional_all':
        if not browser.cache_settings.get('cache_additional', False):
            return jsonify({'message': 'Additional page caching is disabled', 'status': 'error'})
        
        count = 0
        for node_dir in browser.cache_dir.iterdir():
            if node_dir.is_dir():
                node_hash = node_dir.name
                name_file = node_dir / "node_name.txt"
                node_name = name_file.read_text(encoding='utf-8') if name_file.exists() else "Unknown"
                
                # Queue for additional page caching
                browser.additional_cache_queue.put((node_hash, node_name))
                count += 1
        
        return jsonify({'message': f'Queued {count} nodes for additional page caching', 'status': 'success'})


    # Save settings after any change
    browser.save_cache_settings()
    return jsonify({'status': 'success'})

@app.route('/api/export-cache')
def api_export_cache():
    import zipfile
    import io
    
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        if browser.cache_dir.exists():
            for node_dir in browser.cache_dir.iterdir():
                if node_dir.is_dir():
                    for file in node_dir.rglob('*'):
                        if file.is_file():
                            zip_file.write(file, file.relative_to(browser.cache_dir))
    
    zip_buffer.seek(0)
    
    return send_file(
        io.BytesIO(zip_buffer.read()),
        mimetype='application/zip',
        as_attachment=True,
        download_name='nomadnet_cache_export.zip'
    )

@app.route('/api/cache-stats')
def api_cache_stats():
    cache_dir = browser.cache_dir
    node_count = 0
    page_count = 0
    valid_page_count = 0
    total_size = 0
    
    if cache_dir.exists():
        for node_dir in cache_dir.iterdir():
            if node_dir.is_dir():
                node_count += 1
                # Count only .mu files
                for file in node_dir.rglob("*.mu"):
                    if file.is_file():
                        page_count += 1
                        total_size += file.stat().st_size
                        
                        # Check if page is valid (doesn't contain "Request failed")
                        try:
                            content = file.read_text(encoding='utf-8', errors='ignore')
                            if "Request failed" not in content:
                                valid_page_count += 1
                        except Exception as e:
                            print(f"Error reading {file}: {e}")
    
    # Format size
    if total_size < 1024:
        cache_size = f"{total_size} B"
    elif total_size < 1024 * 1024:
        cache_size = f"{total_size / 1024:.1f} KB"
    else:
        cache_size = f"{total_size / (1024 * 1024):.1f} MB"
    
    return jsonify({
        'node_count': node_count,
        'page_count': page_count,
        'valid_page_count': valid_page_count,
        'cache_size': cache_size
    })

@app.route('/api/ping/<node_hash>', methods=['POST'])
def api_ping_node(node_hash):
    """Ping a NomadNet node"""
    print(f"API Request: Pinging node {node_hash[:16]}...")
    
    response = browser.ping_node(node_hash)
    
    if response["status"] == "success":
        print(f"API Response: Ping successful - RTT: {response.get('rtt', 0):.2f}s")
    else:
        print(f"API Response: Ping failed - {response.get('error', 'Unknown error')}")
    
    return jsonify(response)

def extract_snippet(content, query, context_length=150):
    """Extract text snippet around search term with highlighting"""
    lower_content = content.lower()
    query_pos = lower_content.find(query.lower())
    
    if query_pos == -1:
        # Query not in content, return beginning of content
        return content[:context_length] + ("..." if len(content) > context_length else "")
    
    start = max(0, query_pos - context_length // 2)
    end = min(len(content), query_pos + len(query) + context_length // 2)
    
    snippet = content[start:end]
    if start > 0:
        snippet = "..." + snippet
    if end < len(content):
        snippet = snippet + "..."
    
    # Highlight the query term (case-insensitive)
    import re
    highlighted = re.sub(
        f'({re.escape(query)})', 
        r'<mark>\1</mark>', 
        snippet, 
        flags=re.IGNORECASE
    )
    
    return highlighted

def start_server(host='0.0.0.0', port=5000):
    import logging

    try:
        from waitress import serve
        print("🚀 Local Web Interface starting with Waitress server...")
        serve(app, host=host, port=port, threads=8)  # Single-threaded for nomadnet compatibility
    except ImportError:
        # Fallback to Flask dev server if waitress not installed
        logging.getLogger('werkzeug').setLevel(logging.ERROR)
        print("⚠️  Waitress not found, falling back to Flask dev server...")
        print("🚀 Local Web Interface starting...")
        app.run(host=host, port=port, debug=False, threaded=True)
        
def main():
    """
    Main function with improved error handling and status management
    """
    parser = argparse.ArgumentParser(description='rBrowser - Standalone NomadNet Browser')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind the web server to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the web server on (default: 5000)')
    args = parser.parse_args()

    try:
        # Check file structure first
        template_path = os.path.join('templates', 'index.html')
        if os.path.exists(template_path):
            print(f"✅ Found HTML template: {template_path}")
        else:
            print(f"❌ HTML template not found: {template_path}")
            print("   Please verify templates/ directory and index.html file")
            return 1
        
        micron_path = os.path.join('script', 'micron-parser_original.js')
        if os.path.exists(micron_path):
            print(f"✅ Found Micron parser: {micron_path}")
        else:
            print(f"⚠️ Micron parser not found: {micron_path}")
            print("   Fallback parser will be used")

        dom_path = os.path.join('script', 'purify.min.js')
        if os.path.exists(dom_path):
            print(f"✅ Found DOMPurify: {dom_path}")
        else:
            print(f"⚠️ DOMPurify not found: {dom_path}")
        
        # Verify browser was initialized successfully
        if not hasattr(browser, 'reticulum_ready') or not browser.reticulum_ready:
            print("❌ Browser initialization failed - Reticulum not ready")
            return 1
            
        if not hasattr(browser, 'identity') or browser.identity is None:
            print("❌ Browser initialization failed - No identity created")
            return 1

        # Start announce monitoring
        browser.start_monitoring()
        
        host_display = 'localhost' if args.host == '0.0.0.0' else args.host
        print(f"🌐 Starting local web server on http://{host_display}:{args.port}")
        print("📡 Listening for NomadNetwork announces...")
        print(f"🔍 Open your browser to http://{host_display}:{args.port}")
        print("=========== Press Ctrl+C to stop and exit ============\n")

        # Start the web server
        start_server(args.host, args.port)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n👋 NomadNet Browser shutting down...")
        browser.running = False
        if hasattr(browser, 'connection_state'):
            browser.connection_state = "shutdown"
        print("✅ Shutdown complete")
        return 0
        
    except Exception as e:
        print(f"\n❌ Startup failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        
        # Set failed state for status API
        if hasattr(browser, 'connection_state'):
            browser.connection_state = "failed"
        else:
            # If browser object doesn't have connection_state, something went very wrong
            print("   Browser object may not be properly initialized")
        
        # Print some diagnostic info
        if hasattr(browser, 'reticulum'):
            print(f"   Reticulum object exists: {browser.reticulum is not None}")
        else:
            print("   No reticulum attribute found on browser object")
            
        if hasattr(browser, 'identity'):
            print(f"   Identity exists: {browser.identity is not None}")
        else:
            print("   No identity attribute found on browser object")
            
        return 1

if __name__ == "__main__":
    main()