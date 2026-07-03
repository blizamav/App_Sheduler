from flask import Flask

from app.config import Configuracion, validar_configuracion_critica
from app.rutas_auditoria import bp_auditoria
from app.rutas_configuracion import bp_configuracion, bp_configuracion_api
from app.rutas_feriados import bp_feriados
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
    return app
