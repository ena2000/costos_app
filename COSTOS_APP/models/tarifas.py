"""Tarifas editables (máquina, operario, diseñador y CIF)."""
from __future__ import annotations

import json
from copy import deepcopy

from models.rutas import archivo_datos

ARCHIVO = "tarifas.json"

COSTOS_MAQUINAS_DEFAULT = {
    "MAQUINA GALAXY": 3.867,
    "MAQUINA LAMINADORA": 3.122,
    "PLOTTER": 3.307,
    "ORISS": 3.474,
    "MIMAKI UJV100-160 PLUS": 3.901,
    "CAMA PLANA": 4.670,
    "MAQUINA LASER": 3.688,
    "MAQUINA 320": 3.715,
    "MAQUINA CORTADORA": 6.140,
}

DEFAULTS = {
    "costo_hora_operario": 4.27,
    "costo_hora_disenador": 5.16,
    "valor_cif_por_hora": 5.7623765,
    "divisor_cif": 5.0,
    "costos_maquinas": COSTOS_MAQUINAS_DEFAULT,
}

_datos: dict = deepcopy(DEFAULTS)


def _combinar(base: dict, extra: dict) -> dict:
    out = deepcopy(base)
    for clave, valor in extra.items():
        if clave == "costos_maquinas" and isinstance(valor, dict):
            maquinas = dict(out.get("costos_maquinas") or {})
            for nombre, costo in valor.items():
                try:
                    maquinas[str(nombre)] = float(costo)
                except (TypeError, ValueError):
                    continue
            out["costos_maquinas"] = maquinas
        elif clave in DEFAULTS:
            try:
                out[clave] = float(valor)
            except (TypeError, ValueError):
                continue
    return out


def cargar() -> dict:
    global _datos
    ruta = archivo_datos(ARCHIVO)
    if ruta.exists():
        try:
            extra = json.loads(ruta.read_text(encoding="utf-8"))
            if isinstance(extra, dict):
                _datos = _combinar(DEFAULTS, extra)
        except Exception:
            _datos = deepcopy(DEFAULTS)
    else:
        _datos = deepcopy(DEFAULTS)
    _aplicar_a_modulos()
    return deepcopy(_datos)


def guardar(nuevos: dict) -> dict:
    global _datos
    _datos = _combinar(DEFAULTS, nuevos)
    ruta = archivo_datos(ARCHIVO)
    ruta.write_text(json.dumps(_datos, indent=2, ensure_ascii=False), encoding="utf-8")
    _aplicar_a_modulos()
    return deepcopy(_datos)


def actuales() -> dict:
    return deepcopy(_datos)


def costo_hora_operario() -> float:
    return float(_datos["costo_hora_operario"])


def costo_hora_disenador() -> float:
    return float(_datos["costo_hora_disenador"])


def valor_cif_por_hora() -> float:
    return float(_datos["valor_cif_por_hora"])


def divisor_cif() -> float:
    valor = float(_datos.get("divisor_cif") or 5)
    return valor if valor else 5.0


def costo_maquina(nombre: str) -> float:
    maquinas = _datos.get("costos_maquinas") or {}
    if nombre not in maquinas:
        raise ValueError("Maquinaria no válida.")
    return float(maquinas[nombre])


def calcular_cif(tiempo_total_obra: float) -> float:
    return (float(tiempo_total_obra) / divisor_cif()) * valor_cif_por_hora()


def _aplicar_a_modulos() -> None:
    try:
        from models import mano_obra
        from models.costo_maquinaria import CostoMaquinaria

        mano_obra.costo_hora_operario = costo_hora_operario()
        mano_obra.costo_hora_disenador = costo_hora_disenador()
        mano_obra.valor_cif_por_hora = valor_cif_por_hora()
        CostoMaquinaria.costos_maquinas = dict(_datos.get("costos_maquinas") or COSTOS_MAQUINAS_DEFAULT)
    except Exception:
        pass


cargar()
