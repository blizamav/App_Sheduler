from dataclasses import dataclass

from flask import current_app

from app.servicios.servicio_control_runtime import (
    adquirir_lock_factory_reset,
    actualizar_lock_factory_reset,
    liberar_lock_factory_reset,
    obtener_estado_factory_reset,
    registrar_marca_factory_reset_completado,
    registrar_evento_factory_reset,
)
from app.servicios.servicio_factory_reset import (
    diagnosticar_operacion_factory_reset,
    validar_manifiesto_bootstrap,
    validar_super_admin_env,
)
from app.servicios.servicio_factory_reset_filesystem import (
    limpiar_roots_factory_reset,
    preparar_roots_factory_reset,
    rollback_roots_factory_reset,
    validar_roots_vacios,
)
from app.servicios.servicio_factory_reset_sql import (
    EjecutorSQLFactoryReset,
    ErrorFactoryResetSQL,
    derivar_bases_temporales_factory_reset,
    validar_configuracion_factory_reset_sql,
)


FRASE_CONFIRMACION_FACTORY_RESET = "RESTABLECER APP SCHEDULER"


@dataclass
class ContextoFactoryReset:
    id_operacion: str
    usuario: str
    origen_usuario: str
    base_actual: str
    base_nueva: str
    base_anterior: str
    base_fallida: str
    manifiesto: dict


def ejecutar_factory_reset(datos_preview, usuario, origen_usuario="BD", ejecutor=None):
    id_operacion = str((datos_preview or {}).get("id_operacion") or "")
    resultado_precheck = _precheck_final(datos_preview, ejecutor=ejecutor)
    if not resultado_precheck["ok"]:
        return _resultado_error(id_operacion, resultado_precheck["mensaje"], "PRECHECK")

    contexto = _crear_contexto(id_operacion, usuario, origen_usuario, resultado_precheck["manifiesto"])
    adquirido, estado_lock = adquirir_lock_factory_reset(
        "FACTORY_RESET_PREPARANDO",
        f"WEB:{contexto.origen_usuario}",
        id_operacion=contexto.id_operacion,
    )
    if not adquirido:
        return _resultado_error(contexto.id_operacion, "Existe otra operacion Factory Reset activa.", estado_lock.get("fase"))

    motor = None
    operaciones_fs = []
    filesystem_aplicado = False
    intercambio_iniciado = False
    housekeeping_iniciado = False
    rollback_sql_ok = None
    rollback_fs_ok = None
    try:
        _avanzar(contexto, "LOCK_ADQUIRIDO", 8, "Lock global adquirido.")
        segundo_precheck = _precheck_final(datos_preview, lock_propio=contexto.id_operacion, ejecutor=ejecutor)
        if not segundo_precheck["ok"]:
            raise RuntimeError(segundo_precheck["mensaje"])

        _avanzar(contexto, "BLOQUEANDO_ACTIVIDAD", 12, "Actividad nueva bloqueada; condiciones recalculadas.")
        operaciones_fs = preparar_roots_factory_reset(contexto.id_operacion)
        motor = ejecutor or EjecutorSQLFactoryReset()
        if not motor.existe_base(contexto.base_actual):
            raise RuntimeError("La base actual no existe segun la conexion administrativa.")
        residuos_previos = motor.listar_bases_residuales(contexto.base_actual)
        if residuos_previos:
            raise RuntimeError("Existen bases residuales de una operacion Factory Reset anterior.")
        for nombre in (contexto.base_nueva, contexto.base_anterior, contexto.base_fallida):
            if motor.existe_base(nombre):
                raise RuntimeError("Existe una base residual de esta operacion; se requiere revision manual.")

        _avanzar(contexto, "CREANDO_BD_TEMPORAL", 20, "Creando base temporal unica.")
        _avanzar(contexto, "EJECUTANDO_BOOTSTRAP", 30, "Ejecutando manifiesto bootstrap oficial.")
        motor.ejecutar_bootstrap(contexto.base_nueva, contexto.manifiesto)

        _avanzar(contexto, "VALIDANDO_BD_TEMPORAL", 48, "Validando base temporal con script 100.")
        motor.validar_bootstrap(contexto.base_nueva, _ruta_validacion(contexto.manifiesto))
        _revalidar_antes_intercambio(contexto, operaciones_fs)

        _avanzar(contexto, "PREPARANDO_INTERCAMBIO", 58, "Verificando conexiones antes del intercambio.")
        sesiones = motor.listar_sesiones(contexto.base_actual)
        registrar_evento_factory_reset(
            contexto.id_operacion,
            "PREPARANDO_INTERCAMBIO",
            "Sesiones SQL inventariadas.",
            datos={"sesiones_detectadas": len(sesiones)},
        )

        _avanzar(contexto, "INTERCAMBIANDO_BD", 65, "Intercambiando base actual y temporal.")
        intercambio_iniciado = True
        motor.intercambiar_bases(contexto.base_actual, contexto.base_nueva, contexto.base_anterior)

        _avanzar(contexto, "LIMPIANDO_FILESYSTEM", 75, "Moviendo runtime anterior a cuarentena reversible.")
        resumen_fs = limpiar_roots_factory_reset(operaciones_fs)
        filesystem_aplicado = True
        if not validar_roots_vacios(operaciones_fs):
            raise RuntimeError("Los roots runtime no quedaron vacios.")
        registrar_evento_factory_reset(
            contexto.id_operacion,
            "LIMPIANDO_FILESYSTEM",
            "Roots operativos vacios; cuarentena conservada para rollback.",
            datos={"roots_limpios": resumen_fs["roots_limpios"]},
        )

        _avanzar(contexto, "VALIDANDO_RESULTADO", 86, "Validando bootstrap en el nombre oficial.")
        motor.validar_bootstrap(contexto.base_actual, _ruta_validacion(contexto.manifiesto))

        _avanzar(contexto, "REGISTRANDO_RESET", 93, "Registrando primer evento de la instalacion nueva.")
        identidad = f"{contexto.usuario} [{contexto.origen_usuario}]"
        motor.registrar_reset_completado(
            contexto.base_actual,
            identidad,
            contexto.id_operacion,
            current_app.config.get("APP_VERSION", "local"),
        )
        motor.validar_resultado_final(contexto.base_actual, contexto.id_operacion)

        _avanzar(contexto, "REGISTRANDO_RESET", 97, "Eliminando bases temporales de la operacion.")
        housekeeping_iniciado = True
        _eliminar_temporales_operacion(
            motor,
            contexto,
            (contexto.base_nueva, contexto.base_fallida, contexto.base_anterior),
        )

        registrar_marca_factory_reset_completado(contexto.id_operacion)
        _avanzar(contexto, "COMPLETADO", 100, "Factory Reset completado.", completado=True)
        if not liberar_lock_factory_reset(contexto.id_operacion):
            actualizar_lock_factory_reset(
                contexto.id_operacion,
                "FACTORY_RESET_ERROR",
                fase="ERROR",
                progreso=100,
                mensaje="Reset completado, pero el lock requiere liberacion manual.",
                error_seguro="No fue posible liberar el lock final.",
            )
            return {
                "ok": False,
                "mensaje": "La instalacion fue reconstruida, pero el lock requiere revision manual.",
                "id_operacion": contexto.id_operacion,
                "requiere_revision_manual": True,
            }
        return {
            "ok": True,
            "mensaje": "APP Scheduler fue restablecido correctamente a su estado de fabrica.",
            "id_operacion": contexto.id_operacion,
            "cuarentena_filesystem": True,
        }
    except Exception as error:
        detalle_sql = f" {error}" if isinstance(error, ErrorFactoryResetSQL) else ""
        mensaje_seguro = f"Factory Reset no pudo completarse ({error.__class__.__name__}).{detalle_sql}"
        registrar_evento_factory_reset(
            contexto.id_operacion,
            "ERROR",
            mensaje_seguro,
            "ERROR",
            {"intercambio_iniciado": intercambio_iniciado, "filesystem_aplicado": filesystem_aplicado},
        )
        if filesystem_aplicado:
            _avanzar_seguro(contexto, "ROLLBACK", 80, "Restaurando filesystem anterior.")
            rollback_fs_ok = rollback_roots_factory_reset(operaciones_fs)["ok"]
        if intercambio_iniciado and motor and not housekeeping_iniciado:
            try:
                _avanzar_seguro(contexto, "ROLLBACK", 70, "Restaurando base anterior.")
                motor.rollback_intercambio(
                    contexto.base_actual,
                    contexto.base_nueva,
                    contexto.base_anterior,
                    contexto.base_fallida,
                )
                if not motor.existe_base(contexto.base_actual) or motor.existe_base(contexto.base_anterior):
                    raise RuntimeError("El rollback no pudo confirmar la restauracion de la base operativa.")
                _eliminar_temporales_operacion(
                    motor,
                    contexto,
                    (contexto.base_nueva, contexto.base_fallida),
                )
                rollback_sql_ok = True
            except Exception:
                rollback_sql_ok = False
        elif not intercambio_iniciado and motor:
            try:
                if not motor.existe_base(contexto.base_actual):
                    raise RuntimeError("La base operativa original no pudo confirmarse.")
                _eliminar_temporales_operacion(motor, contexto, (contexto.base_nueva,))
                rollback_sql_ok = True
            except Exception:
                rollback_sql_ok = False
        residuos_sql = _listar_residuos_seguro(motor, contexto)
        if residuos_sql:
            registrar_evento_factory_reset(
                contexto.id_operacion,
                "RESIDUOS_SQL",
                "Quedaron bases temporales que requieren recuperacion o limpieza manual.",
                "ERROR",
                {"bases": residuos_sql},
            )
        detalle = "Rollback SQL=%s; filesystem=%s." % (
            _estado_bool(rollback_sql_ok),
            _estado_bool(rollback_fs_ok),
        )
        actualizar_lock_factory_reset(
            contexto.id_operacion,
            "FACTORY_RESET_ERROR",
            fase="ERROR",
            progreso=0,
            mensaje="Factory Reset en error; requiere revision manual. " + detalle,
            error_seguro=mensaje_seguro,
        )
        return {
            "ok": False,
            "mensaje": mensaje_seguro + " " + detalle,
            "id_operacion": contexto.id_operacion,
            "requiere_revision_manual": True,
        }


def _precheck_final(datos_preview, lock_propio=None, ejecutor=None):
    configuracion = validar_configuracion_factory_reset_sql()
    if not configuracion["disponible"]:
        return {"ok": False, "mensaje": configuracion["bloqueos"][0], "manifiesto": None}
    try:
        motor = ejecutor or EjecutorSQLFactoryReset()
        permisos = motor.validar_permisos_administrativos()
    except Exception:
        return {
            "ok": False,
            "mensaje": "No fue posible validar los privilegios de la credencial administrativa.",
            "manifiesto": None,
        }
    if not permisos["disponible"]:
        return {"ok": False, "mensaje": permisos["mensaje"], "manifiesto": None}
    lock = obtener_estado_factory_reset()
    if lock["bloquea"] and lock.get("id_operacion") != lock_propio:
        return {"ok": False, "mensaje": "Existe un lock Factory Reset activo o dudoso.", "manifiesto": None}
    manifiesto = validar_manifiesto_bootstrap()
    if not manifiesto["valido"]:
        return {"ok": False, "mensaje": "El manifiesto bootstrap no es valido.", "manifiesto": manifiesto}
    if manifiesto.get("hash_conjunto") != (datos_preview or {}).get("manifest_hash"):
        return {"ok": False, "mensaje": "El bootstrap cambio despues del preview.", "manifiesto": manifiesto}
    if not validar_super_admin_env()["disponible"]:
        return {"ok": False, "mensaje": "SUPER_ADMIN_ENV no esta disponible.", "manifiesto": manifiesto}
    try:
        diagnostico = diagnosticar_operacion_factory_reset()
    except Exception:
        return {"ok": False, "mensaje": "No fue posible recalcular el estado operativo.", "manifiesto": manifiesto}
    if diagnostico["total_ejecuciones_activas"]:
        return {"ok": False, "mensaje": "Existen ejecuciones EN_EJECUCION.", "manifiesto": manifiesto}
    if diagnostico["pids_vivos_registrados"] or diagnostico["procesos_hijos_conocidos"]:
        return {"ok": False, "mensaje": "Existen procesos de scripts activos.", "manifiesto": manifiesto}
    try:
        residuos = motor.listar_bases_residuales(current_app.config.get("FACTORY_RESET_DB_TARGET"))
    except Exception:
        return {"ok": False, "mensaje": "No fue posible validar residuos SQL de Factory Reset.", "manifiesto": manifiesto}
    if residuos:
        return {
            "ok": False,
            "mensaje": "Existen bases residuales de Factory Reset pendientes de recuperacion o limpieza: " + ", ".join(residuos),
            "manifiesto": manifiesto,
        }
    try:
        preparar_roots_factory_reset((datos_preview or {}).get("id_operacion"))
    except Exception:
        return {"ok": False, "mensaje": "Los roots runtime no superaron la validacion de seguridad.", "manifiesto": manifiesto}
    return {"ok": True, "mensaje": "Precheck correcto.", "manifiesto": manifiesto}


def _crear_contexto(id_operacion, usuario, origen_usuario, manifiesto):
    actual = str(current_app.config.get("FACTORY_RESET_DB_TARGET") or "").strip()
    temporales = derivar_bases_temporales_factory_reset(actual, id_operacion)
    return ContextoFactoryReset(
        id_operacion=id_operacion,
        usuario=str(usuario or "administrador")[:100],
        origen_usuario="ENV" if str(origen_usuario).upper() == "ENV" else "BD",
        base_actual=actual,
        base_nueva=temporales["NEW"],
        base_anterior=temporales["OLD"],
        base_fallida=temporales["FAILED"],
        manifiesto=manifiesto,
    )


def _revalidar_antes_intercambio(contexto, operaciones_fs):
    lock = obtener_estado_factory_reset()
    if lock.get("id_operacion") != contexto.id_operacion or lock.get("dudoso"):
        raise RuntimeError("El lock dejo de ser confiable antes del intercambio.")
    if not validar_configuracion_factory_reset_sql()["disponible"]:
        raise RuntimeError("La configuracion administrativa cambio durante el bootstrap.")
    manifiesto_actual = validar_manifiesto_bootstrap()
    if not manifiesto_actual["valido"] or manifiesto_actual.get("hash_conjunto") != contexto.manifiesto.get("hash_conjunto"):
        raise RuntimeError("El bootstrap cambio durante la operacion.")
    if not validar_super_admin_env()["disponible"]:
        raise RuntimeError("SUPER_ADMIN_ENV dejo de estar disponible.")
    diagnostico = diagnosticar_operacion_factory_reset()
    if diagnostico["total_ejecuciones_activas"] or diagnostico["pids_vivos_registrados"] or diagnostico["procesos_hijos_conocidos"]:
        raise RuntimeError("Se detecto actividad operativa antes del intercambio.")
    roots_actuales = preparar_roots_factory_reset(contexto.id_operacion)
    if [item["root"] for item in roots_actuales] != [item["root"] for item in operaciones_fs]:
        raise RuntimeError("La configuracion de roots cambio durante la operacion.")


def _eliminar_temporales_operacion(motor, contexto, nombres):
    for nombre in nombres:
        motor.eliminar_base_temporal_operacion(nombre, contexto.base_actual, contexto.id_operacion)
    residuos = motor.listar_bases_residuales(contexto.base_actual)
    if residuos:
        raise RuntimeError("Persisten bases residuales de Factory Reset: " + ", ".join(residuos))


def _listar_residuos_seguro(motor, contexto):
    if not motor:
        return []
    try:
        return motor.listar_bases_residuales(contexto.base_actual)
    except Exception:
        return ["ESTADO_NO_CONFIRMABLE"]


def _ruta_validacion(manifiesto):
    from app.config import BASE_DIR

    ultimo = manifiesto["scripts"][-1]
    if int(ultimo["order"]) != 100:
        raise RuntimeError("El manifiesto no termina en validacion 100.")
    return (BASE_DIR / ultimo["file"]).resolve()


def _avanzar(contexto, fase, progreso, mensaje, completado=False):
    estado = "FACTORY_RESET_EN_PROGRESO" if fase not in {"LOCK_ADQUIRIDO"} else "FACTORY_RESET_PREPARANDO"
    if not actualizar_lock_factory_reset(
        contexto.id_operacion,
        estado,
        fase=fase,
        progreso=progreso,
        mensaje=mensaje,
        completado=completado,
    ):
        raise RuntimeError("No fue posible actualizar el lock global.")


def _avanzar_seguro(contexto, fase, progreso, mensaje):
    try:
        _avanzar(contexto, fase, progreso, mensaje)
    except Exception:
        try:
            registrar_evento_factory_reset(contexto.id_operacion, fase, mensaje, "WARNING")
        except Exception:
            pass


def _resultado_error(id_operacion, mensaje, fase):
    return {"ok": False, "mensaje": mensaje, "id_operacion": id_operacion or None, "fase": fase or "PRECHECK"}


def _estado_bool(valor):
    if valor is None:
        return "NO_APLICA"
    return "OK" if valor else "ERROR"
