#!/usr/bin/env python3
"""Local GitHub Pages subpath preview: http://127.0.0.1:8765/study-notes/"""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import os
ROOT = Path(__file__).resolve().parent.parent/'docs'
BASE = os.getenv('SITE_BASE', '/study-notes/')
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs): super().__init__(*args,directory=str(ROOT),**kwargs)
    def do_GET(self):
        if self.path in ('/',BASE.rstrip('/')):
            self.send_response(302);self.send_header('Location',BASE);self.end_headers();return
        if not self.path.startswith(BASE):self.send_error(404);return
        self.path='/'+self.path[len(BASE):]
        super().do_GET()
print(f'Preview: http://127.0.0.1:8765{BASE}',flush=True)
ThreadingHTTPServer(('127.0.0.1',8765),Handler).serve_forever()
