from datetime import datetime

from app.repositorios.repositorio_feriados import (
    actualizar_feriado_api_nager,
    crear_feriado_api_nager,
    obtener_feriado_por_fecha_pais,
)
from app.repositorios.repositorio_reglas_feriados import obtener_regla_irrenunciable
from app.servicios.cliente_nager_date import ErrorNagerDate, consultar_nager_feriados
from app.servicios.servicio_logs_sistema import registrar_log_sistema


ACCION_NUEVO = "NUEVO"
ACCION_ACTUALIZAR = "ACTUALIZAR"
ACCION_SIN_CAMBIOS = "SIN_CAMBIOS"
ACCION_MANUAL = "MANUAL_NO_SOBRESCRIBE"
ACCION_INACTIVO = "INACTIVO_REVISION"
ACCION_ERROR = "ERROR"


def preparar_preview_sincronizacion(anio, pais, usuario=None):
    anio, pais = _validar_parametros(anio, pais)
    registrar_log_sistema(
        "FERIADOS_SYNC_CONSULTA",
        "FERIADOS",
        f"Consulta de sincronizacion solicitada para {pais} {anio}.",
        usuario=usuario,
    )

    try:
        datos_api = consultar_nager_feriados(anio, pais)
    except ErrorNagerDate as error:
        registrar_log_sistema(
            "FERIADOS_SYNC_API_ERROR",
            "FERIADOS",
            str(error),
            usuario=usuario,
            nivel="ERROR",
        )
        return False, [str(error)], None

    if not datos_api:
        return False, ["Nager.Date no retorno feriados para los parametros indicados."], None

    feriados_preview = []
    resumen = _resumen_vacio()
    for item_api in datos_api:
        try:
            normalizado = normalizar_feriado_nager(item_api, pais)
            local = obtener_feriado_por_fecha_pais(normalizado["fecha"], normalizado["pais"])
            item_preview = clasificar_feriado_api_vs_local(normalizado, local)
        except Exception as error:
            item_preview = {
                "accion": ACCION_ERROR,
                "accion_texto": "Error",
                "fecha": str(item_api.get("date") or ""),
                "pais": pais,
                "nombre_api": str(item_api.get("localName") or item_api.get("name") or ""),
                "nombre_local": None,
                "tipo": None,
                "irrenunciable": False,
                "origen_local": None,
                "activo_local": None,
                "mensaje": f"No fue posible normalizar el feriado: {error.__class__.__name__}.",
                "api": {},
            }
        feriados_preview.append(item_preview)
        resumen[_clave_resumen(item_preview["accion"])] += 1

    preview = {"anio": anio, "pais": pais, "feriados_preview": feriados_preview, "resumen": resumen}
    registrar_log_sistema(
        "FERIADOS_SYNC_PREVIEW",
        "FERIADOS",
        f"Vista previa generada para {pais} {anio}.",
        usuario=usuario,
        valor_nuevo=str(resumen),
    )
    return True, ["Vista previa generada correctamente."], preview


def aplicar_sincronizacion(preview, usuario=None):
    if not preview or not isinstance(preview.get("feriados_preview"), list):
        return False, ["No existe una vista previa valida para aplicar."], None

    resumen = _resumen_vacio()
    errores = []
    for item in preview["feriados_preview"]:
        api = item.get("api") or {}
        if not api:
            resumen["errores"] += 1
            continue

        try:
            local = obtener_feriado_por_fecha_pais(api["fecha"], api["pais"])
            clasificado = clasificar_feriado_api_vs_local(api, local)
            accion = clasificado["accion"]
            datos = {**api, "usuario": usuario}
            if accion == ACCION_NUEVO:
                crear_feriado_api_nager(datos)
            elif accion == ACCION_ACTUALIZAR and local:
                actualizar_feriado_api_nager(local["id_feriado"], datos)
            resumen[_clave_resumen(accion)] += 1
        except Exception as error:
            errores.append(f"{api.get('fecha', '-')}: {error.__class__.__name__}")
            resumen["errores"] += 1

    registrar_log_sistema(
        "FERIADOS_SYNC_APLICADA",
        "FERIADOS",
        f"Sincronizacion de feriados aplicada para {preview.get('pais')} {preview.get('anio')}.",
        usuario=usuario,
        valor_nuevo=str({**resumen, "errores_detalle": errores[:5]}),
        nivel="ERROR" if errores else "INFO",
    )
    mensajes = ["Sincronizacion aplicada correctamente." if not errores else "Sincronizacion aplicada con errores controlados."]
    return True, mensajes, {"resumen": resumen, "errores": errores}


def normalizar_feriado_nager(item, pais_esperado):
    fecha = str(item.get("date") or "").strip()
    if not fecha:
        raise ValueError("Fecha vacia.")
    datetime.strptime(fecha, "%Y-%m-%d")
    pais = str(item.get("countryCode") or pais_esperado or "CL").strip().upper()
    nombre_local = str(item.get("localName") or item.get("name") or "").strip()
    nombre_ingles = str(item.get("name") or "").strip()
    tipos = item.get("types") or []
    tipo = str(tipos[0]).strip() if isinstance(tipos, list) and tipos else None
    irrenunciable = obtener_irrenunciable_por_regla(fecha, pais)
    global_api = item.get("global")
    fixed = item.get("fixed")
    observacion = f"Sincronizado desde Nager.Date. Nombre ingles: {nombre_ingles}. Global: {global_api}. Fixed: {fixed}."
    return {
        "fecha": fecha,
        "nombre": nombre_local[:200],
        "pais": pais[:10],
        "tipo": tipo[:50] if tipo else None,
        "irrenunciable": irrenunciable,
        "observacion": observacion[:500],
        "nombre_ingles": nombre_ingles,
        "global": global_api,
        "fixed": fixed,
    }


def obtener_irrenunciable_por_regla(fecha, pais="CL"):
    fecha_dt = datetime.strptime(str(fecha)[:10], "%Y-%m-%d")
    regla = obtener_regla_irrenunciable(str(pais or "CL").upper(), fecha_dt.month, fecha_dt.day)
    return bool(regla and regla.get("irrenunciable"))


def clasificar_feriado_api_vs_local(api_item, local_item):
    if not local_item:
        return _preview_item(api_item, None, ACCION_NUEVO, "Nuevo", "Se insertara.")

    if not bool(local_item.get("activo")):
        return _preview_item(api_item, local_item, ACCION_INACTIVO, "Existe inactivo - requiere revision", "No se reactivara automaticamente.")

    if local_item.get("origen") == "MANUAL":
        return _preview_item(api_item, local_item, ACCION_MANUAL, "Ya existe manual - no se sobrescribe", "Manual tiene prioridad.")

    if local_item.get("origen") == "API_NAGER":
        if _requiere_actualizacion(api_item, local_item):
            return _preview_item(api_item, local_item, ACCION_ACTUALIZAR, "Se actualizara", "Se actualizaran datos API_NAGER.")
        return _preview_item(api_item, local_item, ACCION_SIN_CAMBIOS, "Sin cambios", "No requiere cambios.")

    return _preview_item(api_item, local_item, ACCION_INACTIVO, "Existe con origen no sincronizable", "Requiere revision manual.")


def validar_parametros_sincronizacion(datos):
    try:
        anio, pais = _validar_parametros(datos.get("anio"), datos.get("pais"))
        return True, [], {"anio": anio, "pais": pais}
    except ValueError as error:
        return False, [str(error)], None


def _validar_parametros(anio, pais):
    try:
        anio = int(str(anio or "").strip())
    except ValueError as error:
        raise ValueError("El ano debe ser numerico.") from error
    if anio < 2000 or anio > 2100:
        raise ValueError("El ano debe estar entre 2000 y 2100.")
    pais = str(pais or "CL").strip().upper()
    if not pais:
        raise ValueError("El pais es obligatorio.")
    if len(pais) > 10:
        raise ValueError("El pais no puede superar 10 caracteres.")
    return anio, pais


def _requiere_actualizacion(api_item, local_item):
    return any(
        [
            (local_item.get("nombre") or "") != (api_item.get("nombre") or ""),
            (local_item.get("tipo") or None) != (api_item.get("tipo") or None),
            bool(local_item.get("irrenunciable")) != bool(api_item.get("irrenunciable")),
            (local_item.get("observacion") or "") != (api_item.get("observacion") or ""),
        ]
    )


def _preview_item(api_item, local_item, accion, accion_texto, mensaje):
    return {
        "accion": accion,
        "accion_texto": accion_texto,
        "fecha": api_item["fecha"],
        "pais": api_item["pais"],
        "nombre_api": api_item["nombre"],
        "nombre_local": local_item.get("nombre") if local_item else None,
        "tipo": api_item.get("tipo"),
        "irrenunciable": bool(api_item.get("irrenunciable")),
        "origen_local": local_item.get("origen") if local_item else None,
        "activo_local": bool(local_item.get("activo")) if local_item else None,
        "mensaje": mensaje,
        "api": api_item,
    }


def _resumen_vacio():
    return {
        "nuevos": 0,
        "actualizar": 0,
        "sin_cambios": 0,
        "omitidos_manual": 0,
        "omitidos_inactivo": 0,
        "errores": 0,
    }


def _clave_resumen(accion):
    return {
        ACCION_NUEVO: "nuevos",
        ACCION_ACTUALIZAR: "actualizar",
        ACCION_SIN_CAMBIOS: "sin_cambios",
        ACCION_MANUAL: "omitidos_manual",
        ACCION_INACTIVO: "omitidos_inactivo",
        ACCION_ERROR: "errores",
    }.get(accion, "errores")
