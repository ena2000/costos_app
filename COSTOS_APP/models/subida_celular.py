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
  body { font-family: system-ui, sans-serif; margin: 0; padding: 20px; background: #f4f6f8; color: #1a1a1a; }
  h1 { font-size: 1.3rem; margin: 0 0 8px; }
  p { color: #555; margin: 0 0 16px; }
  .card { background: #fff; border-radius: 12px; padding: 16px; box-shadow: 0 1px 4px rgba(0,0,0,.08); }
  button, label.btn {
    display: block; width: 100%; box-sizing: border-box; margin: 10px 0;
    padding: 14px; font-size: 1rem; border: 0; border-radius: 10px;
    background: #1f6feb; color: #fff; text-align: center; cursor: pointer;
  }
  label.btn.secondary { background: #57606a; }
  input[type=file] { display: none; }
  #status { margin-top: 12px; font-size: .95rem; white-space: pre-wrap; }
  .ok { color: #1a7f37; }
  .err { color: #cf222e; }
</style>
</head>
<body>
  <div class="card">
    <h1>Fotos de la orden</h1>
    <p>Celular y laptop en la misma WiFi. Puedes tomar foto o elegir de la galería.</p>
    <label class="btn">
      Tomar / elegir fotos
      <input id="files" type="file" accept="image/*" capture="environment" multiple/>
    </label>
    <button id="send" type="button">Enviar a la laptop</button>
    <div id="status"></div>
  </div>
<script>
const statusEl = document.getElementById('status');
const input = document.getElementById('files');
document.getElementById('send').onclick = async () => {
  const files = input.files;
  if (!files || !files.length) {
    statusEl.className = 'err';
    statusEl.textContent = 'Elige al menos una foto.';
    return;
  }
  statusEl.className = '';
  statusEl.textContent = 'Enviando ' + files.length + ' foto(s)...';
  const images = [];
  for (const f of files) {
    const b64 = await new Promise((resolve, reject) => {
      const r = new FileReader();
      r.onload = () => resolve(String(r.result).split(',')[1]);
      r.onerror = reject;
      r.readAsDataURL(f);
    });
    images.push({ name: f.name || ('foto_' + Date.now() + '.jpg'), data: b64 });
  }
  try {
    const res = await fetch('/upload', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ images })
    });
    const txt = await res.text();
    if (!res.ok) throw new Error(txt || res.status);
    statusEl.className = 'ok';
    statusEl.textContent = 'Listo. Ya están en la laptop.\\nPuedes enviar más o volver a la app.';
    input.value = '';
  } catch (e) {
    statusEl.className = 'err';
    statusEl.textContent = 'Error: ' + e.message;
  }
};
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
