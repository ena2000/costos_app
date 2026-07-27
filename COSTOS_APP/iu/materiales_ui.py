import tkinter as tk
from tkinter import ttk, messagebox
from models import database

class MaterialesUI:
    def __init__(self, master):
        """
        Inicializa la pestaña de la interfaz de usuario para la gestión de materiales.
        """
        self.master = master
        
        # --- Variables de Estado ---
        # Variable para almacenar el costo total de los materiales. Es crucial para el cálculo.
        self.total_costo = 0.0
        # Almacena los resultados de la búsqueda para no tener que consultar la BD de nuevo.
        self.search_results_data = []

        # --- Configuración de la Interfaz ---
        self._setup_widgets()

    def _setup_widgets(self):
        """Crea y posiciona todos los widgets en la pestaña."""
        
        # --- Frame de Búsqueda ---
        search_frame = ttk.LabelFrame(self.master, text="Buscar Producto", padding="10")
        search_frame.pack(fill="x", expand=False, padx=5, pady=5)
        search_frame.columnconfigure(1, weight=1)

        ttk.Label(search_frame, text="Buscar:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Vincular la tecla Enter a la función de búsqueda
        self.search_entry.bind("<Return>", lambda event: self._buscar_productos())

        search_button = ttk.Button(search_frame, text="Buscar", command=self._buscar_productos)
        search_button.grid(row=0, column=2, padx=5, pady=5)

        # --- Frame de Resultados y Adición ---
        results_frame = ttk.Frame(self.master, padding="10")
        results_frame.pack(fill="x", expand=False, padx=5)
        results_frame.columnconfigure(0, weight=1)
        results_frame.columnconfigure(2, weight=1)

        # Resultados de la búsqueda
        ttk.Label(results_frame, text="Resultados de Búsqueda:").grid(row=0, column=0, sticky="w")
        self.results_listbox = tk.Listbox(results_frame, height=6)
        self.results_listbox.grid(row=1, column=0, padx=(0, 5), sticky="nsew")

        # Controles para añadir
        add_controls_frame = ttk.Frame(results_frame)
        add_controls_frame.grid(row=1, column=1, padx=5)
        
        ttk.Label(add_controls_frame, text="Cantidad:").pack(pady=2)
        self.quantity_entry = ttk.Entry(add_controls_frame, width=10)
        self.quantity_entry.pack(pady=2)
        
        add_button = ttk.Button(add_controls_frame, text="→\nAñadir\nMaterial", command=self._agregar_material)
        add_button.pack(pady=10)

        # --- Frame de Materiales Agregados (usando un Treeview) ---
        materials_frame = ttk.LabelFrame(self.master, text="Materiales del Proyecto", padding="10")
        materials_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        columns = ("codigo", "descripcion", "costo_unitario", "cantidad", "subtotal")
        self.materials_treeview = ttk.Treeview(materials_frame, columns=columns, show="headings")
        
        # Definir encabezados
        self.materials_treeview.heading("codigo", text="Código")
        self.materials_treeview.heading("descripcion", text="Descripción")
        self.materials_treeview.heading("costo_unitario", text="Costo Unitario")
        self.materials_treeview.heading("cantidad", text="Cantidad")
        self.materials_treeview.heading("subtotal", text="Subtotal")
        
        # Ajustar tamaño de columnas
        self.materials_treeview.column("codigo", width=80)
        self.materials_treeview.column("descripcion", width=300)
        self.materials_treeview.column("costo_unitario", width=100, anchor="e")
        self.materials_treeview.column("cantidad", width=80, anchor="e")
        self.materials_treeview.column("subtotal", width=100, anchor="e")

        self.materials_treeview.pack(fill="both", expand=True, side="left")

        # --- Frame de Acciones y Total ---
        actions_frame = ttk.Frame(materials_frame)
        actions_frame.pack(fill="y", side="right", padx=(10, 0))

        remove_button = ttk.Button(actions_frame, text="Quitar Seleccionado", command=self._quitar_material)
        remove_button.pack(pady=5)
        
        self.total_label = ttk.Label(actions_frame, text="TOTAL: $0.00", font=("Helvetica", 12, "bold"))
        self.total_label.pack(pady=20, side="bottom")

    def _buscar_productos(self):
        """Busca productos en la base de datos y los muestra en la listbox."""
        termino = self.search_entry.get()
        if not termino:
            return
            
        self.results_listbox.delete(0, tk.END)
        self.search_results_data = database.buscar_productos(termino)
        
        for producto in self.search_results_data:
            # producto = (codigo, descripcion, costo_unitario, unidad)
            display_text = f"{producto[1]} (${producto[2]:.2f} / {producto[3]})"
            self.results_listbox.insert(tk.END, display_text)

    def _agregar_material(self):
        """Añade el material seleccionado del listbox al treeview."""
        selected_indices = self.results_listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("Selección Vacía", "Por favor, selecciona un producto de la lista de resultados.")
            return

        try:
            cantidad = float(self.quantity_entry.get())
            if cantidad <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Cantidad Inválida", "Por favor, ingresa una cantidad numérica mayor a cero.")
            return

        selected_index = selected_indices[0]
        producto = self.search_results_data[selected_index]
        
        codigo, descripcion, costo_unitario, unidad = producto
        subtotal = costo_unitario * cantidad
        
        # Añadir al Treeview
        values = (codigo, descripcion, f"${costo_unitario:,.2f}", f"{cantidad:.2f}", f"${subtotal:,.2f}")
        self.materials_treeview.insert("", tk.END, values=values)

        # Actualizar total
        self.total_costo += subtotal
        self._actualizar_total_label()
        
        # Limpiar campos
        self.quantity_entry.delete(0, tk.END)
        self.results_listbox.selection_clear(0, tk.END)

    def _quitar_material(self):
        """Quita el material seleccionado del treeview y actualiza el total."""
        selected_items = self.materials_treeview.selection()
        if not selected_items:
            messagebox.showwarning("Selección Vacía", "Por favor, selecciona uno o más materiales de la lista para quitar.")
            return

        for item_id in selected_items:
            item_values = self.materials_treeview.item(item_id, 'values')
            # El subtotal está en la última columna (índice 4)
            subtotal_str = item_values[4].replace('$', '').replace(',', '')
            subtotal = float(subtotal_str)
            
            # Restar del total
            self.total_costo -= subtotal
            
            # Quitar del treeview
            self.materials_treeview.delete(item_id)
        
        self._actualizar_total_label()

    def _actualizar_total_label(self):
        """Actualiza el texto de la etiqueta del total."""
        self.total_label.config(text=f"TOTAL: ${self.total_costo:,.2f}")

    def limpiar_campos(self):
        """Limpia toda la selección de materiales y resetea el total."""
        for i in self.materials_treeview.get_children():
            self.materials_treeview.delete(i)
        
        self.search_entry.delete(0, tk.END)
        self.results_listbox.delete(0, tk.END)
        self.quantity_entry.delete(0, tk.END)
        self.total_costo = 0.0
        self._actualizar_total_label()
        print("Campos de materiales limpiados.")

    # --- MÉTODO CLAVE PARA SOLUCIONAR EL ERROR ---
    def get_total_costo(self):
        """
        Devuelve el valor actual del costo total de los materiales.
        Este es el método que main.py necesita para funcionar correctamente.
        """
        return round(self.total_costo, 2)