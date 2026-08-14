"""Inicializacion central de infraestructura Flask."""

from flask import Flask

from app_scheduler.compartido.csrf import iniciar_csrf
from app_scheduler.compartido.errores import registrar_manejadores_errores


def iniciar_extensiones(app: Flask) -> None:
    iniciar_csrf(app)
    registrar_manejadores_errores(app)
