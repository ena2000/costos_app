# Costos por hora
costo_hora_operario = 4.27
costo_hora_disenador = 5.16
# Valor actualizado y utilizado en la nueva fórmula
valor_cif_por_hora = 5.7623765

# Máquinas utilizadas por el diseñador
horas_maquinas_disenador = [
    "M.O MAQUINA GALAXY",
    "M.O MAQUINA LAMINADORA",
    "M.O PLOTTER",
    "M.O ORISS",
    "M.O MIMAKI UJV100-160 PLUS",
    "M.O CAMA PLANA",
    "M.O MAQUINA LASER",
    "M.O MAQUINA 320",
]


# Cálculo para diseñador
def calcular_manodeobra_disenador(maquinas_seleccionadas: list, tiempo_empleado: float):
    detalles = []
    total_horas_disenador = tiempo_empleado
    total_costo_disenador = tiempo_empleado * costo_hora_disenador

    for maquina in maquinas_seleccionadas:
        detalles.append((maquina, tiempo_empleado, total_costo_disenador))

    return detalles, total_horas_disenador, total_costo_disenador


# Cálculo para operario
def calcular_manodeobra_operario(actividad: str, horas_empleadas: float, cantidad_operarios: int):
    costo_individual = horas_empleadas * costo_hora_operario
    costo_total = costo_individual * cantidad_operarios
    return actividad, horas_empleadas, costo_individual, costo_total


# Cálculo de CIF (MODIFICADO)
def calcular_cif(tiempo_total_obra: float):
    """CIF = (horas de obra / divisor) × valor CIF por hora."""
    from models import tarifas
    return tarifas.calcular_cif(tiempo_total_obra)