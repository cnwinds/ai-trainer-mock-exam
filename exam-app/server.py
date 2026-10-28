# -*- coding: utf-8 -*-
"""人工智能训练师刷题系统 - 本地服务（仅依赖 Python 标准库）

python server.py  →  http://127.0.0.1:8765
"""
import json, os, sys, time, pathlib, threading, webbrowser
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote

APP = pathlib.Path(__file__).resolve().parent
ROOT = APP.parent
WEB = APP / "web"
BANK = APP / "data" / "bank"
PROGRESS = APP / "data" / "progress.json"
SUBMIT = APP / "submissions"
FEEDBACK = APP / "feedback"
DOCS = ROOT / "备考输出"
PORT = int(os.environ.get("PORT", "8848"))
LOCK = threading.Lock()

for d in (SUBMIT, FEEDBACK, PROGRESS.parent):
    d.mkdir(parents=True, exist_ok=True)


def read_json(p, default):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(p, obj):
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, p)


class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(WEB), **kw)

    def log_message(self, fmt, *args):
        if "/api/" in (args[0] if args else ""):
            sys.stderr.write("%s\n" % (fmt % args))

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        n = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(n).decode("utf-8")) if n else {}

    def do_GET(self):
        u = urlparse(self.path)
        p = u.path
        if p == "/api/bank":
            items, files = [], []
            for f in sorted(BANK.glob("*.json")):
                data = read_json(f, None)
                if not isinstance(data, list):
                    files.append({"file": f.name, "error": "invalid json"})
                    continue
                for q in data:
                    q["_file"] = f.name
                items.extend(data)
                files.append({"file": f.name, "count": len(data)})
            return self._json({"items": items, "files": files})
        if p == "/api/progress":
            return self._json(read_json(PROGRESS, {}))
        if p == "/api/doc":
            name = unquote(parse_qs(u.query).get("name", [""])[0])
            f = (DOCS / name).resolve()
            if DOCS.resolve() not in f.parents or not f.is_file():
                return self._json({"error": "not found"}, 404)
            return self._json({"name": name, "text": f.read_text(encoding="utf-8")})
        if p == "/api/submissions":
            out = []
            for f in sorted(SUBMIT.glob("*.json"), reverse=True):
                s = read_json(f, {})
                fb = read_json(FEEDBACK / f.name, None)
                out.append({"id": s.get("id"), "created": s.get("created"), "kind": s.get("kind"),
                            "title": s.get("title"), "autoScore": s.get("autoScore"), "maxScore": s.get("maxScore"),
                            "feedback": fb})
            return self._json(out)
        if p.startswith("/api/submission/"):
            sid = p.rsplit("/", 1)[-1]
            s = read_json(SUBMIT / f"{sid}.json", None)
            if s is None:
                return self._json({"error": "not found"}, 404)
            return self._json({"submission": s, "feedback": read_json(FEEDBACK / f"{sid}.json", None)})
        return super().do_GET()

    def do_POST(self):
        p = urlparse(self.path).path
        try:
            body = self._body()
        except Exception as e:
            return self._json({"error": str(e)}, 400)
        if p == "/api/progress":
            with LOCK:
                write_json(PROGRESS, body)
            return self._json({"ok": True})
        if p == "/api/submit":
            sid = body.get("id") or time.strftime("%Y%m%d-%H%M%S")
            body["id"] = sid
            with LOCK:
                write_json(SUBMIT / f"{sid}.json", body)
            return self._json({"ok": True, "id": sid})
        return self._json({"error": "unknown"}, 404)


def main():
    srv = None
    for port in (PORT, 8848, 18765, 28765, 0):
        try:
            srv = ThreadingHTTPServer(("127.0.0.1", port), H)
            break
        except OSError:
            continue
    url = f"http://127.0.0.1:{srv.server_address[1]}/"
    print(f"刷题系统已启动：{url}  (Ctrl+C 退出)", flush=True)
    if "--no-browser" not in sys.argv:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
