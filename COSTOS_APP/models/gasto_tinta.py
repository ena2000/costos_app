def calcular_gasto_tinta(maquina: str, medidas: list) -> dict:
    """
    Calcula el gasto de tinta basado en la máquina y las medidas proporcionadas.

    Args:
        maquina: Nombre de la máquina a utilizar
        medidas: Lista de tuplas con (repeticiones, largo_cm, ancho_cm, alto_cm, es_doble_cara)

    Returns:
        Diccionario con los resultados del cálculo:
        {
            'maquina': str,
            'detalles': list,
            'area_base_total': float,
            'area_total_reps': float,
            'gasto_total': float,
            'costo_por_m2': float
        }
    """
    costos_maquinas = {
        "CAMA PLANA": 2.25,
        "MIMAKI UU": 2.25,
        "ORISS": 1.64,
        "GALAXY": 1.64,
        "P.320": 1.64,
    }

    if maquina not in costos_maquinas:
        raise ValueError(f"La máquina '{maquina}' no tiene un costo definido")

    costo_m2 = costos_maquinas[maquina]
    resultados = {
        'maquina': maquina,
        'detalles': [],
        'area_base_total': 0,
        'area_total_reps': 0,
        'gasto_total': 0,
        'costo_por_m2': costo_m2
    }

    for idx, (repeticiones, largo_cm, ancho_cm, alto_cm, es_doble_cara) in enumerate(medidas, 1):
        try:
            largo_m = largo_cm / 100
            ancho_m = ancho_cm / 100
            alto_m = alto_cm / 100 if alto_cm is not None else None

            if alto_m:
                area_base = 2 * (largo_m * ancho_m + largo_m * alto_m + ancho_m * alto_m)
            else:
                area_base = largo_m * ancho_m

            area_por_unidad = area_base * 2 if es_doble_cara else area_base
            area_total = repeticiones * area_por_unidad
            subtotal = round(area_total * costo_m2, 2)

            resultados['area_base_total'] += area_base
            resultados['area_total_reps'] += area_total
            resultados['gasto_total'] += subtotal

            detalle = {
                'medida': idx,
                'repeticiones': repeticiones,
                'dimensiones': f"{largo_cm}x{ancho_cm}" + (f"x{alto_cm}" if alto_cm else ""),
                'area_base': area_base,
                'area_por_unidad': area_por_unidad,
                'area_total': area_total,
                'subtotal': subtotal,
                'doble_cara': es_doble_cara
            }
            resultados['detalles'].append(detalle)

        except (TypeError, ValueError) as e:
            resultados['detalles'].append({
                'medida': idx,
                'error': f"Datos inválidos: {str(e)}"
            })

    resultados['area_base_total'] = round(resultados['area_base_total'], 2)
    resultados['area_total_reps'] = round(resultados['area_total_reps'], 2)
    resultados['gasto_total'] = round(resultados['gasto_total'], 2)

    return resultados
