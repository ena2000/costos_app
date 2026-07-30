"""UI para cargar fotos de hojas de orden y revisar datos extraídos."""
from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

from models import ocr_orden


class CargarFotosDialog(tk.Toplevel):
    def __init__(self, parent, on_aplicar):
        super().__init__(parent)
        self.title("Cargar fotos de orden")
        self.geometry("820x620")
        self.transient(parent)
        self.grab_set()

        self.on_aplicar = on_aplicar
        self.rutas: list[str] = []
        self.datos: dict | None = None

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
        ttk.Button(btns, text="Quitar seleccionada", command=self._quitar).pack(side="left", padx=4)
        ttk.Button(btns, text="Configurar API key Gemini", command=self._config_key).pack(side="left", padx=4)
        ttk.Button(btns, text="Probar ejemplo SEGARVI", command=self._ejemplo).pack(side="left", padx=4)
        ttk.Button(btns, text="Leer fotos", command=self._leer).pack(side="right", padx=4)

        self.status = ttk.Label(self, text="Selecciona orden, máquinas, mano de obra y egreso.")
        self.status.grid(row=1, column=0, sticky="w", padx=12)

        review = ttk.LabelFrame(self, text="Datos detectados (revisa antes de aplicar)", padding=10)
        review.grid(row=2, column=0, sticky="nsew", padx=10, pady=8)
        review.columnconfigure(0, weight=1)
        review.rowconfigure(0, weight=1)

        self.txt = tk.Text(review, wrap="word", font=("Consolas", 10))
        scroll = ttk.Scrollbar(review, orient="vertical", command=self.txt.yview)
        self.txt.configure(yscrollcommand=scroll.set)
        self.txt.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

        bottom = ttk.Frame(self, padding=10)
        bottom.grid(row=3, column=0, sticky="ew")
        ttk.Button(bottom, text="Cancelar", command=self.destroy).pack(side="right", padx=4)
        self.btn_aplicar = ttk.Button(bottom, text="Aplicar a la orden", command=self._aplicar, state="disabled")
        self.btn_aplicar.pack(side="right", padx=4)

    def _agregar(self):
        files = filedialog.askopenfilenames(
            title="Seleccionar fotos de la orden",
            filetypes=(
                ("Imágenes", "*.jpg *.jpeg *.png *.webp *.bmp"),
                ("Todos", "*.*"),
            ),
        )
        for f in files:
            if f not in self.rutas:
                self.rutas.append(f)
                self.lista.insert(tk.END, f)

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

    def _ejemplo(self):
        """Carga datos conocidos de la orden SEGARVI (sin llamar a la API)."""
        datos = ocr_orden.datos_ejemplo_segarvi()
        self._mostrar_datos(datos)
        self.status.config(text="Ejemplo SEGARVI cargado (sin OCR). Revisa y aplica.")

    def _leer(self):
        if not self.rutas:
            messagebox.showwarning("Faltan fotos", "Agrega al menos una foto.", parent=self)
            return
        if not ocr_orden.obtener_api_key():
            self._config_key()
            if not ocr_orden.obtener_api_key():
                return

        self.status.config(text="Leyendo fotos… (puede tardar unos segundos)")
        self.btn_aplicar.config(state="disabled")
        self.txt.delete("1.0", tk.END)
        self.update_idletasks()

        def worker():
            try:
                datos = ocr_orden.extraer_datos_de_fotos(self.rutas)
                self.after(0, lambda: self._mostrar_datos(datos))
            except Exception as e:
                self.after(0, lambda: self._error(str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _error(self, msg: str):
        self.status.config(text="Error al leer fotos.")
        messagebox.showerror("Error OCR", msg, parent=self)

    def _mostrar_datos(self, datos: dict):
        self.datos = datos
        self.txt.delete("1.0", tk.END)
        self.txt.insert(tk.END, _formatear_resumen(datos))
        self.status.config(text="Revisa los datos y pulsa Aplicar.")
        self.btn_aplicar.config(state="normal")

    def _aplicar(self):
        if not self.datos:
            return
        try:
            self.on_aplicar(self.datos)
            messagebox.showinfo("Aplicado", "Datos cargados en la orden. Revisa cada pestaña.", parent=self)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron aplicar los datos:\n{e}", parent=self)


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
    for item in d.get("maquinarias") or []:
        lineas.append(
            f"- {item['maquina']}: {item['hora_inicio']} → {item['hora_fin']}"
            + (f"  ({item['fecha']})" if item.get("fecha") else "")
        )
    if not d.get("maquinarias"):
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


def aplicar_datos_a_app(app, datos: dict) -> None:
    """Rellena cabecera y pestañas a partir del dict normalizado."""
    # Cabecera
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

    # Limpiar pestañas antes de cargar
    app.maquinaria_ui.limpiar_campos()
    app.mano_obra_ui.limpiar_campos()
    app.tinta_ui.limpiar_para_carga()
    app.materiales_ui.limpiar_campos()

    # Maquinaria
    app.maquinaria_ui.cargar_desde_datos(datos.get("maquinarias") or [], disenador)

    # Mano de obra + instalación
    app.mano_obra_ui.cargar_desde_datos(
        datos.get("mano_obra") or [],
        datos.get("instalacion") or {},
    )

    # Tinta (una o varias medidas)
    medidas = datos.get("medidas_tinta") or []
    if not medidas and datos.get("medida_tinta"):
        medidas = [datos["medida_tinta"]]
    app.tinta_ui.cargar_desde_datos(
        datos.get("maquina_tinta") or "ORISS",
        medidas,
    )

    # Materiales
    app.materiales_ui.cargar_desde_datos(datos.get("materiales") or [])
