"""Pestaña para editar tarifas de máquina, operario, diseñador y CIF."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from models import tarifas


def _fmt(valor) -> str:
    numero = float(valor)
    texto = f"{numero:.8f}".rstrip("0").rstrip(".")
    return texto.replace(".", ",")


def _leer(texto: str) -> float:
    return float(str(texto).strip().replace(",", "."))


class TarifasUI:
    def __init__(self, parent):
        self.root = parent
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.entries_maquinas = {}

        main = ttk.Frame(self.root, padding=10)
        main.grid(row=0, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(1, weight=1)

        ttk.Label(
            main,
            text="Estos valores se usan al calcular. Cámbialos cuando quieras y pulsa Guardar.",
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        canvas_frame = ttk.Frame(main)
        canvas_frame.grid(row=1, column=0, sticky="nsew")
        canvas_frame.columnconfigure(0, weight=1)
        canvas_frame.rowconfigure(0, weight=1)

        canvas = tk.Canvas(canvas_frame, highlightthickness=0)
        scroll = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")

        mo = ttk.LabelFrame(inner, text="Mano de obra y CIF", padding=10)
        mo.pack(fill="x", pady=5)
        mo.columnconfigure(1, weight=1)

        self.entry_operario = self._fila(mo, 0, "Costo hora operario ($):")
        self.entry_disenador = self._fila(mo, 1, "Costo hora diseñador ($):")
        self.entry_cif = self._fila(mo, 2, "Valor CIF por hora ($):")
        self.entry_divisor = self._fila(mo, 3, "Divisor CIF (horas / este número):")
        ttk.Label(
            mo,
            text="Fórmula CIF: (horas de obra ÷ divisor) × valor CIF por hora",
            foreground="#555",
        ).grid(row=4, column=0, columnspan=2, sticky="w", pady=(6, 0))

        maq = ttk.LabelFrame(inner, text="Costo por hora de cada máquina ($)", padding=10)
        maq.pack(fill="x", pady=8)
        maq.columnconfigure(1, weight=1)

        datos = tarifas.actuales()
        for i, nombre in enumerate(tarifas.COSTOS_MAQUINAS_DEFAULT.keys()):
            ttk.Label(maq, text=f"{nombre}:").grid(row=i, column=0, sticky="w", padx=5, pady=3)
            entry = ttk.Entry(maq, width=14)
            entry.grid(row=i, column=1, sticky="w", padx=5, pady=3)
            self.entries_maquinas[nombre] = entry

        btns = ttk.Frame(main)
        btns.grid(row=2, column=0, sticky="ew", pady=10)
        ttk.Button(btns, text="Guardar tarifas", command=self.guardar).pack(side="left", padx=5)
        ttk.Button(btns, text="Restablecer valores originales", command=self.restablecer).pack(side="left", padx=5)

        self.cargar_en_formulario(datos)

    def _fila(self, parent, fila, etiqueta):
        ttk.Label(parent, text=etiqueta).grid(row=fila, column=0, sticky="w", padx=5, pady=3)
        entry = ttk.Entry(parent, width=14)
        entry.grid(row=fila, column=1, sticky="w", padx=5, pady=3)
        return entry

    def cargar_en_formulario(self, datos: dict):
        pares = (
            (self.entry_operario, datos["costo_hora_operario"]),
            (self.entry_disenador, datos["costo_hora_disenador"]),
            (self.entry_cif, datos["valor_cif_por_hora"]),
            (self.entry_divisor, datos.get("divisor_cif", 5)),
        )
        for entry, valor in pares:
            entry.delete(0, tk.END)
            entry.insert(0, _fmt(valor))
        maquinas = datos.get("costos_maquinas") or {}
        for nombre, entry in self.entries_maquinas.items():
            entry.delete(0, tk.END)
            if nombre in maquinas:
                entry.insert(0, _fmt(maquinas[nombre]))

    def _leer_formulario(self) -> dict:
        costos = {}
        for nombre, entry in self.entries_maquinas.items():
            costos[nombre] = _leer(entry.get())
        return {
            "costo_hora_operario": _leer(self.entry_operario.get()),
            "costo_hora_disenador": _leer(self.entry_disenador.get()),
            "valor_cif_por_hora": _leer(self.entry_cif.get()),
            "divisor_cif": _leer(self.entry_divisor.get()),
            "costos_maquinas": costos,
        }

    def guardar(self):
        try:
            datos = self._leer_formulario()
            if datos["divisor_cif"] <= 0:
                raise ValueError("El divisor CIF debe ser mayor que cero.")
            for nombre, costo in datos["costos_maquinas"].items():
                if costo < 0:
                    raise ValueError(f"El costo de {nombre} no puede ser negativo.")
            tarifas.guardar(datos)
            messagebox.showinfo(
                "Tarifas guardadas",
                "Los nuevos costos se usarán en los próximos cálculos.\n"
                "Las órdenes ya guardadas no cambian.",
            )
        except ValueError as e:
            messagebox.showerror("Dato inválido", str(e) if str(e) else "Revisa que todos los valores sean números.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron guardar las tarifas:\n{e}")

    def restablecer(self):
        if not messagebox.askyesno("Restablecer", "¿Volver a los costos originales de la app?"):
            return
        self.cargar_en_formulario(tarifas.DEFAULTS)
        self.guardar()
