"""Rutas de datos de la app (código fuente o .exe empaquetado)."""
from __future__ import annotations

import os
import sys
from pathlib import Path


def _esta_empaquetada() -> bool:
    return bool(getattr(sys, "frozen", False))


def directorio_datos() -> Path:
    """Carpeta donde se guardan la base de datos y la configuración.

    - Si corres el código: la carpeta COSTOS_APP (igual que antes).
    - Si corres el .exe: %APPDATA%\\PUBLISTIK\\CostosApp
      (salvo que pongas inventario_app.db al lado del .exe, modo portable).
    """
    if _esta_empaquetada():
        exe_dir = Path(sys.executable).resolve().parent
        if (exe_dir / "inventario_app.db").exists() or (exe_dir / "portable.txt").exists():
            return exe_dir
        dest = Path(os.environ.get("APPDATA", str(Path.home()))) / "PUBLISTIK" / "CostosApp"
        dest.mkdir(parents=True, exist_ok=True)
        return dest
    return Path(__file__).resolve().parent.parent


def archivo_datos(nombre: str) -> Path:
    return directorio_datos() / nombre
