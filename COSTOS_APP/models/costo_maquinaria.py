class CostoMaquinaria:
    # Costo por hora de cada máquina
    costos_maquinas = {
        "MAQUINA GALAXY": 3.867,
        "MAQUINA LAMINADORA": 3.122,
        "PLOTTER": 3.307,
        "ORISS": 3.474,
        "MIMAKI UJV100-160 PLUS": 3.901,
        "CAMA PLANA": 4.670,
        "MAQUINA LASER": 3.688,
        "MAQUINA 320": 3.715,
        "MAQUINA CORTADORA": 6.140
    }

    def __init__(self, maquina, horas_trabajo):
        self.maquina = maquina
        self.horas_trabajo = horas_trabajo

    def calcular_costo(self):
        from models import tarifas

        costo_hora = tarifas.costo_maquina(self.maquina)
        costo_total = costo_hora * self.horas_trabajo
        return round(costo_total, 2)
