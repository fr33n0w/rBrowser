#!/usr/bin/env python3
"""
NomadNet protocol helpers.

This module contains the low-level helpers that interact with Reticulum
NomadNet nodes. They are intentionally focused on network communication and
avoid any direct dependency on Flask or higher-level application concerns.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import RNS


def _clean_hash(destination_hash: str) -> bytes:
    """Convert NomadNet destination hash strings into raw bytes."""
    stripped = destination_hash.replace("<", "").replace(">", "").replace(":", "")
    return bytes.fromhex(stripped)


def _wait_for_path(destination_hash: bytes, timeout: float = 30) -> bool:
    """
    Ensure Reticulum has a path to the destination before continuing.

    Returns True when a path becomes available inside the timeout window.
    """
    if RNS.Transport.has_path(destination_hash):
        return True

    RNS.Transport.request_path(destination_hash)
    start_time = time.time()

    while not RNS.Transport.has_path(destination_hash):
        if time.time() - start_time > timeout:
            return False
        time.sleep(0.1)

    return True


def _recall_destination(destination_hash: bytes) -> Optional[RNS.Identity]:
    """Recall an identity for the provided destination hash."""
    identity = RNS.Identity.recall(destination_hash)
    if not identity:
        print("❌ Could not recall identity for destination "
              f"{RNS.prettyhexrep(destination_hash)[:16]}...")
    return identity


@dataclass
class RequestResult:
    """Simple container for asynchronous NomadNet responses."""

    data: Any = None
    received: bool = False
    rtt: Optional[float] = None


class NomadNetBrowser:
    """
    High-level NomadNet page fetch helper.

    Instances are short lived and typically created per request, receiving
    a reference to the owning web browser instance for caching and identity
    management.
    """

    def __init__(self, main_browser: "NomadNetWebBrowser", destination_hash: str) -> None:
        self.main_browser = main_browser
        self.destination_hash = _clean_hash(destination_hash)

        self.destination: Optional[RNS.Destination] = None
        self.link: Optional[RNS.Link] = None
        self.result = RequestResult()
        self.response_event = threading.Event()
        self.page_path: str = "/page/index.mu"
        self.form_data: Optional[Dict[str, Any]] = None
        self.ping_start_time: Optional[float] = None

    # ------------------------------------------------------------------ #
    # Page fetching                                                      #
    # ------------------------------------------------------------------ #

    def fetch_page(
        self,
        page_path: str = "/page/index.mu",
        form_data: Optional[Dict[str, Any]] = None,
        timeout: float = 30,
    ) -> Dict[str, Any]:
        """Fetch a page from the remote NomadNet node."""
        try:
            pretty_hash = RNS.prettyhexrep(self.destination_hash)[:16]
            print(f"🔍 Checking path to {pretty_hash}...")

            if not _wait_for_path(self.destination_hash, timeout=timeout):
                return {"error": "No path", "content": "No path to destination", "status": "error"}

            identity = _recall_destination(self.destination_hash)
            if not identity:
                return {"error": "No identity", "content": "Could not recall identity", "status": "error"}

            print("✅ Path found, establishing connection...")

            self.destination = RNS.Destination(
                identity,
                RNS.Destination.OUT,
                RNS.Destination.SINGLE,
                "nomadnetwork",
                "node",
            )
            self.link = RNS.Link(self.destination)
            self.result = RequestResult()
            self.response_event.clear()

            self.page_path = page_path
            self.form_data = form_data or None

            if self.form_data:
                print(f"🌐 Requesting page: {page_path} with form data: {self.form_data}")
            else:
                print(f"🌐 Requesting page: {page_path}")

            self.link.set_link_established_callback(self._on_link_established)
            success = self.response_event.wait(timeout=timeout)

            if success and self.result.received:
                return {
                    "content": self.result.data or "Empty response",
                    "status": "success",
                    "error": None,
                }

            return {"error": "Timeout", "content": "Request timeout", "status": "error"}

        except Exception as exc:  # pragma: no cover - defensive logging
            print(f"❌ Exception during fetch: {exc}")
            return {"error": str(exc), "content": f"Exception: {exc}", "status": "error"}

    def _on_link_established(self, link: RNS.Link) -> None:
        """Handle the moment the Reticulum link is established."""
        try:
            if self.form_data:
                print(f"🔗 Link established, requesting: {self.page_path} with field_data: {self.form_data}")
                prefixed_data = self._build_prefixed_form_data(self.form_data)
                print(f"📝 Prefixed form data: {prefixed_data}")
                link.request(
                    self.page_path,
                    data=prefixed_data,
                    response_callback=self._on_response,
                    failed_callback=self._on_request_failed,
                )
                return

            print(f"🔗 Link established, requesting: {self.page_path}")
            link.request(
                self.page_path,
                data=None,
                response_callback=self._on_response,
                failed_callback=self._on_request_failed,
            )

        except Exception as exc:
            print(f"❌ Request error: {exc}")
            self.result = RequestResult(data=f"Request error: {exc}", received=True)
            self.response_event.set()

    @staticmethod
    def _build_prefixed_form_data(form_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Some NomadNet applications expect both field_ and var_ prefixes.
        Provide both to maximise compatibility.
        """
        prefixed: Dict[str, str] = {}
        for key, value in form_data.items():
            prefixed[f"var_{key}"] = str(value)
            prefixed[f"field_{key}"] = str(value)
        return prefixed

    def _on_response(self, receipt: RNS.RequestReceipt) -> None:
        """Process successful responses."""
        try:
            data = receipt.response
            if data:
                if isinstance(data, bytes):
                    try:
                        decoded = data.decode("utf-8")
                        self.result.data = decoded
                        print(f"✅ Received {len(decoded)} characters")
                    except UnicodeDecodeError:
                        self.result.data = f"Binary data: {data.hex()[:200]}..."
                        print(f"⚠️ Received binary data: {len(data)} bytes")
                else:
                    text = str(data)
                    self.result.data = text
                    print(f"✅ Received text data: {len(text)} characters")
            else:
                self.result.data = "Empty response"
                print("⚠️ Empty response received")

            self.result.received = True
            self.response_event.set()

        except Exception as exc:
            print(f"❌ Response processing error: {exc}")
            self.result = RequestResult(data=f"Response error: {exc}", received=True)
            self.response_event.set()

    def _on_request_failed(self, _receipt: RNS.RequestReceipt) -> None:
        """Handle failed requests."""
        print("❌ Request failed")
        self.result = RequestResult(data="Request failed", received=True)
        self.response_event.set()

    # ------------------------------------------------------------------ #
    # Ping & fingerprint helpers                                         #
    # ------------------------------------------------------------------ #

    def ping_node(self, node_hash: str) -> Dict[str, Any]:
        """Convenience wrapper around send_ping for compatibility."""
        try:
            print(f"Pinging node {node_hash[:16]}...")
            browser = NomadNetBrowser(self.main_browser, node_hash)
            return browser.send_ping()
        except Exception as exc:
            print(f"Ping failed: {exc}")
            return {"error": f"Ping failed: {exc}", "message": "", "status": "error"}

    def send_ping(self, timeout: float = 15) -> Dict[str, Any]:
        """Send a ping to test reachability."""
        try:
            pretty_hash = RNS.prettyhexrep(self.destination_hash)[:16]
            print(f"Pinging {pretty_hash}...")

            if not _wait_for_path(self.destination_hash, timeout=timeout):
                return {"error": "No path", "message": "No path to destination", "status": "error"}

            identity = _recall_destination(self.destination_hash)
            if not identity:
                return {"error": "No identity", "message": "Could not recall identity", "status": "error"}

            print("✅ Path found, measuring round-trip time...")
            destination = RNS.Destination(
                identity,
                RNS.Destination.OUT,
                RNS.Destination.SINGLE,
                "nomadnetwork",
                "node",
            )

            self.link = RNS.Link(destination)
            self.result = RequestResult()
            self.response_event.clear()
            self.ping_start_time = time.time()

            self.link.set_link_established_callback(self._on_ping_link_established)
            success = self.response_event.wait(timeout=timeout)

            if success and self.result.received:
                rtt = self.result.rtt or 0.0
                return {
                    "message": f"Pong received! Round-trip time: {rtt:.2f}s",
                    "rtt": rtt,
                    "status": "success",
                    "error": None,
                }

            return {"error": "Timeout", "message": "Ping timeout", "status": "error"}

        except Exception as exc:
            print(f"❌ Exception during ping: {exc}")
            return {"error": str(exc), "message": f"Exception: {exc}", "status": "error"}

    def _on_ping_link_established(self, link: RNS.Link) -> None:
        try:
            print("🔗 Ping link established, sending ping request...")
            link.request(
                "/page/index.mu",
                data=None,
                response_callback=self._on_ping_response,
                failed_callback=self._on_ping_failed,
            )
        except Exception as exc:  # pragma: no cover - defensive logging
            print(f"❌ Ping request error: {exc}")
            self.result.received = True
            self.response_event.set()

    def _on_ping_response(self, _receipt: RNS.RequestReceipt) -> None:
        try:
            if self.ping_start_time is None:
                raise RuntimeError("Ping start time not set")

            rtt = time.time() - self.ping_start_time
            self.result.rtt = rtt
            self.result.received = True
            print(f"✅ Pong! RTT: {rtt:.2f}s")
            self.response_event.set()
        except Exception as exc:
            print(f"❌ Ping response error: {exc}")
            self.result.received = True
            self.response_event.set()

    def _on_ping_failed(self, _receipt: RNS.RequestReceipt) -> None:
        print("❌ Ping failed")
        self.result.received = True
        self.response_event.set()

    def send_fingerprint(self, timeout: float = 30) -> Dict[str, Any]:
        """
        Send fingerprint using RNS link.identify() like MeshChat.
        Mirrors the legacy behaviour from the monolithic implementation.
        """
        try:
            pretty_hash = RNS.prettyhexrep(self.destination_hash)[:16]
            print(f"Sending fingerprint to {pretty_hash}...")

            cached_links = getattr(self.main_browser, "nomadnet_cached_links", {})
            existing_link = cached_links.get(self.destination_hash)

            if existing_link and existing_link.status == RNS.Link.ACTIVE:
                print("Using existing cached link for identity establishment")
                self._identify_over_link(existing_link)
                return {"message": "Identity established on existing link", "status": "success", "error": None}

            response = self.main_browser.fetch_page(self.destination_hash.hex(), "/page/index.mu")

            if response["status"] == "success":
                cached_links = getattr(self.main_browser, "nomadnet_cached_links", {})
                link = cached_links.get(self.destination_hash)
                if link:
                    self._identify_over_link(link)
                    return {"message": "Identity established on new link", "status": "success", "error": None}

            return {"error": "Failed to establish link", "message": "Could not create or identify on link", "status": "error"}

        except Exception as exc:
            print(f"Exception during fingerprint send: {exc}")
            return {"error": str(exc), "message": f"Exception: {exc}", "status": "error"}

    def _identify_over_link(self, link: RNS.Link) -> None:
        """Attach identity information to a link and cache LXMF destination."""
        link.identify(self.main_browser.identity)
        lxmf_dest_hash = RNS.Destination.hash(self.main_browser.identity, "lxmf", "delivery")
        link.fingerprint_data = {"dest": lxmf_dest_hash.hex()}

        print(f"Identity established on link: {RNS.prettyhexrep(self.main_browser.identity.hash)}")
        print(f"LXMF dest stored: {lxmf_dest_hash.hex()}")


class NomadNetFileBrowser:
    """Helper for downloading binary files from NomadNet nodes."""

    def __init__(self, main_browser: "NomadNetWebBrowser", destination_hash: str) -> None:
        self.main_browser = main_browser
        self.destination_hash = _clean_hash(destination_hash)

        self.destination: Optional[RNS.Destination] = None
        self.link: Optional[RNS.Link] = None
        self.result = RequestResult()
        self.response_event = threading.Event()
        self.file_path: str = ""

    def fetch_file(self, file_path: str, timeout: float = 60) -> Dict[str, Any]:
        """Fetch a binary file from the remote node."""
        try:
            pretty_hash = RNS.prettyhexrep(self.destination_hash)[:16]
            print(f"🔍 Checking path to {pretty_hash} for file...")

            if not _wait_for_path(self.destination_hash, timeout=timeout):
                return {"error": "No path", "content": b"", "status": "error"}

            identity = _recall_destination(self.destination_hash)
            if not identity:
                return {"error": "No identity", "content": b"", "status": "error"}

            print("✅ Path found, establishing connection for file transfer...")

            self.destination = RNS.Destination(
                identity,
                RNS.Destination.OUT,
                RNS.Destination.SINGLE,
                "nomadnetwork",
                "node",
            )
            self.link = RNS.Link(self.destination)
            self.result = RequestResult()
            self.response_event.clear()
            self.file_path = file_path

            print(f"📁 Requesting file: {file_path}")
            self.link.set_link_established_callback(self._on_link_established)
            success = self.response_event.wait(timeout=timeout)

            if success and self.result.received:
                return {"content": self.result.data or b"", "status": "success", "error": None}

            return {"error": "Timeout", "content": b"", "status": "error"}

        except Exception as exc:
            print(f"❌ Exception during file fetch: {exc}")
            return {"error": str(exc), "content": b"", "status": "error"}

    def _on_link_established(self, link: RNS.Link) -> None:
        try:
            print(f"🔗 Link established, requesting file: {self.file_path}")
            link.request(
                self.file_path,
                data=None,
                response_callback=self._on_response,
                failed_callback=self._on_request_failed,
            )
        except Exception as exc:
            print(f"❌ File request error: {exc}")
            self.result = RequestResult(data=b"", received=True)
            self.response_event.set()

    def _on_response(self, receipt: RNS.RequestReceipt) -> None:
        try:
            data = receipt.response
            print(f"📁 Received response type: {type(data)}")

            if isinstance(data, bytes):
                self.result.data = data
                print(f"✅ Received file data: {len(data)} bytes")
            elif isinstance(data, str):
                encoded = data.encode("utf-8")
                self.result.data = encoded
                print(f"✅ Received text file: {len(data)} characters")
            elif isinstance(data, list):
                self.result.data = self._handle_list_response(data)
            elif hasattr(data, "read"):
                self.result.data = self._read_file_object(data)
            else:
                print(f"❌ Unknown data type: {type(data)}")
                self.result.data = b""

            self.result.received = True
            self.response_event.set()

        except Exception as exc:
            print(f"❌ File response processing error: {exc}")
            self.result = RequestResult(data=b"", received=True)
            self.response_event.set()

    def _handle_list_response(self, data: list[Any]) -> bytes:
        """Handle list responses, preserving binary data whenever possible."""
        try:
            if all(isinstance(item, bytes) for item in data):
                combined = b"".join(data)
                print(f"✅ Joined {len(data)} byte chunks: {len(combined)} total bytes")
                return combined

            binary_parts = []
            for item in data:
                if isinstance(item, bytes):
                    binary_parts.append(item)
                elif isinstance(item, str):
                    binary_parts.append(item.encode("latin1"))
                else:
                    print(f"⚠️ Unexpected item type: {type(item)}")

            combined = b"".join(binary_parts)
            print(f"✅ Processed mixed list: {len(combined)} total bytes")
            return combined

        except Exception as exc:
            print(f"❌ Error processing list data: {exc}")
            return b""

    @staticmethod
    def _read_file_object(file_obj: Any) -> bytes:
        """Read and normalise data from file-like objects."""
        try:
            if hasattr(file_obj, "seek"):
                file_obj.seek(0)
            content = file_obj.read()
            if hasattr(file_obj, "close"):
                file_obj.close()

            if isinstance(content, bytes):
                print(f"✅ Successfully read file: {len(content)} bytes")
                return content

            encoded = content.encode("latin1")
            print(f"✅ Successfully read file (text -> bytes): {len(encoded)} bytes")
            return encoded

        except Exception as exc:
            print(f"❌ Error reading file object: {exc}")
            return b""

    def _on_request_failed(self, _receipt: RNS.RequestReceipt) -> None:
        print("❌ File request failed")
        self.result = RequestResult(data=b"", received=True)
        self.response_event.set()


class NomadNetAnnounceHandler:
    """Reticulum announce handler façade."""

    def __init__(self, browser: "NomadNetWebBrowser") -> None:
        self.browser = browser
        self.aspect_filter = "nomadnetwork.node"

    def received_announce(
        self,
        destination_hash: bytes,
        announced_identity: RNS.Identity,
        app_data: Optional[bytes],
    ) -> None:
        self.browser.process_nomadnet_announce(destination_hash, announced_identity, app_data)


# Circular imports are only needed for type checking.
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from .web_browser import NomadNetWebBrowser
