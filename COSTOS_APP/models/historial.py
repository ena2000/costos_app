from models.database import obtener_conexion
from datetime import datetime
from collections import defaultdict


def _parse_fecha(fecha_str):
    """Parsea fechas en formato DD/MM/YYYY (o variantes comunes)."""
    if not fecha_str:
        return None
    fecha_str = str(fecha_str).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(fecha_str, fmt)
        except ValueError:
            continue
    return None


def registrar_orden(datos, detalle_maquinas=None, detalle_operarios=None):
    """
    Inserta la lista de datos en el historial y guarda el desglose de horas.

    'datos' debe ser una lista con exactamente 15 valores en este orden:
    [cliente, descripcion, f_inicio, f_fin, h_maq, h_mo, h_tot, c_maq, c_mo, c_ins, via, cif, tinta, mat, total]

    detalle_maquinas: lista de dicts {maquina, operario, horas}
    detalle_operarios: lista de dicts {tipo, concepto, operario, horas}
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
        orden_id = cursor.lastrowid

        for item in (detalle_maquinas or []):
            cursor.execute(
                """
                INSERT INTO historial_detalle_maquina (orden_id, maquina, operario, horas)
                VALUES (?, ?, ?, ?)
                """,
                (
                    orden_id,
                    item.get("maquina") or "",
                    item.get("operario") or "",
                    float(item.get("horas") or 0),
                ),
            )

        for item in (detalle_operarios or []):
            cursor.execute(
                """
                INSERT INTO historial_detalle_operario (orden_id, tipo, concepto, operario, horas)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    orden_id,
                    item.get("tipo") or "OPERARIO",
                    item.get("concepto") or "",
                    item.get("operario") or "",
                    float(item.get("horas") or 0),
                ),
            )

        conn.commit()
        return orden_id
    except Exception as e:
        conn.rollback()
        print(f"Error al insertar en historial: {e}")
        raise e
    finally:
        conn.close()


def eliminar_orden(orden_id):
    """Elimina una orden y su desglose asociado."""
    conn = obtener_conexion()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM historial_detalle_maquina WHERE orden_id = ?", (orden_id,))
        cursor.execute("DELETE FROM historial_detalle_operario WHERE orden_id = ?", (orden_id,))
        cursor.execute("DELETE FROM historial_ordenes WHERE id = ?", (orden_id,))
        conn.commit()
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


def _ordenes_en_rango(fecha_desde=None, fecha_hasta=None):
    """Devuelve filas de historial_ordenes filtradas por fecha_inicio (DD/MM/YYYY)."""
    conn = obtener_conexion()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, fecha_inicio, fecha_fin, cliente, descripcion,
               horas_maquina, horas_mano_obra, horas_totales_ejecutadas,
               costo_total_orden, fecha_registro
        FROM historial_ordenes
        ORDER BY id DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    dt_desde = _parse_fecha(fecha_desde) if fecha_desde else None
    dt_hasta = _parse_fecha(fecha_hasta) if fecha_hasta else None

    filtradas = []
    for r in rows:
        dt = _parse_fecha(r[1]) or _parse_fecha(str(r[9])[:10] if r[9] else None)
        if dt_desde and (dt is None or dt.date() < dt_desde.date()):
            continue
        if dt_hasta and (dt is None or dt.date() > dt_hasta.date()):
            continue
        filtradas.append(r)
    return filtradas


def consultar_horas_desglose(fecha_desde=None, fecha_hasta=None):
    """
    Consulta horas filtradas por rango de fechas.

    Retorna dict con:
      - ordenes: lista de órdenes
      - horas_totales, horas_maquina, horas_mano_obra
      - por_mes: [{mes, anio, etiqueta, horas_totales, horas_maquina, horas_mo, ordenes}]
      - por_maquina: [{maquina, horas, operarios: {nombre: horas}}]
      - por_operario: [{operario, tipo, horas, conceptos: {concepto: horas}}]
    """
    ordenes = _ordenes_en_rango(fecha_desde, fecha_hasta)
    orden_ids = [r[0] for r in ordenes]
    orden_fecha = {}
    for r in ordenes:
        dt = _parse_fecha(r[1]) or _parse_fecha(str(r[9])[:10] if r[9] else None)
        orden_fecha[r[0]] = dt

    horas_totales = sum((r[7] or 0) for r in ordenes)
    horas_maquina = sum((r[5] or 0) for r in ordenes)
    horas_mano_obra = sum((r[6] or 0) for r in ordenes)

    por_mes_map = defaultdict(lambda: {
        "horas_totales": 0.0,
        "horas_maquina": 0.0,
        "horas_mo": 0.0,
        "ordenes": 0,
    })
    for r in ordenes:
        dt = orden_fecha.get(r[0])
        if dt is None:
            key = (0, 0)
            etiqueta = "Sin fecha"
        else:
            key = (dt.year, dt.month)
            meses = (
                "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
            )
            etiqueta = f"{meses[dt.month]} {dt.year}"
        bucket = por_mes_map[key]
        bucket["etiqueta"] = etiqueta
        bucket["anio"] = key[0]
        bucket["mes"] = key[1]
        bucket["horas_totales"] += r[7] or 0
        bucket["horas_maquina"] += r[5] or 0
        bucket["horas_mo"] += r[6] or 0
        bucket["ordenes"] += 1

    por_mes = sorted(
        por_mes_map.values(),
        key=lambda x: (x.get("anio", 0), x.get("mes", 0)),
    )

    maquina_map = defaultdict(lambda: {"horas": 0.0, "operarios": defaultdict(float)})
    operario_map = defaultdict(lambda: {"horas": 0.0, "tipo": "", "conceptos": defaultdict(float)})

    if orden_ids:
        placeholders = ",".join("?" * len(orden_ids))
        conn = obtener_conexion()
        cursor = conn.cursor()

        cursor.execute(
            f"""
            SELECT orden_id, maquina, operario, horas
            FROM historial_detalle_maquina
            WHERE orden_id IN ({placeholders})
            """,
            orden_ids,
        )
        for orden_id, maquina, operario, horas in cursor.fetchall():
            h = float(horas or 0)
            m = maquina or "SIN MÁQUINA"
            maquina_map[m]["horas"] += h
            if operario:
                maquina_map[m]["operarios"][operario] += h
            # Laminadora se contabiliza como operario (no diseñador) en detalle_operario
            if operario and m.upper() != "MAQUINA LAMINADORA":
                operario_map[operario]["horas"] += h
                operario_map[operario]["tipo"] = "DISEÑADOR"
                operario_map[operario]["conceptos"][m] += h

        cursor.execute(
            f"""
            SELECT orden_id, tipo, concepto, operario, horas
            FROM historial_detalle_operario
            WHERE orden_id IN ({placeholders})
            """,
            orden_ids,
        )
        for orden_id, tipo, concepto, operario, horas in cursor.fetchall():
            h = float(horas or 0)
            nombre = (operario or concepto or "OPERARIO").strip() or "OPERARIO"
            operario_map[nombre]["horas"] += h
            if not operario_map[nombre]["tipo"]:
                operario_map[nombre]["tipo"] = tipo or "OPERARIO"
            elif tipo and tipo != "DISEÑADOR":
                operario_map[nombre]["tipo"] = tipo
            operario_map[nombre]["conceptos"][concepto or tipo or "GENERAL"] += h

        conn.close()

    por_maquina = [
        {
            "maquina": m,
            "horas": data["horas"],
            "operarios": dict(data["operarios"]),
        }
        for m, data in sorted(maquina_map.items(), key=lambda x: -x[1]["horas"])
    ]

    por_operario = [
        {
            "operario": nombre,
            "tipo": data["tipo"] or "OPERARIO",
            "horas": data["horas"],
            "conceptos": dict(data["conceptos"]),
        }
        for nombre, data in sorted(operario_map.items(), key=lambda x: -x[1]["horas"])
    ]

    return {
        "ordenes": [
            {
                "id": r[0],
                "fecha_inicio": r[1],
                "fecha_fin": r[2],
                "cliente": r[3],
                "descripcion": r[4],
                "horas_maquina": r[5] or 0,
                "horas_mano_obra": r[6] or 0,
                "horas_totales": r[7] or 0,
                "costo_total": r[8] or 0,
            }
            for r in ordenes
        ],
        "horas_totales": horas_totales,
        "horas_maquina": horas_maquina,
        "horas_mano_obra": horas_mano_obra,
        "por_mes": por_mes,
        "por_maquina": por_maquina,
        "por_operario": por_operario,
    }
