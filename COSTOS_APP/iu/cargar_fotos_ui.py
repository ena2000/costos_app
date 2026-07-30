"""UI para cargar fotos de hojas de orden y revisar datos extraídos."""
from __future__ import annotations

import re
import tempfile
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox, simpledialog

from PIL import Image, ImageGrab, ImageTk
import qrcode

from models import ocr_orden
from models.subida_celular import SubidaCelularServer
from models.notificaciones import notificar


class CargarFotosDialog(tk.Toplevel):
    def __init__(self, parent, on_aplicar):
        super().__init__(parent)
        self.title("Cargar fotos de orden")
        self.geometry("860x640")
        self.transient(parent)
        self.grab_set()

        self.on_aplicar = on_aplicar
        self.rutas: list[str] = []
        self.datos: dict | None = None
        self._paste_dir = Path(tempfile.mkdtemp(prefix="costos_paste_"))
        self._server: SubidaCelularServer | None = None
        self._poll_job = None

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        top = ttk.LabelFrame(self, text="Fotos de las hojas", padding=10)
        top.grid(row=0, column=0, sticky="ew", padx=10, pady=8)
        top.columnconfigure(0, weight=1)

        self.lista = tk.Listbox(top, height=5)
        self.lista.grid(row=0, column=0, sticky="ew")
        btns = ttk.Frame(top)
        btns.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(btns, text="Agregar fotos…", command=self._agregar).pack(side="left", padx=4)
        ttk.Button(btns, text="Pegar foto (Ctrl+V)", command=self._pegar).pack(side="left", padx=4)
        ttk.Button(btns, text="📱 Desde celular (WiFi)", command=self._desde_celular).pack(side="left", padx=4)
        ttk.Button(btns, text="Quitar seleccionada", command=self._quitar).pack(side="left", padx=4)
        ttk.Button(btns, text="API key Gemini", command=self._config_key).pack(side="left", padx=4)
        ttk.Button(btns, text="Leer fotos", command=self._leer).pack(side="right", padx=4)

        self.status = ttk.Label(
            self,
            text="Rápido: 📱 Desde celular (misma WiFi)  ·  o Ctrl+V si copiaste la imagen",
        )
        self.status.grid(row=1, column=0, sticky="w", padx=12)

        review = ttk.LabelFrame(
            self,
            text="Datos detectados — PUEDES EDITARLOS aquí antes de aplicar",
            padding=10,
        )
        review.grid(row=2, column=0, sticky="nsew", padx=10, pady=8)
        review.columnconfigure(0, weight=1)
        review.rowconfigure(0, weight=1)

        self.txt = tk.Text(review, wrap="word", font=("Consolas", 10), undo=True)
        scroll = ttk.Scrollbar(review, orient="vertical", command=self.txt.yview)
        self.txt.configure(yscrollcommand=scroll.set)
        self.txt.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

        bottom = ttk.Frame(self, padding=10)
        bottom.grid(row=3, column=0, sticky="ew")
        ttk.Button(bottom, text="Cancelar", command=self._cerrar).pack(side="right", padx=4)
        self.btn_aplicar = ttk.Button(bottom, text="Aplicar a la orden", command=self._aplicar, state="disabled")
        self.btn_aplicar.pack(side="right", padx=4)

        self.bind("<Control-v>", lambda e: self._pegar())
        self.bind("<Control-V>", lambda e: self._pegar())
        self.protocol("WM_DELETE_WINDOW", self._cerrar)

    def _agregar_ruta(self, ruta: str):
        if ruta and ruta not in self.rutas:
            self.rutas.append(ruta)
            self.lista.insert(tk.END, ruta)
            self.status.config(text=f"{len(self.rutas)} foto(s) listas. Pulsa Leer fotos cuando termines.")

    def _agregar(self):
        files = filedialog.askopenfilenames(
            title="Seleccionar fotos de la orden",
            filetypes=(
                ("Imágenes", "*.jpg *.jpeg *.png *.webp *.bmp"),
                ("Todos", "*.*"),
            ),
        )
        for f in files:
            self._agregar_ruta(f)

    def _pegar(self):
        """Pega imagen del portapapeles (ej. copiada desde WhatsApp Desktop)."""
        try:
            img = ImageGrab.grabclipboard()
        except Exception as e:
            messagebox.showerror("Portapapeles", f"No se pudo leer el portapapeles:\n{e}", parent=self)
            return

        if img is None:
            messagebox.showwarning(
                "Sin imagen",
                "No hay una imagen en el portapapeles.\n\n"
                "En WhatsApp Desktop: clic derecho en la foto → Copiar,\n"
                "luego aquí Ctrl+V o 'Pegar foto'.",
                parent=self,
            )
            return

        if isinstance(img, list):
            # A veces Windows devuelve rutas de archivos
            for p in img:
                if Path(p).is_file():
                    self._agregar_ruta(str(p))
            return

        if not isinstance(img, Image.Image):
            messagebox.showwarning("Sin imagen", "El portapapeles no tiene una imagen.", parent=self)
            return

        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        elif img.mode == "L":
            img = img.convert("RGB")

        dest = self._paste_dir / f"pegado_{int(time.time() * 1000)}.jpg"
        img.save(dest, format="JPEG", quality=90)
        self._agregar_ruta(str(dest))

    def _desde_celular(self):
        try:
            if self._server is None:
                self._server = SubidaCelularServer(
                    on_archivo=lambda ruta: self.after(0, lambda r=ruta: self._agregar_ruta(r))
                )
                url = self._server.iniciar()
            else:
                url = self._server.url
        except OSError as e:
            messagebox.showerror(
                "WiFi",
                f"No se pudo abrir el servidor local.\n{e}\n\n"
                "Cierra otras apps que usen el puerto 8765 e intenta de nuevo.",
                parent=self,
            )
            return

        win = tk.Toplevel(self)
        win.title("Subir desde el celular")
        win.geometry("420x520")
        win.transient(self)
        win.grab_set()

        ttk.Label(
            win,
            text="1. Celular y laptop en la MISMA WiFi\n"
                 "2. Escanea este QR con la cámara del celular:",
            justify="center",
            font=("Segoe UI", 10),
        ).pack(padx=16, pady=(16, 8))

        qr_img = qrcode.make(url)
        if not isinstance(qr_img, Image.Image):
            qr_img = qr_img.convert("RGB")
        qr_img = qr_img.resize((280, 280), Image.Resampling.NEAREST)
        photo = ImageTk.PhotoImage(qr_img)
        win._qr_photo = photo  # evitar que el GC lo borre
        lbl_qr = ttk.Label(win, image=photo)
        lbl_qr.pack(pady=8)

        ttk.Label(
            win,
            text="3. En el celular: ve agregando fotos una a una\n"
                 "   (se guardan en la página). Al final: Enviar todas.\n"
                 "4. Aquí aparecen en la lista → Leer fotos.",
            justify="center",
        ).pack(padx=16, pady=8)

        ttk.Button(win, text="Listo / Cerrar", command=win.destroy).pack(pady=12)

        if self._poll_job is None:
            self._poll_nuevos()

    def _poll_nuevos(self):
        if self._server:
            for ruta in self._server.tomar_nuevos():
                self._agregar_ruta(ruta)
        self._poll_job = self.after(800, self._poll_nuevos)

    def _quitar(self):
        sel = list(self.lista.curselection())
        for i in reversed(sel):
            self.lista.delete(i)
            del self.rutas[i]

    def _config_key(self):
        actual = ocr_orden.obtener_api_key() or ""
        key = simpledialog.askstring(
            "API key Gemini",
            "Pega tu API key gratis de https://aistudio.google.com/apikey",
            initialvalue=actual,
            parent=self,
            show="*",
        )
        if key and key.strip():
            ocr_orden.guardar_api_key(key.strip())
            messagebox.showinfo("Listo", "API key guardada.", parent=self)

    def _leer(self):
        if not self.rutas:
            messagebox.showwarning("Faltan fotos", "Agrega al menos una foto.", parent=self)
            return
        if not ocr_orden.obtener_api_key():
            self._config_key()
            if not ocr_orden.obtener_api_key():
                return

        self.status.config(text="Leyendo fotos… (te aviso cuando termine)")
        self.btn_aplicar.config(state="disabled")
        self.txt.delete("1.0", tk.END)
        self.update_idletasks()
        t0 = time.time()

        def worker():
            try:
                datos = ocr_orden.extraer_datos_de_fotos(self.rutas)
                segs = int(time.time() - t0)
                self.after(0, lambda: self._mostrar_datos(datos, segs))
            except Exception as e:
                self.after(0, lambda: self._error(str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _error(self, msg: str):
        self.status.config(text="Error al leer fotos.")
        notificar("Error al leer fotos", "Revisa el mensaje en la app.")
        messagebox.showerror("Error OCR", msg, parent=self)

    def _mostrar_datos(self, datos: dict, segundos: int = 0):
        self.datos = datos
        self.txt.delete("1.0", tk.END)
        self.txt.insert(tk.END, _formatear_resumen(datos))
        self.status.config(
            text=f"Listo en {segundos}s. Corrige lo que esté mal en el texto y luego Aplicar."
        )
        self.btn_aplicar.config(state="normal")
        notificar(
            "Fotos leídas ✔",
            f"Ya están los datos ({segundos}s). Puedes editarlos antes de aplicar.",
        )

    def _aplicar(self):
        if not self.datos and not self.txt.get("1.0", tk.END).strip():
            return
        try:
            texto = self.txt.get("1.0", tk.END)
            base = self.datos or {}
            editados = _parsear_resumen(texto, base)
            # Re-normaliza alias de máquinas/actividades por si editaron a mano
            self.datos = ocr_orden.normalizar_datos(_a_raw_para_normalizar(editados))
            self.on_aplicar(self.datos)
            notificar("Orden cargada ✔", "Datos aplicados (con tus correcciones).")
            messagebox.showinfo(
                "Aplicado",
                "Datos cargados en la orden.\nRevisa las pestañas por si falta algo.",
                parent=self,
            )
            self._cerrar()
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"No se pudieron aplicar los datos.\n"
                f"Revisa el formato del texto editado.\n\n{e}",
                parent=self,
            )

    def _cerrar(self):
        if self._poll_job is not None:
            try:
                self.after_cancel(self._poll_job)
            except Exception:
                pass
            self._poll_job = None
        if self._server:
            try:
                self._server.detener()
            except Exception:
                pass
            self._server = None
        self.destroy()


def _formatear_resumen(d: dict) -> str:
    lineas = [
        f"Cliente: {d.get('cliente')}",
        f"Trabajo: {d.get('trabajo')}",
        f"Inicio: {d.get('fecha_inicio')}   Fin: {d.get('fecha_fin')}",
        f"Diseñador (por defecto): {d.get('disenador')}",
        "",
        "=== TINTA ===",
        f"Máquina: {d.get('maquina_tinta')}",
    ]
    medidas = d.get("medidas_tinta") or []
    if not medidas and d.get("medida_tinta"):
        medidas = [d["medida_tinta"]]
    if medidas:
        for i, m in enumerate(medidas, 1):
            lineas.append(
                f"Medida {i}: {m.get('repeticiones')}x  {m.get('largo_cm')} x {m.get('ancho_cm')} cm"
                + (" (doble cara)" if m.get("doble_cara") else "")
            )
    else:
        lineas.append("Medidas: (ninguna)")
    lineas.append("")
    lineas.append("=== MAQUINARIA ===")
    maqs = d.get("maquinarias") or []
    if maqs:
        lineas.append(f"Total entradas detectadas: {len(maqs)}")
        for item in maqs:
            lineas.append(
                f"- {item['maquina']}: {item['hora_inicio']} → {item['hora_fin']}"
                + (f"  ({item['fecha']})" if item.get("fecha") else "")
            )
    else:
        lineas.append("(ninguna)")

    lineas.append("")
    lineas.append("=== MANO DE OBRA ===")
    for item in d.get("mano_obra") or []:
        noms = ", ".join(item.get("responsables") or [])
        lineas.append(
            f"- {item['actividad']}: {item['hora_inicio']} → {item['hora_fin']} | "
            f"operarios={item['cantidad_operarios']} ({noms})"
        )
    if not d.get("mano_obra"):
        lineas.append("(ninguna)")

    inst = d.get("instalacion") or {}
    lineas.append("")
    lineas.append("=== INSTALACIÓN ===")
    if inst.get("cantidad_operarios") or inst.get("dias"):
        lineas.append(f"Operarios: {inst.get('cantidad_operarios')}  Viáticos: {inst.get('viaticos')}")
        for dia in inst.get("dias") or []:
            lineas.append(f"- {dia['hora_inicio']} → {dia['hora_fin']}")
    else:
        lineas.append("(sin datos)")

    lineas.append("")
    lineas.append("=== MATERIALES (egreso) ===")
    for mat in d.get("materiales") or []:
        lineas.append(
            f"- {mat['producto']}: cant={mat['cantidad']} {mat['unidad']} | "
            f"unit=${mat['costo_unitario']} | sub=${mat['subtotal']}"
        )
    if not d.get("materiales"):
        lineas.append("(ninguno)")

    return "\n".join(lineas)


def _a_raw_para_normalizar(d: dict) -> dict:
    """Convierte el dict editado al formato que espera normalizar_datos."""
    return {
        "cliente": d.get("cliente"),
        "trabajo": d.get("trabajo"),
        "cantidad_item": d.get("cantidad_item") or 1,
        "fecha_inicio": d.get("fecha_inicio"),
        "fecha_fin": d.get("fecha_fin"),
        "medidas_tinta": d.get("medidas_tinta") or [],
        "maquina_tinta": d.get("maquina_tinta"),
        "maquinarias": d.get("maquinarias") or [],
        "mano_obra": d.get("mano_obra") or [],
        "instalacion": d.get("instalacion") or {},
        "materiales": d.get("materiales") or [],
    }


def _parsear_resumen(texto: str, base: dict | None = None) -> dict:
    """Lee el texto editable y arma el dict de datos (respeta lo que el usuario cambió)."""
    base = dict(base or {})
    out = {
        "cliente": base.get("cliente") or "",
        "trabajo": base.get("trabajo") or "",
        "cantidad_item": base.get("cantidad_item") or 1,
        "fecha_inicio": base.get("fecha_inicio") or "",
        "fecha_fin": base.get("fecha_fin") or "",
        "disenador": base.get("disenador") or "XAVIER CABRERA",
        "maquina_tinta": base.get("maquina_tinta") or "ORISS",
        "medidas_tinta": [],
        "maquinarias": [],
        "mano_obra": [],
        "instalacion": {
            "cantidad_operarios": 0,
            "viaticos": 0.0,
            "dias": [],
        },
        "materiales": [],
    }

    seccion = "cabecera"
    for raw in texto.splitlines():
        line = raw.strip()
        if not line:
            continue
        up = line.upper()

        if up.startswith("=== TINTA"):
            seccion = "tinta"
            continue
        if up.startswith("=== MAQUINARIA"):
            seccion = "maquinaria"
            continue
        if up.startswith("=== MANO DE OBRA"):
            seccion = "mano_obra"
            continue
        if up.startswith("=== INSTAL"):
            seccion = "instalacion"
            continue
        if up.startswith("=== MATERIAL"):
            seccion = "materiales"
            continue

        if seccion == "cabecera":
            if line.lower().startswith("cliente:"):
                out["cliente"] = line.split(":", 1)[1].strip()
            elif line.lower().startswith("trabajo:"):
                out["trabajo"] = line.split(":", 1)[1].strip()
            elif line.lower().startswith("inicio:"):
                # Inicio: 22/06   Fin: 24/06
                m = re.search(
                    r"Inicio:\s*(\S+)\s+Fin:\s*(\S+)",
                    line,
                    re.IGNORECASE,
                )
                if m:
                    out["fecha_inicio"] = m.group(1)
                    out["fecha_fin"] = m.group(2)
            elif "diseñador" in line.lower() or "disenador" in line.lower():
                out["disenador"] = line.split(":", 1)[1].strip()
            continue

        if seccion == "tinta":
            if line.lower().startswith("máquina:") or line.lower().startswith("maquina:"):
                out["maquina_tinta"] = line.split(":", 1)[1].strip()
            elif line.lower().startswith("medida"):
                # Medida 1: 2x  30.0 x 10.0 cm (doble cara)
                m = re.search(
                    r"(\d+)\s*x\s*([\d.,]+)\s*x\s*([\d.,]+)",
                    line,
                    re.IGNORECASE,
                )
                if m:
                    out["medidas_tinta"].append({
                        "repeticiones": int(m.group(1)),
                        "largo_cm": float(m.group(2).replace(",", ".")),
                        "ancho_cm": float(m.group(3).replace(",", ".")),
                        "doble_cara": "doble" in line.lower(),
                    })
            continue

        if seccion == "maquinaria":
            if line.startswith("Total") or line.startswith("("):
                continue
            # - ORISS: 15:00 → 15:15  (24/06)
            m = re.search(
                r"-?\s*(.+?):\s*(\d{1,2}:\d{2})\s*(?:→|->|–|-)\s*(\d{1,2}:\d{2})(?:\s*\(([^)]+)\))?",
                line,
            )
            if m:
                out["maquinarias"].append({
                    "maquina": m.group(1).strip(),
                    "hora_inicio": m.group(2),
                    "hora_fin": m.group(3),
                    "fecha": (m.group(4) or "").strip(),
                    "responsable": "",
                })
            continue

        if seccion == "mano_obra":
            if line.startswith("("):
                continue
            # - REFILACION: 10:40 → 10:50 | operarios=1 (Kevin)
            m = re.search(
                r"-?\s*(.+?):\s*(\d{1,2}:\d{2})\s*(?:→|->|–|-)\s*(\d{1,2}:\d{2})"
                r"(?:\s*\|\s*operarios\s*=\s*(\d+))?"
                r"(?:\s*\(([^)]*)\))?",
                line,
                re.IGNORECASE,
            )
            if m:
                noms = [n.strip() for n in (m.group(5) or "").split(",") if n.strip()]
                ops = int(m.group(4) or (len(noms) if noms else 1))
                if not noms and ops:
                    noms = [f"Operario {i+1}" for i in range(ops)]
                out["mano_obra"].append({
                    "actividad": m.group(1).strip(),
                    "hora_inicio": m.group(2),
                    "hora_fin": m.group(3),
                    "fecha": "",
                    "responsables": noms,
                    "cantidad_operarios": ops,
                })
            continue

        if seccion == "instalacion":
            if line.lower().startswith("operarios:"):
                m = re.search(
                    r"Operarios:\s*(\d+)\s*Viáticos:\s*([\d.,]+)",
                    line,
                    re.IGNORECASE,
                )
                if m:
                    out["instalacion"]["cantidad_operarios"] = int(m.group(1))
                    out["instalacion"]["viaticos"] = float(m.group(2).replace(",", "."))
            elif line.startswith("-"):
                m = re.search(
                    r"(\d{1,2}:\d{2})\s*(?:→|->|–|-)\s*(\d{1,2}:\d{2})",
                    line,
                )
                if m:
                    out["instalacion"]["dias"].append({
                        "hora_inicio": m.group(1),
                        "hora_fin": m.group(2),
                    })
            continue

        if seccion == "materiales":
            if line.startswith("("):
                continue
            # - PRODUCTO: cant=1.0 m. | unit=$1.47 | sub=$1.47
            m = re.search(
                r"-?\s*(.+?):\s*cant\s*=\s*([\d.,]+)\s*(\S*)\s*\|\s*unit\s*=\s*\$?\s*([\d.,]+)"
                r"\s*\|\s*sub\s*=\s*\$?\s*([\d.,]+)",
                line,
                re.IGNORECASE,
            )
            if m:
                out["materiales"].append({
                    "codigo": "",
                    "producto": m.group(1).strip(),
                    "cantidad": float(m.group(2).replace(",", ".")),
                    "unidad": (m.group(3) or "u").strip(),
                    "costo_unitario": float(m.group(4).replace(",", ".")),
                    "subtotal": float(m.group(5).replace(",", ".")),
                })
            continue

    return out


def aplicar_datos_a_app(app, datos: dict) -> None:
    """Rellena cabecera y pestañas a partir del dict normalizado."""
    app.entry_cliente.delete(0, tk.END)
    app.entry_cliente.insert(0, datos.get("cliente") or "")
    app.entry_desc.delete(0, tk.END)
    app.entry_desc.insert(0, datos.get("trabajo") or "")
    if datos.get("fecha_inicio"):
        app.entry_fecha_inicio.delete(0, tk.END)
        app.entry_fecha_inicio.insert(0, datos["fecha_inicio"])
    if datos.get("fecha_fin"):
        app.entry_fecha_fin.delete(0, tk.END)
        app.entry_fecha_fin.insert(0, datos["fecha_fin"])

    disenador = datos.get("disenador") or "XAVIER CABRERA"

    app.maquinaria_ui.limpiar_campos()
    app.mano_obra_ui.limpiar_campos()
    app.tinta_ui.limpiar_para_carga()
    app.materiales_ui.limpiar_campos()

    app.maquinaria_ui.cargar_desde_datos(datos.get("maquinarias") or [], disenador)
    app.mano_obra_ui.cargar_desde_datos(
        datos.get("mano_obra") or [],
        datos.get("instalacion") or {},
    )

    medidas = datos.get("medidas_tinta") or []
    if not medidas and datos.get("medida_tinta"):
        medidas = [datos["medida_tinta"]]
    app.tinta_ui.cargar_desde_datos(
        datos.get("maquina_tinta") or "ORISS",
        medidas,
    )
    app.materiales_ui.cargar_desde_datos(datos.get("materiales") or [])
