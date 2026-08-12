import json
import os
import socket
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from flask import current_app

from app.config import BASE_DIR


ESTADO_NORMAL = "NORMAL"
ESTADOS_FACTORY_RESET = {
    "FACTORY_RESET_PREPARANDO",
    "FACTORY_RESET_EN_PROGRESO",
    "FACTORY_RESET_ERROR",
}
NOMBRE_LOCK_FACTORY_RESET = "factory_reset.lock"


def obtener_estado_factory_reset():
    ruta = _ruta_lock()
    if not ruta.exists():
        return _estado_normal(ruta)
    if ruta.is_symlink() or not ruta.is_file():
        return _estado_dudoso(ruta, "El lock no es un archivo regular seguro.")

    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        estado = str(datos.get("estado") or "").strip().upper()
        if estado not in ESTADOS_FACTORY_RESET:
            return _estado_dudoso(ruta, "El lock contiene un estado no reconocido.")
        fecha = _parsear_fecha(datos.get("fecha_creacion"))
        if not fecha:
            return _estado_dudoso(ruta, "El lock no contiene una fecha valida.")
        antiguedad = max(0, int((datetime.now(timezone.utc) - fecha).total_seconds()))
        timeout = _timeout_lock()
        return {
            "estado": estado,
            "bloquea": True,
            "existe": True,
            "dudoso": False,
            "expirado": antiguedad > timeout,
            "antiguedad_segundos": antiguedad,
            "timeout_segundos": timeout,
            "id_operacion": str(datos.get("id_operacion") or "")[:80],
            "origen": str(datos.get("origen") or "desconocido")[:80],
            "pid": _entero_seguro(datos.get("pid")),
            "fecha_creacion": fecha.isoformat(),
            "ruta_configurada": str(ruta.parent),
            "mensaje": (
                "Lock expirado o potencialmente huerfano; requiere validacion manual."
                if antiguedad > timeout
                else "Factory Reset mantiene bloqueadas las nuevas ejecuciones."
            ),
        }
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return _estado_dudoso(ruta, "El lock no pudo ser interpretado de forma segura.")


def adquirir_lock_factory_reset(estado, origen, id_operacion=None):
    estado = str(estado or "").strip().upper()
    if estado not in ESTADOS_FACTORY_RESET:
        raise ValueError("Estado de Factory Reset no permitido.")

    ruta = _ruta_lock(crear_root=True)
    operacion = str(id_operacion or uuid4())
    datos = {
        "version": 1,
        "estado": estado,
        "fecha_creacion": datetime.now(timezone.utc).isoformat(),
        "pid": os.getpid(),
        "host": socket.gethostname()[:150],
        "origen": str(origen or "desconocido")[:80],
        "id_operacion": operacion[:80],
    }
    descriptor = None
    try:
        descriptor = os.open(str(ruta), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        contenido = json.dumps(datos, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
        os.write(descriptor, contenido)
        os.fsync(descriptor)
    except FileExistsError:
        return False, obtener_estado_factory_reset()
    except Exception:
        if descriptor is not None:
            os.close(descriptor)
            descriptor = None
        try:
            ruta.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    finally:
        if descriptor is not None:
            os.close(descriptor)
    return True, obtener_estado_factory_reset()


def actualizar_lock_factory_reset(id_operacion, estado):
    actual = obtener_estado_factory_reset()
    if not actual["existe"] or actual["dudoso"]:
        return False
    if not id_operacion or actual["id_operacion"] != str(id_operacion):
        return False
    estado = str(estado or "").strip().upper()
    if estado not in ESTADOS_FACTORY_RESET:
        return False

    ruta = _ruta_lock()
    temporal = ruta.with_suffix(".tmp")
    datos = {
        "version": 1,
        "estado": estado,
        "fecha_creacion": actual["fecha_creacion"],
        "pid": actual["pid"],
        "host": socket.gethostname()[:150],
        "origen": actual["origen"],
        "id_operacion": actual["id_operacion"],
    }
    temporal.write_text(json.dumps(datos, ensure_ascii=True, separators=(",", ":")), encoding="utf-8")
    os.replace(temporal, ruta)
    return True


def liberar_lock_factory_reset(id_operacion):
    actual = obtener_estado_factory_reset()
    if not actual["existe"]:
        return True
    if actual["dudoso"] or not id_operacion or actual["id_operacion"] != str(id_operacion):
        return False
    try:
        _ruta_lock().unlink()
        return True
    except OSError:
        return False


def factory_reset_bloquea_ejecuciones():
    estado = obtener_estado_factory_reset()
    return bool(estado["bloquea"]), estado


def _ruta_lock(crear_root=False):
    valor = str(current_app.config.get("RUTA_CONTROL_RUNTIME", "runtime_control")).strip() or "runtime_control"
    root = Path(valor).expanduser()
    if not root.is_absolute():
        root = BASE_DIR / root
    root = root.resolve()
    if crear_root:
        root.mkdir(parents=True, exist_ok=True)
    return root / NOMBRE_LOCK_FACTORY_RESET


def _timeout_lock():
    return max(300, _entero_seguro(current_app.config.get("FACTORY_RESET_LOCK_TIMEOUT_SEGUNDOS"), 1800))


def _estado_normal(ruta):
    return {
        "estado": ESTADO_NORMAL,
        "bloquea": False,
        "existe": False,
        "dudoso": False,
        "expirado": False,
        "antiguedad_segundos": 0,
        "timeout_segundos": _timeout_lock(),
        "id_operacion": None,
        "origen": None,
        "pid": None,
        "fecha_creacion": None,
        "ruta_configurada": str(ruta.parent),
        "mensaje": "Operacion normal; no existe lock de Factory Reset.",
    }


def _estado_dudoso(ruta, mensaje):
    return {
        "estado": "FACTORY_RESET_ERROR",
        "bloquea": True,
        "existe": True,
        "dudoso": True,
        "expirado": False,
        "antiguedad_segundos": None,
        "timeout_segundos": _timeout_lock(),
        "id_operacion": None,
        "origen": "desconocido",
        "pid": None,
        "fecha_creacion": None,
        "ruta_configurada": str(ruta.parent),
        "mensaje": mensaje + " No se libera automaticamente.",
    }


def _parsear_fecha(valor):
    try:
        fecha = datetime.fromisoformat(str(valor))
        if fecha.tzinfo is None:
            fecha = fecha.replace(tzinfo=timezone.utc)
        return fecha.astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def _entero_seguro(valor, defecto=0):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return defecto
