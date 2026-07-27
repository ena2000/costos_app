import tkinter as tk
from tkinter import ttk, messagebox
from models import mano_obra
from itertools import combinations
from datetime import datetime, timedelta
from functools import partial

class ManoObraUI:
    def __init__(self, master):
        self.master = master
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)

        self.inicializar_variables()
        self.configurar_ui()

    def configurar_ui(self):
        """Configura los elementos de la interfaz de usuario."""
        main_frame = ttk.Frame(self.master, padding="10 10 10 10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1) 
        main_frame.rowconfigure(5, weight=0) 
        main_frame.rowconfigure(8, weight=1)

        operario_main_frame = ttk.LabelFrame(main_frame, text="Costo de Operario", padding="10 10 10 10")
        operario_main_frame.grid(row=1, column=0, rowspan=3, columnspan=4, sticky="nsew", pady=5)
        operario_main_frame.columnconfigure(0, weight=1)
        operario_main_frame.rowconfigure(1, weight=1) 

        top_operario_frame = ttk.Frame(operario_main_frame)
        top_operario_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ttk.Label(top_operario_frame, text="¿Cuántas actividades se realizan?").pack(side="left", padx=(0, 5))
        self.entry_num_actividades = ttk.Entry(top_operario_frame, width=10)
        self.entry_num_actividades.pack(side="left", padx=5)
        ttk.Button(top_operario_frame, text="Generar Formulario", command=self._generar_formulario_actividades).pack(side="left", padx=5)

        canvas_frame = ttk.Frame(operario_main_frame)
        canvas_frame.grid(row=1, column=0, sticky="nsew")
        canvas_frame.columnconfigure(0, weight=1)
        canvas_frame.rowconfigure(0, weight=1)
        
        self.canvas_operario = tk.Canvas(canvas_frame, borderwidth=0, highlightthickness=0)
        self.scrollbar_operario = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas_operario.yview)
        self.frame_actividades = ttk.Frame(self.canvas_operario)
        self.canvas_operario.configure(yscrollcommand=self.scrollbar_operario.set)
        self.canvas_operario.create_window((0, 0), window=self.frame_actividades, anchor="nw", tags="self.frame_actividades")
        self.frame_actividades.bind("<Configure>", lambda e: self.canvas_operario.configure(scrollregion=self.canvas_operario.bbox("all")))
        self.canvas_operario.grid(row=0, column=0, sticky="nsew")
        self.scrollbar_operario.grid(row=0, column=1, sticky="ns")

        installation_frame = ttk.LabelFrame(main_frame, text="Costo de Instalación", padding="10 10 10 10")
        installation_frame.grid(row=5, column=0, columnspan=4, sticky="ew", pady=5)
        
        top_installation_controls_frame = ttk.Frame(installation_frame)
        top_installation_controls_frame.grid(row=0, column=0, sticky="ew", pady=2)
        top_installation_controls_frame.columnconfigure(1, weight=1)
        top_installation_controls_frame.columnconfigure(3, weight=1)
        top_installation_controls_frame.columnconfigure(5, weight=1)

        ttk.Label(top_installation_controls_frame, text="Cantidad total de operarios:").grid(row=0, column=0, sticky="w", padx=5)
        self.entry_cantidad_operarios_instalacion = ttk.Entry(top_installation_controls_frame, width=15)
        self.entry_cantidad_operarios_instalacion.grid(row=0, column=1, padx=5, sticky="ew")

        ttk.Label(top_installation_controls_frame, text="Viáticos ($):").grid(row=0, column=2, sticky="w", padx=5)
        self.entry_viaticos_instalacion = ttk.Entry(top_installation_controls_frame, width=15)
        self.entry_viaticos_instalacion.grid(row=0, column=3, padx=5, sticky="ew")
        
        ttk.Label(top_installation_controls_frame, text="En cuántos días se realiza?").grid(row=0, column=4, sticky="w", padx=5)
        self.entry_num_dias_instalacion = ttk.Entry(top_installation_controls_frame, width=8)
        self.entry_num_dias_instalacion.grid(row=0, column=5, padx=5, sticky="w")
        ttk.Button(top_installation_controls_frame, text="Generar Entradas de Horas", command=self._generar_formulario_dias_instalacion).grid(row=0, column=6, sticky="w", padx=5)

        self.frame_dias_instalacion = ttk.Frame(installation_frame)
        self.frame_dias_instalacion.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        button_frame = ttk.Frame(main_frame, padding="5 0 5 0")
        button_frame.grid(row=7, column=0, columnspan=4, sticky="ew", pady=10)
        button_frame.columnconfigure(0, weight=1)
        button_sub_frame = ttk.Frame(button_frame)
        button_sub_frame.grid(row=0, column=0)
        self.btn_calcular = ttk.Button(button_sub_frame, text="Calcular Costo Total", command=self.calcular)
        self.btn_calcular.pack(side="left", padx=5)
        self.btn_copiar = ttk.Button(button_sub_frame, text="Copiar Formato Excel", command=self.copiar_a_portapapeles)
        self.btn_copiar.pack(side="left", padx=5)
        self.btn_limpiar = ttk.Button(button_sub_frame, text="Limpiar", command=self.limpiar_campos)
        self.btn_limpiar.pack(side="left", padx=5)
        
        result_frame = ttk.LabelFrame(main_frame, text="Resultados del Cálculo", padding="10 10 10 10")
        result_frame.grid(row=8, column=0, columnspan=4, padx=5, pady=5, sticky="nsew")
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)
        self.resultado = tk.Text(result_frame, height=15, width=90, wrap=tk.WORD, font=("Consolas", 10))
        self.resultado.grid(row=0, column=0, sticky="nsew")
        result_scroll = ttk.Scrollbar(result_frame, orient="vertical", command=self.resultado.yview)
        result_scroll.grid(row=0, column=1, sticky="ns")
        self.resultado.config(yscrollcommand=result_scroll.set)

    def inicializar_variables(self):
        """Inicializa las variables de la clase."""
        self.maquinas_disenador = []
        self.salida_excel = ""
        self.horas_laminacion_total = 0
        self.var_almuerzo_disenador = tk.BooleanVar()
        self.horas_disenador_cif = 0
        self.horas_operario_cif = 0
        self.inputs_actividades = []
        self.inputs_dias_instalacion = []
        self.lista_actividades = [
            "LAMINACION", "REFILACION", "BRANDEO", "PEGADO", "DOBLADO",
            "ARMADO", "PINTADO", "CORTE", "SELLADO", "FIJACION", "SOLDAR"
        ]

    def _generar_formulario_actividades(self):
        for widget in self.frame_actividades.winfo_children():
            widget.destroy()
        self.inputs_actividades = []

        try:
            num_actividades = int(self.entry_num_actividades.get())
            if num_actividades <= 0: raise ValueError
        except (ValueError, TypeError):
            messagebox.showerror("Error", "Ingrese un número válido de actividades.")
            return

        for i in range(num_actividades):
            actividad_frame = ttk.LabelFrame(self.frame_actividades, text=f"Actividad #{i+1}", padding=10)
            actividad_frame.pack(pady=5, padx=5, fill="x", expand=True)
            
            controles_frame = ttk.Frame(actividad_frame)
            controles_frame.pack(fill="x", expand=True)
            
            ttk.Label(controles_frame, text="Actividad:").pack(side="left", padx=(0,5))
            combo_actividad = ttk.Combobox(controles_frame, values=self.lista_actividades, state="readonly", width=15)
            combo_actividad.pack(side="left", padx=5)
            
            ttk.Label(controles_frame, text="En cuántos días se realiza?").pack(side="left", padx=(10,5))
            entry_dias = ttk.Entry(controles_frame, width=8)
            entry_dias.pack(side="left", padx=5)

            frame_dias = ttk.Frame(actividad_frame, padding="5 0 0 0")
            frame_dias.pack(fill="x", expand=True)

            btn_generar_dias = ttk.Button(controles_frame, text="Generar Formulario Días")
            btn_generar_dias.config(command=partial(self._generar_formulario_dias, entry_dias, frame_dias, i))
            btn_generar_dias.pack(side="left", padx=5)

            self.inputs_actividades.append({
                "combo_actividad": combo_actividad,
                "entry_dias": entry_dias,
                "frame_dias": frame_dias,
                "daily_inputs": []
            })
        self.canvas_operario.update_idletasks()
        self.canvas_operario.config(scrollregion=self.canvas_operario.bbox("all"))


    def _generar_formulario_dias(self, entry_dias_widget, frame_dias_widget, actividad_index):
        for widget in frame_dias_widget.winfo_children():
            widget.destroy()
        self.inputs_actividades[actividad_index]["daily_inputs"] = []
        
        try:
            num_dias = int(entry_dias_widget.get())
            if num_dias <= 0: raise ValueError
        except (ValueError, TypeError):
            messagebox.showerror("Error", "Ingrese un número válido de días.")
            return
            
        for i in range(num_dias):
            dia_frame = ttk.Frame(frame_dias_widget)
            dia_frame.pack(pady=3, fill="x", expand=True)
            
            ttk.Label(dia_frame, text=f"Día #{i+1} - Hora Inicio (HH:MM):").pack(side="left")
            entry_inicio = ttk.Entry(dia_frame, width=8)
            entry_inicio.pack(side="left", padx=5)
            
            ttk.Label(dia_frame, text="Hora Fin (HH:MM):").pack(side="left")
            entry_fin = ttk.Entry(dia_frame, width=8)
            entry_fin.pack(side="left", padx=5)
            
            ttk.Label(dia_frame, text="Cant. de Operarios:").pack(side="left")
            entry_operarios = ttk.Entry(dia_frame, width=8)
            entry_operarios.pack(side="left", padx=5)
            
            var_almuerzo_dia = tk.BooleanVar()
            check_almuerzo = ttk.Checkbutton(dia_frame, text="Almuerzo (0.5h)", variable=var_almuerzo_dia)
            check_almuerzo.pack(side="left", padx=5)
            
            self.inputs_actividades[actividad_index]["daily_inputs"].append({
                "inicio": entry_inicio, 
                "fin": entry_fin, 
                "operarios": entry_operarios,
                "almuerzo_var": var_almuerzo_dia
            })
        self.canvas_operario.update_idletasks()
        self.canvas_operario.config(scrollregion=self.canvas_operario.bbox("all"))

    def _generar_formulario_dias_instalacion(self):
        for widget in self.frame_dias_instalacion.winfo_children():
            widget.destroy()
        self.inputs_dias_instalacion = []
        
        try:
            num_dias = int(self.entry_num_dias_instalacion.get())
            if num_dias <= 0: raise ValueError
        except (ValueError, TypeError):
            messagebox.showerror("Error", "Ingrese un número válido de días.")
            return
            
        for i in range(num_dias):
            dia_frame = ttk.Frame(self.frame_dias_instalacion)
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
            
            self.inputs_dias_instalacion.append({
                "inicio": entry_inicio, 
                "fin": entry_fin, 
                "almuerzo_var": var_almuerzo_dia
            })

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

    def update_designer_machines(self, maquina_nombre=None, horas=None, disenador=None, reset=False, is_laminadora=False):
        """Callback que recibe datos desde la pestaña de Maquinaria."""
        if reset:
            self.maquinas_disenador = []
            self.horas_laminacion_total = 0
        elif maquina_nombre and horas is not None and disenador is not None:
            if is_laminadora:
                self.horas_laminacion_total += horas
            else:
                # Buscar si ya existe una entrada para esta máquina y diseñador
                entry_key = (maquina_nombre, disenador)
                found_index = -1
                for i, (m, h, d) in enumerate(self.maquinas_disenador):
                    if (m, d) == entry_key:
                        found_index = i
                        break
                
                if found_index == -1:
                    self.maquinas_disenador.append((maquina_nombre, horas, disenador))
                else:
                    m_old, h_old, d_old = self.maquinas_disenador[found_index]
                    self.maquinas_disenador[found_index] = (maquina_nombre, h_old + horas, disenador)
                
    def calcular(self):
        """Calcula los costos de mano de obra y CIF."""
        self.resultado.config(state="normal")
        self.resultado.delete("1.0", tk.END)
        self.salida_excel = ""
        self.horas_disenador_cif = 0
        self.horas_operario_cif = 0

        designer_input_exists = bool(self.maquinas_disenador)
        operario_input_exists = bool(self.inputs_actividades) or self.horas_laminacion_total > 0
        instalacion_input_exists = bool(self.entry_cantidad_operarios_instalacion.get())

        if not (designer_input_exists or operario_input_exists or instalacion_input_exists):
            return

        self.calcular_disenador()
        self.calcular_operario()
        self.calcular_instalacion()
        self.calcular_cif()
        self.mostrar_formato_excel()
        self.resultado.config(state="disabled")

    def calcular_disenador(self):
        """Calcula los costos de mano de obra del diseñador basados en el uso de maquinaria."""
        if self.maquinas_disenador:
            self.resultado.insert(tk.END, "=== COSTO DE MANO DE OBRA - DISEÑADOR ===\n")
            
            designer_data = {}
            for maquina, horas, disenador in self.maquinas_disenador:
                if disenador not in designer_data:
                    designer_data[disenador] = {"details": []}
                designer_data[disenador]["details"].append([maquina, horas])
            
            total_costo_final = 0
            total_horas_final = 0

            for disenador, data in designer_data.items():
                self.resultado.insert(tk.END, f"  Responsable: {disenador}\n")
                horas_por_responsable = 0
                costo_por_responsable = 0

                for detalle in data["details"]:
                    maquina_nom, horas = detalle
                    costo = horas * mano_obra.costo_hora_disenador
                    self.resultado.insert(tk.END, f"    - {maquina_nom}: {self.formato_coma(horas)} hrs -> ${self.formato_coma(costo)}\n")
                    
                    linea = f"{self.formato_coma(horas)}\tHORAS\t{maquina_nom.upper()}\t{self.formato_coma(costo)}"
                    self.salida_excel += linea + "\n"
                    
                    horas_por_responsable += horas
                    costo_por_responsable += costo

                total_horas_final += horas_por_responsable
                total_costo_final += costo_por_responsable
            
            self.horas_disenador_cif = total_horas_final
            self.resultado.insert(tk.END, f"GRAN TOTAL HORAS DISEÑADOR: {self.formato_coma(total_horas_final)} HORAS\n")
            self.resultado.insert(tk.END, f"GRAN TOTAL COSTO DISEÑADOR: ${self.formato_coma(total_costo_final)}\n\n")

    def calcular_operario(self):
        """Calcula los costos de mano de obra del operario."""
        if not self.inputs_actividades and self.horas_laminacion_total <= 0:
            return

        self.resultado.insert(tk.END, "=== COSTO DE MANO DE OBRA - OPERARIO ===\n")
        total_horas_operario_final = 0
        total_costo_operario_final = 0
        total_horas_para_cif = 0

        if self.horas_laminacion_total > 0:
            costo_laminacion = self.horas_laminacion_total * mano_obra.costo_hora_operario
            total_horas_operario_final += self.horas_laminacion_total
            total_costo_operario_final += costo_laminacion
            total_horas_para_cif += self.horas_laminacion_total

            self.resultado.insert(tk.END, f"  Actividad: LAMINACION (MAQUINA) - Total Horas: {self.formato_coma(self.horas_laminacion_total)} - Costo: ${self.formato_coma(costo_laminacion)}\n")
            linea = f"{self.formato_coma(self.horas_laminacion_total)}\tHORAS\tM.O LAMINACION\t{self.formato_coma(costo_laminacion)}"
            self.salida_excel += linea + "\n"

        for i, actividad_data in enumerate(self.inputs_actividades):
            actividad_nombre = actividad_data["combo_actividad"].get()
            if not actividad_nombre: continue

            total_horas_actividad = 0
            horas_actividad_para_cif = 0

            for j, daily_input in enumerate(actividad_data["daily_inputs"]):
                try:
                    inicio = daily_input["inicio"].get()
                    fin = daily_input["fin"].get()
                    operarios = int(daily_input["operarios"].get() or 0)
                    almuerzo_marcado = daily_input["almuerzo_var"].get()
                    horas_decimales = self._convertir_a_horas_decimales(inicio, fin)
                    if horas_decimales is None or operarios <= 0: continue
                    
                    horas_dia_para_cif = horas_decimales
                    if almuerzo_marcado and horas_dia_para_cif > 0.5:
                        horas_dia_para_cif -= 0.5
                    
                    total_horas_actividad += horas_dia_para_cif * operarios
                    horas_actividad_para_cif += horas_dia_para_cif
                except: continue
            
            if total_horas_actividad > 0:
                costo_actividad = total_horas_actividad * mano_obra.costo_hora_operario
                total_horas_operario_final += total_horas_actividad
                total_costo_operario_final += costo_actividad
                total_horas_para_cif += horas_actividad_para_cif

                self.resultado.insert(tk.END, f"  Actividad: {actividad_nombre} - Total Horas: {self.formato_coma(total_horas_actividad)} - Costo: ${self.formato_coma(costo_actividad)}\n")
                linea = f"{self.formato_coma(total_horas_actividad)}\tHORAS\tM.O {actividad_nombre.upper()}\t{self.formato_coma(costo_actividad)}"
                self.salida_excel += linea + "\n"

        self.horas_operario_cif = total_horas_para_cif
        self.resultado.insert(tk.END, f"GRAN TOTAL HORAS OPERARIO: {self.formato_coma(total_horas_operario_final)} HORAS\n")
        self.resultado.insert(tk.END, f"GRAN TOTAL COSTO OPERARIO: ${self.formato_coma(total_costo_operario_final)}\n\n")

    def calcular_instalacion(self):
        """Calcula los costos de mano de obra de instalación."""
        try:
            cantidad_operarios_str = self.entry_cantidad_operarios_instalacion.get()
            if not cantidad_operarios_str: return

            cantidad_operarios = int(cantidad_operarios_str)
            viaticos = float(self.entry_viaticos_instalacion.get() or 0.0)

            total_horas_por_operario = 0
            for dia_input in self.inputs_dias_instalacion:
                inicio_str = dia_input["inicio"].get()
                fin_str = dia_input["fin"].get()
                almuerzo_marcado = dia_input["almuerzo_var"].get()

                horas_decimales = self._convertir_a_horas_decimales(inicio_str, fin_str)
                if horas_decimales is None: continue

                if almuerzo_marcado and horas_decimales > 0.5:
                    horas_decimales -= 0.5
                total_horas_por_operario += horas_decimales
            
            total_horas_mano_obra = total_horas_por_operario * cantidad_operarios
            costo_mano_obra = total_horas_mano_obra * mano_obra.costo_hora_operario
            costo_total_instalacion = costo_mano_obra + viaticos
            
            if total_horas_mano_obra > 0 or viaticos > 0:
                self.resultado.insert(tk.END, "=== COSTO DE MANO DE OBRA - INSTALACIÓN ===\n")
                if total_horas_mano_obra > 0:
                    linea_mo = f"{self.formato_coma(total_horas_mano_obra)}\tHORAS\tM.O INSTALACION\t{self.formato_coma(costo_mano_obra)}"
                    self.salida_excel += linea_mo + "\n"
                if viaticos > 0:
                    linea_viaticos = f"\t\tVIATICOS\t{self.formato_coma(viaticos)}"
                    self.salida_excel += linea_viaticos + "\n"
                self.resultado.insert(tk.END, f"TOTAL INSTALACIÓN: ${self.formato_coma(costo_total_instalacion)}\n\n")
        except: pass

    def calcular_cif(self):
        tiempo_total_obra_cif = self.horas_disenador_cif + self.horas_operario_cif
        if tiempo_total_obra_cif > 0:
            total_cif = mano_obra.calcular_cif(tiempo_total_obra_cif)
            linea_cif = f"{self.formato_coma(tiempo_total_obra_cif)}\tHORAS\tCIF\t{self.formato_coma(total_cif)}"
            self.salida_excel += linea_cif + "\n"
            self.resultado.insert(tk.END, f"TOTAL CIF: ${self.formato_coma(total_cif)}\n\n")

    def mostrar_formateado(self):
        return self.salida_excel

    def mostrar_formato_excel(self):
        if self.salida_excel:
            self.resultado.insert(tk.END, "\n=== FORMATO TABULADO PARA EXCEL ===\n")
            self.resultado.insert(tk.END, self.salida_excel)

    def copiar_a_portapapeles(self):
        if not self.salida_excel: return
        formato_excel_completo = "HORAS\tUNIDAD\tDETALLE\tCOSTO\n" + self.salida_excel
        self.master.clipboard_clear()
        self.master.clipboard_append(formato_excel_completo)
        messagebox.showinfo("Copiado", "Copiado al portapapeles.")

    def limpiar_campos(self):
        self.entry_num_actividades.delete(0, tk.END)
        for widget in self.frame_actividades.winfo_children(): widget.destroy()
        self.entry_num_dias_instalacion.delete(0, tk.END)
        self.entry_cantidad_operarios_instalacion.delete(0, tk.END)
        self.entry_viaticos_instalacion.delete(0, tk.END)
        for widget in self.frame_dias_instalacion.winfo_children(): widget.destroy()
        self.resultado.config(state="normal")
        self.resultado.delete("1.0", tk.END)
        self.resultado.config(state="disabled")
        self.inicializar_variables()

    def formato_coma(self, numero):
        return f"{numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    @property
    def total_horas_disenador(self):
        return sum(h for m, h, d in self.maquinas_disenador)

    @property
    def total_horas_operario(self):
        total = self.horas_laminacion_total
        for actividad in self.inputs_actividades:
            for daily in actividad["daily_inputs"]:
                try:
                    h = self._convertir_a_horas_decimales(daily["inicio"].get(), daily["fin"].get()) or 0.0
                    if daily["almuerzo_var"].get() and h > 0.5: h -= 0.5
                    total += (h * int(daily["operarios"].get() or 0))
                except: continue
        return total

    @property
    def total_horas_instalacion(self):
        total = 0
        try:
            ope_inst = int(self.entry_cantidad_operarios_instalacion.get() or 0)
            for dia in self.inputs_dias_instalacion:
                h = self._convertir_a_horas_decimales(dia["inicio"].get(), dia["fin"].get()) or 0.0
                if dia["almuerzo_var"].get() and h > 0.5: h -= 0.5
                total += (h * ope_inst)
        except: pass
        return total

    def get_totales(self):
        h_dis = self.total_horas_disenador
        h_ope = self.total_horas_operario
        h_inst = self.total_horas_instalacion
        c_mo = (h_dis * mano_obra.costo_hora_disenador) + (h_ope * mano_obra.costo_hora_operario)
        c_inst = h_inst * mano_obra.costo_hora_operario
        h_para_cif = self.horas_disenador_cif + self.horas_operario_cif
        return {
            "horas_total": h_dis + h_ope,
            "costo_mo_total": c_mo,
            "costo_ins_total": c_inst,
            "viaticos": float(self.entry_viaticos_instalacion.get() or 0.0),
            "cif": mano_obra.calcular_cif(h_para_cif) if h_para_cif > 0 else 0.0
        }