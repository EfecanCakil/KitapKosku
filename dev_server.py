"""Geliştirme sunucusu: arayüzü tarayıcıda test etmek için web/ klasörünü sunar ve Api metotlarını HTTP ile açar.

Kullanım: python dev_server.py [port]   →   http://127.0.0.1:8797
Yalnızca 127.0.0.1'de dinler.
"""
import json
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import app

WEB = Path(__file__).resolve().parent / "web"


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_POST(self):
        name = self.path.removeprefix("/api/")
        fn = getattr(app.api, name, None)
        if name.startswith("_") or not callable(fn):
            self.send_error(404)
            return
        args = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"[]")
        try:
            body = json.dumps(fn(*args), ensure_ascii=False, default=str).encode("utf-8")
            self.send_response(200)
        except Exception as e:  # noqa: BLE001
            body = str(e).encode("utf-8")
            self.send_response(500)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    import atexit

    atexit.register(app.api._tr.shutdown)
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8797
    print(f"http://127.0.0.1:{port}")
    ThreadingHTTPServer(("127.0.0.1", port), partial(Handler, directory=str(WEB))).serve_forever()
