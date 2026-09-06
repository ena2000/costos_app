import tkinter as tk
from tkinter import ttk, messagebox
from ttkthemes import ThemedTk
from datetime import datetime

# Importación de interfaces (UI)
from iu.costo_maquinaria_ui import CostoMaquinariaUI
from iu.mano_obra_ui import ManoObraUI
from iu.gasto_tinta_ui import GastoTintaUI
from iu.costo_materiales_ui import CostoMaterialesUI
from iu.inventario_ui import InventarioUI
from iu.historial_ui import HistorialUI
from iu.tarifas_ui import TarifasUI
from iu.cargar_fotos_ui import CargarFotosDialog, aplicar_datos_a_app

# Importación de modelos y base de datos
from models import database
from models.historial import registrar_orden

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Calculadora de Costos - PUBLISTIK")
        self.root.geometry("950x700") 

        database.crear_tablas()
        from models import tarifas
        tarifas.cargar()

        style = ttk.Style()
        style.configure(".", font=("Segoe UI", 9))
        style.configure("TNotebook.Tab", padding=[8, 2])
        style.configure("Copiar.TButton", font=("Segoe UI", 9)) 
        
        self.setup_ui()

    def setup_ui(self):
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)

        datos_orden_frame = ttk.LabelFrame(self.root, text=" Datos Generales de la Orden ", padding=10)
        datos_orden_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)

        ttk.Label(datos_orden_frame, text="Cliente:").grid(row=0, column=0, padx=5, sticky="w")
        self.entry_cliente = ttk.Entry(datos_orden_frame, width=30)
        self.entry_cliente.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(datos_orden_frame, text="Trabajo:").grid(row=0, column=2, padx=5, sticky="w")
        self.entry_desc = ttk.Entry(datos_orden_frame, width=40)
        self.entry_desc.grid(row=0, column=3, padx=5, pady=5)

        fecha_actual = datetime.now().strftime("%d/%m/%Y")
        ttk.Label(datos_orden_frame, text="Inicio:").grid(row=1, column=0, padx=5, sticky="w")
        self.entry_fecha_inicio = ttk.Entry(datos_orden_frame, width=15)
        self.entry_fecha_inicio.insert(0, fecha_actual)
        self.entry_fecha_inicio.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(datos_orden_frame, text="Fin:").grid(row=1, column=2, padx=5, sticky="w")
        self.entry_fecha_fin = ttk.Entry(datos_orden_frame, width=15)
        self.entry_fecha_fin.insert(0, fecha_actual)
        self.entry_fecha_fin.grid(row=1, column=3, padx=5, pady=5, sticky="w")

        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        # 1. Mano de Obra
        self.frame_mo = ttk.Frame(self.notebook)
        self.mano_obra_ui = ManoObraUI(self.frame_mo)

        # 2. Maquinaria
        self.frame_maq = ttk.Frame(self.notebook)
        self.maquinaria_ui = CostoMaquinariaUI(
            self.frame_maq, 
            on_maquinaria_agregada=self.mano_obra_ui.update_designer_machines
        )

        self.tinta_ui = GastoTintaUI(ttk.Frame(self.notebook))
        self.materiales_ui = CostoMaterialesUI(ttk.Frame(self.notebook))
        self.inventario_ui = InventarioUI(ttk.Frame(self.notebook))
        self.historial_ui = HistorialUI(ttk.Frame(self.notebook))
        self.tarifas_ui = TarifasUI(ttk.Frame(self.notebook))

        self.notebook.add(self.maquinaria_ui.root, text="⚙️ Maquinaria")
        self.notebook.add(self.mano_obra_ui.master, text="👥 Mano de Obra")
        self.notebook.add(self.tinta_ui.root, text="💧 Tinta")
        self.notebook.add(self.materiales_ui.main_frame, text="📦 Materiales")
        self.notebook.add(self.inventario_ui.root, text="🔍 Inventario")
        self.notebook.add(self.historial_ui.root, text="📜 Historial")
        self.notebook.add(self.tarifas_ui.root, text="💲 Tarifas")

        btn_frame = ttk.Frame(self.root, padding="10")
        btn_frame.grid(row=2, column=0, sticky="ew")

        ttk.Button(btn_frame, text="🗑️ Limpiar Todo", command=self.limpiar_todo).pack(side="right", padx=5)
        ttk.Button(
            btn_frame,
            text="Solo copiar a Excel (no guarda)",
            command=self.copiar_resultado,
            style="Copiar.TButton",
        ).pack(side="right", padx=5)

        ttk.Button(btn_frame, text="📷 Cargar fotos de orden", command=self.abrir_cargar_fotos).pack(side="left", padx=5)
        tk.Button(
            btn_frame,
            text="💾  GUARDAR Y COPIAR",
            command=self.ejecutar_finalizado_completo,
            bg="#1565C0",
            fg="white",
            activebackground="#0D47A1",
            activeforeground="white",
            font=("Segoe UI", 10, "bold"),
            relief="raised",
            padx=14,
            pady=5,
            cursor="hand2",
        ).pack(side="left", padx=5)

    def abrir_cargar_fotos(self):
        CargarFotosDialog(self.root, on_aplicar=lambda datos: aplicar_datos_a_app(self, datos))

    def ejecutar_finalizado_completo(self):
        if not self.entry_cliente.get().strip():
            messagebox.showwarning("Faltan Datos", "Complete el Cliente.")
            return
        self.guardar_orden()
        self.copiar_resultado()

    def guardar_orden(self):
        try:
            self.mano_obra_ui.calcular() 
            self.maquinaria_ui._calcular_costo_total()

            datos_mo = self.mano_obra_ui.get_totales()
            h_maq = float(self.maquinaria_ui.total_horas_maquina)
            c_maq = float(self.maquinaria_ui.total_costo_maquinaria)
            c_tinta = float(getattr(self.tinta_ui, 'total_gasto', 0.0))
            c_mat = float(getattr(self.materiales_ui, 'total_costo', 0.0))

            h_dis = float(self.mano_obra_ui.horas_disenador_cif)
            h_ope = float(self.mano_obra_ui.horas_operario_cif)
            h_tot_db = (h_dis + h_ope)
            
            total_final = c_maq + datos_mo["costo_mo_total"] + datos_mo["costo_ins_total"] + datos_mo["viaticos"] + datos_mo["cif"] + c_tinta + c_mat

            detalle_maquinas = self.maquinaria_ui.get_detalle_maquinas()
            detalle_operarios = self.mano_obra_ui.get_detalle_operarios()

            registrar_orden(
                [
                    self.entry_cliente.get(), self.entry_desc.get(),
                    self.entry_fecha_inicio.get(), self.entry_fecha_fin.get(),
                    h_maq, datos_mo["horas_total"], h_tot_db, c_maq,
                    datos_mo["costo_mo_total"], datos_mo["costo_ins_total"],
                    datos_mo["viaticos"], datos_mo["cif"], c_tinta, c_mat, total_final
                ],
                detalle_maquinas=detalle_maquinas,
                detalle_operarios=detalle_operarios,
            )
            messagebox.showinfo("Éxito", "Orden guardada en el historial.")
            if hasattr(self, "historial_ui"):
                self.historial_ui.cargar_datos()
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar: {e}")

    def obtener_resultados(self):
        """Genera el texto con el formato exacto para pegar en Excel."""
        # Forzamos a que todas las pestañas realicen sus cálculos finales
        self.mano_obra_ui.calcular()
        self.maquinaria_ui._calcular_costo_total()
        
        # 1. Encabezado principal (Cliente y Trabajo)
        res = f"CLIENTE: {self.entry_cliente.get()}\tTRABAJO: {self.entry_desc.get()}\n\n"
        
        # 2. Sección: MAQUINARIA
        res += "=== COSTO DE MAQUINARIA ===\n"
        if self.maquinaria_ui.salida_excel:
            res += self.maquinaria_ui.salida_excel
        res += "\n" # Espacio de separación
            
        # 3. Sección: MANO DE OBRA (Aquí ya vienen los diseñadores agrupados)
        res += "=== COSTO DE MANO DE OBRA ===\n"
        if self.mano_obra_ui.salida_excel:
            res += self.mano_obra_ui.salida_excel
        res += "\n" # Espacio de separación
            
        # 4. Sección: MATERIALES
        res += "=== COSTO DE MATERIALES ===\n"
        if hasattr(self.materiales_ui, 'salida_excel') and self.materiales_ui.salida_excel:
            res += self.materiales_ui.salida_excel
        res += "\n" # Espacio de separación
            
        # 5. Sección: TINTA
        res += "=== GASTO DE TINTA ===\n"
        if hasattr(self.tinta_ui, 'resultado_formateado') and self.tinta_ui.resultado_formateado:
            res += self.tinta_ui.resultado_formateado + "\n"

        return res

    def copiar_resultado(self, silencioso=False):
        """Copia el desglose completo en el formato tabulado para Excel."""
        try:
            res = self.obtener_resultados()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo armar el formato:\n{e}")
            return

        if not res.strip():
            messagebox.showwarning("Sin datos", "No hay costos para copiar.")
            return

        self.root.clipboard_clear()
        self.root.clipboard_append(res)
        self.root.update()
        if not silencioso:
            messagebox.showinfo(
                "Copiado",
                "Listo. Ya está en el portapapeles.\n\n"
                "Pega en Excel con Ctrl+V.",
            )

    def formato_coma(self, n):
        return f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def limpiar_todo(self):
        if messagebox.askyesno("Limpiar", "¿Borrar todos los datos?"):
            self.entry_cliente.delete(0, tk.END)
            self.entry_desc.delete(0, tk.END)
            self.maquinaria_ui.limpiar_campos()
            self.mano_obra_ui.limpiar_campos()
            self.tinta_ui.limpiar_campos()
            self.materiales_ui.limpiar_campos()

if __name__ == '__main__':
    root = ThemedTk(theme="arc") 
    app = App(root)
    root.mainloop()
