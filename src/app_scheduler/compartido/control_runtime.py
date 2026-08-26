"""Lectura fail-closed del lock compartido con Factory Reset."""

from __future__ import annotations

import json
from pathlib import Path


ESTADOS_BLOQUEANTES = {"FACTORY_RESET_PREPARANDO", "FACTORY_RESET_EN_PROGRESO", "FACTORY_RESET_ERROR"}


def obtener_estado_control_runtime(root: Path) -> dict[str, object]:
    """Expone solo el estado seguro necesario para bloquear y orientar al usuario."""
    ruta = Path(root).expanduser().resolve() / "factory_reset.lock"
    if not ruta.exists():
        return {
            "estado": "NORMAL", "bloquea": False, "desde": None,
            "motivo": "Operacion normal.", "origen": None,
        }
    if ruta.is_symlink() or not ruta.is_file():
        return _estado_inseguro("LOCK_INVALIDO")
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        estado = str(datos.get("estado") or "").strip().upper()
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return _estado_inseguro("LOCK_ILEGIBLE")
    if estado not in ESTADOS_BLOQUEANTES:
        return _estado_inseguro(estado or "LOCK_INVALIDO")
    motivos = {
        "FACTORY_RESET_PREPARANDO": "Factory Reset esta preparando el entorno.",
        "FACTORY_RESET_EN_PROGRESO": "Factory Reset se encuentra en progreso.",
        "FACTORY_RESET_ERROR": "Un Factory Reset anterior finalizo con error y requiere revision manual.",
    }
    return {
        "estado": estado,
        "bloquea": True,
        "desde": str(datos.get("fecha_creacion") or "")[:40] or None,
        "motivo": motivos[estado],
        "origen": str(datos.get("origen") or "desconocido")[:80],
    }


def factory_reset_bloquea(root: Path) -> tuple[bool, str]:
    estado = obtener_estado_control_runtime(root)
    return bool(estado["bloquea"]), str(estado["estado"])


def _estado_inseguro(estado: str) -> dict[str, object]:
    return {
        "estado": estado,
        "bloquea": True,
        "desde": None,
        "motivo": "El control de mantenimiento no pudo validarse de forma segura.",
        "origen": "desconocido",
    }
