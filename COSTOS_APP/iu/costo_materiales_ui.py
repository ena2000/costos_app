import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from models import database

class CostoMaterialesUI:
    def __init__(self, master):
        # master ya es el ttk.Frame(self.notebook) que viene de main.py
        self.master = master
        self.main_frame = master 
        
        self.total_costo = 0.0
        self.search_results_data = []
        self.salida_excel = ""

        self._setup_widgets()

    def _setup_widgets(self):
        """Configura los widgets directamente sobre self.main_frame"""
        # NO crear un nuevo ttk.Frame(self.master) aquí.
        # Usamos self.main_frame que ya es el frame del notebook.
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(2, weight=1) 

        # --- Frame de Sincronización ---
        sync_frame = ttk.LabelFrame(self.main_frame, text="Gestión de Inventario", padding="10")
        sync_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        sync_frame.columnconfigure(1, weight=1)

        sync_button = ttk.Button(sync_frame, text="Sincronizar Inventario desde Excel/CSV", command=self._sincronizar_inventario)
        sync_button.grid(row=0, column=0, padx=5, pady=5)
        
        self.sync_status_label = ttk.Label(sync_frame, text="El inventario está listo.", foreground="blue")
        self.sync_status_label.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        # --- Frame de Búsqueda y Adición ---
        search_frame = ttk.LabelFrame(self.main_frame, text="Añadir Material al Proyecto", padding="10")
        search_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        search_frame.columnconfigure(1, weight=1)

        ttk.Label(search_frame, text="Buscar Producto:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        self.search_entry.bind("<Return>", lambda event: self._buscar_productos())

        ttk.Button(search_frame, text="Buscar", command=self._buscar_productos).grid(row=0, column=2, padx=5, pady=5)

        self.results_listbox = tk.Listbox(search_frame, height=5)
        self.results_listbox.grid(row=1, column=0, columnspan=3, sticky="ew", padx=5, pady=(5,0))

        add_controls_frame = ttk.Frame(search_frame)
        add_controls_frame.grid(row=2, column=0, columnspan=3, pady=5)
        
        ttk.Label(add_controls_frame, text="Cantidad:").pack(side="left", padx=5)
        self.quantity_entry = ttk.Entry(add_controls_frame, width=10)
        self.quantity_entry.pack(side="left", padx=5)
        
        ttk.Button(add_controls_frame, text="Añadir Material Seleccionado", command=self._agregar_material).pack(side="left", padx=10)

        # --- Frame de Materiales Agregados ---
        materials_frame = ttk.LabelFrame(self.main_frame, text="Materiales del Proyecto", padding="10")
        materials_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        materials_frame.columnconfigure(0, weight=1)
        materials_frame.rowconfigure(0, weight=1)
        
        columns = ("cantidad", "unidad", "descripcion", "costo_unitario", "subtotal")
        self.materials_treeview = ttk.Treeview(materials_frame, columns=columns, show="headings")
        
        for col in columns:
            self.materials_treeview.heading(col, text=col.replace("_", " ").title())
        
        self.materials_treeview.column("cantidad", width=80, anchor="e")
        self.materials_treeview.column("unidad", width=80, anchor="center")
        self.materials_treeview.column("descripcion", width=300)
        self.materials_treeview.column("costo_unitario", width=100, anchor="e")
        self.materials_treeview.column("subtotal", width=100, anchor="e")

        self.materials_treeview.grid(row=0, column=0, sticky="nsew")
        
        scrollbar = ttk.Scrollbar(materials_frame, orient="vertical", command=self.materials_treeview.yview)
        self.materials_treeview.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")

        # --- Frame de Acciones y Total ---
        actions_frame = ttk.Frame(self.main_frame)
        actions_frame.grid(row=3, column=0, sticky="e", padx=5, pady=10)

        self.total_label = ttk.Label(actions_frame, text="TOTAL MATERIALES: $0,00", font=("Arial", 12, "bold"))
        self.total_label.pack(side="right", padx=10)

        remove_button = ttk.Button(actions_frame, text="Quitar Seleccionado", command=self._quitar_material)
        remove_button.pack(side="right")

    def _sincronizar_inventario(self):
        filepath = filedialog.askopenfilename(
            title="Seleccionar archivo de inventario",
            filetypes=(("Archivos Excel", "*.xlsx"), ("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*"))
        )
        if not filepath: return

        def status_update(message):
            self.sync_status_label.config(text=message)
            self.master.update_idletasks()

        try:
            database.sincronizar_inteligentemente(filepath, status_update)
        except Exception as e:
            status_update(f"Error: {e}")
            messagebox.showerror("Error", f"Ocurrió un error: {e}")

    def _buscar_productos(self):
        termino = self.search_entry.get()
        self.results_listbox.delete(0, tk.END)
        self.search_results_data = database.buscar_productos(termino)
        
        for producto in self.search_results_data:
            display_text = f"{producto[1]} (${self.formato_coma(producto[2])} / {producto[3]})"
            self.results_listbox.insert(tk.END, display_text)

    def _agregar_material(self):
        selected_indices = self.results_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Selección Vacía", "Selecciona un producto de la lista.")
            return

        try:
            cantidad_str = self.quantity_entry.get().replace(",", ".")
            cantidad = float(cantidad_str)
            if cantidad <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Ingresa una cantidad válida.")
            return

        producto = self.search_results_data[selected_indices[0]]
        codigo, descripcion, costo_unitario, unidad = producto
        subtotal = costo_unitario * cantidad
        
        values = (
            self.formato_coma(cantidad), 
            unidad,
            descripcion,
            f"${self.formato_coma(costo_unitario)}", 
            f"${self.formato_coma(subtotal)}"
        )
        
        item_id = self.materials_treeview.insert("", tk.END, values=values)
        # Importante: Guardamos el subtotal numérico en el primer tag para facilitar la suma
        self.materials_treeview.item(item_id, tags=(str(subtotal), self.formato_coma(cantidad), unidad, descripcion, self.formato_coma(subtotal)))
        
        self._actualizar_total_y_formato()
        self.quantity_entry.delete(0, tk.END)

    def _quitar_material(self):
        selected_items = self.materials_treeview.selection()
        if not selected_items: return
        for item_id in selected_items:
            self.materials_treeview.delete(item_id)
        self._actualizar_total_y_formato()

    def _actualizar_total_y_formato(self):
        total_actual = 0.0
        nueva_salida_excel = ""
        
        for item_id in self.materials_treeview.get_children():
            item_tags = self.materials_treeview.item(item_id, 'tags')
            subtotal_numeric = float(item_tags[0])
            total_actual += subtotal_numeric
            
            linea = f"{item_tags[1]}\t{item_tags[2]}\t{item_tags[3]}\t{item_tags[4]}"
            nueva_salida_excel += linea + "\n"

        self.total_costo = total_actual
        self.salida_excel = nueva_salida_excel
        self.total_label.config(text=f"TOTAL MATERIALES: ${self.formato_coma(self.total_costo)}")

    def get_total_materiales(self):
        """Método para que main.py obtenga el costo total de materiales."""
        return self.total_costo

    def limpiar_campos(self):
        for i in self.materials_treeview.get_children():
            self.materials_treeview.delete(i)
        self.search_entry.delete(0, tk.END)
        self.results_listbox.delete(0, tk.END)
        self.quantity_entry.delete(0, tk.END)
        self.total_costo = 0.0
        self.salida_excel = ""
        self._actualizar_total_y_formato()

    def formato_coma(self, numero):
        """Formatea números al estilo local (coma decimal)."""
        return f"{numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def cargar_desde_datos(self, materiales: list):
        """Carga materiales del egreso (producto, cantidad, costo, subtotal)."""
        for mat in materiales:
            producto = (mat.get("producto") or "").strip()
            if not producto:
                continue
            cantidad = float(mat.get("cantidad") or 0)
            unidad = mat.get("unidad") or "u"
            costo_unitario = float(mat.get("costo_unitario") or 0)
            subtotal = float(mat.get("subtotal") or 0)
            if subtotal <= 0:
                subtotal = round(cantidad * costo_unitario, 2)
            if cantidad <= 0 and subtotal <= 0:
                continue
            if costo_unitario <= 0 and cantidad > 0 and subtotal > 0:
                costo_unitario = round(subtotal / cantidad, 6)

            values = (
                self.formato_coma(cantidad),
                unidad,
                producto,
                f"${self.formato_coma(costo_unitario)}",
                f"${self.formato_coma(subtotal)}",
            )
            item_id = self.materials_treeview.insert("", tk.END, values=values)
            self.materials_treeview.item(
                item_id,
                tags=(
                    str(subtotal),
                    self.formato_coma(cantidad),
                    unidad,
                    producto,
                    self.formato_coma(subtotal),
                ),
            )
        self._actualizar_total_y_formato()

