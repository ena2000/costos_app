"""Extracción de datos de hojas de orden mediante visión (Gemini)."""
from __future__ import annotations

import base64
import io
import json
import os
import re
from pathlib import Path

import requests
from PIL import Image

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config_ocr.json"
GEMINI_MODELS = (
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-flash-latest",
)

MAQUINA_ALIASES = {
    "GALAXY": "MAQUINA GALAXY",
    "MAQUINA GALAXY": "MAQUINA GALAXY",
    "LAMINADORA": "MAQUINA LAMINADORA",
    "MAQUINA LAMINADORA": "MAQUINA LAMINADORA",
    "PLOTTER": "PLOTTER",
    "PLOTTER #1": "PLOTTER",
    "PLOTTER #2": "PLOTTER",
    "PLOTTER 1": "PLOTTER",
    "PLOTTER 2": "PLOTTER",
    "ORISS": "ORISS",
    "MIMAKI": "MIMAKI UJV100-160 PLUS",
    "MIMAKI UV": "MIMAKI UJV100-160 PLUS",
    "MIMAKI UU": "MIMAKI UJV100-160 PLUS",
    "MIMAKI UJV100-160 PLUS": "MIMAKI UJV100-160 PLUS",
    "CAMA PLANA": "CAMA PLANA",
    "LASER": "MAQUINA LASER",
    "LÁSER": "MAQUINA LASER",
    "MAQUINA LASER": "MAQUINA LASER",
    "CORTADORA": "MAQUINA CORTADORA",
    "MAQUINA CORTADORA": "MAQUINA CORTADORA",
    "LÁSER / CORTADORA": "MAQUINA LASER",
    "LASER / CORTADORA": "MAQUINA LASER",
    "320": "MAQUINA 320",
    "P.320": "MAQUINA 320",
    "MAQUINA 320": "MAQUINA 320",
}

TINTA_ALIASES = {
    "CAMA PLANA": "CAMA PLANA",
    "MIMAKI": "MIMAKI UU",
    "MIMAKI UV": "MIMAKI UU",
    "MIMAKI UU": "MIMAKI UU",
    "ORISS": "ORISS",
    "GALAXY": "GALAXY",
    "320": "P.320",
    "P.320": "P.320",
    "MAQUINA 320": "P.320",
}

ACTIVIDAD_ALIASES = {
    "LAMINACION": "LAMINACION",
    "LAMINACIÓN": "LAMINACION",
    "REFILACION": "REFILACION",
    "REFILACIÓN": "REFILACION",
    "BRANDEO": "BRANDEO",
    "PEGADO": "PEGADO",
    "DOBLADO": "DOBLADO",
    "ARMADO": "ARMADO",
    "PINTADO": "PINTADO",
    "PINTURA": "PINTADO",
    "CORTE": "CORTE",
    "SELLADO": "SELLADO",
    "FIJACION": "FIJACION",
    "FIJACIÓN": "FIJACION",
    "SOLDAR": "SOLDAR",
}

PROMPT = """
Eres un extractor de datos de hojas de producción de un taller de impresión/señalética (PUBLISTIK / Grupo Termock).
Analiza TODAS las imágenes (pueden ser: orden de pedido, cartilla, hoja de impresión, corte/laminado/instalación, mano de obra, egreso de inventario Contifico).
Devuelve SOLO un JSON válido (sin markdown) con esta estructura exacta:

{
  "cliente": "",
  "trabajo": "",
  "cantidad_item": 1,
  "fecha_inicio": "DD/MM/YYYY o DD-mes",
  "fecha_fin": "DD/MM/YYYY o DD-mes",
  "medidas_tinta": [
    {"largo_cm": 0, "ancho_cm": 0, "repeticiones": 1, "doble_cara": false}
  ],
  "maquina_tinta": "",
  "maquinarias": [
    {"maquina": "", "hora_inicio": "HH:MM", "hora_fin": "HH:MM", "fecha": "", "responsable": ""}
  ],
  "mano_obra": [
    {"actividad": "", "fecha": "", "hora_inicio": "HH:MM", "hora_fin": "HH:MM", "responsables": [""]}
  ],
  "instalacion": {
    "cantidad_operarios": 0,
    "viaticos": 0,
    "dias": [{"hora_inicio": "HH:MM", "hora_fin": "HH:MM"}]
  },
  "materiales": [
    {"codigo": "", "producto": "", "cantidad": 0, "unidad": "", "costo_unitario": 0, "subtotal": 0}
  ]
}

Reglas:
- Solo incluye maquinarias/mano_obra con horas reales escritas (no filas vacías).
- MUY IMPORTANTE maquinarias: revisa TODAS las hojas de producción.
  * Hoja IMPRESIÓN: bloques 320, ORISS, GALAXY, CAMA PLANA, MIMAKI UV.
  * Hoja CORTE/LAMINADO: LÁSER/CORTADORA, PLOTTER #1, PLOTTER #2, LAMINADORA.
  * Si hay horas en 2, 3 o más máquinas, DEBES devolver TODAS en el array "maquinarias" (una entrada por cada fila con hora inicio y hora fin).
  * No te quedes solo con la primera máquina encontrada.
- En mano_obra, lista cada nombre de RESPONSABLES por separado; si hay varios nombres, ponlos todos en el array.
- Si hay VARIAS medidas de impresión/señaléticas (ej. 30x10 y 60x60), incluye TODAS en medidas_tinta.
- Preferir medidas del trabajo (ej. 140x55cm), no el ancho del rollo de vinil.
- repeticiones = cantidad de esa medida (si dice 2 de 30x10, repeticiones=2).
- maquina_tinta = máquina de impresión usada (ORISS, GALAXY, CAMA PLANA, MIMAKI, 320).
- materiales: preferir el egreso de inventario Contifico (producto, cantidad, costo unitario, subtotal).
- Si un dato no aparece, usa null, 0 o [].
- Normaliza horas a HH:MM.
"""


def cargar_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def guardar_config(data: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def obtener_api_key() -> str | None:
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if key:
        return key.strip()
    cfg = cargar_config()
    key = (cfg.get("gemini_api_key") or "").strip()
    return key or None


def guardar_api_key(key: str) -> None:
    cfg = cargar_config()
    cfg["gemini_api_key"] = key.strip()
    guardar_config(cfg)


def _imagen_a_base64(path: str, max_side: int = 1600) -> tuple[str, str]:
    img = Image.open(path)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    elif img.mode == "L":
        img = img.convert("RGB")

    w, h = img.size
    scale = min(1.0, max_side / max(w, h))
    if scale < 1.0:
        img = img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode("ascii"), "image/jpeg"


def _extraer_json(texto: str) -> dict:
    texto = texto.strip()
    if texto.startswith("```"):
        texto = re.sub(r"^```(?:json)?\s*", "", texto)
        texto = re.sub(r"\s*```$", "", texto)
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", texto, re.DOTALL)
        if not match:
            raise ValueError("La IA no devolvió JSON válido.")
        return json.loads(match.group(0))


def extraer_datos_de_fotos(rutas: list[str], api_key: str | None = None) -> dict:
    """Envía las fotos a Gemini y devuelve un dict normalizado de la orden."""
    api_key = api_key or obtener_api_key()
    if not api_key:
        raise ValueError(
            "Falta la API key de Gemini. Consíguela gratis en "
            "https://aistudio.google.com/apikey"
        )
    if not rutas:
        raise ValueError("No se seleccionaron imágenes.")

    parts = [{"text": PROMPT}]
    for ruta in rutas:
        b64, mime = _imagen_a_base64(ruta)
        parts.append({"inline_data": {"mime_type": mime, "data": b64}})

    payload = {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"},
    }

    body = None
    last_error = None
    for model in GEMINI_MODELS:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={api_key}"
        )
        resp = requests.post(url, json=payload, timeout=120)
        if resp.status_code == 200:
            body = resp.json()
            break
        last_error = f"{model} → {resp.status_code}: {resp.text[:300]}"
        # Si la key es inválida, no probar más modelos
        if resp.status_code in (400, 403) and "API key" in resp.text:
            break

    if body is None:
        raise RuntimeError(f"Error Gemini: {last_error}")

    try:
        texto = body["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Respuesta inesperada de Gemini: {body}") from exc

    raw = _extraer_json(texto)
    return normalizar_datos(raw)


def datos_ejemplo_segarvi() -> dict:
    """Datos de la orden de ejemplo (SEGARVI) para probar sin API."""
    raw = {
        "cliente": "SEGARVI",
        "trabajo": "SEÑALETICA",
        "cantidad_item": 1,
        "fecha_inicio": "22-jun",
        "fecha_fin": "24-jun",
        "medidas_tinta": [
            {
                "largo_cm": 140,
                "ancho_cm": 55,
                "repeticiones": 1,
                "doble_cara": False,
            }
        ],
        "maquina_tinta": "ORISS",
        "maquinarias": [
            {
                "maquina": "ORISS",
                "hora_inicio": "15:00",
                "hora_fin": "15:15",
                "fecha": "",
                "responsable": "",
            }
        ],
        "mano_obra": [
            {
                "actividad": "REFILACION",
                "fecha": "24/06",
                "hora_inicio": "10:40",
                "hora_fin": "10:50",
                "responsables": ["Kevin Merchán"],
            },
            {
                "actividad": "BRANDEO",
                "fecha": "24/06",
                "hora_inicio": "10:50",
                "hora_fin": "10:55",
                "responsables": ["Kevin Merchán"],
            },
        ],
        "instalacion": {"cantidad_operarios": 0, "viaticos": 0, "dias": []},
        "materiales": [
            {
                "codigo": "PINV033",
                "producto": "VINIL BLANCO IMPRESION BRILLANTE 152X50",
                "cantidad": 1.0,
                "unidad": "m.",
                "costo_unitario": 1.468106,
                "subtotal": 1.47,
            },
            {
                "codigo": "PINV038",
                "producto": "VINIL DE LAMINACIÓN MATE 1.52M",
                "cantidad": 1.0,
                "unidad": "m.",
                "costo_unitario": 1.416377,
                "subtotal": 1.42,
            },
        ],
    }
    return normalizar_datos(raw)


def contar_operarios(responsables) -> int:
    if isinstance(responsables, int):
        return max(0, responsables)
    if not responsables:
        return 0
    if isinstance(responsables, str):
        partes = re.split(r"[,;/&+]|\by\b", responsables, flags=re.IGNORECASE)
        nombres = [p.strip() for p in partes if p.strip()]
        return max(1, len(nombres)) if nombres else 0
    if isinstance(responsables, list):
        total = 0
        for r in responsables:
            total += contar_operarios(r) if isinstance(r, str) else (1 if r else 0)
        return total
    return 0


def _map_maquina(nombre: str | None) -> str | None:
    if not nombre:
        return None
    key = str(nombre).strip().upper()
    if key in MAQUINA_ALIASES:
        return MAQUINA_ALIASES[key]
    for alias, canon in MAQUINA_ALIASES.items():
        if alias in key or key in alias:
            return canon
    return None


def _map_tinta(nombre: str | None) -> str | None:
    if not nombre:
        return None
    key = str(nombre).strip().upper()
    if key in TINTA_ALIASES:
        return TINTA_ALIASES[key]
    for alias, canon in TINTA_ALIASES.items():
        if alias in key:
            return canon
    return None


def _map_actividad(nombre: str | None) -> str | None:
    if not nombre:
        return None
    key = str(nombre).strip().upper()
    return ACTIVIDAD_ALIASES.get(key) or ACTIVIDAD_ALIASES.get(key.replace("Á", "A").replace("É", "E"))


def _norm_hora(valor) -> str | None:
    if not valor:
        return None
    s = str(valor).strip().replace(".", ":")
    m = re.search(r"(\d{1,2}):(\d{2})", s)
    if not m:
        return None
    h, mi = int(m.group(1)), int(m.group(2))
    if h > 23 or mi > 59:
        return None
    return f"{h:02d}:{mi:02d}"


def _norm_fecha(valor) -> str:
    if not valor:
        return ""
    s = str(valor).strip()
    meses = {
        "ene": "01", "feb": "02", "mar": "03", "abr": "04", "may": "05", "jun": "06",
        "jul": "07", "ago": "08", "sep": "09", "oct": "10", "nov": "11", "dic": "12",
    }
    m = re.match(r"(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})", s)
    if m:
        d, mo, y = m.groups()
        if len(y) == 2:
            y = "20" + y
        return f"{int(d):02d}/{int(mo):02d}/{y}"
    m = re.match(r"(\d{1,2})[/-]?([a-záéíóú]+)", s, re.I)
    if m:
        d, mes = m.group(1), m.group(2)[:3].lower()
        mo = meses.get(mes, "01")
        return f"{int(d):02d}/{mo}"
    return s


def normalizar_datos(raw: dict) -> dict:
    # Soporta lista medidas_tinta o el formato viejo medida_tinta (una sola)
    medidas_raw = raw.get("medidas_tinta")
    if not medidas_raw:
        una = raw.get("medida_tinta")
        medidas_raw = [una] if una else []
    if isinstance(medidas_raw, dict):
        medidas_raw = [medidas_raw]

    medidas_tinta = []
    for med in medidas_raw:
        if not isinstance(med, dict):
            continue
        try:
            largo = float(med.get("largo_cm") or 0)
            ancho = float(med.get("ancho_cm") or 0)
            reps = int(med.get("repeticiones") or 1)
        except (TypeError, ValueError):
            continue
        if largo <= 0 or ancho <= 0:
            continue
        medidas_tinta.append({
            "largo_cm": largo,
            "ancho_cm": ancho,
            "repeticiones": max(1, reps),
            "doble_cara": bool(med.get("doble_cara") or False),
        })

    maquinarias = []
    for item in raw.get("maquinarias") or []:
        maq = _map_maquina(item.get("maquina"))
        hi = _norm_hora(item.get("hora_inicio"))
        hf = _norm_hora(item.get("hora_fin"))
        if maq and hi and hf:
            maquinarias.append({
                "maquina": maq,
                "hora_inicio": hi,
                "hora_fin": hf,
                "fecha": item.get("fecha") or "",
                "responsable": item.get("responsable") or "",
            })

    mano_obra = []
    for item in raw.get("mano_obra") or []:
        act = _map_actividad(item.get("actividad"))
        hi = _norm_hora(item.get("hora_inicio"))
        hf = _norm_hora(item.get("hora_fin"))
        responsables = item.get("responsables") or []
        ops = contar_operarios(responsables)
        if act and hi and hf and ops > 0:
            mano_obra.append({
                "actividad": act,
                "fecha": item.get("fecha") or "",
                "hora_inicio": hi,
                "hora_fin": hf,
                "responsables": responsables if isinstance(responsables, list) else [str(responsables)],
                "cantidad_operarios": ops,
            })

    inst = raw.get("instalacion") or {}
    dias_inst = []
    for d in inst.get("dias") or []:
        hi = _norm_hora(d.get("hora_inicio"))
        hf = _norm_hora(d.get("hora_fin"))
        if hi and hf:
            dias_inst.append({"hora_inicio": hi, "hora_fin": hf})

    materiales = []
    for mat in raw.get("materiales") or []:
        producto = (mat.get("producto") or "").strip()
        if not producto:
            continue
        try:
            cantidad = float(str(mat.get("cantidad") or 0).replace(",", "."))
        except ValueError:
            cantidad = 0.0
        try:
            costo = float(str(mat.get("costo_unitario") or 0).replace(",", "."))
        except ValueError:
            costo = 0.0
        try:
            subtotal = float(str(mat.get("subtotal") or 0).replace(",", "."))
        except ValueError:
            subtotal = round(cantidad * costo, 2)
        if cantidad <= 0 and subtotal <= 0:
            continue
        if cantidad <= 0 and costo > 0 and subtotal > 0:
            cantidad = round(subtotal / costo, 4)
        if costo <= 0 and cantidad > 0 and subtotal > 0:
            costo = round(subtotal / cantidad, 6)
        materiales.append({
            "codigo": mat.get("codigo") or "",
            "producto": producto,
            "cantidad": cantidad,
            "unidad": mat.get("unidad") or "u",
            "costo_unitario": costo,
            "subtotal": subtotal or round(cantidad * costo, 2),
        })

    maquina_tinta = _map_tinta(raw.get("maquina_tinta"))
    if not maquina_tinta and maquinarias:
        for m in maquinarias:
            t = _map_tinta(m["maquina"].replace("MAQUINA ", ""))
            if t:
                maquina_tinta = t
                break

    trabajo = (raw.get("trabajo") or "").strip()
    cant = raw.get("cantidad_item") or 1
    try:
        cant = int(cant)
    except (TypeError, ValueError):
        cant = 1
    if cant and trabajo and str(cant) not in trabajo:
        trabajo = f"{cant} {trabajo}".strip()

    return {
        "cliente": (raw.get("cliente") or "").strip(),
        "trabajo": trabajo,
        "cantidad_item": cant,
        "fecha_inicio": _norm_fecha(raw.get("fecha_inicio")),
        "fecha_fin": _norm_fecha(raw.get("fecha_fin")),
        "medidas_tinta": medidas_tinta,
        "maquina_tinta": maquina_tinta or "ORISS",
        "maquinarias": maquinarias,
        "mano_obra": mano_obra,
        "instalacion": {
            "cantidad_operarios": int(inst.get("cantidad_operarios") or 0),
            "viaticos": float(inst.get("viaticos") or 0),
            "dias": dias_inst,
        },
        "materiales": materiales,
        "disenador": "XAVIER CABRERA",
    }
