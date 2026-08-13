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
NOMBRE_ULTIMO_RESET = "factory_reset_last_success.json"
FASES_OPERACION = {
    "PRECHECK",
    "LOCK_ADQUIRIDO",
    "BLOQUEANDO_ACTIVIDAD",
    "CUARENTENA_FILESYSTEM",
    "ADQUIRIENDO_APPLOCK",
    "EJECUTANDO_RESET_IN_PLACE",
    "CONFIRMANDO_COMMIT",
    "VALIDANDO_RESULTADO",
    "LIMPIANDO_CUARENTENA",
    "COMPLETADO",
    "ERROR",
    "ROLLBACK_FILESYSTEM",
}


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
            "mensaje": str(datos.get("mensaje") or (
                "Lock expirado o potencialmente huerfano; requiere validacion manual."
                if antiguedad > timeout
                else "Factory Reset mantiene bloqueadas las nuevas ejecuciones."
            ))[:500],
            "fase": str(datos.get("fase") or "LOCK_ADQUIRIDO")[:80],
            "progreso": max(0, min(100, _entero_seguro(datos.get("progreso"), 0))),
            "error_seguro": str(datos.get("error_seguro") or "")[:500] or None,
            "completado": bool(datos.get("completado", False)),
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
        "fase": "LOCK_ADQUIRIDO",
        "progreso": 5,
        "error_seguro": None,
        "completado": False,
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


def actualizar_lock_factory_reset(id_operacion, estado, fase=None, progreso=None, mensaje=None, error_seguro=None, completado=False):
    actual = obtener_estado_factory_reset()
    if not actual["existe"] or actual["dudoso"]:
        return False
    if not id_operacion or actual["id_operacion"] != str(id_operacion):
        return False
    estado = str(estado or "").strip().upper()
    if estado not in ESTADOS_FACTORY_RESET:
        return False
    fase = str(fase or actual.get("fase") or "LOCK_ADQUIRIDO").strip().upper()
    if fase not in FASES_OPERACION:
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
        "fase": fase,
        "progreso": max(0, min(100, _entero_seguro(progreso, actual.get("progreso", 0)))),
        "mensaje": str(mensaje or actual.get("mensaje") or "")[:500],
        "error_seguro": str(error_seguro or "")[:500] or None,
        "completado": bool(completado),
    }
    temporal.write_text(json.dumps(datos, ensure_ascii=True, separators=(",", ":")), encoding="utf-8")
    os.replace(temporal, ruta)
    registrar_evento_factory_reset(
        actual["id_operacion"],
        fase,
        mensaje or actual.get("mensaje") or "Estado actualizado.",
        "ERROR" if estado == "FACTORY_RESET_ERROR" else "INFO",
        {"estado": estado, "progreso": datos["progreso"], "completado": bool(completado)},
    )
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


def registrar_evento_factory_reset(id_operacion, fase, mensaje, nivel="INFO", datos=None):
    operacion = _id_operacion_seguro(id_operacion)
    root = _ruta_lock(crear_root=True).parent
    ruta_log = root / f"factory_reset_{operacion}.jsonl"
    ruta_estado = root / f"factory_reset_{operacion}.estado.json"
    evento = {
        "fecha_utc": datetime.now(timezone.utc).isoformat(),
        "id_operacion": operacion,
        "fase": str(fase or "ERROR")[:80],
        "nivel": str(nivel or "INFO")[:20],
        "mensaje": str(mensaje or "")[:1000],
        "datos": _sanitizar_datos_control(datos or {}),
    }
    linea = (json.dumps(evento, ensure_ascii=True, separators=(",", ":")) + "\n").encode("utf-8")
    descriptor = os.open(str(ruta_log), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        os.write(descriptor, linea)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    temporal = ruta_estado.with_suffix(".tmp")
    temporal.write_text(json.dumps(evento, ensure_ascii=True, separators=(",", ":")), encoding="utf-8")
    os.replace(temporal, ruta_estado)
    return evento


def obtener_estado_operacion_factory_reset(id_operacion):
    operacion = _id_operacion_seguro(id_operacion)
    ruta = _ruta_lock().parent / f"factory_reset_{operacion}.estado.json"
    if not ruta.is_file() or ruta.is_symlink():
        return None
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return None


def registrar_marca_factory_reset_completado(id_operacion):
    operacion = _id_operacion_seguro(id_operacion)
    ruta = _ruta_lock(crear_root=True).parent / NOMBRE_ULTIMO_RESET
    datos = {
        "id_operacion": operacion,
        "fecha_epoch": datetime.now(timezone.utc).timestamp(),
        "fecha_utc": datetime.now(timezone.utc).isoformat(),
    }
    temporal = ruta.with_suffix(".tmp")
    temporal.write_text(json.dumps(datos, ensure_ascii=True, separators=(",", ":")), encoding="utf-8")
    os.replace(temporal, ruta)
    return datos


def sesion_es_anterior_ultimo_factory_reset(fecha_sesion_epoch):
    ruta = _ruta_lock().parent / NOMBRE_ULTIMO_RESET
    if not ruta.exists():
        return False
    if ruta.is_symlink() or not ruta.is_file():
        return True
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        return float(fecha_sesion_epoch or 0) < float(datos["fecha_epoch"])
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        return True


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
        "fase": "COMPLETADO",
        "progreso": 100,
        "error_seguro": None,
        "completado": True,
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
        "fase": "ERROR",
        "progreso": 0,
        "error_seguro": mensaje[:500],
        "completado": False,
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


def _id_operacion_seguro(valor):
    texto = str(valor or "")
    if not texto or len(texto) > 80 or any(caracter not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for caracter in texto):
        raise ValueError("Identificador de operacion no valido.")
    return texto


def _sanitizar_datos_control(datos):
    resultado = {}
    for clave, valor in dict(datos).items():
        nombre = str(clave)[:80]
        if any(sensible in nombre.lower() for sensible in ("password", "secret", "token", "credential", "cadena")):
            continue
        if isinstance(valor, (str, int, float, bool)) or valor is None:
            resultado[nombre] = str(valor)[:500] if isinstance(valor, str) else valor
    return resultado
