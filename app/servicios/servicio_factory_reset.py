import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.config import BASE_DIR, VALORES_PLANTILLA
from app.repositorios.repositorio_configuracion_scheduler import obtener_configuracion_activa
from app.repositorios.repositorio_factory_reset import (
    listar_ejecuciones_activas_factory_reset,
    obtener_conteos_factory_reset,
    obtener_version_bootstrap_sql,
)
from app.repositorios.repositorio_scheduler import listar_tareas_programadas_activas
from app.servicios.servicio_control_runtime import obtener_estado_factory_reset
from app.servicios.servicio_procesos import PROCESOS_EJECUCION
from app.servicios.servicio_worker_heartbeat import clasificar_estado_worker, obtener_estado_worker


VERSION_PREVIEW = "1.0"
SALT_PREVIEW = "app-scheduler-factory-reset-preview-v1"
ROOTS_FILESYSTEM = (
    ("scripts", "RUTA_BASE_SCRIPTS", "scripts"),
    ("env_scripts", "RUTA_BASE_ENV_SCRIPTS", "env_scripts"),
    ("logs_tareas", "RUTA_BASE_LOGS_TAREAS", "logs_tareas"),
    ("logs_sistema", "RUTA_BASE_LOGS_SISTEMA", "logs_sistema"),
    ("logs_worker", "RUTA_BASE_LOGS_WORKER", "logs"),
)


def generar_preview_factory_reset(usuario):
    generado = datetime.now(timezone.utc)
    lock = obtener_estado_factory_reset()
    bloqueos = []
    errores = []

    try:
        conteos = obtener_conteos_factory_reset()
        version_bootstrap_sql = obtener_version_bootstrap_sql()
        diagnostico = _diagnosticar_operacion()
    except Exception as error:
        conteos = {}
        version_bootstrap_sql = None
        diagnostico = _diagnostico_no_disponible()
        errores.append(f"No fue posible completar el inventario SQL: {error.__class__.__name__}.")
        bloqueos.append("La base de datos no pudo validarse completamente.")

    filesystem = _inventariar_filesystem()
    manifiesto = validar_manifiesto_bootstrap()
    manifiesto["version_instalada"] = version_bootstrap_sql
    manifiesto["version_coincide"] = bool(
        manifiesto["valido"]
        and version_bootstrap_sql
        and version_bootstrap_sql == manifiesto["version"]
    )
    super_admin_env = validar_super_admin_env()
    from app.servicios.servicio_factory_reset_sql import validar_configuracion_factory_reset_sql

    configuracion_reset = validar_configuracion_factory_reset_sql()

    if lock["bloquea"]:
        bloqueos.append("Existe un lock global de Factory Reset activo o dudoso.")
    if diagnostico["ejecuciones_activas"]:
        bloqueos.append("Existen ejecuciones EN_EJECUCION.")
    if not manifiesto["valido"]:
        bloqueos.append("El manifiesto bootstrap no esta disponible o es invalido.")
    if not super_admin_env["disponible"]:
        bloqueos.append("SUPER_ADMIN_ENV no esta disponible para recuperar acceso.")
    if diagnostico["procesos_hijos_conocidos"] or diagnostico["pids_vivos_registrados"]:
        bloqueos.append("Existen procesos de ejecucion activos o PID vivos.")
    bloqueos.extend(configuracion_reset["bloqueos"])

    preview = {
        "version_preview": VERSION_PREVIEW,
        "id_operacion": str(uuid4()),
        "generado_utc": generado.isoformat(),
        "expira_segundos": _ttl_preview(),
        "estado": "BLOQUEADO" if bloqueos else "LISTO_PARA_CONFIRMACION_FUTURA",
        "bloqueos": bloqueos,
        "errores": errores,
        "lock": lock,
        "base_datos": {
            "conteos": conteos,
            "total_registros": sum(conteos.values()),
        },
        "diagnostico": diagnostico,
        "filesystem": filesystem,
        "bootstrap": manifiesto,
        "super_admin_env": super_admin_env,
        "configuracion_reset": configuracion_reset,
        "reset_destructivo_habilitado": not bloqueos and configuracion_reset["disponible"],
    }
    resumen_hash = _hash_preview(preview)
    preview["resumen_hash"] = resumen_hash
    preview["token_preview"] = _serializador().dumps(
        {
            "usuario": str(usuario or "")[:150],
            "emitido": int(generado.timestamp()),
            "resumen_hash": resumen_hash,
            "estado_lock": lock["estado"],
            "id_operacion": preview["id_operacion"],
            "manifest_hash": manifiesto.get("hash_conjunto"),
        }
    )
    return preview


def validar_token_preview(token, usuario, resumen_hash=None, max_age=None):
    try:
        datos = _serializador().loads(token, max_age=_ttl_preview() if max_age is None else max_age)
    except SignatureExpired:
        return False, "El preview expiro. Genera uno nuevo.", None
    except (BadSignature, TypeError):
        return False, "El token de preview no es valido.", None

    if datos.get("usuario") != str(usuario or "")[:150]:
        return False, "El preview pertenece a otra sesion.", None
    if resumen_hash and datos.get("resumen_hash") != resumen_hash:
        return False, "El resumen del preview no coincide.", None
    return True, "Preview vigente.", datos


def validar_manifiesto_bootstrap():
    ruta = BASE_DIR / "database" / "bootstrap" / "manifest.json"
    resultado = {
        "valido": False,
        "version": None,
        "cantidad_scripts": 0,
        "orden": [],
        "faltantes": [],
        "mensaje": "Manifiesto no validado.",
        "hash_conjunto": None,
        "scripts": [],
    }
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        scripts = datos.get("scripts") or []
        ordenes = [int(item["order"]) for item in scripts]
        archivos = [str(item["file"]) for item in scripts]
        faltantes = []
        rutas_validas = True
        hasher = hashlib.sha256(ruta.read_bytes())
        scripts_normalizados = []
        for archivo in archivos:
            relativa = Path(archivo)
            if relativa.is_absolute() or ".." in relativa.parts:
                rutas_validas = False
                faltantes.append("ruta_invalida")
                continue
            candidata = BASE_DIR / relativa
            absoluta = candidata.resolve()
            tiene_symlink = candidata.is_symlink() or any(
                padre.is_symlink() for padre in candidata.parents if padre != BASE_DIR and BASE_DIR in padre.parents
            )
            if BASE_DIR not in absoluta.parents or tiene_symlink or absoluta.suffix.lower() != ".sql":
                rutas_validas = False
                faltantes.append("ruta_invalida")
                continue
            if not absoluta.is_file():
                faltantes.append(relativa.name)
                continue
            hasher.update(str(relativa).replace("\\", "/").encode("utf-8"))
            hasher.update(absoluta.read_bytes())
        for item in scripts:
            scripts_normalizados.append({
                "order": int(item["order"]),
                "file": str(item["file"]),
                "type": str(item.get("type") or "")[:30],
            })
        orden_valido = (
            ordenes == sorted(set(ordenes))
            and bool(ordenes)
            and ordenes[0] == 1
            and ordenes[-1] == 100
            and len(set(archivos)) == len(archivos)
        )
        resultado.update(
            {
                "valido": bool(rutas_validas and orden_valido and not faltantes),
                "version": str(datos.get("version") or "")[:30],
                "cantidad_scripts": len(scripts),
                "orden": ordenes,
                "faltantes": faltantes,
                "hash_conjunto": hasher.hexdigest() if rutas_validas and not faltantes else None,
                "scripts": scripts_normalizados,
            }
        )
        resultado["mensaje"] = "Bootstrap disponible y ordenado." if resultado["valido"] else "Bootstrap incompleto o desordenado."
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        resultado["mensaje"] = "No fue posible validar manifest.json."
    return resultado


def validar_super_admin_env():
    usuario = str(current_app.config.get("USUARIO_ADMIN_DEFECTO") or "").strip()
    password = str(current_app.config.get("PASSWORD_ADMIN_DEFECTO") or "")
    disponible = bool(usuario and password and usuario not in VALORES_PLANTILLA and password not in VALORES_PLANTILLA)
    return {
        "disponible": disponible,
        "estado": "DISPONIBLE" if disponible else "NO_DISPONIBLE",
        "mensaje": (
            "Administrador inicial de recuperacion configurado."
            if disponible
            else "Falta configuracion segura de recuperacion por entorno."
        ),
    }


def _diagnosticar_operacion():
    ejecuciones = listar_ejecuciones_activas_factory_reset()
    ejecuciones_resumen = []
    for item in ejecuciones:
        pid = item.get("pid_proceso")
        ejecuciones_resumen.append(
            {
                "id_ejecucion": item.get("id_ejecucion"),
                "id_tarea": item.get("id_tarea"),
                "origen": item.get("origen_ejecucion"),
                "pid_registrado": bool(pid),
                "pid_vivo": _pid_vivo(pid),
            }
        )

    heartbeat = obtener_estado_worker()
    configuracion = obtener_configuracion_activa() or {}
    estado_worker = clasificar_estado_worker(heartbeat, configuracion)
    candidatos = listar_tareas_programadas_activas()
    hijos_vivos = sum(1 for proceso in PROCESOS_EJECUCION.values() if proceso and proceso.poll() is None)
    return {
        "ejecuciones_activas": ejecuciones_resumen,
        "total_ejecuciones_activas": len(ejecuciones_resumen),
        "pids_vivos_registrados": sum(1 for item in ejecuciones_resumen if item["pid_vivo"]),
        "procesos_hijos_conocidos": hijos_vivos,
        "worker": {
            "detectado": bool(heartbeat),
            "estado": estado_worker.get("codigo"),
            "activo": estado_worker.get("codigo") in {"ACTIVO", "ADVERTENCIA"},
        },
        "tareas_candidatas": len(candidatos),
    }


def diagnosticar_operacion_factory_reset():
    return _diagnosticar_operacion()


def inventariar_filesystem_factory_reset():
    return _inventariar_filesystem()


def _diagnostico_no_disponible():
    return {
        "ejecuciones_activas": [],
        "total_ejecuciones_activas": 0,
        "pids_vivos_registrados": 0,
        "procesos_hijos_conocidos": 0,
        "worker": {"detectado": False, "estado": "NO_DISPONIBLE", "activo": False},
        "tareas_candidatas": 0,
    }


def _inventariar_filesystem():
    roots = []
    total_archivos = 0
    total_bytes = 0
    total_py = 0
    total_env = 0
    total_logs = 0
    for nombre, clave, defecto in ROOTS_FILESYSTEM:
        ruta = Path(str(current_app.config.get(clave, defecto))).expanduser()
        if not ruta.is_absolute():
            ruta = BASE_DIR / ruta
        resumen = _inventariar_root(nombre, ruta.resolve())
        roots.append(resumen)
        total_archivos += resumen["archivos"]
        total_bytes += resumen["bytes_aproximados"]
        total_py += resumen["archivos_py"]
        total_env += resumen["archivos_env"]
        total_logs += resumen["archivos_log"]
    return {
        "roots": roots,
        "total_archivos": total_archivos,
        "bytes_aproximados": total_bytes,
        "archivos_py": total_py,
        "archivos_env": total_env,
        "archivos_log": total_logs,
    }


def _inventariar_root(nombre, ruta):
    resumen = {
        "nombre": nombre,
        "existe": ruta.is_dir(),
        "archivos": 0,
        "carpetas": 0,
        "bytes_aproximados": 0,
        "archivos_py": 0,
        "archivos_env": 0,
        "archivos_log": 0,
    }
    if not ruta.is_dir():
        return resumen
    for _actual, carpetas, archivos in os.walk(ruta, followlinks=False):
        resumen["carpetas"] += len(carpetas)
        for nombre_archivo in archivos:
            archivo = Path(_actual) / nombre_archivo
            resumen["archivos"] += 1
            sufijo = archivo.suffix.lower()
            resumen["archivos_py"] += int(sufijo == ".py")
            resumen["archivos_env"] += int(nombre_archivo.lower() == ".env" or sufijo == ".env")
            resumen["archivos_log"] += int(sufijo == ".log")
            try:
                resumen["bytes_aproximados"] += archivo.stat().st_size
            except OSError:
                pass
    return resumen


def _pid_vivo(pid):
    if not pid:
        return False
    try:
        os.kill(int(pid), 0)
        return True
    except (OSError, TypeError, ValueError):
        return False


def _hash_preview(preview):
    contenido = json.dumps(preview, ensure_ascii=True, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(contenido.encode("utf-8")).hexdigest()


def _serializador():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt=SALT_PREVIEW)


def _ttl_preview():
    try:
        return max(60, int(current_app.config.get("FACTORY_RESET_PREVIEW_TTL_SEGUNDOS", 300)))
    except (TypeError, ValueError):
        return 300
