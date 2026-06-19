import json
from datetime import datetime

from app.repositorios.repositorio_tareas import (
    actualizar_tarea,
    asegurar_snapshots_tarea,
    buscar_duplicado_tarea,
    cambiar_estado_tarea,
    crear_tarea,
    existe_ejecucion_en_curso_tarea,
    listar_catalogo,
    listar_tareas,
    marcar_tarea_eliminada_operativa,
    obtener_tarea,
)
from app.servicios.servicio_logs_sistema import registrar_log_sistema
from app.servicios.servicio_auditoria import registrar_auditoria
from app.servicios.servicio_duplicados import (
    MENSAJE_DUPLICADO_SQL,
    es_error_duplicado_sql,
    registrar_bloqueo_duplicado,
    validar_sin_duplicado,
)


TIPOS_PROGRAMACION = ("MANUAL", "DIARIA", "SEMANAL", "MENSUAL", "FECHA_ESPECIFICA")
MODOS_EJECUCION = ("UNA_VEZ", "INTERVALO")
DIAS_SEMANA = ("LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO")


def obtener_catalogos_tareas():
    return {
        "clientes": listar_catalogo("dbo.clientes", "id_cliente", "nombre_cliente"),
        "categorias": listar_catalogo("dbo.categorias", "id_categoria", "nombre_categoria"),
        "tipos": listar_catalogo("dbo.tipos", "id_tipo", "nombre_tipo"),
        "tipos_programacion": TIPOS_PROGRAMACION,
        "modos_ejecucion": MODOS_EJECUCION,
        "dias_semana": DIAS_SEMANA,
    }


def listar_tareas_admin(filtros=None):
    tareas = listar_tareas(filtros)
    for tarea in tareas:
        tarea["resumen_programacion"] = resumir_programacion(tarea)
        _enriquecer_disponibilidad_ejecucion(tarea)
    return tareas


def obtener_tarea_admin(id_tarea):
    tarea = obtener_tarea(id_tarea)
    if tarea and tarea.get("dias_semana"):
        tarea["dias_semana_lista"] = tarea["dias_semana"].split(",")
    return tarea


def validar_tarea(datos, id_tarea=None, usuario_accion=None):
    errores = []
    nombre = datos.get("nombre_tarea", "").strip()
    id_cliente = datos.get("id_cliente")
    id_categoria = datos.get("id_categoria")
    id_tipo = datos.get("id_tipo")

    if not nombre:
        errores.append("El nombre de la tarea es obligatorio.")
    if not id_cliente:
        errores.append("Debes seleccionar un cliente.")
    if not id_categoria:
        errores.append("Debes seleccionar una categoria.")
    if not id_tipo:
        errores.append("Debes seleccionar un tipo.")

    if nombre and id_cliente and id_categoria and id_tipo:
        mensaje = validar_sin_duplicado(
            buscar_duplicado_tarea(nombre, id_cliente, id_categoria, id_tipo, id_tarea),
            "tareas",
            usuario_accion,
            valores={
                "nombre_tarea": nombre,
                "id_cliente": id_cliente,
                "id_categoria": id_categoria,
                "id_tipo": id_tipo,
            },
            modulo="TAREAS",
        )
        if mensaje:
            errores.append(mensaje)

    errores.extend(_validar_programacion(datos))
    return errores


def crear_tarea_admin(datos, usuario_accion):
    errores = validar_tarea(datos, usuario_accion=usuario_accion)
    if errores:
        registrar_log_sistema(
            "TAREA_VALIDACION_ERROR",
            "TAREAS",
            "Error controlado al validar programacion de tarea.",
            usuario=usuario_accion,
            valor_nuevo="; ".join(errores),
            nivel="WARNING",
        )
        return False, errores, None

    datos_tarea, datos_programacion = _preparar_datos(datos, usuario_accion)
    try:
        id_tarea = crear_tarea(datos_tarea, datos_programacion)
    except Exception as error:
        if es_error_duplicado_sql(error):
            registrar_bloqueo_duplicado(
                "tareas",
                usuario_accion,
                MENSAJE_DUPLICADO_SQL,
                nombre_entidad=datos_tarea["nombre_tarea"],
                valores={
                    "nombre_tarea": datos_tarea["nombre_tarea"],
                    "id_cliente": datos_tarea["id_cliente"],
                    "id_categoria": datos_tarea["id_categoria"],
                    "id_tipo": datos_tarea["id_tipo"],
                },
                modulo="TAREAS",
            )
            return False, [MENSAJE_DUPLICADO_SQL], None
        raise
    registrar_log_sistema("TAREA_CREADA", "TAREAS", f"Tarea creada: {datos_tarea['nombre_tarea']}.", usuario=usuario_accion)
    registrar_log_sistema("PROGRAMACION_CREADA", "TAREAS", f"Programacion creada para tarea: {datos_tarea['nombre_tarea']}.", usuario=usuario_accion)
    registrar_auditoria(
        "CREAR",
        "tareas",
        id_entidad=id_tarea,
        nombre_entidad=datos_tarea["nombre_tarea"],
        descripcion=f"Tarea creada: {datos_tarea['nombre_tarea']}.",
        valores_despues={"tarea": datos_tarea, "programacion": datos_programacion},
        modulo="TAREAS",
        usuario=usuario_accion,
    )
    return True, ["Tarea creada correctamente."], id_tarea


def actualizar_tarea_admin(id_tarea, datos, usuario_accion):
    actual = obtener_tarea(id_tarea)
    if not actual:
        return False, ["Tarea no encontrada."]

    errores = validar_tarea(datos, id_tarea, usuario_accion)
    if errores:
        registrar_log_sistema(
            "TAREA_VALIDACION_ERROR",
            "TAREAS",
            "Error controlado al validar programacion de tarea.",
            usuario=usuario_accion,
            valor_nuevo="; ".join(errores),
            nivel="WARNING",
        )
        return False, errores

    datos_tarea, datos_programacion = _preparar_datos(datos, usuario_accion)
    if not _hay_cambios_tarea(actual, datos_tarea, datos_programacion):
        return False, ["No hay cambios para guardar."]

    try:
        actualizar_tarea(id_tarea, datos_tarea, datos_programacion)
    except Exception as error:
        if es_error_duplicado_sql(error):
            registrar_bloqueo_duplicado(
                "tareas",
                usuario_accion,
                MENSAJE_DUPLICADO_SQL,
                id_entidad=id_tarea,
                nombre_entidad=actual["nombre_tarea"],
                valores={
                    "nombre_tarea": datos_tarea["nombre_tarea"],
                    "id_cliente": datos_tarea["id_cliente"],
                    "id_categoria": datos_tarea["id_categoria"],
                    "id_tipo": datos_tarea["id_tipo"],
                },
                modulo="TAREAS",
            )
            return False, [MENSAJE_DUPLICADO_SQL]
        raise
    registrar_log_sistema("TAREA_EDITADA", "TAREAS", f"Tarea editada: {datos_tarea['nombre_tarea']}.", usuario=usuario_accion, valor_anterior=str(actual))
    registrar_log_sistema("PROGRAMACION_EDITADA", "TAREAS", f"Programacion editada para tarea: {datos_tarea['nombre_tarea']}.", usuario=usuario_accion)
    registrar_auditoria(
        "EDITAR",
        "tareas",
        id_entidad=id_tarea,
        nombre_entidad=datos_tarea["nombre_tarea"],
        descripcion=f"Tarea editada: {datos_tarea['nombre_tarea']}.",
        valores_antes=actual,
        valores_despues={"tarea": datos_tarea, "programacion": datos_programacion},
        modulo="TAREAS",
        usuario=usuario_accion,
    )
    return True, ["Tarea actualizada correctamente."]


def cambiar_estado_tarea_admin(id_tarea, activo, usuario_accion):
    tarea = obtener_tarea(id_tarea)
    if not tarea:
        return False, "Tarea no encontrada."
    cambiar_estado_tarea(id_tarea, activo, usuario_accion)
    accion = "TAREA_ACTIVADA" if activo else "TAREA_DESACTIVADA"
    registrar_log_sistema(accion, "TAREAS", f"Estado actualizado para tarea: {tarea['nombre_tarea']}.", usuario=usuario_accion)
    registrar_auditoria(
        "ACTIVAR" if activo else "DESACTIVAR",
        "tareas",
        id_entidad=id_tarea,
        nombre_entidad=tarea["nombre_tarea"],
        descripcion=f"Estado actualizado para tarea: {tarea['nombre_tarea']}.",
        valores_antes={"activo": tarea.get("activo"), "estado_tarea": tarea.get("estado_tarea")},
        valores_despues={"activo": 1 if activo else 0, "estado_tarea": "ACTIVA" if activo else "INACTIVA"},
        modulo="TAREAS",
        usuario=usuario_accion,
    )
    return True, "Tarea activada correctamente." if activo else "Tarea desactivada correctamente."


def eliminar_tarea_admin(id_tarea, usuario_accion):
    tarea = obtener_tarea(id_tarea)
    if not tarea:
        return False, "Tarea no encontrada."

    if existe_ejecucion_en_curso_tarea(id_tarea):
        mensaje = "No se puede borrar porque existe una ejecucion en curso. Verifique o detenga la ejecucion antes de borrar."
        registrar_log_sistema(
            "TAREA_BORRADO_BLOQUEADO_EN_EJECUCION",
            "TAREAS",
            f"Intento de borrar tarea con ejecucion en curso: {tarea['nombre_tarea']}.",
            usuario=usuario_accion,
            valor_anterior=str({"id_tarea": id_tarea}),
            nivel="WARNING",
        )
        registrar_auditoria(
            "BLOQUEO_ELIMINAR_TAREA_EN_EJECUCION",
            "tareas",
            id_entidad=id_tarea,
            nombre_entidad=tarea["nombre_tarea"],
            descripcion="Intento bloqueado de borrar tarea con ejecucion en curso.",
            valores_antes={"id_tarea": id_tarea},
            resultado="BLOQUEADO",
            modulo="TAREAS",
            usuario=usuario_accion,
        )
        return False, mensaje

    asegurar_snapshots_tarea(id_tarea)
    marcar_tarea_eliminada_operativa(
        id_tarea,
        usuario_accion,
        "Borrado operativo seguro. Eliminacion permanente disponible solo desde Papelera operativa.",
    )
    registrar_log_sistema(
        "TAREA_BORRADA_OPERATIVA",
        "TAREAS",
        f"Tarea retirada de operacion conservando historial: {tarea['nombre_tarea']}.",
        usuario=usuario_accion,
        valor_anterior=str({"id_tarea": id_tarea}),
    )
    registrar_auditoria(
        "BORRAR_OPERATIVO",
        "tareas",
        id_entidad=id_tarea,
        nombre_entidad=tarea["nombre_tarea"],
        descripcion=f"Tarea retirada de operacion conservando historial: {tarea['nombre_tarea']}.",
        valores_antes=tarea,
        valores_despues={"eliminado_operativo": 1, "activo": 0},
        modulo="TAREAS",
        usuario=usuario_accion,
    )
    return True, "Tarea borrada de la operacion y enviada a Papelera operativa. El historial de ejecuciones se conserva."


def _validar_programacion(datos):
    errores = []
    tipo = datos.get("tipo_programacion", "MANUAL")
    modo = datos.get("modo_ejecucion_dia", "UNA_VEZ")

    if tipo not in TIPOS_PROGRAMACION:
        errores.append("Tipo de programacion no valido.")
        return errores

    if tipo == "MANUAL":
        return errores

    if modo not in MODOS_EJECUCION:
        errores.append("Modo de ejecucion no valido.")
        return errores

    dias_semana = datos.getlist("dias_semana") if hasattr(datos, "getlist") else datos.get("dias_semana", [])
    if tipo == "SEMANAL" and not dias_semana:
        errores.append("La programacion semanal requiere al menos un dia.")

    if tipo == "MENSUAL":
        try:
            dia_mes = int(datos.get("dia_mes", ""))
            if dia_mes < 1 or dia_mes > 31:
                errores.append("El dia del mes debe estar entre 1 y 31.")
        except ValueError:
            errores.append("La programacion mensual requiere dia del mes.")

    if tipo == "FECHA_ESPECIFICA":
        if not datos.get("fecha_especifica"):
            errores.append("La programacion por fecha especifica requiere fecha.")
        else:
            try:
                datetime.strptime(datos["fecha_especifica"], "%Y-%m-%d")
            except ValueError:
                errores.append("La fecha especifica no tiene formato valido.")

    if modo == "UNA_VEZ":
        if not datos.get("hora_ejecucion"):
            errores.append("El modo una vez requiere hora de ejecucion.")
    elif modo == "INTERVALO":
        try:
            intervalo = int(datos.get("intervalo_minutos", "0"))
            if intervalo <= 0:
                errores.append("El intervalo debe ser mayor a 0.")
        except ValueError:
            errores.append("El intervalo debe ser numerico.")

        inicio = datos.get("hora_inicio_intervalo")
        fin = datos.get("hora_fin_intervalo")
        if not inicio or not fin:
            errores.append("El modo intervalo requiere hora inicio y hora fin.")
        elif inicio >= fin:
            errores.append("La hora inicio debe ser menor que la hora fin.")

    return errores


def _preparar_datos(datos, usuario_accion):
    tipo_programacion = datos.get("tipo_programacion", "MANUAL")
    activo = 1 if datos.get("activo") else 0
    datos_tarea = {
        "nombre_tarea": datos["nombre_tarea"].strip(),
        "descripcion": datos.get("descripcion", "").strip() or None,
        "observacion_tecnica": datos.get("observacion_tecnica", "").strip() or None,
        "id_cliente": int(datos["id_cliente"]),
        "id_categoria": int(datos["id_categoria"]),
        "id_tipo": int(datos["id_tipo"]),
        "tipo_tarea": "MANUAL" if tipo_programacion == "MANUAL" else "PROGRAMADA",
        "estado_tarea": "ACTIVA" if activo else "INACTIVA",
        "permite_ejecucion_manual": 1,
        "usuario_accion": usuario_accion,
        "activo": activo,
    }

    modo = None if tipo_programacion == "MANUAL" else datos.get("modo_ejecucion_dia", "UNA_VEZ")
    dias = ",".join(datos.getlist("dias_semana")) if hasattr(datos, "getlist") else ""
    datos_programacion = {
        "tipo_programacion": tipo_programacion,
        "modo_ejecucion_dia": modo,
        "hora_ejecucion": datos.get("hora_ejecucion") if modo == "UNA_VEZ" else None,
        "dias_semana": dias if tipo_programacion == "SEMANAL" and dias else None,
        "dia_mes": int(datos["dia_mes"]) if tipo_programacion == "MENSUAL" and datos.get("dia_mes") else None,
        "fecha_especifica": datos.get("fecha_especifica") if tipo_programacion == "FECHA_ESPECIFICA" else None,
        "intervalo_minutos": int(datos["intervalo_minutos"]) if modo == "INTERVALO" and datos.get("intervalo_minutos") else None,
        "hora_inicio_intervalo": datos.get("hora_inicio_intervalo") if modo == "INTERVALO" else None,
        "hora_fin_intervalo": datos.get("hora_fin_intervalo") if modo == "INTERVALO" else None,
        "ejecutar_en_feriados": 1 if datos.get("ejecutar_en_feriados") else 0,
        "configuracion_json": json.dumps({"fase": "6", "sin_scheduler": True}),
    }
    return datos_tarea, datos_programacion


def _hay_cambios_tarea(actual, datos_tarea, datos_programacion):
    return _normalizar_actual(actual) != _normalizar_nuevo(datos_tarea, datos_programacion)


def _enriquecer_disponibilidad_ejecucion(tarea):
    motivo = None

    if not bool(tarea.get("tarea_activo", tarea.get("activo"))):
        motivo = "Tarea inactiva"
    elif bool(tarea.get("tarea_eliminada_operativo")):
        motivo = "Tarea borrada operativamente"
    elif int(tarea.get("ejecuciones_en_curso") or 0) > 0:
        motivo = "Ejecucion en curso"
    elif not tarea.get("id_script"):
        motivo = "Sin script asociado"
    elif bool(tarea.get("script_eliminado_operativo")):
        motivo = "Script borrado operativamente"
    elif not bool(tarea.get("script_activo")):
        motivo = "Script inactivo"
    elif not tarea.get("id_version_activa_script") or not tarea.get("id_version_activa"):
        motivo = "Sin version activa"
    elif bool(tarea.get("version_eliminada_operativo")):
        motivo = "Version borrada operativamente"
    elif not bool(tarea.get("version_es_activa")) or tarea.get("estado_version_activa") != "ACTIVA":
        motivo = "Version no disponible"

    tarea["ejecutable"] = motivo is None
    tarea["motivo_no_ejecutable"] = motivo
    tarea["disponibilidad_ejecucion"] = "Ejecutable" if motivo is None else f"No ejecutable: {motivo}"


def _normalizar_actual(actual):
    tipo = actual.get("tipo_programacion") or "MANUAL"
    modo = "" if tipo == "MANUAL" else _texto(actual.get("modo_ejecucion_dia"))
    return {
        "nombre_tarea": _texto(actual.get("nombre_tarea")),
        "descripcion": _texto(actual.get("descripcion")),
        "id_cliente": _texto(actual.get("id_cliente")),
        "id_categoria": _texto(actual.get("id_categoria")),
        "id_tipo": _texto(actual.get("id_tipo")),
        "observacion_tecnica": _texto(actual.get("observacion_tecnica")),
        "activo": bool(actual.get("activo")),
        "tipo_programacion": tipo,
        "modo_ejecucion_dia": modo,
        "hora_ejecucion": _hora(actual.get("hora_ejecucion")) if modo == "UNA_VEZ" else "",
        "dias_semana": _dias_ordenados(actual.get("dias_semana")) if tipo == "SEMANAL" else [],
        "dia_mes": _texto(actual.get("dia_mes")) if tipo == "MENSUAL" else "",
        "fecha_especifica": _fecha(actual.get("fecha_especifica")) if tipo == "FECHA_ESPECIFICA" else "",
        "intervalo_minutos": _texto(actual.get("intervalo_minutos")) if modo == "INTERVALO" else "",
        "hora_inicio_intervalo": _hora(actual.get("hora_inicio_intervalo")) if modo == "INTERVALO" else "",
        "hora_fin_intervalo": _hora(actual.get("hora_fin_intervalo")) if modo == "INTERVALO" else "",
        "ejecutar_en_feriados": False if tipo == "MANUAL" else bool(actual.get("ejecutar_en_feriados")),
    }


def _normalizar_nuevo(datos_tarea, datos_programacion):
    tipo = datos_programacion.get("tipo_programacion") or "MANUAL"
    modo = "" if tipo == "MANUAL" else _texto(datos_programacion.get("modo_ejecucion_dia"))
    return {
        "nombre_tarea": _texto(datos_tarea.get("nombre_tarea")),
        "descripcion": _texto(datos_tarea.get("descripcion")),
        "id_cliente": _texto(datos_tarea.get("id_cliente")),
        "id_categoria": _texto(datos_tarea.get("id_categoria")),
        "id_tipo": _texto(datos_tarea.get("id_tipo")),
        "observacion_tecnica": _texto(datos_tarea.get("observacion_tecnica")),
        "activo": bool(datos_tarea.get("activo")),
        "tipo_programacion": tipo,
        "modo_ejecucion_dia": modo,
        "hora_ejecucion": _hora(datos_programacion.get("hora_ejecucion")) if modo == "UNA_VEZ" else "",
        "dias_semana": _dias_ordenados(datos_programacion.get("dias_semana")) if tipo == "SEMANAL" else [],
        "dia_mes": _texto(datos_programacion.get("dia_mes")) if tipo == "MENSUAL" else "",
        "fecha_especifica": _fecha(datos_programacion.get("fecha_especifica")) if tipo == "FECHA_ESPECIFICA" else "",
        "intervalo_minutos": _texto(datos_programacion.get("intervalo_minutos")) if modo == "INTERVALO" else "",
        "hora_inicio_intervalo": _hora(datos_programacion.get("hora_inicio_intervalo")) if modo == "INTERVALO" else "",
        "hora_fin_intervalo": _hora(datos_programacion.get("hora_fin_intervalo")) if modo == "INTERVALO" else "",
        "ejecutar_en_feriados": False if tipo == "MANUAL" else bool(datos_programacion.get("ejecutar_en_feriados")),
    }


def _texto(valor):
    if valor is None:
        return ""
    return " ".join(str(valor).strip().split())


def _fecha(valor):
    return str(valor)[:10] if valor else ""


def _dias_ordenados(valor):
    if not valor:
        return []
    if isinstance(valor, str):
        return sorted(dia.strip() for dia in valor.split(",") if dia.strip())
    return sorted(str(dia).strip() for dia in valor if str(dia).strip())


def resumir_programacion(tarea):
    tipo = tarea.get("tipo_programacion") or "MANUAL"
    modo = tarea.get("modo_ejecucion_dia")
    if tipo == "MANUAL":
        return "Manual"

    prefijos = {
        "DIARIA": "Diaria",
        "SEMANAL": "Semanal " + _dias_legibles(tarea.get("dias_semana")),
        "MENSUAL": f"Mensual dia {tarea.get('dia_mes')}",
        "FECHA_ESPECIFICA": f"Fecha especifica {tarea.get('fecha_especifica')}",
    }
    prefijo = prefijos.get(tipo, tipo)
    if modo == "INTERVALO":
        return f"{prefijo} cada {tarea.get('intervalo_minutos')} min entre {_hora(tarea.get('hora_inicio_intervalo'))} y {_hora(tarea.get('hora_fin_intervalo'))}"
    return f"{prefijo} a las {_hora(tarea.get('hora_ejecucion'))}"


def _hora(valor):
    return str(valor)[:5] if valor else "-"


def _dias_legibles(valor):
    if not valor:
        return ""
    nombres = {
        "LUNES": "lunes",
        "MARTES": "martes",
        "MIERCOLES": "miercoles",
        "JUEVES": "jueves",
        "VIERNES": "viernes",
        "SABADO": "sabado",
        "DOMINGO": "domingo",
    }
    return ", ".join(nombres.get(dia, dia.lower()) for dia in valor.split(","))
