"""Lectura fail-closed del lock compartido con Factory Reset."""

from __future__ import annotations

import json
from pathlib import Path


ESTADOS_BLOQUEANTES = {"FACTORY_RESET_PREPARANDO", "FACTORY_RESET_EN_PROGRESO", "FACTORY_RESET_ERROR"}


def factory_reset_bloquea(root: Path) -> tuple[bool, str]:
    ruta = Path(root).expanduser().resolve() / "factory_reset.lock"
    if not ruta.exists():
        return False, "NORMAL"
    if ruta.is_symlink() or not ruta.is_file():
        return True, "LOCK_INVALIDO"
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        estado = str(datos.get("estado") or "").strip().upper()
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return True, "LOCK_ILEGIBLE"
    return (estado in ESTADOS_BLOQUEANTES, estado or "LOCK_INVALIDO")
