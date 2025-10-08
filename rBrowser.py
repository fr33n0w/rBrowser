#!/usr/bin/env python3
"""
rBrowser entrypoint.

This module keeps the runtime bootstrap logic lean by delegating the majority
of the work to the `rbrowser` package. It exists primarily to provide a CLI
interface and to remain compatible with the historical `python rBrowser.py`
usage.
"""

from __future__ import annotations

import argparse
import logging
import os
import secrets
import sys
from typing import Tuple

from flask import Flask

from rbrowser.routes import register_routes
from rbrowser.web_browser import NomadNetWebBrowser


# Ensure UTF-8 output for Windows console
if sys.platform == "win32":
    try:
        os.system("chcp 65001 >nul")
    except Exception:
        pass


def create_app() -> Tuple[Flask, NomadNetWebBrowser]:
    """Factory used by both the CLI entrypoint and potential WSGI imports."""
    app = Flask(__name__)
    app.secret_key = secrets.token_hex(16)

    browser = NomadNetWebBrowser()
    register_routes(app, browser)
    return app, browser


app, browser = create_app()


def start_server(flask_app: Flask, host: str = "0.0.0.0", port: int = 5000) -> None:
    """Start the HTTP server, preferring Waitress when available."""
    try:
        from waitress import serve

        print("🚀 Local Web Interface starting with Waitress server...")
        serve(flask_app, host=host, port=port, threads=8)
    except ImportError:
        logging.getLogger("werkzeug").setLevel(logging.ERROR)
        print("⚠️  Waitress not found, falling back to Flask dev server...")
        print("🚀 Local Web Interface starting...")
        flask_app.run(host=host, port=port, debug=False, threaded=True)


def main() -> int:
    """CLI entrypoint with sanity checks before serving traffic."""
    parser = argparse.ArgumentParser(description="rBrowser - Standalone NomadNet Browser")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind the web server to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=5000, help="Port to run the web server on (default: 5000)")
    args = parser.parse_args()

    try:
        template_path = os.path.join("templates", "index.html")
        if os.path.exists(template_path):
            print(f"✅ Found HTML template: {template_path}")
        else:
            print(f"❌ HTML template not found: {template_path}")
            print("   Please verify templates/ directory and index.html file")
            return 1

        micron_path = os.path.join("script", "micron-parser_original.js")
        if os.path.exists(micron_path):
            print(f"✅ Found Micron parser: {micron_path}")
        else:
            print(f"⚠️ Micron parser not found: {micron_path}")
            print("   Fallback parser will be used")

        dom_path = os.path.join("script", "purify.min.js")
        if os.path.exists(dom_path):
            print(f"✅ Found DOMPurify: {dom_path}")
        else:
            print(f"⚠️ DOMPurify not found: {dom_path}")

        if not getattr(browser, "reticulum_ready", False):
            print("❌ Browser initialization failed - Reticulum not ready")
            return 1

        if not getattr(browser, "identity", None):
            print("❌ Browser initialization failed - No identity created")
            return 1

        browser.start_monitoring()

        host_display = "localhost" if args.host == "0.0.0.0" else args.host
        print(f"🌐 Starting local web server on http://{host_display}:{args.port}")
        print("📡 Listening for NomadNetwork announces...")
        print(f"🔍 Open your browser to http://{host_display}:{args.port}")
        print("=========== Press Ctrl+C to stop and exit ============\n")

        start_server(app, args.host, args.port)
        return 0

    except KeyboardInterrupt:
        print("\n👋 NomadNet Browser shutting down...")
        browser.running = False
        if hasattr(browser, "connection_state"):
            browser.connection_state = "shutdown"
        print("✅ Shutdown complete")
        return 0

    except Exception as exc:
        print(f"\n❌ Startup failed: {exc}")
        print(f"   Error type: {type(exc).__name__}")

        if hasattr(browser, "connection_state"):
            browser.connection_state = "failed"

        if hasattr(browser, "reticulum"):
            print(f"   Reticulum object exists: {browser.reticulum is not None}")
        else:
            print("   No reticulum attribute found on browser object")

        if hasattr(browser, "identity"):
            print(f"   Identity exists: {browser.identity is not None}")
        else:
            print("   No identity attribute found on browser object")

        return 1


if __name__ == "__main__":
    sys.exit(main())
