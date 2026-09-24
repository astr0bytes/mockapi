"""HTTP server built on http.server."""

import json
import random
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

from mockapi.router import render_body, serialize

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "*",
}


def make_handler(source, cors: bool):
    class MockHandler(BaseHTTPRequestHandler):
        server_version = "mockapi"

        def _read_body(self):
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length) if length else b""
            try:
                return json.loads(raw) if raw else None
            except json.JSONDecodeError:
                return raw.decode(errors="replace")

        def _send(self, status: int, payload: bytes, content_type: str, headers: dict):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            for name, value in {**self.default_headers, **(CORS_HEADERS if cors else {}), **headers}.items():
                self.send_header(name, value)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(payload)

        def _handle(self):
            url = urlsplit(self.path)
            router, self.default_headers = source.current()
            request_body = self._read_body()

            if cors and self.command == "OPTIONS":
                return self._send(204, b"", "text/plain", {})

            match = router.match(self.command, url.path)
            if match is None:
                allowed = router.allowed_methods(url.path)
                if allowed:
                    payload, ctype = serialize({"error": "method not allowed", "allowed": allowed})
                    return self._send(405, payload, ctype, {"Allow": ", ".join(allowed)})
                payload, ctype = serialize({"error": "not found", "path": url.path})
                return self._send(404, payload, ctype, {})

            route = match.route
            if route.delay_ms:
                time.sleep(route.delay_ms / 1000)

            if route.fail_rate and random.random() < route.fail_rate:
                payload, ctype = serialize({"error": "simulated failure"})
                return self._send(500, payload, ctype, {})

            if route.echo:
                body = {
                    "method": self.command,
                    "path": url.path,
                    "params": match.params,
                    "query": dict(parse_qsl(url.query)),
                    "headers": dict(self.headers),
                    "body": request_body,
                }
            elif route.body_file:
                body = Path(route.body_file).read_text()
                if route.body_file.endswith(".json"):
                    body = json.loads(body)
            else:
                body = route.body

            context = {"params": match.params, "query": dict(parse_qsl(url.query))}
            payload, ctype = serialize(render_body(body, context))
            self._send(route.status, payload, ctype, route.headers)

        do_GET = do_POST = do_PUT = do_PATCH = do_DELETE = do_HEAD = do_OPTIONS = _handle

        def log_message(self, fmt, *args):
            stamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{stamp}] {self.address_string()} {fmt % args}")

    return MockHandler


def serve(source, host: str, port: int, cors: bool = False):
    handler = make_handler(source, cors)
    with ThreadingHTTPServer((host, port), handler) as httpd:
        print(f"mockapi listening on http://{host}:{port} (Ctrl+C to stop)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")
