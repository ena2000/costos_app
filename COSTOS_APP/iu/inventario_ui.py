# iu/inventario_ui.py

import tkinter as tk
from tkinter import ttk
from models import database

class InventarioUI:
    def __init__(self, parent):
        self.root = parent
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        controles_frame = ttk.LabelFrame(self.root, text="Buscar Producto", padding="10")
        controles_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        controles_frame.columnconfigure(1, weight=1)

        ttk.Label(controles_frame, text="Buscar:").grid(row=0, column=0, sticky="w", padx=5)
        self.entry_busqueda = ttk.Entry(controles_frame)
        self.entry_busqueda.grid(row=0, column=1, sticky="ew", padx=5)
        self.entry_busqueda.bind("<Return>", self.buscar) 

        self.btn_buscar = ttk.Button(controles_frame, text="Buscar", command=self.buscar)
        self.btn_buscar.grid(row=0, column=2, padx=5)

        resultados_frame = ttk.Frame(self.root)
        resultados_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        resultados_frame.columnconfigure(0, weight=1)
        resultados_frame.rowconfigure(0, weight=1)

        columnas = ('codigo', 'descripcion', 'costo')
        self.tree = ttk.Treeview(resultados_frame, columns=columnas, show='headings', height=15)
        
        self.tree.heading('codigo', text='Código')
        self.tree.heading('descripcion', text='Descripción')
        self.tree.heading('costo', text='Costo Unitario')

        self.tree.column('codigo', width=120, anchor=tk.W)
        self.tree.column('descripcion', width=450, anchor=tk.W)
        self.tree.column('costo', width=120, anchor=tk.E)

        self.tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(resultados_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        self.buscar()

    def buscar(self, event=None):
        termino = self.entry_busqueda.get()
        for i in self.tree.get_children():
            self.tree.delete(i)
            
        resultados = database.buscar_productos(termino)
        
        # --- LÍNEA CORREGIDA ---
        for codigo, descripcion, costo, unidad in resultados:
            costo_formateado = f"${costo:,.2f}"
            self.tree.insert('', tk.END, values=(codigo, descripcion, costo_formateado))