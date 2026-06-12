from flask import Flask

from app.config import Configuracion
from app.rutas import bp_principal


def crear_app():
    """Crea la aplicacion Flask, carga configuracion y registra rutas base."""
    app = Flask(__name__)
    app.config.from_object(Configuracion)
    app.register_blueprint(bp_principal)
    return app
