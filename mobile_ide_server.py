import json, io, os, contextlib
from http.server import BaseHTTPRequestHandler, HTTPServer
from lexer import tokenize
from parser import Parser
from interpreter import Interp

HTML = """<!DOCTYPE html><html><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1,maximum-scale=1">
<meta name=theme-color content=#0d1117><title>SahajCore IDE</title>
<style>body{background:#0d1117;color:#e6edf3;font-family:monospace;margin:0;padding:10px}
select,button{background:#21262d;color:#e6edf3;border:1px solid #30363d;border-radius:6px;padding:8px;margin:4px 2px;font-size:14px}
button.run{background:#238636;border:0;color:#fff}
textarea{width:100%;height:45vh;background:#161b22;color:#7ee787;border:1px solid #30363d;border-radius:6px;padding:10px;font-family:monospace;font-size:14px;box-sizing:border-box}
pre{background:#161b22;border:1px solid #30363d;border-radius:6px;padding:10px;height:20vh;overflow:auto;white-space:pre-wrap;font-size:13px}</style></head>
<body><h2>SahajCore IDE</h2>
<select id=files onchange=load()></select>
<button onclick=save()>Save</button>
<button class=run onclick=run()>Run</button>
<textarea id=code spellcheck=false></textarea>
<pre id=out></pre>
<script>
async function list(){const r=await fetch('/list');const f=await r.json();
const s=document.getElementById('files');s.innerHTML=f.map(x=>`<option>${x}</option>`).join('');load();}
async function load(){const n=document.getElementById('files').value;if(!n)return;
const r=await fetch('/read?name='+n);const d=await r.json();document.getElementById('code').value=d.code;}
async function save(){const n=document.getElementById('files').value;
await fetch('/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:n,code:document.getElementById('code').value})});alert('Saved');}
async function run(){const r=await fetch('/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({code:document.getElementById('code').value})});
const d=await r.json();document.getElementById('out').textContent=d.output;}
list();</script></body></html>"""

class H(BaseHTTPRequestHandler):
    def _send(self, body, ctype='text/html'):
        data = body.encode()
        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)
    def do_GET(self):
        if self.path == '/': self._send(HTML)
        elif self.path.startswith('/list'):
            files = [f for f in os.listdir('.') if f.endswith('.sahaj')]
            self._send(json.dumps(files), 'application/json')
        elif self.path.startswith('/read'):
            name = self.path.split('name=')[1]
            self._send(json.dumps({'code': open(name).read()}), 'application/json')
    def do_POST(self):
        ln = int(self.headers.get('Content-Length', 0))
        body = json.loads(self.rfile.read(ln))
        if self.path == '/save':
            open(body['name'], 'w').write(body['code'])
            self._send(json.dumps({'ok': True}), 'application/json')
        elif self.path == '/run':
            buf = io.StringIO()
            try:
                with contextlib.redirect_stdout(buf):
                    Interp().run(Parser(tokenize(body['code'])).parse())
                out = buf.getvalue()
            except Exception as e:
                out = 'Error: ' + str(e)
            self._send(json.dumps({'output': out}), 'application/json')
    def log_message(self, *a): pass

print("Mobile IDE: http://127.0.0.1:8081")
HTTPServer(('0.0.0.0', 8081), H).serve_forever()
