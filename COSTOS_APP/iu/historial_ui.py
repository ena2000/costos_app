# iu/historial_ui.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from models.database import obtener_conexion
import pandas as pd
from datetime import datetime
import os

class HistorialUI:
    def __init__(self, parent):
        self.root = parent
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        # --- PANEL SUPERIOR: Resumen y Exportación ---
        self.resumen_frame = ttk.LabelFrame(self.root, text=" Resumen Mensual ", padding=10)
        self.resumen_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        
        self.lbl_horas = ttk.Label(self.resumen_frame, text="Horas Totales: 0.0 hrs", font=("Segoe UI", 11, "bold"))
        self.lbl_horas.pack(side="left", padx=20)
        
        # Botones de acción
        ttk.Button(self.resumen_frame, text="📊 Exportar Excel Profesional", command=self.exportar_excel).pack(side="right", padx=5)
        ttk.Button(self.resumen_frame, text="🔄 Actualizar Lista", command=self.cargar_datos).pack(side="right", padx=5)

        # --- PANEL CENTRAL: Tabla ---
        tabla_frame = ttk.Frame(self.root)
        tabla_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        tabla_frame.columnconfigure(0, weight=1)
        tabla_frame.rowconfigure(0, weight=1)

        # Definimos las columnas que queremos ver en la tabla
        self.columnas = ("id", "fecha", "cliente", "descripcion", "horas", "total")
        self.tree = ttk.Treeview(tabla_frame, columns=self.columnas, show="headings")

        # Ajuste de anchos
        self.tree.column("id", width=40, anchor="center")
        self.tree.column("fecha", width=100, anchor="center")
        self.tree.column("cliente", width=150, anchor="w")
        self.tree.column("descripcion", width=250, anchor="w")
        self.tree.column("horas", width=80, anchor="center")
        self.tree.column("total", width=100, anchor="e")
        
        # Encabezados
        for col in self.columnas:
            self.tree.heading(col, text=col.capitalize())

        self.tree.grid(row=0, column=0, sticky="nsew")

        # Scrollbar
        scroll = ttk.Scrollbar(tabla_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.grid(row=0, column=1, sticky="ns")

        # Botón eliminar
        ttk.Button(self.root, text="🗑️ Eliminar Registro Seleccionado", command=self.eliminar_registro).grid(row=2, column=0, pady=10)

        # Cargar datos al iniciar
        self.cargar_datos()

    def cargar_datos(self):
        # Limpiar tabla antes de cargar
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            conn = obtener_conexion()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    id, 
                    fecha_inicio, 
                    cliente, 
                    descripcion, 
                    horas_totales_ejecutadas, 
                    costo_total_orden 
                FROM historial_ordenes 
                ORDER BY id DESC
            """)
            rows = cursor.fetchall()

            total_horas_mes = 0
            for r in rows:
                self.tree.insert("", "end", values=(
                    r[0], 
                    r[1], 
                    r[2], 
                    r[3], 
                    f"{r[4]:.2f}", 
                    f"$ {r[5]:.2f}"
                ))
                total_horas_mes += (r[4] if r[4] else 0)

            conn.close()
            self.lbl_horas.config(text=f"Horas Totales: {total_horas_mes:.2f} hrs")
            
        except Exception as e:
            messagebox.showerror("Error de Carga", f"No se pudo leer el historial: {e}")

    def exportar_excel(self):
        """Exporta todo el historial a un archivo Excel con formato profesional."""
        try:
            conn = obtener_conexion()
            # Traemos todos los datos para el reporte detallado
            df = pd.read_sql_query("SELECT * FROM historial_ordenes ORDER BY id DESC", conn)
            conn.close()

            if df.empty:
                messagebox.showwarning("Sin Datos", "No hay registros en el historial para exportar.")
                return

            # Renombrar columnas para el Excel
            columnas_bonitas = {
                'id': 'ID Orden',
                'fecha_registro': 'Fecha Registro',
                'cliente': 'Cliente',
                'descripcion': 'Trabajo / Descripción',
                'fecha_inicio': 'F. Inicio',
                'fecha_fin': 'F. Fin',
                'horas_maquina': 'Hrs Máquina',
                'horas_mano_obra': 'Hrs M.O.',
                'horas_totales_ejecutadas': 'Hrs Producción (Total)',
                'costo_maquinaria': 'Costo Maquinaria ($)',
                'costo_mano_obra': 'Costo Mano Obra ($)',
                'costo_instalacion': 'Costo Instalación ($)',
                'viaticos': 'Viáticos ($)',
                'cif': 'CIF ($)',
                'costo_tinta': 'Costo Tinta ($)',
                'costo_materiales': 'Costo Materiales ($)',
                'costo_total_orden': 'TOTAL GENERAL ($)'
            }
            df = df.rename(columns=columnas_bonitas)

            # Seleccionar ruta de guardado
            ruta = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Archivos Excel", "*.xlsx")],
                initialfile=f"Historial_Ordenes_{datetime.now().strftime('%Y_%m_%d')}.xlsx"
            )

            if not ruta:
                return

            # Crear el Excel usando un motor de estilo (openpyxl)
            with pd.ExcelWriter(ruta, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Historial Completo')
                
                workbook = writer.book
                worksheet = writer.sheets['Historial Completo']

                # --- Estilos Profesionales ---
                from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
                
                # Encabezados: Azul oscuro, letra blanca, negrita
                header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
                header_font = Font(bold=True, color="FFFFFF")
                center_align = Alignment(horizontal="center", vertical="center")

                for cell in worksheet[1]:
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = center_align

                # Ajustar ancho de columnas automáticamente
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except: pass
                    worksheet.column_dimensions[column_letter].width = max_length + 3

                # Formato de Moneda ($) para las columnas de dinero (desde la columna J hasta la Q)
                for row in range(2, worksheet.max_row + 1):
                    for col_idx in range(10, 18): # Columnas J a Q
                        worksheet.cell(row=row, column=col_idx).number_format = '"$"#,##0.00'
                    # Columna I (Horas Producción) 2 decimales
                    worksheet.cell(row=row, column=9).number_format = '0.00'

            messagebox.showinfo("Éxito", f"Historial exportado correctamente:\n{ruta}")

        except Exception as e:
            messagebox.showerror("Error de Exportación", f"No se pudo generar el Excel: {e}")

    def eliminar_registro(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Atención", "Selecciona una fila para eliminar.")
            return

        if messagebox.askyesno("Confirmar", "¿Seguro que deseas borrar este registro del historial?"):
            item_id = self.tree.item(selected[0])['values'][0]
            try:
                conn = obtener_conexion()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM historial_ordenes WHERE id = ?", (item_id,))
                conn.commit()
                conn.close()
                self.cargar_datos() # Refrescar
                messagebox.showinfo("Éxito", "Registro eliminado.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar: {e}")