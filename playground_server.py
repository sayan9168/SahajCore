import json, io, contextlib
from http.server import BaseHTTPRequestHandler, HTTPServer
from lexer import tokenize
from parser import Parser
from interpreter import Interp

HTML = """<!DOCTYPE html><html><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>SahajCore Playground</title>
<style>body{background:#0d1117;color:#e6edf3;font-family:monospace;padding:16px}
textarea{width:100%;height:200px;background:#161b22;color:#7ee787;border:1px solid #30363d;border-radius:6px;padding:10px;font-family:monospace}
button{background:#238636;color:#fff;border:0;padding:10px 20px;border-radius:6px;margin:10px 0;font-size:16px}
pre{background:#161b22;border:1px solid #30363d;border-radius:6px;padding:10px;min-height:100px;white-space:pre-wrap}</style></head>
<body><h1>SahajCore Playground</h1>
<textarea id=code>let x = 10
fn double(n) { return n * 2 }
print(double(x))</textarea>
<button onclick=run()>Run</button>
<pre id=out></pre>
<script>async function run(){const code=document.getElementById('code').value;
const r=await fetch('/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({code})});
const d=await r.json();document.getElementById('out').textContent=d.output;}
run();</script></body></html>"""

class H(BaseHTTPRequestHandler):
    def _send(self, body, ctype='text/html'):
        data = body.encode()
        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)
    def do_GET(self): self._send(HTML)
    def do_POST(self):
        ln = int(self.headers.get('Content-Length', 0))
        code = json.loads(self.rfile.read(ln)).get('code', '')
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                Interp().run(Parser(tokenize(code)).parse())
            out = buf.getvalue()
        except Exception as e:
            out = 'Error: ' + str(e)
        self._send(json.dumps({'output': out}), 'application/json')
    def log_message(self, *a): pass

print("Playground: http://127.0.0.1:8080")
HTTPServer(('0.0.0.0', 8080), H).serve_forever()
