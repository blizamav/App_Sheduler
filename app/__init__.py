from flask import Flask, flash, redirect, request, session, url_for

from app.config import Configuracion, validar_configuracion_critica
from app.rutas_auditoria import bp_auditoria
from app.rutas_configuracion import bp_configuracion, bp_configuracion_api
from app.rutas_feriados import bp_feriados
from app.rutas_factory_reset import bp_factory_reset
from app.rutas_mantenedores import bp_mantenedores
from app.rutas_papelera import bp_papelera
from app.rutas import bp_principal
from app.rutas_ejecuciones import bp_ejecuciones
from app.rutas_scripts import bp_scripts
from app.rutas_scheduler import bp_scheduler, bp_worker_api
from app.rutas_tareas import bp_tareas, bp_tareas_api
from app.rutas_usuarios import bp_usuarios


def crear_app():
    """Crea la aplicacion Flask, carga configuracion y registra rutas base."""
    app = Flask(__name__)
    app.config.from_object(Configuracion)
    app.config["ADVERTENCIAS_CONFIGURACION"] = validar_configuracion_critica()
    if app.config["ADVERTENCIAS_CONFIGURACION"]:
        app.logger.warning(
            "Configuracion critica incompleta o con valores de plantilla: %s",
            ", ".join(app.config["ADVERTENCIAS_CONFIGURACION"]),
        )
    app.register_blueprint(bp_principal)
    app.register_blueprint(bp_usuarios)
    app.register_blueprint(bp_mantenedores)
    app.register_blueprint(bp_papelera)
    app.register_blueprint(bp_configuracion)
    app.register_blueprint(bp_configuracion_api)
    app.register_blueprint(bp_tareas)
    app.register_blueprint(bp_tareas_api)
    app.register_blueprint(bp_scripts)
    app.register_blueprint(bp_ejecuciones)
    app.register_blueprint(bp_scheduler)
    app.register_blueprint(bp_worker_api)
    app.register_blueprint(bp_feriados)
    app.register_blueprint(bp_auditoria)
    app.register_blueprint(bp_factory_reset)

    @app.before_request
    def invalidar_sesion_anterior_factory_reset():
        from app.servicios.servicio_control_runtime import obtener_estado_factory_reset

        lock = obtener_estado_factory_reset()
        endpoints_control = {
            "static",
            "factory_reset.pantalla",
            "factory_reset.preview",
            "factory_reset.ejecutar",
            "factory_reset.estado",
        }
        if lock["bloquea"] and request.endpoint not in endpoints_control:
            if lock["estado"] == "FACTORY_RESET_ERROR" and request.endpoint == "principal.login":
                return None
            return "APP Scheduler se encuentra en proceso de mantenimiento critico.", 503
        if not session.get("usuario") or request.endpoint in {"principal.login", "static"}:
            return None
        from app.servicios.servicio_control_runtime import sesion_es_anterior_ultimo_factory_reset

        if sesion_es_anterior_ultimo_factory_reset(session.get("sesion_iniciada_epoch")):
            session.clear()
            flash("La sesion fue invalidada por un restablecimiento del sistema.", "info")
            return redirect(url_for("principal.login"))
        return None

    return app
