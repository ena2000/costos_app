from models.database import obtener_conexion

def registrar_orden(datos):
    """
    Inserta la lista de datos en el historial.
    'datos' debe ser una lista con exactamente 15 valores en este orden:
    [cliente, descripcion, f_inicio, f_fin, h_maq, h_mo, h_tot, c_maq, c_mo, c_ins, via, cif, tinta, mat, total]
    """
    conn = obtener_conexion()
    cursor = conn.cursor()
    
    query = """
        INSERT INTO historial_ordenes (
            cliente, descripcion, fecha_inicio, fecha_fin,
            horas_maquina, horas_mano_obra, horas_totales_ejecutadas,
            costo_maquinaria, costo_mano_obra, costo_instalacion, 
            viaticos, cif, costo_tinta, costo_materiales, costo_total_orden
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    try:
        cursor.execute(query, datos)
        conn.commit()
    except Exception as e:
        print(f"Error al insertar en historial: {e}")
        raise e
    finally:
        conn.close()

def obtener_resumen_mes():
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT SUM(horas_totales_ejecutadas), COUNT(id)
        FROM historial_ordenes 
        WHERE strftime('%m', fecha_registro) = strftime('%m', 'now')
          AND strftime('%Y', fecha_registro) = strftime('%Y', 'now')
    """)
    res = cursor.fetchone()
    conn.close()
    return (res[0] if res[0] else 0.0, res[1] if res[1] else 0)