"""Lectura fail-closed del lock compartido con Factory Reset."""

from __future__ import annotations

import json
import os
import socket
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


ESTADOS_BLOQUEANTES = {"FACTORY_RESET_PREPARANDO", "FACTORY_RESET_EN_PROGRESO", "FACTORY_RESET_ERROR"}
FASES_FACTORY_RESET = {
    "PRECHECK", "LOCK_ADQUIRIDO", "BLOQUEANDO_ACTIVIDAD",
    "CUARENTENA_FILESYSTEM", "ADQUIRIENDO_APPLOCK",
    "EJECUTANDO_RESET_IN_PLACE", "CONFIRMANDO_COMMIT",
    "VALIDANDO_RESULTADO", "LIMPIANDO_CUARENTENA", "COMPLETADO",
    "ERROR", "ROLLBACK_FILESYSTEM",
}


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


def obtener_estado_factory_reset(root: Path, timeout_segundos: int = 1800) -> dict[str, object]:
    """Lee el lock completo sin confiar en contenido no validado."""
    ruta = _ruta_lock(root)
    if not ruta.exists():
        return {
            "estado": "NORMAL", "bloquea": False, "existe": False,
            "dudoso": False, "expirado": False, "id_operacion": None,
            "fase": "COMPLETADO", "progreso": 100, "mensaje": "Operacion normal.",
            "error_seguro": None, "completado": True, "fecha_creacion": None,
        }
    if ruta.is_symlink() or not ruta.is_file():
        return _estado_factory_inseguro("El lock no es un archivo regular seguro.")
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        estado = str(datos.get("estado") or "").strip().upper()
        fecha = _fecha_utc(datos.get("fecha_creacion"))
        if estado not in ESTADOS_BLOQUEANTES or fecha is None:
            return _estado_factory_inseguro("El lock contiene datos no reconocidos.")
        antiguedad = max(0, int((datetime.now(timezone.utc) - fecha).total_seconds()))
        return {
            "estado": estado, "bloquea": True, "existe": True, "dudoso": False,
            "expirado": antiguedad > max(60, int(timeout_segundos)),
            "id_operacion": _id_seguro(datos.get("id_operacion"), permitir_vacio=True),
            "fase": str(datos.get("fase") or "LOCK_ADQUIRIDO")[:80],
            "progreso": max(0, min(100, int(datos.get("progreso") or 0))),
            "mensaje": str(datos.get("mensaje") or "Factory Reset bloquea actividad nueva.")[:500],
            "error_seguro": str(datos.get("error_seguro") or "")[:500] or None,
            "completado": bool(datos.get("completado", False)),
            "fecha_creacion": fecha.isoformat(),
        }
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return _estado_factory_inseguro("El lock no pudo interpretarse de forma segura.")


def adquirir_lock_factory_reset(root: Path, estado: str, origen: str, *,
                                id_operacion: str | None = None,
                                timeout_segundos: int = 1800):
    estado = str(estado or "").strip().upper()
    if estado not in ESTADOS_BLOQUEANTES:
        raise ValueError("Estado de Factory Reset no permitido.")
    operacion = _id_seguro(id_operacion or uuid4())
    ruta = _ruta_lock(root, crear=True)
    datos = {
        "version": 1, "estado": estado,
        "fecha_creacion": datetime.now(timezone.utc).isoformat(),
        "pid": os.getpid(), "host": socket.gethostname()[:150],
        "origen": str(origen or "desconocido")[:80],
        "id_operacion": operacion, "fase": "LOCK_ADQUIRIDO",
        "progreso": 5, "mensaje": "Lock global adquirido.",
        "error_seguro": None, "completado": False,
    }
    descriptor = None
    try:
        descriptor = os.open(str(ruta), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.write(descriptor, json.dumps(datos, ensure_ascii=True, separators=(",", ":")).encode("utf-8"))
        os.fsync(descriptor)
    except FileExistsError:
        return False, obtener_estado_factory_reset(root, timeout_segundos)
    finally:
        if descriptor is not None:
            os.close(descriptor)
    registrar_evento_factory_reset(root, operacion, "LOCK_ADQUIRIDO", "Lock global adquirido.")
    return True, obtener_estado_factory_reset(root, timeout_segundos)


def actualizar_lock_factory_reset(root: Path, id_operacion: str, estado: str, *,
                                  fase: str, progreso: int, mensaje: str,
                                  error_seguro: str | None = None,
                                  completado: bool = False,
                                  timeout_segundos: int = 1800) -> bool:
    actual = obtener_estado_factory_reset(root, timeout_segundos)
    operacion = _id_seguro(id_operacion)
    fase = str(fase or "").strip().upper()
    estado = str(estado or "").strip().upper()
    if (not actual["existe"] or actual["dudoso"]
            or actual.get("id_operacion") != operacion
            or estado not in ESTADOS_BLOQUEANTES or fase not in FASES_FACTORY_RESET):
        return False
    datos = {
        "version": 1, "estado": estado,
        "fecha_creacion": actual["fecha_creacion"], "pid": os.getpid(),
        "host": socket.gethostname()[:150], "origen": "WEB_RECONSTRUIDA",
        "id_operacion": operacion, "fase": fase,
        "progreso": max(0, min(100, int(progreso))),
        "mensaje": str(mensaje or "")[:500],
        "error_seguro": str(error_seguro or "")[:500] or None,
        "completado": bool(completado),
    }
    _escribir_atomico(_ruta_lock(root), datos)
    registrar_evento_factory_reset(
        root, operacion, fase, mensaje,
        "ERROR" if estado == "FACTORY_RESET_ERROR" else "INFO",
        {"estado": estado, "progreso": datos["progreso"], "completado": completado},
    )
    return True


def liberar_lock_factory_reset(root: Path, id_operacion: str,
                               timeout_segundos: int = 1800) -> bool:
    actual = obtener_estado_factory_reset(root, timeout_segundos)
    if not actual["existe"]:
        return True
    if actual["dudoso"] or actual.get("id_operacion") != _id_seguro(id_operacion):
        return False
    try:
        _ruta_lock(root).unlink()
        return True
    except OSError:
        return False


def registrar_evento_factory_reset(root: Path, id_operacion: str, fase: str,
                                   mensaje: str, nivel: str = "INFO", datos=None):
    operacion = _id_seguro(id_operacion)
    directorio = Path(root).expanduser().resolve()
    directorio.mkdir(parents=True, exist_ok=True)
    evento = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(),
        "id_operacion": operacion, "fase": str(fase or "ERROR")[:80],
        "nivel": str(nivel or "INFO")[:20], "mensaje": str(mensaje or "")[:1000],
        "datos": _sanitizar_datos(datos or {}),
    }
    ruta_log = directorio / f"factory_reset_{operacion}.jsonl"
    descriptor = os.open(str(ruta_log), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        os.write(descriptor, (json.dumps(evento, ensure_ascii=True, separators=(",", ":")) + "\n").encode("utf-8"))
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    _escribir_atomico(directorio / f"factory_reset_{operacion}.estado.json", evento)
    return evento


def obtener_estado_operacion_factory_reset(root: Path, id_operacion: str):
    ruta = Path(root).expanduser().resolve() / f"factory_reset_{_id_seguro(id_operacion)}.estado.json"
    if not ruta.is_file() or ruta.is_symlink():
        return None
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return None


def registrar_marca_factory_reset_completado(root: Path, id_operacion: str):
    datos = {
        "id_operacion": _id_seguro(id_operacion),
        "fecha_epoch": datetime.now(timezone.utc).timestamp(),
        "fecha_utc": datetime.now(timezone.utc).isoformat(),
    }
    _escribir_atomico(Path(root).expanduser().resolve() / "factory_reset_last_success.json", datos)
    return datos


def _estado_inseguro(estado: str) -> dict[str, object]:
    return {
        "estado": estado,
        "bloquea": True,
        "desde": None,
        "motivo": "El control de mantenimiento no pudo validarse de forma segura.",
        "origen": "desconocido",
    }


def _ruta_lock(root: Path, crear: bool = False) -> Path:
    directorio = Path(root).expanduser().resolve()
    if crear:
        directorio.mkdir(parents=True, exist_ok=True)
    return directorio / "factory_reset.lock"


def _escribir_atomico(ruta: Path, datos) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    temporal = ruta.with_suffix(ruta.suffix + ".tmp")
    temporal.write_text(json.dumps(datos, ensure_ascii=True, separators=(",", ":")), encoding="utf-8")
    os.replace(temporal, ruta)


def _fecha_utc(valor):
    try:
        fecha = datetime.fromisoformat(str(valor))
        return fecha.replace(tzinfo=timezone.utc) if fecha.tzinfo is None else fecha.astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def _id_seguro(valor, *, permitir_vacio=False) -> str | None:
    texto = str(valor or "")
    valido = texto and len(texto) <= 80 and all(
        caracter.isalnum() or caracter in "-_" for caracter in texto
    )
    if not valido:
        if permitir_vacio and not texto:
            return None
        raise ValueError("Identificador de operacion no valido.")
    return texto


def _estado_factory_inseguro(mensaje: str) -> dict[str, object]:
    return {
        "estado": "FACTORY_RESET_ERROR", "bloquea": True, "existe": True,
        "dudoso": True, "expirado": False, "id_operacion": None,
        "fase": "ERROR", "progreso": 0, "mensaje": mensaje,
        "error_seguro": mensaje[:500], "completado": False,
        "fecha_creacion": None,
    }


def _sanitizar_datos(datos) -> dict[str, object]:
    resultado = {}
    for clave, valor in dict(datos).items():
        nombre = str(clave)[:80]
        if any(fragmento in nombre.lower() for fragmento in ("password", "secret", "token", "credential", "cadena")):
            continue
        if isinstance(valor, (str, int, float, bool)) or valor is None:
            resultado[nombre] = str(valor)[:500] if isinstance(valor, str) else valor
    return resultado
