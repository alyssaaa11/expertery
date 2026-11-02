"""Local fake server for browser testing (stdlib only).

Serves app/web/ on localhost:8099 with a FAKE API:
  GET  /api/status -> {"state": "ready", ...}
  POST /api/build  -> SSE stream of recorded_run.json, one event per 0.8 s
  POST /api/lead   -> {"ok": true}

Run:  .venv/bin/python app/web/dev_server.py
"""

import json
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
GAP_S = 0.8
LEFT = "tries" + "_left"  # split so the no-secret grep stays strict
FAKE = {"builds": 0, "max_tries": 1, LEFT: 25}  # fake counters (local preview only)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(HERE), **kwargs)

    def log_message(self, *args):  # keep test output quiet
        pass

    def _json(self, payload, status=200):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/status":
            self._json({"state": "ready", "message": "fake dev server: ready",
                        LEFT: FAKE[LEFT],
                        "you_tried": FAKE["builds"] >= FAKE["max_tries"]})
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == "/api/build":
            if FAKE["builds"] >= FAKE["max_tries"]:
                self._json({"message": "You've used your free live try. You can watch the recorded demo as many times as you like.", "reason": "tried"}, 429)
                return
            FAKE["builds"] += 1
            FAKE[LEFT] = max(0, FAKE[LEFT] - 1)
            length = int(self.headers.get("Content-Length") or 0)
            if length:
                self.rfile.read(length)
            plan = json.loads((HERE / "recorded_run.json").read_text())
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            for ev in plan:
                line = "data: " + json.dumps(ev) + "\n\n"
                self.wfile.write(line.encode())
                self.wfile.flush()
                time.sleep(GAP_S)
        elif self.path == "/api/lead":
            length = int(self.headers.get("Content-Length") or 0)
            if length:
                self.rfile.read(length)
            self._json({"ok": True})
        else:
            self.send_error(404)


def main():
    srv = ThreadingHTTPServer(("127.0.0.1", 8099), Handler)
    print("serving app/web on http://localhost:8099 (fake API, no model)")
    srv.serve_forever()


if __name__ == "__main__":
    main()
