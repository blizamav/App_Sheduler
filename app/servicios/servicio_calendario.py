from datetime import datetime

from app.repositorios.repositorio_feriados import (
    actualizar_feriado,
    cambiar_estado_feriado,
    crear_feriado,
    eliminar_feriado,
    existe_feriado_activo,
    listar_feriados as repo_listar_feriados,
    obtener_feriado_por_fecha,
    obtener_feriado_por_id,
)
from app.servicios.servicio_logs_sistema import registrar_log_sistema


def es_feriado(fecha, pais="CL"):
    return obtener_feriado(fecha, pais) is not None


def obtener_feriado(fecha, pais="CL"):
    try:
        return obtener_feriado_por_fecha(_fecha_texto(fecha), _pais(pais))
    except Exception as error:
        registrar_log_sistema(
            "CALENDARIO_CONSULTA_ERROR",
            "FERIADOS",
            "Error controlado al consultar calendario local de feriados.",
            usuario="sistema",
            valor_nuevo=str(error),
            nivel="WARNING",
        )
        return None


def validar_fecha_laboral(fecha, pais="CL"):
    feriado = obtener_feriado(fecha, pais)
    if feriado:
        return {"es_laboral": False, "es_feriado": True, "feriado": feriado}
    return {"es_laboral": True, "es_feriado": False, "feriado": None}


def listar_feriados(filtros=None):
    return repo_listar_feriados(filtros)


def obtener_feriado_admin(id_feriado):
    return obtener_feriado_por_id(id_feriado)


def guardar_feriado(datos, usuario, id_feriado=None):
    actual = obtener_feriado_por_id(id_feriado) if id_feriado else None
    if id_feriado and not actual:
        return False, ["Feriado no encontrado."], None

    normalizados = _normalizar(datos, usuario)
    errores = _validar(normalizados, id_feriado)
    if errores:
        return False, errores, actual

    if actual and _sin_cambios(actual, normalizados):
        return False, ["No hay cambios para guardar."], actual

    if id_feriado:
        actualizar_feriado(id_feriado, normalizados)
        registrar_log_sistema(
            "FERIADO_EDITADO",
            "FERIADOS",
            f"Feriado editado: {normalizados['fecha']} {normalizados['pais']}.",
            usuario=usuario,
            valor_anterior=str(actual),
            valor_nuevo=str(normalizados),
        )
        return True, ["Feriado actualizado correctamente."], obtener_feriado_por_id(id_feriado)

    nuevo_id = crear_feriado(normalizados)
    registrar_log_sistema(
        "FERIADO_CREADO",
        "FERIADOS",
        f"Feriado creado: {normalizados['fecha']} {normalizados['pais']}.",
        usuario=usuario,
        valor_nuevo=str(normalizados),
    )
    return True, ["Feriado creado correctamente."], obtener_feriado_por_id(nuevo_id)


def cambiar_estado_feriado_admin(id_feriado, activo, usuario):
    actual = obtener_feriado_por_id(id_feriado)
    if not actual:
        return False, "Feriado no encontrado."
    if activo and existe_feriado_activo(actual["fecha"], actual["pais"], id_feriado):
        return False, "Ya existe un feriado activo para esa fecha y pais."
    cambiar_estado_feriado(id_feriado, activo, usuario)
    accion = "FERIADO_ACTIVADO" if activo else "FERIADO_DESACTIVADO"
    registrar_log_sistema(
        accion,
        "FERIADOS",
        f"Feriado {'activado' if activo else 'desactivado'}: {actual['fecha']} {actual['pais']}.",
        usuario=usuario,
        valor_anterior=str(actual["activo"]),
        valor_nuevo=str(1 if activo else 0),
    )
    return True, "Feriado activado correctamente." if activo else "Feriado desactivado correctamente."


def eliminar_feriado_admin(id_feriado, usuario):
    actual = obtener_feriado_por_id(id_feriado)
    if not actual:
        return False, "Feriado no encontrado."
    eliminar_feriado(id_feriado)
    registrar_log_sistema(
        "FERIADO_ELIMINADO",
        "FERIADOS",
        f"Feriado eliminado definitivamente: {actual['fecha']} {actual['pais']}.",
        usuario=usuario,
        valor_anterior=str(actual),
    )
    return True, "Feriado eliminado definitivamente."


def _normalizar(datos, usuario):
    return {
        "fecha": (datos.get("fecha") or "").strip(),
        "nombre": (datos.get("nombre") or "").strip(),
        "tipo": (datos.get("tipo") or "").strip() or None,
        "pais": _pais(datos.get("pais") or "CL"),
        "irrenunciable": datos.get("irrenunciable") == "1" or datos.get("irrenunciable") is True,
        "activo": datos.get("activo") == "1" or datos.get("activo") is True,
        "observacion": (datos.get("observacion") or "").strip() or None,
        "usuario": usuario,
    }


def _validar(datos, id_feriado=None):
    errores = []
    if not datos["fecha"]:
        errores.append("La fecha es obligatoria.")
    else:
        try:
            datetime.strptime(datos["fecha"], "%Y-%m-%d")
        except ValueError:
            errores.append("La fecha no tiene formato valido.")
    if not datos["nombre"]:
        errores.append("El nombre es obligatorio.")
    if not datos["pais"]:
        errores.append("El pais es obligatorio.")
    if len(datos["nombre"]) > 200:
        errores.append("El nombre no puede superar 200 caracteres.")
    if datos.get("tipo") and len(datos["tipo"]) > 50:
        errores.append("El tipo no puede superar 50 caracteres.")
    if len(datos["pais"]) > 10:
        errores.append("El pais no puede superar 10 caracteres.")
    if datos.get("observacion") and len(datos["observacion"]) > 500:
        errores.append("La observacion no puede superar 500 caracteres.")
    if not errores and datos["activo"] and existe_feriado_activo(datos["fecha"], datos["pais"], id_feriado):
        errores.append("Ya existe un feriado activo para esa fecha y pais.")
    return errores


def _sin_cambios(actual, datos):
    return {
        "fecha": _fecha_texto(actual.get("fecha")),
        "nombre": actual.get("nombre") or "",
        "tipo": actual.get("tipo") or None,
        "pais": actual.get("pais") or "CL",
        "irrenunciable": bool(actual.get("irrenunciable")),
        "activo": bool(actual.get("activo")),
        "observacion": actual.get("observacion") or None,
    } == {
        "fecha": datos["fecha"],
        "nombre": datos["nombre"],
        "tipo": datos.get("tipo"),
        "pais": datos["pais"],
        "irrenunciable": bool(datos.get("irrenunciable")),
        "activo": bool(datos.get("activo")),
        "observacion": datos.get("observacion"),
    }


def _fecha_texto(fecha):
    return str(fecha)[:10]


def _pais(pais):
    return str(pais or "CL").strip().upper()
