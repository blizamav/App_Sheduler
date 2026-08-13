from dataclasses import dataclass

from flask import current_app

from app.servicios.servicio_control_runtime import (
    adquirir_lock_factory_reset,
    actualizar_lock_factory_reset,
    liberar_lock_factory_reset,
    obtener_estado_factory_reset,
    registrar_evento_factory_reset,
    registrar_marca_factory_reset_completado,
)
from app.servicios.servicio_factory_reset import (
    diagnosticar_operacion_factory_reset,
    validar_manifiesto_bootstrap,
    validar_super_admin_env,
)
from app.servicios.servicio_factory_reset_filesystem import (
    eliminar_cuarentena_factory_reset,
    limpiar_roots_factory_reset,
    preparar_roots_factory_reset,
    rollback_roots_factory_reset,
    validar_roots_vacios,
)
from app.servicios.servicio_factory_reset_sql import (
    EjecutorSQLFactoryReset,
    ErrorFactoryResetSQL,
    validar_configuracion_factory_reset_sql,
)


FRASE_CONFIRMACION_FACTORY_RESET = "RESTABLECER APP SCHEDULER"


@dataclass
class ContextoFactoryReset:
    id_operacion: str
    usuario: str
    origen_usuario: str
    base_actual: str
    manifiesto: dict


def ejecutar_factory_reset(datos_preview, usuario, origen_usuario="BD", ejecutor=None):
    id_operacion = str((datos_preview or {}).get("id_operacion") or "")
    precheck = _precheck_final(datos_preview, ejecutor=ejecutor)
    if not precheck["ok"]:
        return _resultado_error(id_operacion, precheck["mensaje"], "PRECHECK")

    contexto = _crear_contexto(id_operacion, usuario, origen_usuario, precheck["manifiesto"])
    adquirido, estado_lock = adquirir_lock_factory_reset(
        "FACTORY_RESET_PREPARANDO",
        f"WEB:{contexto.origen_usuario}",
        id_operacion=contexto.id_operacion,
    )
    if not adquirido:
        return _resultado_error(
            contexto.id_operacion,
            "Existe otra operacion Factory Reset activa.",
            estado_lock.get("fase"),
        )

    operaciones_fs = []
    filesystem_aplicado = False
    commit_sql_confirmado = False
    motor = ejecutor or EjecutorSQLFactoryReset()
    try:
        _avanzar(contexto, "LOCK_ADQUIRIDO", 8, "Lock global externo adquirido.")
        segundo_precheck = _precheck_final(
            datos_preview,
            lock_propio=contexto.id_operacion,
            ejecutor=motor,
        )
        if not segundo_precheck["ok"]:
            raise RuntimeError(segundo_precheck["mensaje"])

        _avanzar(contexto, "BLOQUEANDO_ACTIVIDAD", 15, "Actividad nueva bloqueada; condiciones recalculadas.")
        operaciones_fs = preparar_roots_factory_reset(contexto.id_operacion)

        _avanzar(contexto, "CUARENTENA_FILESYSTEM", 25, "Respaldando y limpiando archivos runtime.")
        resumen_fs = limpiar_roots_factory_reset(operaciones_fs)
        filesystem_aplicado = True
        if not validar_roots_vacios(operaciones_fs):
            raise RuntimeError("Los roots runtime no quedaron vacios.")
        registrar_evento_factory_reset(
            contexto.id_operacion,
            "CUARENTENA_FILESYSTEM",
            "Roots runtime en cuarentena reversible antes del COMMIT SQL.",
            datos={"roots_limpios": resumen_fs["roots_limpios"]},
        )

        _revalidar_antes_reset(contexto, operaciones_fs)
        _avanzar(contexto, "ADQUIRIENDO_APPLOCK", 35, "Iniciando sesion SQL transaccional y applock exclusivo.")
        _avanzar(contexto, "EJECUTANDO_RESET_IN_PLACE", 48, "Reconstruyendo APP_SCHEDULER_QA dentro de una transaccion.")
        identidad = f"{contexto.usuario} [{contexto.origen_usuario}]"
        motor.ejecutar_reset_in_place(
            contexto.id_operacion,
            identidad,
            current_app.config.get("APP_VERSION", "local"),
        )
        commit_sql_confirmado = True

        _avanzar(contexto, "CONFIRMANDO_COMMIT", 78, "COMMIT SQL confirmado por el runner in-place.")
        _avanzar(contexto, "VALIDANDO_RESULTADO", 88, "Validando estructura, configuracion y auditoria base.")
        motor.validar_resultado_final(contexto.id_operacion)

        _avanzar(contexto, "LIMPIANDO_CUARENTENA", 95, "Eliminando la cuarentena ya innecesaria.")
        limpieza = eliminar_cuarentena_factory_reset(operaciones_fs)
        if not limpieza["ok"]:
            raise RuntimeError("El reset fue confirmado, pero no pudo eliminarse toda la cuarentena filesystem.")

        registrar_marca_factory_reset_completado(contexto.id_operacion)
        _avanzar(contexto, "COMPLETADO", 100, "Factory Reset in-place completado.", completado=True)
        if not liberar_lock_factory_reset(contexto.id_operacion):
            raise RuntimeError("El reset termino, pero el lock externo requiere revision manual.")
        return {
            "ok": True,
            "mensaje": "APP Scheduler fue restablecido in-place correctamente.",
            "id_operacion": contexto.id_operacion,
            "modo": "IN_PLACE",
        }
    except Exception as error:
        mensaje_seguro = _mensaje_error_seguro(error)
        rollback_fs_ok = None
        if filesystem_aplicado and not commit_sql_confirmado:
            _avanzar_seguro(contexto, "ROLLBACK_FILESYSTEM", 20, "Restaurando archivos runtime anteriores.")
            rollback_fs_ok = rollback_roots_factory_reset(operaciones_fs)["ok"]
        registrar_evento_factory_reset(
            contexto.id_operacion,
            "ERROR",
            mensaje_seguro,
            "ERROR",
            {
                "commit_sql_confirmado": commit_sql_confirmado,
                "filesystem_aplicado": filesystem_aplicado,
                "rollback_filesystem": rollback_fs_ok,
            },
        )
        if commit_sql_confirmado:
            detalle = " SQL ya confirmo COMMIT; no se restauro filesystem antiguo."
        else:
            detalle = f" Rollback filesystem={_estado_bool(rollback_fs_ok)}."
        actualizar_lock_factory_reset(
            contexto.id_operacion,
            "FACTORY_RESET_ERROR",
            fase="ERROR",
            progreso=0,
            mensaje="Factory Reset en error; requiere revision manual." + detalle,
            error_seguro=mensaje_seguro,
        )
        return {
            "ok": False,
            "mensaje": mensaje_seguro + detalle,
            "id_operacion": contexto.id_operacion,
            "requiere_revision_manual": True,
            "commit_sql_confirmado": commit_sql_confirmado,
        }


def _precheck_final(datos_preview, lock_propio=None, ejecutor=None):
    configuracion = validar_configuracion_factory_reset_sql()
    if not configuracion["disponible"]:
        return {"ok": False, "mensaje": configuracion["bloqueos"][0], "manifiesto": None}
    try:
        motor = ejecutor or EjecutorSQLFactoryReset()
        entorno = motor.validar_entorno_in_place()
    except Exception:
        return {
            "ok": False,
            "mensaje": "No fue posible validar la cuenta SQL de mantenimiento en la base objetivo.",
            "manifiesto": None,
        }
    if not entorno["disponible"]:
        return {"ok": False, "mensaje": entorno["mensaje"], "manifiesto": None}
    lock = obtener_estado_factory_reset()
    if lock["bloquea"] and lock.get("id_operacion") != lock_propio:
        return {"ok": False, "mensaje": "Existe un lock Factory Reset activo o dudoso.", "manifiesto": None}
    manifiesto = validar_manifiesto_bootstrap()
    if not manifiesto["valido"]:
        return {"ok": False, "mensaje": "El manifiesto in-place no es valido.", "manifiesto": manifiesto}
    if manifiesto.get("hash_conjunto") != (datos_preview or {}).get("manifest_hash"):
        return {"ok": False, "mensaje": "El runner in-place cambio despues del preview.", "manifiesto": manifiesto}
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
        preparar_roots_factory_reset((datos_preview or {}).get("id_operacion"))
    except Exception:
        return {"ok": False, "mensaje": "Los roots runtime no superaron la validacion de seguridad.", "manifiesto": manifiesto}
    return {"ok": True, "mensaje": "Precheck in-place correcto.", "manifiesto": manifiesto}


def _crear_contexto(id_operacion, usuario, origen_usuario, manifiesto):
    return ContextoFactoryReset(
        id_operacion=id_operacion,
        usuario=str(usuario or "administrador")[:100],
        origen_usuario="ENV" if str(origen_usuario).upper() == "ENV" else "BD",
        base_actual=str(current_app.config.get("FACTORY_RESET_DB_TARGET") or "").strip(),
        manifiesto=manifiesto,
    )


def _revalidar_antes_reset(contexto, operaciones_fs):
    lock = obtener_estado_factory_reset()
    if lock.get("id_operacion") != contexto.id_operacion or lock.get("dudoso"):
        raise RuntimeError("El lock dejo de ser confiable antes del reset in-place.")
    manifiesto = validar_manifiesto_bootstrap()
    if not manifiesto["valido"] or manifiesto.get("hash_conjunto") != contexto.manifiesto.get("hash_conjunto"):
        raise RuntimeError("El runner in-place cambio durante la operacion.")
    diagnostico = diagnosticar_operacion_factory_reset()
    if diagnostico["total_ejecuciones_activas"] or diagnostico["pids_vivos_registrados"] or diagnostico["procesos_hijos_conocidos"]:
        raise RuntimeError("Se detecto actividad operativa antes del reset in-place.")
    if not validar_roots_vacios(operaciones_fs):
        raise RuntimeError("Los roots runtime cambiaron antes del reset in-place.")


def _avanzar(contexto, fase, progreso, mensaje, completado=False):
    estado = "FACTORY_RESET_PREPARANDO" if fase == "LOCK_ADQUIRIDO" else "FACTORY_RESET_EN_PROGRESO"
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


def _mensaje_error_seguro(error):
    detalle = f" {error}" if isinstance(error, ErrorFactoryResetSQL) else ""
    return f"Factory Reset no pudo completarse ({error.__class__.__name__}).{detalle}"[:4500]


def _resultado_error(id_operacion, mensaje, fase):
    return {"ok": False, "mensaje": mensaje, "id_operacion": id_operacion or None, "fase": fase or "PRECHECK"}


def _estado_bool(valor):
    if valor is None:
        return "NO_APLICA"
    return "OK" if valor else "ERROR"
