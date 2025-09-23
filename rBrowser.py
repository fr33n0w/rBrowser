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
        
        
        print("=" * 90)
        print("🌐 rBrowser v1.0 - Standalone Nomadnet Browser - https://github.com/fr33n0w/rBrowser")
        print("=" * 90)
        print("⚡ Initializing rBrowser v1.0 NomadNet Web Browser...")
        print("📋 RNS LOG LEVEL SET TO: CRITICAL")
        print("🔗 Connecting to Reticulum...")
        print("=" * 90)
        self.init_reticulum()
        
    def init_reticulum(self):
        try:
            # Set initial connecting state
            self.connection_state = "connecting"
            
            print("🔗 Connecting to Reticulum...")
            RNS.loglevel = RNS.LOG_CRITICAL
            self.reticulum = RNS.Reticulum()
            
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
        
        # CRITICAL FIX: Update connection state to "active" when we receive valid announces
        if self.connection_state == "connected":
            self.connection_state = "active"
            print(f"🟢 Connection state updated to ACTIVE (received first valid announce)")
        
        print(f"🌐 NomadNet Announce #{self.announce_count}: {clean_hash_str} -> {node_name} (node announces: {self.nomadnet_nodes[hash_str]['node_announce_count']})")

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
            print(f"🌐 Fetching {page_path} from {node_hash[:16]}...")
            if form_data:
                print(f"📝 With form data: {form_data}")
            browser = NomadNetBrowser(self, node_hash)
            response = browser.fetch_page(page_path, form_data)  # Pass the form_data parameter
            return response
        except Exception as e:
            print(f"❌ Fetch failed: {str(e)}")
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
            if app_uptime < 45:
                return jsonify({
                    "status": "waiting", 
                    "message": "Waiting for announces...",
                    "color": "yellow"
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
                        "message": "No recent announces (connection may be stale)",
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

def start_server():
    """Automatically choose the best server available"""
    import platform
    
    # Try Waitress first on Windows
    if platform.system() == "Windows":
        try:
            from waitress import serve
            print("🚀 Local Web Interface served with Waitress (Windows optimized)...")
            print("📝 Web Server Access logs disabled for cleaner terminal output")
            print("✅ Interface started, Waiting for NomadNet announces... ")
            print("=" * 90)
            serve(app, host='0.0.0.0', port=5000, threads=8)
            return
        except ImportError:
            pass
    
    # Try Gunicorn on Unix/Linux
    try:
        import gunicorn.app.wsgiapp as wsgi
        # Configure gunicorn to suppress access logs
        sys.argv = [
            'gunicorn',
            '--bind', '0.0.0.0:5000',
            '--workers', '4',
            '--access-logfile', '/dev/null',  # Disable access logs
            '--error-logfile', '-',           # Errors to stderr
            '--log-level', 'warning',         # Only warnings and errors
            f'{os.path.basename(__file__).split(".")[0]}:app'
        ]
        print("🚀 Local Web Interface served with Gunicorn for optimal performance...")
        print("📝 Web Server Access logs disabled for cleaner terminal output")
        print("✅ Interface started, Waiting for NomadNet announces... ")
        print("=" * 90)
        wsgi.run()
        return
    except ImportError:
        pass
    
    # Fallback to Flask development server
    system_name = platform.system()
    if system_name == "Windows":
        print("⚠️  Waitress not found - using Flask development server")
        print("   For better performance on Windows: pip install waitress")
    else:
        print("⚠️  Gunicorn not found - using Flask development server")
        print("   For better performance: pip install gunicorn")
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)

def main():
    """
    Main function with improved error handling and status management
    """
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
        
        print("🌐 Starting local web server on http://localhost:5000")
        print("📡 Listening for NomadNetwork announces...")
        print("🔍 Open your browser to http://localhost:5000")
        print("=========== Press Ctrl+C to stop and exit ============\n")
        
        # Start the web server
        start_server()
        
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