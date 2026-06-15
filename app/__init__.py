from flask import Flask

from app.config import Configuracion, validar_configuracion_critica
from app.rutas_mantenedores import bp_mantenedores
from app.rutas import bp_principal
from app.rutas_ejecuciones import bp_ejecuciones
from app.rutas_scripts import bp_scripts
from app.rutas_tareas import bp_tareas
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
    app.register_blueprint(bp_tareas)
    app.register_blueprint(bp_scripts)
    app.register_blueprint(bp_ejecuciones)
    return app
