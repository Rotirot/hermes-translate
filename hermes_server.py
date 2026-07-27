"""
Hermes Translate — Local HTTP Server
=====================================
Runs a lightweight server on localhost:7473 so the browser extension
can send text for translation without any internet connection.

Usage:
    python hermes_server.py

Keep this running in the background while using the browser extension.
The server only accepts connections from localhost — it is not exposed
to the network.
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

# Re-use core translation logic from hermes.py
import importlib, sys, os
sys.path.insert(0, os.path.dirname(__file__))

try:
    from hermes import translate_chunks, LANGUAGE_PAIRS, PAIR_LABELS
except ImportError:
    print("ERROR: hermes.py must be in the same folder as hermes_server.py")
    sys.exit(1)

HOST = "127.0.0.1"
PORT = 7473


class HermesHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        # Suppress default access logs; print a cleaner line
        print(f"  [{self.command}] {self.path.split('?')[0]}")

    def _send_json(self, data: dict, status: int = 200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        # Allow the unpacked extension to call us
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_cors_preflight(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._send_cors_preflight()

    def do_GET(self):
        if self.path == "/pairs":
            pairs = [{"label": lbl,
                      "from": LANGUAGE_PAIRS[i][1],
                      "to":   LANGUAGE_PAIRS[i][3]}
                     for i, lbl in enumerate(PAIR_LABELS)]
            self._send_json({"pairs": pairs})
        elif self.path == "/ping":
            self._send_json({"status": "ok", "version": "1.0"})
        else:
            self._send_json({"error": "Not found"}, 404)

    def do_POST(self):
        if self.path != "/translate":
            self._send_json({"error": "Not found"}, 404)
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            text      = body.get("text", "").strip()
            from_code = body.get("from", "en")
            to_code   = body.get("to",   "fr")
            if not text:
                self._send_json({"error": "No text provided"}, 400)
                return
            result = translate_chunks(text, from_code, to_code)
            self._send_json({"translation": result})
        except Exception as e:
            self._send_json({"error": str(e)}, 500)


def run():
    server = HTTPServer((HOST, PORT), HermesHandler)
    print(f"\n  ⬡  Hermes server running on http://{HOST}:{PORT}")
    print(f"     Load the browser extension, then right-click any text to translate.")
    print(f"     Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")
        server.server_close()


if __name__ == "__main__":
    run()
