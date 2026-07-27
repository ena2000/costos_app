import tkinter as tk
from tkinter import ttk, messagebox
from models.gasto_tinta import calcular_gasto_tinta

class GastoTintaUI:
    def __init__(self, parent):
        self.root = parent
        # Configuración para que el marco principal se expanda con la ventana
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1) # Asumiendo que el main_frame estará en la fila 0 y se expandirá

        # VARIABLES DE ESTADO (Cruciales para main.py)
        self.total_gasto = 0.0  # Aquí se guardará el valor para la DB
        self.resultado_formateado = ""
        self.inputs_medidas = []

        # Marco principal para mejor relleno y estructura
        main_frame = ttk.Frame(self.root, padding="10 10 10 10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        # Configuración de columnas y filas del main_frame para que se redimensionen
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1) # Permite que canvas_frame (donde están las medidas) se expanda
        main_frame.rowconfigure(4, weight=1) # Permite que result_frame se expanda


        # Título
        #ttk.Label(main_frame, text="Calculadora de Gasto de Tinta", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=3, pady=(0, 10), sticky="ew")

        # Marco de controles superiores
        top_controls_frame = ttk.LabelFrame(main_frame, text="Configuración Inicial", padding="10 10 10 10")
        top_controls_frame.grid(row=1, column=0, sticky="ew", pady=5)
        top_controls_frame.columnconfigure(0, weight=1) # Hace que esta columna sea expandible
        top_controls_frame.columnconfigure(1, weight=1) # Para que entry_total_medidas se expanda
        top_controls_frame.columnconfigure(4, weight=1) # Para que combo_maquina se expanda

        ttk.Label(top_controls_frame, text="¿Cuántas medidas diferentes vas a ingresar?").grid(row=0, column=0, sticky="w")
        self.entry_total_medidas = ttk.Entry(top_controls_frame, width=8)
        self.entry_total_medidas.grid(row=0, column=1, padx=5, sticky="ew")
        ttk.Button(top_controls_frame, text="Generar Formulario", command=self.generar_formulario_medidas).grid(row=0, column=2, padx=5)

        ttk.Label(top_controls_frame, text="Máquina:").grid(row=0, column=3, padx=10, sticky="e")
        self.combo_maquina = ttk.Combobox(top_controls_frame, values=["CAMA PLANA", "MIMAKI UU", "ORISS", "GALAXY", "P.320"], state="readonly", width=15)
        self.combo_maquina.grid(row=0, column=4, sticky="ew")
        self.combo_maquina.current(0)

        # Marco de entrada de medidas (con desplazamiento)
        canvas_frame = ttk.LabelFrame(main_frame, text="Detalle de Medidas", padding="10 10 10 10")
        canvas_frame.grid(row=2, column=0, sticky="nsew", pady=5)
        canvas_frame.columnconfigure(0, weight=1)
        canvas_frame.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(canvas_frame, borderwidth=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.frame_medidas = ttk.Frame(self.canvas) # Usar ttk.Frame aquí

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.create_window((0, 0), window=self.frame_medidas, anchor="nw", tags="self.frame_medidas")

        self.frame_medidas.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        # Marco de botones
        button_frame = ttk.Frame(main_frame, padding="5 0 5 0")
        button_frame.grid(row=3, column=0, sticky="ew", pady=5)
        button_frame.columnconfigure(0, weight=1) # Centrar botones

        button_sub_frame = ttk.Frame(button_frame)
        button_sub_frame.grid(row=0, column=0)

        self.btn_calcular = ttk.Button(button_sub_frame, text="Calcular Gasto de Tinta", command=self.calcular)
        self.btn_calcular.pack(side="left", padx=5)

        self.btn_copiar = ttk.Button(button_sub_frame, text="Copiar Formato Excel", command=self.copiar_formato_excel, state="disabled")
        self.btn_copiar.pack(side="left", padx=5)

        self.btn_limpiar = ttk.Button(button_sub_frame, text="Limpiar", command=self.limpiar_campos)
        self.btn_limpiar.pack(side="left", padx=5)

        # Marco de resultados
        result_frame = ttk.LabelFrame(main_frame, text="Resultados", padding="10 10 10 10")
        result_frame.grid(row=4, column=0, sticky="nsew", pady=5)
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)


        self.result_text = tk.Text(result_frame, height=12, wrap=tk.WORD, font=("Consolas", 10))
        scroll_result = ttk.Scrollbar(result_frame, command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=scroll_result.set)

        self.result_text.grid(row=0, column=0, sticky="nsew")
        scroll_result.grid(row=0, column=1, sticky="ns")


        self.resultado_formateado = ""
        self.inputs_medidas = []

        self.mostrar_mensaje_inicial()

    def mostrar_mensaje_inicial(self):
        mensaje = """
        BIENVENIDO A LA CALCULADORA DE GASTO DE TINTA

        Instrucciones:
        1. Ingrese el número de medidas diferentes
        2. Haga clic en 'Generar Formulario'
        3. Complete los datos para cada medida (Largo, Ancho, Alto - opcional)
        4. Seleccione la máquina a utilizar
        5. Haga clic en 'Calcular Gasto de Tinta'
        6. Use 'Copiar Formato Excel' para llevar los resultados al portapapeles
        7. Use 'Limpiar' para borrar todos los campos.
        """
        self.result_text.insert(tk.END, mensaje)
        self.result_text.config(state="disabled") # Hacerlo de solo lectura

    def generar_formulario_medidas(self):
        for widget in self.frame_medidas.winfo_children():
            widget.destroy()
        self.inputs_medidas = []

        try:
            total_medidas = int(self.entry_total_medidas.get())
            if total_medidas <= 0:
                raise ValueError("Debe ingresar un número positivo")

            for i in range(total_medidas):
                frame = ttk.LabelFrame(self.frame_medidas, text=f"Medida #{i+1}", padding="10 5 10 5")
                frame.pack(fill="x", pady=5, padx=2)
                # Las columnas internas también se configuran para ser redimensionables
                frame.columnconfigure(1, weight=1) # Permite que la entrada de Repeticiones se expanda
                frame.columnconfigure(3, weight=1) # Permite que la entrada de Largo se expanda
                frame.columnconfigure(5, weight=1) # Permite que la entrada de Ancho se expanda
                frame.columnconfigure(7, weight=1) # Permite que la entrada de Alto se expanda

                ttk.Label(frame, text="Repeticiones:").grid(row=0, column=0, sticky="w", padx=2, pady=2)
                entry_rep = ttk.Entry(frame, width=8)
                entry_rep.grid(row=0, column=1, padx=2, pady=2, sticky="ew")

                ttk.Label(frame, text="Largo (cm):").grid(row=0, column=2, sticky="w", padx=(10,2), pady=2)
                entry_largo = ttk.Entry(frame, width=10)
                entry_largo.grid(row=0, column=3, padx=2, pady=2, sticky="ew")

                ttk.Label(frame, text="Ancho (cm):").grid(row=0, column=4, sticky="w", padx=(10,2), pady=2)
                entry_ancho = ttk.Entry(frame, width=10)
                entry_ancho.grid(row=0, column=5, padx=2, pady=2, sticky="ew")

                ttk.Label(frame, text="Alto (cm):").grid(row=0, column=6, sticky="w", padx=(10,2), pady=2)
                entry_alto = ttk.Entry(frame, width=10)
                entry_alto.grid(row=0, column=7, padx=2, pady=2, sticky="ew")

                var_doble = tk.BooleanVar()
                ttk.Checkbutton(frame, text="Doble cara", variable=var_doble).grid(row=1, column=0, columnspan=8, sticky="w", pady=5)

                self.inputs_medidas.append((entry_rep, entry_largo, entry_ancho, entry_alto, var_doble))

            self.frame_medidas.update_idletasks()
            self.canvas.config(scrollregion=self.canvas.bbox("all"))

        except ValueError as e:
            messagebox.showerror("Error", f"Entrada inválida: {str(e)}")

    def calcular(self):
        if not self.inputs_medidas:
            messagebox.showwarning("Advertencia", "No hay medidas ingresadas para calcular.")
            return

        maquina = self.combo_maquina.get()
        medidas = []

        for idx, (rep_entry, largo_entry, ancho_entry, alto_entry, var_doble) in enumerate(self.inputs_medidas):
            try:
                rep = int(rep_entry.get())
                largo = float(largo_entry.get())
                ancho = float(ancho_entry.get())
                alto = float(alto_entry.get()) if alto_entry.get() else None
                doble = var_doble.get()

                if rep <= 0 or largo <= 0 or ancho <= 0:
                    raise ValueError("Valores de repeticiones, largo y ancho deben ser positivos")
                if alto is not None and alto <= 0:
                    raise ValueError("El valor de alto debe ser positivo o vacío")

                medidas.append((rep, largo, ancho, alto, doble))

            except ValueError as e:
                messagebox.showerror("Error", f"Medida #{idx+1}: {str(e)}")
                return

        try:
            resultado = calcular_gasto_tinta(maquina, medidas)

            # --- CORRECCIÓN CLAVE PARA GUARDAR EN BASE DE DATOS ---
            self.total_gasto = resultado.get('gasto_total', 0.0)
            # -----------------------------------------------------

            self.result_text.config(state="normal") # Habilitar escritura
            self.result_text.delete(1.0, tk.END)

            self.result_text.insert(tk.END, f"=== RESULTADOS DE GASTO DE TINTA PARA {maquina.upper()} ===\n\n")

            for key, value in resultado.items():
                if key == 'detalles':
                    for detalle in value:
                        if 'error' in detalle:
                            self.result_text.insert(tk.END, f"Medida {detalle['medida']}: {detalle['error']}\n\n")
                        else:
                            self.result_text.insert(tk.END, (
                                f"  Medida {detalle['medida']}:\n"
                                f"    Repeticiones: {detalle['repeticiones']}x\n"
                                f"    Dimensiones: {detalle['dimensiones']} cm\n"
                                f"    Área base: {self.formato_coma(detalle['area_base'])} m²\n"
                                f"    Área {'(doble cara)' if detalle['doble_cara'] else ''}: {self.formato_coma(detalle['area_por_unidad'])} m²\n"
                                f"    Área total por esta medida: {self.formato_coma(detalle['area_total'])} m²\n"
                                f"    Subtotal costo: ${self.formato_coma(detalle['subtotal'])}\n\n"
                            ))
                elif key == 'gasto_total' or key == 'area_total_reps':
                    self.result_text.insert(tk.END, f"TOTAL {key.replace('_', ' ').upper()}: {self.formato_coma(value)}\n")
                elif isinstance(value, float):
                    self.result_text.insert(tk.END, f"{key.replace('_', ' ').title()}: {self.formato_coma(value)}\n")
                else:
                    self.result_text.insert(tk.END, f"{key.replace('_', ' ').title()}: {value}\n")

            metros = resultado.get('area_total_reps', 0)
            costo = resultado.get('gasto_total', 0)
            
            # --- INICIO DE LA MODIFICACIÓN ---
            # Determinar el tipo de tinta según la máquina seleccionada
            if maquina in ["CAMA PLANA", "MIMAKI UU"]:
                tipo_tinta = "TINTA UV"
            else:
                tipo_tinta = "TINTA"

            # Usar la variable tipo_tinta para crear el formato de Excel
            self.resultado_formateado = f"{self.formato_coma(metros)}\tMETROS CUADRADOS\t{tipo_tinta}\t{self.formato_coma(costo)}"
            # --- FIN DE LA MODIFICACIÓN ---

            self.result_text.insert(tk.END, "\n=== FORMATO PARA EXCEL ===\n")
            self.result_text.insert(tk.END, self.resultado_formateado + "\n")

            self.btn_copiar.config(state="normal")
            self.result_text.config(state="disabled") # Hacerlo de solo lectura de nuevo

        except Exception as e:
            messagebox.showerror("Error", f"Error en cálculo: {str(e)}")
            self.result_text.config(state="disabled") # Hacerlo de solo lectura

    def copiar_formato_excel(self):
        if not self.resultado_formateado:
            messagebox.showwarning("Advertencia", "No hay resultados para copiar")
            return

        self.root.clipboard_clear()
        self.root.clipboard_append(self.resultado_formateado)
        self.root.update()
        messagebox.showinfo("Copiado", "Formato copiado al portapapeles")

    def limpiar_campos(self):
        self.entry_total_medidas.delete(0, tk.END)
        self.generar_formulario_medidas()  # Esto limpiará y regenerará el formulario
        self.combo_maquina.set("CAMA PLANA")
        self.result_text.config(state="normal") # Habilitar escritura para limpiar
        self.result_text.delete(1.0, tk.END)
        self.resultado_formateado = ""
        self.btn_copiar.config(state="disabled")
        self.mostrar_mensaje_inicial()
        self.result_text.config(state="disabled") # Hacerlo de solo lectura

    def formato_coma(self, numero):
        """Formatea un número con coma como separador decimal."""
        return f"{numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
