import tkinter as tk
from tkinter import ttk, messagebox
from models.costo_maquinaria import CostoMaquinaria
from datetime import datetime, timedelta

class CostoMaquinariaUI:
    def __init__(self, parent, on_maquinaria_agregada=None):
        self.root = parent
        self.on_maquinaria_agregada_callback = on_maquinaria_agregada

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        main_frame = ttk.Frame(self.root)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1) # Permite que el área de resultados se expanda

        ttk.Label(main_frame, text="Calculadora de Costo de Maquinaria", font=("Segoe UI", 16, "bold")).grid(row=0, column=0, columnspan=4, pady=(0, 10), sticky="ew")

        input_frame = ttk.LabelFrame(main_frame, text="Agregar Maquinaria", padding=10)
        input_frame.grid(row=1, column=0, sticky="ew", pady=5)
        input_frame.columnconfigure(0, weight=1)

        maquina_disenador_frame = ttk.Frame(input_frame)
        maquina_disenador_frame.grid(row=0, column=0, sticky="ew", pady=2)
        maquina_disenador_frame.columnconfigure(1, weight=1)
        maquina_disenador_frame.columnconfigure(3, weight=1)

        ttk.Label(maquina_disenador_frame, text="Selecciona la maquinaria:").grid(row=0, column=0, sticky="w", padx=5)
        self.combo_maquinaria = ttk.Combobox(maquina_disenador_frame, values=[
            "MAQUINA GALAXY", "MAQUINA LAMINADORA", "PLOTTER", "ORISS",
            "MIMAKI UJV100-160 PLUS", "CAMA PLANA", "MAQUINA LASER", "MAQUINA CORTADORA", "MAQUINA 320"
        ], state="readonly", width=30)
        self.combo_maquinaria.grid(row=0, column=1, padx=5, sticky="ew")
        self.combo_maquinaria.current(0)

        ttk.Label(maquina_disenador_frame, text="Diseñador asociado:").grid(row=0, column=2, sticky="w", padx=5)
        self.combo_disenador = ttk.Combobox(maquina_disenador_frame, values=["XAVIER CABRERA","CRISTOPHER NARANJO","ANTONY LINO"], state="readonly", width=25)
        self.combo_disenador.grid(row=0, column=3, padx=5, sticky="ew")
        self.combo_disenador.current(0)

        dias_frame = ttk.Frame(input_frame)
        dias_frame.grid(row=1, column=0, sticky="ew", pady=(10, 5), padx=5)
        dias_frame.columnconfigure(4, weight=1)

        ttk.Label(dias_frame, text="En cuántos días se utiliza?").grid(row=0, column=0, sticky="w")
        self.entry_num_dias = ttk.Entry(dias_frame, width=8)
        self.entry_num_dias.grid(row=0, column=1, sticky="w", padx=5)
        ttk.Button(dias_frame, text="Generar Entradas de Horas", command=self._generar_formulario_dias_maquinaria).grid(row=0, column=2, sticky="w", padx=5)
        
        ttk.Button(dias_frame, text="Agregar Maquinaria", command=self._agregar_maquinaria).grid(row=0, column=5, sticky="e")
        
        self.frame_dias_maquinaria = ttk.Frame(input_frame)
        self.frame_dias_maquinaria.grid(row=2, column=0, sticky="ew", padx=5, pady=5)

        ttk.Label(main_frame, text="Maquinarias Agregadas:").grid(row=2, column=0, columnspan=4, sticky="w", padx=5, pady=(5,0))
        self.lista_maquinarias = tk.Listbox(main_frame, height=6)
        self.lista_maquinarias.grid(row=3, column=0, columnspan=4, padx=5, pady=5, sticky="nsew")
        list_scroll = ttk.Scrollbar(main_frame, orient="vertical", command=self.lista_maquinarias.yview)
        list_scroll.grid(row=3, column=4, sticky="ns")
        self.lista_maquinarias.config(yscrollcommand=list_scroll.set)

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=4, sticky="ew", pady=10)
        button_frame.columnconfigure(0, weight=1)
        button_sub_frame = ttk.Frame(button_frame)
        button_sub_frame.grid(row=0, column=0) # Centra el sub-frame
        ttk.Button(button_sub_frame, text="Calcular Costo Total", command=self._calcular_costo_total).pack(side="left", padx=5)
        self.btn_copiar = ttk.Button(button_sub_frame, text="Copiar Formato Excel", command=self._copiar_a_portapapeles, state="disabled")
        self.btn_copiar.pack(side="left", padx=5)
        self.btn_limpiar = ttk.Button(button_sub_frame, text="Limpiar", command=self.limpiar_campos)
        self.btn_limpiar.pack(side="left", padx=5)

        result_frame = ttk.LabelFrame(main_frame, text="Resultados del Cálculo", padding=10)
        result_frame.grid(row=5, column=0, columnspan=4, padx=5, pady=10, sticky="nsew")
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)
        self.text_resultado = tk.Text(result_frame, height=10, wrap=tk.WORD)
        self.text_resultado.grid(row=0, column=0, sticky="nsew")
        result_scroll = ttk.Scrollbar(result_frame, orient="vertical", command=self.text_resultado.yview)
        result_scroll.grid(row=0, column=1, sticky="ns")
        self.text_resultado.config(yscrollcommand=result_scroll.set)

        self.maquinarias_agregadas = []
        self.salida_excel = ""
        self.text_resultado.config(state="disabled")
        self.inputs_dias_maquinaria = []

    def _formato_coma(self, numero):
        return f"{numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def _convertir_a_horas_decimales(self, inicio_str, fin_str):
        try:
            formato = "%H:%M"
            hora_inicio = datetime.strptime(inicio_str, formato)
            hora_fin = datetime.strptime(fin_str, formato)
            
            if hora_fin < hora_inicio:
                hora_fin += timedelta(days=1)

            diferencia = hora_fin - hora_inicio
            return diferencia.total_seconds() / 3600.0
        except ValueError:
            return None

    def _generar_formulario_dias_maquinaria(self):
        for widget in self.frame_dias_maquinaria.winfo_children():
            widget.destroy()
        self.inputs_dias_maquinaria = []
        
        try:
            num_dias = int(self.entry_num_dias.get())
            if num_dias <= 0: raise ValueError
        except (ValueError, TypeError):
            messagebox.showerror("Error", "Ingrese un número válido de días.")
            return
            
        for i in range(num_dias):
            dia_frame = ttk.Frame(self.frame_dias_maquinaria)
            dia_frame.pack(pady=3, fill="x", expand=True)
            
            ttk.Label(dia_frame, text=f"Día #{i+1} - Hora Inicio (HH:MM):").pack(side="left")
            entry_inicio = ttk.Entry(dia_frame, width=8)
            entry_inicio.pack(side="left", padx=5)
            
            ttk.Label(dia_frame, text="Hora Fin (HH:MM):").pack(side="left")
            entry_fin = ttk.Entry(dia_frame, width=8)
            entry_fin.pack(side="left", padx=5)
            
            var_almuerzo_dia = tk.BooleanVar()
            check_almuerzo = ttk.Checkbutton(dia_frame, text="Almuerzo (0.5h)", variable=var_almuerzo_dia)
            check_almuerzo.pack(side="left", padx=5)
            
            self.inputs_dias_maquinaria.append({
                "inicio": entry_inicio, 
                "fin": entry_fin, 
                "almuerzo_var": var_almuerzo_dia
            })

    def _agregar_maquinaria(self):
        maquina = self.combo_maquinaria.get()
        disenador = self.combo_disenador.get()

        try:
            if not self.inputs_dias_maquinaria:
                messagebox.showerror("Error", "Por favor, genere las entradas de horas y complete los datos.")
                return

            horas_trabajo_total = 0
            for i, dia_input in enumerate(self.inputs_dias_maquinaria):
                inicio_str = dia_input["inicio"].get()
                fin_str = dia_input["fin"].get()
                almuerzo_marcado = dia_input["almuerzo_var"].get()

                if not inicio_str or not fin_str:
                    messagebox.showerror("Error", f"Día #{i+1}: Por favor, complete la hora de inicio y fin.")
                    return

                horas_decimales = self._convertir_a_horas_decimales(inicio_str, fin_str)
                if horas_decimales is None:
                    messagebox.showerror("Error", f"Día #{i+1}: Formato de hora incorrecto. Use HH:MM.")
                    return

                if almuerzo_marcado:
                    if horas_decimales > 0.5:
                        horas_decimales -= 0.5
                
                horas_trabajo_total += horas_decimales

            if horas_trabajo_total <= 0:
                messagebox.showerror("Error", "El total de horas de trabajo debe ser mayor a cero.")
                return

            horas_trabajo = horas_trabajo_total

            self.maquinarias_agregadas.append((maquina, horas_trabajo, disenador))
            display_text = f"{maquina} - {self._formato_coma(horas_trabajo)} horas"
            self.lista_maquinarias.insert(tk.END, display_text)
            
            self.entry_num_dias.delete(0, tk.END)
            for widget in self.frame_dias_maquinaria.winfo_children():
                widget.destroy()
            self.inputs_dias_maquinaria = []

            if self.on_maquinaria_agregada_callback:
                is_laminadora = (maquina == "MAQUINA LAMINADORA")
                self.on_maquinaria_agregada_callback(
                    maquina_nombre=f"M.O {maquina}",
                    horas=horas_trabajo,
                    disenador=disenador,
                    is_laminadora=is_laminadora
                )
        except ValueError:
            messagebox.showerror("Error", "Error en los valores ingresados.")
        except Exception as e:
            messagebox.showerror("Error Inesperado", f"Ocurrió un error al agregar la maquinaria: {e}")

    def _calcular_costo_total(self):
        self.text_resultado.config(state="normal")
        self.text_resultado.delete("1.0", tk.END)
        self.salida_excel = ""

        if not self.maquinarias_agregadas:
            messagebox.showwarning("Advertencia", "No hay maquinarias agregadas para calcular.")
            self.text_resultado.insert(tk.END, "Por favor, agregue maquinarias para calcular su costo.")
            self.text_resultado.config(state="disabled")
            return
        
        self.text_resultado.insert(tk.END, "=== COSTO TOTAL POR MAQUINARIA ===\n\n")
        
        maquinaria_calculada = []
        for maquina, horas_trabajo, _ in self.maquinarias_agregadas:
            try:
                costo = CostoMaquinaria(maquina, horas_trabajo).calcular_costo()
                maquinaria_calculada.append({'maquina': maquina, 'horas': horas_trabajo, 'costo': costo})
            except (ValueError, Exception) as e:
                self.text_resultado.insert(tk.END, f"  ❌ Error para '{maquina}': {e}\n")
        
        total_costo_maquinaria = 0.0
        for item in maquinaria_calculada:
            total_costo_maquinaria += item['costo']
            self.text_resultado.insert(tk.END, f"  {item['maquina']}: {self._formato_coma(item['horas'])} horas, Costo: ${self._formato_coma(item['costo'])}\n")
            linea = f"{self._formato_coma(item['horas'])}\tHORAS\t{item['maquina'].upper()}\t{self._formato_coma(item['costo'])}"
            self.salida_excel += linea + "\n"
        
        self.text_resultado.insert(tk.END, f"\nTOTAL GENERAL MAQUINARIA: ${self._formato_coma(total_costo_maquinaria)}\n")
        if self.salida_excel:
            self.text_resultado.insert(tk.END, "\n=== FORMATO TABULADO PARA EXCEL ===\n")
            self.text_resultado.insert(tk.END, self.salida_excel)
        
        self.btn_copiar.config(state="normal")
        self.text_resultado.config(state="disabled")

    def _copiar_a_portapapeles(self):
        if not self.salida_excel:
            messagebox.showwarning("Advertencia", "No hay datos para copiar. Calcula el costo total primero.")
            return
        formato_excel_completo = "HORAS\tUNIDAD\tDETALLE\tCOSTO\n" + self.salida_excel
        self.root.clipboard_clear()
        self.root.clipboard_append(formato_excel_completo)
        self.root.update()
        messagebox.showinfo("Copiado", "Formato copiado al portapapeles.")

    def limpiar_campos(self):
        self.combo_maquinaria.set("MAQUINA GALAXY")
        self.entry_num_dias.delete(0, tk.END)
        for widget in self.frame_dias_maquinaria.winfo_children():
            widget.destroy()
        self.inputs_dias_maquinaria = []

        self.lista_maquinarias.delete(0, tk.END)
        self.text_resultado.config(state="normal")
        self.text_resultado.delete("1.0", tk.END)
        self.text_resultado.config(state="disabled")
        self.maquinarias_agregadas = []
        self.salida_excel = ""
        self.combo_disenador.current(0)
        if self.on_maquinaria_agregada_callback:
            self.on_maquinaria_agregada_callback(reset=True)

    # === ESTO DEBE TENER 4 ESPACIOS DE SANGRÍA (ALINEADO CON LOS DE ARRIBA) ===
    @property
    def total_costo_maquinaria(self):
        """Suma el costo de todas las máquinas agregadas a la lista"""
        total = 0.0
        for maquina, horas, _ in self.maquinarias_agregadas:
            # Usamos la clase CostoMaquinaria que ya importaste al inicio del archivo
            costo = CostoMaquinaria(maquina, horas).calcular_costo()
            total += costo
        return total

    @property
    def total_horas_maquina(self):
        """Suma todas las horas de máquina registradas"""
        return sum(item[1] for item in self.maquinarias_agregadas)

    def get_detalle_maquinas(self):
        """Desglose para historial: horas por máquina y diseñador."""
        return [
            {"maquina": maquina, "operario": disenador, "horas": float(horas)}
            for maquina, horas, disenador in self.maquinarias_agregadas
        ]

    def cargar_desde_datos(self, maquinarias: list, disenador: str = "XAVIER CABRERA"):
        """Carga máquinas desde OCR: lista de {maquina, hora_inicio, hora_fin}."""
        # Agrupa por máquina sumando horas del mismo equipo
        acumulado = {}
        for item in maquinarias:
            maquina = item.get("maquina")
            hi = item.get("hora_inicio")
            hf = item.get("hora_fin")
            if not maquina or not hi or not hf:
                continue
            horas = self._convertir_a_horas_decimales(hi, hf)
            if horas is None or horas <= 0:
                continue
            acumulado[maquina] = acumulado.get(maquina, 0.0) + horas

        valores = list(self.combo_disenador["values"])
        if disenador in valores:
            self.combo_disenador.set(disenador)
        else:
            disenador = self.combo_disenador.get() or valores[0]

        for maquina, horas_trabajo in acumulado.items():
            if maquina not in self.combo_maquinaria["values"]:
                continue
            self.maquinarias_agregadas.append((maquina, horas_trabajo, disenador))
            display_text = f"{maquina} - {self._formato_coma(horas_trabajo)} horas"
            self.lista_maquinarias.insert(tk.END, display_text)
            if self.on_maquinaria_agregada_callback:
                is_laminadora = (maquina == "MAQUINA LAMINADORA")
                self.on_maquinaria_agregada_callback(
                    maquina_nombre=f"M.O {maquina}",
                    horas=horas_trabajo,
                    disenador=disenador,
                    is_laminadora=is_laminadora,
                )

        if self.maquinarias_agregadas:
            self._calcular_costo_total()