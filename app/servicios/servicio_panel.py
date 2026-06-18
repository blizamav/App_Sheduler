from app.repositorios.repositorio_panel import (
    listar_ultimas_ejecuciones,
    obtener_configuracion_scheduler_panel,
    obtener_metricas_panel,
    obtener_ultima_ejecucion,
)
from app.servicios.servicio_worker_heartbeat import clasificar_estado_worker, obtener_estado_worker


def obtener_panel_principal():
    datos_ok = True
    errores = []

    try:
        metricas = _normalizar_metricas(obtener_metricas_panel())
    except Exception as error:
        datos_ok = False
        errores.append(error.__class__.__name__)
        metricas = _metricas_vacias()

    try:
        configuracion = obtener_configuracion_scheduler_panel()
    except Exception as error:
        datos_ok = False
        errores.append(error.__class__.__name__)
        configuracion = None

    try:
        ultima_ejecucion = obtener_ultima_ejecucion()
        ultimas_ejecuciones = listar_ultimas_ejecuciones(limite=6)
    except Exception as error:
        datos_ok = False
        errores.append(error.__class__.__name__)
        ultima_ejecucion = None
        ultimas_ejecuciones = []

    scheduler = _normalizar_scheduler(configuracion)
    heartbeat = obtener_estado_worker()
    estado_worker = clasificar_estado_worker(heartbeat, scheduler)
    return {
        "metricas": metricas,
        "scheduler": scheduler,
        "worker": {"heartbeat": heartbeat, "estado": estado_worker},
        "ultima_ejecucion": ultima_ejecucion,
        "ultimas_ejecuciones": ultimas_ejecuciones,
        "estado_general": _estado_general(datos_ok, scheduler, metricas, estado_worker),
        "datos_ok": datos_ok,
        "errores": errores,
    }


def _metricas_vacias():
    return {
        "total_tareas": 0,
        "tareas_activas": 0,
        "scripts_activos": 0,
        "tareas_con_script": 0,
        "ejecuciones_hoy": 0,
        "exitosas_hoy": 0,
        "errores_hoy": 0,
        "en_curso": 0,
        "feriados_anio_actual": 0,
    }


def _normalizar_metricas(metricas):
    base = _metricas_vacias()
    metricas = metricas or {}
    for clave in base:
        base[clave] = int(metricas.get(clave) or 0)
    return base


def _normalizar_scheduler(configuracion):
    if not configuracion:
        return {
            "existe": False,
            "scheduler_activo": False,
            "permitir_ejecucion_automatica": False,
            "modo_mantenimiento": False,
            "intervalo_revision_segundos": 0,
            "max_ejecuciones_concurrentes": 0,
        }

    return {
        "existe": True,
        "scheduler_activo": bool(configuracion.get("scheduler_activo")),
        "permitir_ejecucion_automatica": bool(configuracion.get("permitir_ejecucion_automatica")),
        "modo_mantenimiento": bool(configuracion.get("modo_mantenimiento")),
        "intervalo_revision_segundos": int(configuracion.get("intervalo_revision_segundos") or 0),
        "max_ejecuciones_concurrentes": int(configuracion.get("max_ejecuciones_concurrentes") or 0),
    }


def _estado_general(datos_ok, scheduler, metricas, estado_worker):
    return [
        {
            "texto": "Base de datos operativa",
            "detalle": "Lectura de metricas del panel correcta." if datos_ok else "No fue posible leer todas las metricas.",
            "estado": "activo" if datos_ok else "advertencia",
        },
        {
            "texto": "Login operativo",
            "detalle": "Sesion web activa con permisos cargados.",
            "estado": "activo",
        },
        {
            "texto": "Modulo tareas operativo",
            "detalle": f"{metricas['total_tareas']} tareas registradas.",
            "estado": "activo",
        },
        {
            "texto": "Ejecucion manual operativa",
            "detalle": "Consola, polling y detencion se mantienen disponibles.",
            "estado": "activo",
        },
        {
            "texto": "Programador configurado",
            "detalle": _detalle_scheduler(scheduler),
            "estado": "activo" if scheduler["existe"] else "advertencia",
        },
        {
            "texto": "Feriados locales operativos",
            "detalle": f"{metricas['feriados_anio_actual']} feriados activos cargados para el anio actual.",
            "estado": "activo",
        },
        {
            "texto": "Senal de vida del programador",
            "detalle": estado_worker["texto"],
            "estado": "activo" if estado_worker["badge"] == "activo" else "error" if estado_worker["badge"] == "error" else "advertencia",
        },
    ]


def _detalle_scheduler(scheduler):
    if not scheduler["existe"]:
        return "No se encontro configuracion activa."
    if scheduler["modo_mantenimiento"]:
        return "Modo mantenimiento activo."
    if not scheduler["scheduler_activo"]:
        return "Programador inactivo por configuracion."
    if not scheduler["permitir_ejecucion_automatica"]:
        return "Programador activo con ejecucion automatica deshabilitada."
    return "Programador activo con ejecucion automatica permitida."
