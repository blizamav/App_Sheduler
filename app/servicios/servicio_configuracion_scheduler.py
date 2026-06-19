import json

from app.repositorios.repositorio_configuracion_scheduler import (
    actualizar_configuracion,
    crear_configuracion_default,
    obtener_configuracion_activa,
)
from app.servicios.servicio_logs_sistema import registrar_log_sistema
from app.servicios.servicio_auditoria import registrar_auditoria


def obtener_configuracion_scheduler(usuario=None):
    configuracion = obtener_configuracion_activa()
    if not configuracion:
        crear_configuracion_default(usuario or "sistema")
        configuracion = obtener_configuracion_activa()
    configuracion["advertencias"] = _advertencias(configuracion)
    return configuracion


def guardar_configuracion_scheduler(formulario, usuario):
    actual = obtener_configuracion_scheduler(usuario)
    datos = _normalizar_formulario(formulario)
    errores = _validar(datos)
    if errores:
        registrar_log_sistema(
            "SCHEDULER_CONFIG_VALIDACION_ERROR",
            "SCHEDULER",
            "; ".join(errores),
            usuario=usuario,
            nivel="WARNING",
        )
        registrar_auditoria(
            "EDITAR_CONFIG_PROGRAMADOR",
            "scheduler_config",
            id_entidad=actual.get("id_configuracion"),
            nombre_entidad=actual.get("nombre_worker_principal"),
            descripcion="Error controlado al validar configuracion del scheduler.",
            valores_antes=_snapshot_config(actual),
            valores_despues={"errores": errores, "datos": datos},
            resultado="ERROR",
            modulo="SCHEDULER",
            usuario=usuario,
        )
        return False, errores, actual

    cambios = _calcular_cambios(actual, datos)
    if not cambios:
        return False, ["No hay cambios para guardar."], actual

    try:
        actualizar_configuracion(actual["id_configuracion"], datos, usuario)
    except Exception as error:
        registrar_auditoria(
            "EDITAR_CONFIG_PROGRAMADOR",
            "scheduler_config",
            id_entidad=actual["id_configuracion"],
            nombre_entidad=actual.get("nombre_worker_principal"),
            descripcion="Error controlado al actualizar configuracion del scheduler.",
            valores_antes={c["campo"]: c["anterior"] for c in cambios},
            valores_despues={"error": error.__class__.__name__},
            resultado="ERROR",
            modulo="SCHEDULER",
            usuario=usuario,
        )
        raise
    nuevo = obtener_configuracion_scheduler(usuario)
    registrar_log_sistema(
        "SCHEDULER_CONFIG_ACTUALIZADA",
        "SCHEDULER",
        "Configuracion operativa del scheduler actualizada.",
        usuario=usuario,
        valor_anterior=json.dumps({c["campo"]: c["anterior"] for c in cambios}, ensure_ascii=False),
        valor_nuevo=json.dumps({c["campo"]: c["nuevo"] for c in cambios}, ensure_ascii=False),
    )
    for cambio in cambios:
        registrar_log_sistema(
            f"SCHEDULER_CONFIG_CAMBIO_{cambio['campo'].upper()}",
            "SCHEDULER",
            f"{cambio['campo']}: {cambio['anterior']} -> {cambio['nuevo']}",
            usuario=usuario,
        )
    registrar_auditoria(
        "CONFIGURAR",
        "configuracion_scheduler",
        id_entidad=actual["id_configuracion"],
        nombre_entidad=actual.get("nombre_worker_principal"),
        descripcion="Configuracion operativa del scheduler actualizada.",
        valores_antes={c["campo"]: c["anterior"] for c in cambios},
        valores_despues={c["campo"]: c["nuevo"] for c in cambios},
        modulo="SCHEDULER",
        usuario=usuario,
    )
    return True, ["Configuracion del scheduler actualizada correctamente."], nuevo


def _normalizar_formulario(formulario):
    return {
        "scheduler_activo": formulario.get("scheduler_activo") == "1",
        "permitir_ejecucion_automatica": formulario.get("permitir_ejecucion_automatica") == "1",
        "modo_mantenimiento": formulario.get("modo_mantenimiento") == "1",
        "intervalo_revision_segundos": _entero(formulario.get("intervalo_revision_segundos")),
        "max_ejecuciones_concurrentes": _entero(formulario.get("max_ejecuciones_concurrentes")),
        "nombre_worker_principal": (formulario.get("nombre_worker_principal") or "").strip() or None,
        "descripcion": (formulario.get("descripcion") or "").strip() or None,
    }


def _entero(valor):
    try:
        return int(str(valor or "").strip())
    except ValueError:
        return None


def _validar(datos):
    errores = []
    intervalo = datos.get("intervalo_revision_segundos")
    maximo = datos.get("max_ejecuciones_concurrentes")
    if intervalo is None:
        errores.append("El intervalo de revision es obligatorio.")
    elif intervalo < 10 or intervalo > 3600:
        errores.append("El intervalo de revision debe estar entre 10 y 3600 segundos.")
    if maximo is None:
        errores.append("El maximo de ejecuciones concurrentes es obligatorio.")
    elif maximo < 1 or maximo > 20:
        errores.append("El maximo de ejecuciones concurrentes debe estar entre 1 y 20.")
    if datos.get("nombre_worker_principal") and len(datos["nombre_worker_principal"]) > 100:
        errores.append("El nombre del worker no puede superar 100 caracteres.")
    if datos.get("descripcion") and len(datos["descripcion"]) > 500:
        errores.append("La descripcion no puede superar 500 caracteres.")
    return errores


def _calcular_cambios(actual, datos):
    campos = (
        "scheduler_activo",
        "permitir_ejecucion_automatica",
        "modo_mantenimiento",
        "intervalo_revision_segundos",
        "max_ejecuciones_concurrentes",
        "nombre_worker_principal",
        "descripcion",
    )
    cambios = []
    for campo in campos:
        anterior = actual.get(campo)
        nuevo = datos.get(campo)
        if isinstance(anterior, bool) or isinstance(nuevo, bool):
            anterior = bool(anterior)
            nuevo = bool(nuevo)
        if anterior != nuevo:
            cambios.append({"campo": campo, "anterior": anterior, "nuevo": nuevo})
    return cambios


def _snapshot_config(configuracion):
    return {
        "scheduler_activo": configuracion.get("scheduler_activo"),
        "permitir_ejecucion_automatica": configuracion.get("permitir_ejecucion_automatica"),
        "modo_mantenimiento": configuracion.get("modo_mantenimiento"),
        "intervalo_revision_segundos": configuracion.get("intervalo_revision_segundos"),
        "max_ejecuciones_concurrentes": configuracion.get("max_ejecuciones_concurrentes"),
        "nombre_worker_principal": configuracion.get("nombre_worker_principal"),
    }


def _advertencias(configuracion):
    advertencias = []
    if configuracion.get("modo_mantenimiento"):
        advertencias.append("El modo mantenimiento esta activo. El worker futuro no debera iniciar ejecuciones automaticas.")
    if not configuracion.get("scheduler_activo"):
        advertencias.append("Scheduler desactivado.")
    if configuracion.get("scheduler_activo") and not configuracion.get("permitir_ejecucion_automatica"):
        advertencias.append("El scheduler esta activo, pero la ejecucion automatica esta deshabilitada.")
    return advertencias
