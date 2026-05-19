from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional

from .service import SoundLocalizationService


def _html() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>snur - sound localization</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 24px; }
    #grid { width: 440px; height: 440px; border: 1px solid #aaa; position: relative; background: #f9f9f9; }
    #dot { width: 14px; height: 14px; border-radius: 50%; background: #2a7fff; position: absolute; transform: translate(-50%, -50%); }
    .row { margin: 12px 0; }
  </style>
</head>
<body>
  <h1>snur - 2D Sound Localization</h1>
  <div class="row">Status: <span id="status">loading...</span></div>
  <div class="row">Coordinates: <span id="coords">-</span></div>
  <div class="row">
    <div id="grid"><div id="dot"></div></div>
  </div>
  <pre id="diag"></pre>
  <script>
    const min = -1.5, max = 1.5, size = 440;
    const dot = document.getElementById("dot");
    function scale(v){ return ((v - min) / (max - min)) * size; }
    async function refresh() {
      try {
        const r = await fetch('/api/location');
        const j = await r.json();
        document.getElementById('status').textContent = j.status;
        if (j.location) {
          const x = j.location.x, y = j.location.y;
          document.getElementById('coords').textContent = `x=${x.toFixed(3)}, y=${y.toFixed(3)}`;
          dot.style.left = `${scale(x)}px`;
          dot.style.top = `${size - scale(y)}px`;
          document.getElementById('diag').textContent = JSON.stringify(j.location.diagnostics, null, 2);
        }
      } catch (e) {
        document.getElementById('status').textContent = 'error';
      }
    }
    setInterval(refresh, 400);
    refresh();
  </script>
</body>
</html>
"""


def make_handler(service: SoundLocalizationService):
    class Handler(BaseHTTPRequestHandler):
        def _send_json(self, payload: object, status: int = 200) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_html(self, body: str) -> None:
            encoded = body.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/" or self.path == "/index.html":
                self._send_html(_html())
                return
            if self.path == "/api/status":
                self._send_json({"status": "ok"})
                return
            if self.path == "/api/location":
                snap = service.latest()
                if snap is None:
                    self._send_json({"status": "warming_up", "location": None})
                else:
                    self._send_json(
                        {
                            "status": "ok",
                            "location": {
                                "timestamp": snap.timestamp,
                                "x": snap.x,
                                "y": snap.y,
                                "diagnostics": snap.diagnostics,
                            },
                        }
                    )
                return
            self._send_json({"error": "not_found"}, status=404)

        def log_message(self, format: str, *args: object) -> None:  # noqa: A003
            return

    return Handler


def run_server(host: str, port: int, service: SoundLocalizationService) -> None:
    server = ThreadingHTTPServer((host, port), make_handler(service))
    try:
        server.serve_forever()
    finally:
        server.server_close()

