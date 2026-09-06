"""Fechas de actividades y máquinas (DD/MM/AAAA)."""
from __future__ import annotations

from datetime import datetime

_FORMATOS = (
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%Y-%m-%d",
    "%d/%m/%y",
    "%d-%m-%y",
    "%d/%m",
    "%d-%m",
)


def hoy_str() -> str:
    return datetime.now().strftime("%d/%m/%Y")


def parsear(fecha_str) -> datetime | None:
    if not fecha_str:
        return None
    texto = str(fecha_str).strip()
    if not texto:
        return None
    anio = datetime.now().year
    for fmt in _FORMATOS:
        try:
            dt = datetime.strptime(texto, fmt)
            if fmt in ("%d/%m", "%d-%m"):
                dt = dt.replace(year=anio)
            return dt
        except ValueError:
            continue
    return None


def normalizar(fecha_str) -> str:
    """Devuelve DD/MM/AAAA, o el texto original si no se pudo interpretar."""
    dt = parsear(fecha_str)
    if dt:
        return dt.strftime("%d/%m/%Y")
    return str(fecha_str or "").strip()
