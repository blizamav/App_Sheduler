from app.repositorios.repositorio_scheduler_eventos import (
    desactivar_eventos_antiguos,
    insertar_evento_programador,
    listar_eventos_programador,
    obtener_eventos_relevantes_recientes,
    obtener_omisiones_por_motivo_hoy,
    obtener_resumen_eventos_hoy,
    listar_eventos_programador_paginado,
    resumir_eventos_recientes,
)


MOTIVOS_OMISION_CONTROLADOS = (
    "FERIADO",
    "FUERA_DE_VENTANA",
    "EJECUCION_EN_CURSO",
    "DUPLICADO_SLOT",
    "LIMITE_CONCURRENCIA",
    "MODO_MANTENIMIENTO",
    "SCHEDULER_INACTIVO",
    "EJECUCION_AUTOMATICA_DESHABILITADA",
)

TIPOS_EVENTO = (
    "CICLO_INICIADO",
    "CICLO_FINALIZADO",
    "TAREA_EVALUADA",
    "TAREA_EJECUTADA",
    "TAREA_OMITIDA",
    "ERROR_SCHEDULER",
)

DECISIONES_EVENTO = ("EJECUTAR", "OMITIR", "ERROR", "INFO")
PER_PAGE_OPCIONES = (10, 25, 50, 100)


def registrar_evento_programador(
    tipo_evento,
    decision,
    nombre_worker=None,
    tarea=None,
    fecha_programada=None,
    clave_programacion=None,
    motivo=None,
    detalle=None,
    configuracion=None,
    feriado=None,
    es_feriado=None,
):
    evento = {
        "nombre_worker": nombre_worker,
        "id_tarea": _valor_tarea(tarea, "id_tarea"),
        "nombre_tarea": _valor_tarea(tarea, "nombre_tarea"),
        "id_programacion": _valor_tarea(tarea, "id_programacion"),
        "fecha_programada": fecha_programada,
        "clave_programacion": clave_programacion,
        "tipo_evento": tipo_evento,
        "decision": decision,
        "motivo": motivo,
        "detalle": detalle,
        "estado_scheduler": _estado_scheduler(configuracion),
        "ejecutar_en_feriados": _bool_o_none(_valor_tarea(tarea, "ejecutar_en_feriados")),
        "es_feriado": _bool_o_none(es_feriado),
        "nombre_feriado": _nombre_feriado(feriado),
    }
    try:
        insertar_evento_programador(evento)
        return True
    except Exception:
        return False


def registrar_ciclo_iniciado(nombre_worker, configuracion=None, total_tareas=None):
    detalle = "Ciclo del programador iniciado."
    if total_tareas is not None:
        detalle = f"Ciclo del programador iniciado. Tareas candidatas: {total_tareas}."
    return registrar_evento_programador(
        "CICLO_INICIADO",
        "INFO",
        nombre_worker=nombre_worker,
        detalle=detalle,
        configuracion=configuracion,
    )


def registrar_ciclo_finalizado(nombre_worker, configuracion=None, evaluadas=0, ejecutadas=0, omitidas=0):
    return registrar_evento_programador(
        "CICLO_FINALIZADO",
        "INFO",
        nombre_worker=nombre_worker,
        detalle=f"Ciclo finalizado. Evaluadas: {evaluadas}; ejecutadas: {ejecutadas}; omitidas: {omitidas}.",
        configuracion=configuracion,
    )


def registrar_tarea_omitida(
    tarea,
    motivo,
    detalle,
    nombre_worker,
    configuracion=None,
    fecha_programada=None,
    clave_programacion=None,
    feriado=None,
):
    return registrar_evento_programador(
        "TAREA_OMITIDA",
        "OMITIR",
        nombre_worker=nombre_worker,
        tarea=tarea,
        fecha_programada=fecha_programada,
        clave_programacion=clave_programacion,
        motivo=motivo,
        detalle=detalle,
        configuracion=configuracion,
        feriado=feriado,
        es_feriado=bool(feriado) if feriado is not None else None,
    )


def registrar_tarea_ejecutada(tarea, nombre_worker, configuracion=None, fecha_programada=None, clave_programacion=None, id_ejecucion=None):
    detalle = "Tarea enviada a ejecucion automatica."
    if id_ejecucion:
        detalle = f"Tarea enviada a ejecucion automatica {id_ejecucion}."
    return registrar_evento_programador(
        "TAREA_EJECUTADA",
        "EJECUTAR",
        nombre_worker=nombre_worker,
        tarea=tarea,
        fecha_programada=fecha_programada,
        clave_programacion=clave_programacion,
        detalle=detalle,
        configuracion=configuracion,
    )


def registrar_error_programador(nombre_worker, error, configuracion=None, detalle=None):
    mensaje = detalle or str(error or "Error controlado del programador.")
    return registrar_evento_programador(
        "ERROR_SCHEDULER",
        "ERROR",
        nombre_worker=nombre_worker,
        motivo="ERROR_VALIDACION",
        detalle=mensaje[:2000],
        configuracion=configuracion,
    )


def obtener_eventos_recientes(limite=8):
    try:
        return resumir_eventos_recientes(limite=limite)
    except Exception:
        return []


def obtener_resumen_inteligente_eventos():
    try:
        resumen = obtener_resumen_eventos_hoy() or {}
    except Exception:
        resumen = {}

    try:
        omisiones = obtener_omisiones_por_motivo_hoy()
    except Exception:
        omisiones = []

    return {
        "eventos_hoy": int(resumen.get("eventos_hoy") or 0),
        "tareas_ejecutadas": int(resumen.get("tareas_ejecutadas") or 0),
        "tareas_omitidas": int(resumen.get("tareas_omitidas") or 0),
        "errores_programador": int(resumen.get("errores_programador") or 0),
        "ultimo_evento": resumen.get("ultimo_evento"),
        "omisiones_por_motivo": _normalizar_omisiones(omisiones),
    }


def obtener_eventos_relevantes(limite=10):
    try:
        return obtener_eventos_relevantes_recientes(limite=limite)
    except Exception:
        return []


def listar_eventos(filtros=None, limite=50):
    try:
        return listar_eventos_programador(filtros=filtros, limite=limite)
    except Exception:
        return []


def limpiar_eventos_antiguos(dias_retencion=90):
    return desactivar_eventos_antiguos(dias_retencion=dias_retencion)


def listar_historial_eventos(filtros=None, page=1, per_page=25):
    filtros_limpios = _limpiar_filtros(filtros or {})
    page_segura = _page_segura(page)
    per_page_seguro = _per_page_seguro(per_page)
    try:
        resultado = listar_eventos_programador_paginado(
            filtros=filtros_limpios,
            page=page_segura,
            per_page=per_page_seguro,
        )
    except Exception:
        resultado = {"eventos": [], "total": 0, "page": page_segura, "per_page": per_page_seguro}

    total = int(resultado.get("total") or 0)
    page_actual = int(resultado.get("page") or 1)
    per_page_actual = int(resultado.get("per_page") or 25)
    total_paginas = max(1, (total + per_page_actual - 1) // per_page_actual)
    if page_actual > total_paginas:
        page_actual = total_paginas

    return {
        "eventos": resultado.get("eventos") or [],
        "total": total,
        "page": page_actual,
        "per_page": per_page_actual,
        "total_paginas": total_paginas,
        "filtros": filtros_limpios,
        "tipos_evento": TIPOS_EVENTO,
        "decisiones": DECISIONES_EVENTO,
        "motivos": tuple(MOTIVOS_OMISION_CONTROLADOS) + ("ERROR_VALIDACION", "OTROS"),
        "per_page_opciones": PER_PAGE_OPCIONES,
    }


def _normalizar_omisiones(omisiones):
    conteos = {motivo: 0 for motivo in MOTIVOS_OMISION_CONTROLADOS}
    otros = 0
    for omision in omisiones or []:
        motivo = omision.get("motivo") or "OTROS"
        total = int(omision.get("total") or 0)
        if motivo in conteos:
            conteos[motivo] += total
        else:
            otros += total
    conteos["OTROS"] = otros
    return [{"motivo": motivo, "total": total} for motivo, total in conteos.items() if total > 0]


def _limpiar_filtros(filtros):
    claves = ("fecha_desde", "fecha_hasta", "tarea", "tipo_evento", "decision", "motivo", "worker", "texto")
    return {clave: str(filtros.get(clave) or "").strip() for clave in claves}


def _per_page_seguro(per_page):
    try:
        valor = int(per_page or 25)
    except ValueError:
        return 25
    return valor if valor in PER_PAGE_OPCIONES else 25


def _page_segura(page):
    try:
        return max(1, int(page or 1))
    except ValueError:
        return 1


def _valor_tarea(tarea, clave):
    if not tarea:
        return None
    if isinstance(tarea, dict):
        return tarea.get(clave)
    return getattr(tarea, clave, None)


def _bool_o_none(valor):
    if valor is None:
        return None
    return 1 if bool(valor) else 0


def _nombre_feriado(feriado):
    if not feriado:
        return None
    if isinstance(feriado, dict):
        return feriado.get("nombre")
    return getattr(feriado, "nombre", None)


def _estado_scheduler(configuracion):
    if not configuracion:
        return None
    if configuracion.get("modo_mantenimiento"):
        return "MODO_MANTENIMIENTO"
    if not configuracion.get("scheduler_activo"):
        return "SCHEDULER_INACTIVO"
    if not configuracion.get("permitir_ejecucion_automatica"):
        return "EJECUCION_AUTOMATICA_DESHABILITADA"
    return "ACTIVO"
