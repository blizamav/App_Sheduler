from app.repositorios.repositorio_panel import (
    listar_ultimas_ejecuciones,
    obtener_configuracion_scheduler_panel,
    obtener_metricas_panel,
    obtener_ultima_ejecucion,
)


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
        ultimas_ejecuciones = listar_ultimas_ejecuciones()
    except Exception as error:
        datos_ok = False
        errores.append(error.__class__.__name__)
        ultima_ejecucion = None
        ultimas_ejecuciones = []

    scheduler = _normalizar_scheduler(configuracion)
    return {
        "metricas": metricas,
        "scheduler": scheduler,
        "ultima_ejecucion": ultima_ejecucion,
        "ultimas_ejecuciones": ultimas_ejecuciones,
        "estado_general": _estado_general(datos_ok, scheduler, metricas),
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


def _estado_general(datos_ok, scheduler, metricas):
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
            "texto": "Scheduler configurado",
            "detalle": _detalle_scheduler(scheduler),
            "estado": "activo" if scheduler["existe"] else "advertencia",
        },
        {
            "texto": "Feriados locales operativos",
            "detalle": f"{metricas['feriados_anio_actual']} feriados activos cargados para el anio actual.",
            "estado": "activo",
        },
        {
            "texto": "Heartbeat worker pendiente de Fase 11B",
            "detalle": "El panel no comprueba aun si el proceso worker esta vivo.",
            "estado": "advertencia",
        },
    ]


def _detalle_scheduler(scheduler):
    if not scheduler["existe"]:
        return "No se encontro configuracion activa."
    if scheduler["modo_mantenimiento"]:
        return "Modo mantenimiento activo."
    if not scheduler["scheduler_activo"]:
        return "Scheduler inactivo por configuracion."
    if not scheduler["permitir_ejecucion_automatica"]:
        return "Scheduler activo con ejecucion automatica deshabilitada."
    return "Scheduler activo con ejecucion automatica permitida."
