# models/database.py

import sqlite3
import pandas as pd
import os
import datetime

from models.rutas import archivo_datos

DB_FILE = str(archivo_datos("inventario_app.db"))

def obtener_conexion():
    """Crea y devuelve una conexión a la base de datos SQLite."""
    conn = sqlite3.connect(DB_FILE)
    return conn

def crear_tablas():
    """Crea las tablas necesarias para el funcionamiento de la aplicación."""
    conn = obtener_conexion()
    cursor = conn.cursor()
    
    # 1. Tabla de productos (Inventario sincronizado de Excel)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            codigo TEXT PRIMARY KEY,
            descripcion TEXT NOT NULL,
            costo_unitario REAL NOT NULL,
            unidad TEXT 
        )
    """)
    
    # 2. Tabla para información de sincronización
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sync_info (
            id INTEGER PRIMARY KEY,
            last_sync_time REAL
        )
    """)
    
    # 3. TABLA ACTUALIZADA: Historial de Órdenes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historial_ordenes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            cliente TEXT,
            descripcion TEXT,
            fecha_inicio TEXT,
            fecha_fin TEXT,
            horas_maquina REAL,
            horas_mano_obra REAL,
            horas_totales_ejecutadas REAL,
            costo_maquinaria REAL,
            costo_mano_obra REAL,
            costo_instalacion REAL,
            viaticos REAL,
            cif REAL,
            costo_tinta REAL,
            costo_materiales REAL,
            costo_total_orden REAL
        )
    """)

    # 4. Desglose de horas por máquina (y diseñador asociado)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historial_detalle_maquina (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            orden_id INTEGER NOT NULL,
            maquina TEXT NOT NULL,
            operario TEXT,
            horas REAL NOT NULL,
            fecha TEXT,
            FOREIGN KEY (orden_id) REFERENCES historial_ordenes(id) ON DELETE CASCADE
        )
    """)

    # 5. Desglose de horas por operario / actividad
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historial_detalle_operario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            orden_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            concepto TEXT NOT NULL,
            operario TEXT,
            horas REAL NOT NULL,
            fecha TEXT,
            FOREIGN KEY (orden_id) REFERENCES historial_ordenes(id) ON DELETE CASCADE
        )
    """)
    
    # Insertar un registro inicial para la sincronización si no existe
    cursor.execute("INSERT OR IGNORE INTO sync_info (id, last_sync_time) VALUES (1, 0)")

    def _asegurar_columna(tabla, columna, tipo):
        cursor.execute(f"PRAGMA table_info({tabla})")
        existentes = {fila[1] for fila in cursor.fetchall()}
        if columna not in existentes:
            cursor.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna} {tipo}")

    _asegurar_columna("historial_detalle_maquina", "fecha", "TEXT")
    _asegurar_columna("historial_detalle_operario", "fecha", "TEXT")
    
    conn.commit()
    conn.close()
    print("Base de datos y tablas aseguradas con la nueva estructura.")

def _actualizar_sync_time(timestamp, conn):
    """Actualiza la fecha de la última sincronización."""
    cursor = conn.cursor()
    cursor.execute("UPDATE sync_info SET last_sync_time = ? WHERE id = 1", (timestamp,))

def obtener_last_sync_time():
    """Obtiene el timestamp de la última sincronización guardada."""
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("SELECT last_sync_time FROM sync_info WHERE id = 1")
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

def sincronizar_inteligentemente(file_path, status_callback):
    """Lee el archivo Excel y actualiza la tabla de productos."""
    try:
        excel_mod_time = os.path.getmtime(file_path)
        # Leer Excel (asegúrate de que los nombres de columnas coincidan con tu archivo)
        df = pd.read_excel(file_path)

        columna_codigo = 'Código'
        columna_descripcion = 'Nombre'
        columna_costo = 'Costo Prom.'
        columna_unidad = 'Unidad'

        conn = obtener_conexion()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM productos")

        productos_a_insertar = []
        for index, row in df.iterrows():
            # Limpieza de strings para el costo
            costo_raw = str(row[columna_costo])
            costo_str = costo_raw.replace('$', '').replace(',', '').strip()
            try:
                costo_float = float(costo_str)
                productos_a_insertar.append((
                    str(row[columna_codigo]), 
                    str(row[columna_descripcion]), 
                    costo_float, 
                    str(row[columna_unidad])
                ))
            except (ValueError, TypeError):
                continue
        
        cursor.executemany(
            "INSERT INTO productos (codigo, descripcion, costo_unitario, unidad) VALUES (?, ?, ?, ?)", 
            productos_a_insertar
        )
        
        _actualizar_sync_time(excel_mod_time, conn)
        conn.commit()
        conn.close()

        status_callback(f"Inventario actualizado: {len(productos_a_insertar)} productos cargados.")

    except Exception as e:
        status_callback(f"Error en sincronización: {e}")

def buscar_productos(termino_busqueda):
    """Busca productos por código o descripción en la base de datos."""
    conn = obtener_conexion()
    cursor = conn.cursor()
    query = "%" + termino_busqueda + "%"
    cursor.execute("""
        SELECT codigo, descripcion, costo_unitario, unidad
        FROM productos 
        WHERE codigo LIKE ? OR descripcion LIKE ?
    """, (query, query))
    resultados = cursor.fetchall()
    conn.close()
    return resultados