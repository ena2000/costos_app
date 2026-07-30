"""Servidor local para subir fotos desde el celular (misma WiFi)."""
from __future__ import annotations

import json
import socket
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

PORT = 8765

HTML_PAGE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1"/>
<title>Subir fotos · COSTOS</title>
<style>
  body { font-family: system-ui, sans-serif; margin: 0; padding: 16px; background: #f4f6f8; color: #1a1a1a; }
  h1 { font-size: 1.25rem; margin: 0 0 6px; }
  p { color: #555; margin: 0 0 14px; line-height: 1.35; }
  .card { background: #fff; border-radius: 12px; padding: 16px; box-shadow: 0 1px 4px rgba(0,0,0,.08); }
  button, label.btn {
    display: block; width: 100%; box-sizing: border-box; margin: 8px 0;
    padding: 14px; font-size: 1rem; border: 0; border-radius: 10px;
    background: #1f6feb; color: #fff; text-align: center; cursor: pointer;
  }
  button.secondary, label.btn.secondary { background: #57606a; }
  button.send { background: #1a7f37; font-weight: 600; }
  button:disabled { opacity: .45; }
  input[type=file] { display: none; }
  #status { margin-top: 10px; font-size: .95rem; white-space: pre-wrap; }
  .ok { color: #1a7f37; }
  .err { color: #cf222e; }
  #count { font-weight: 600; margin: 8px 0 4px; }
  #gallery {
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px;
    margin: 10px 0 6px;
  }
  .thumb {
    position: relative; aspect-ratio: 1; border-radius: 8px; overflow: hidden;
    background: #eaeef2;
  }
  .thumb img { width: 100%; height: 100%; object-fit: cover; display: block; }
  .thumb button {
    position: absolute; top: 4px; right: 4px; width: 28px; height: 28px;
    margin: 0; padding: 0; border-radius: 50%; background: rgba(0,0,0,.65);
    font-size: 14px; line-height: 28px;
  }
</style>
</head>
<body>
  <div class="card">
    <h1>Fotos de la orden</h1>
    <p>Ve tomando o eligiendo fotos. Se van guardando aquí. Cuando tengas todas, envíalas de una vez.</p>

    <label class="btn">
      📷 Tomar / agregar foto
      <input id="files" type="file" accept="image/*" capture="environment" multiple/>
    </label>
    <label class="btn secondary">
      🖼️ Agregar de galería
      <input id="galleryPick" type="file" accept="image/*" multiple/>
    </label>

    <div id="count">0 fotos listas</div>
    <div id="gallery"></div>

    <button id="send" class="send" type="button" disabled>Enviar todas a la laptop</button>
    <button id="clear" class="secondary" type="button">Vaciar lista</button>
    <div id="status"></div>
  </div>
<script>
const statusEl = document.getElementById('status');
const countEl = document.getElementById('count');
const galleryEl = document.getElementById('gallery');
const sendBtn = document.getElementById('send');
const pending = []; // { name, data, previewUrl }

function refresh() {
  countEl.textContent = pending.length + (pending.length === 1 ? ' foto lista' : ' fotos listas');
  sendBtn.disabled = pending.length === 0;
  galleryEl.innerHTML = '';
  pending.forEach((item, idx) => {
    const div = document.createElement('div');
    div.className = 'thumb';
    const img = document.createElement('img');
    img.src = item.previewUrl;
    const del = document.createElement('button');
    del.type = 'button';
    del.textContent = '×';
    del.onclick = () => {
      URL.revokeObjectURL(item.previewUrl);
      pending.splice(idx, 1);
      refresh();
    };
    div.appendChild(img);
    div.appendChild(del);
    galleryEl.appendChild(div);
  });
}

async function addFiles(fileList) {
  const files = Array.from(fileList || []);
  for (const f of files) {
    if (!f.type.startsWith('image/')) continue;
    const b64 = await new Promise((resolve, reject) => {
      const r = new FileReader();
      r.onload = () => resolve(String(r.result).split(',')[1]);
      r.onerror = reject;
      r.readAsDataURL(f);
    });
    pending.push({
      name: f.name || ('foto_' + Date.now() + '.jpg'),
      data: b64,
      previewUrl: URL.createObjectURL(f),
    });
  }
  refresh();
  statusEl.className = '';
  statusEl.textContent = files.length ? 'Agregada(s). Sigue tomando más o envía todas.' : '';
}

document.getElementById('files').addEventListener('change', (e) => {
  addFiles(e.target.files);
  e.target.value = '';
});
document.getElementById('galleryPick').addEventListener('change', (e) => {
  addFiles(e.target.files);
  e.target.value = '';
});

document.getElementById('clear').onclick = () => {
  pending.forEach(p => URL.revokeObjectURL(p.previewUrl));
  pending.length = 0;
  refresh();
  statusEl.textContent = '';
};

sendBtn.onclick = async () => {
  if (!pending.length) return;
  statusEl.className = '';
  statusEl.textContent = 'Enviando ' + pending.length + ' foto(s)...';
  sendBtn.disabled = true;
  try {
    const res = await fetch('/upload', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        images: pending.map(p => ({ name: p.name, data: p.data }))
      })
    });
    const txt = await res.text();
    if (!res.ok) throw new Error(txt || res.status);
    statusEl.className = 'ok';
    statusEl.textContent = 'Listo. Las ' + pending.length + ' fotos ya están en la laptop.';
    pending.forEach(p => URL.revokeObjectURL(p.previewUrl));
    pending.length = 0;
    refresh();
  } catch (e) {
    statusEl.className = 'err';
    statusEl.textContent = 'Error: ' + e.message;
    sendBtn.disabled = pending.length === 0;
  }
};

refresh();
</script>
</body>
</html>
"""


def obtener_ip_local() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


class SubidaCelularServer:
    def __init__(self, on_archivo=None, port: int = PORT):
        self.port = port
        self.on_archivo = on_archivo
        self.upload_dir = Path(tempfile.mkdtemp(prefix="costos_fotos_"))
        self._httpd: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self.archivos_nuevos: list[str] = []
        self._lock = threading.Lock()

    @property
    def url(self) -> str:
        return f"http://{obtener_ip_local()}:{self.port}"

    def iniciar(self) -> str:
        if self._httpd:
            return self.url

        server = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                return

            def do_GET(self):
                path = urlparse(self.path).path
                if path in ("/", "/index.html"):
                    body = HTML_PAGE.encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                else:
                    self.send_error(404)

            def do_POST(self):
                if urlparse(self.path).path != "/upload":
                    self.send_error(404)
                    return
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    raw = self.rfile.read(length)
                    payload = json.loads(raw.decode("utf-8"))
                    guardados = []
                    for i, img in enumerate(payload.get("images") or []):
                        data_b64 = img.get("data") or ""
                        if not data_b64:
                            continue
                        import base64
                        data = base64.b64decode(data_b64)
                        nombre = img.get("name") or f"foto_{int(time.time())}_{i}.jpg"
                        safe = "".join(c for c in nombre if c.isalnum() or c in "._-") or f"foto_{i}.jpg"
                        if not Path(safe).suffix:
                            safe += ".jpg"
                        dest = server.upload_dir / f"{int(time.time() * 1000)}_{safe}"
                        dest.write_bytes(data)
                        guardados.append(str(dest))
                        with server._lock:
                            server.archivos_nuevos.append(str(dest))
                        if server.on_archivo:
                            server.on_archivo(str(dest))
                    body = json.dumps({"ok": True, "count": len(guardados)}).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                except Exception as e:
                    msg = str(e).encode("utf-8")
                    self.send_response(500)
                    self.send_header("Content-Type", "text/plain; charset=utf-8")
                    self.send_header("Content-Length", str(len(msg)))
                    self.end_headers()
                    self.wfile.write(msg)

        self._httpd = ThreadingHTTPServer(("0.0.0.0", self.port), Handler)
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        return self.url

    def tomar_nuevos(self) -> list[str]:
        with self._lock:
            out = list(self.archivos_nuevos)
            self.archivos_nuevos.clear()
            return out

    def detener(self):
        if self._httpd:
            self._httpd.shutdown()
            self._httpd.server_close()
            self._httpd = None
            self._thread = None
