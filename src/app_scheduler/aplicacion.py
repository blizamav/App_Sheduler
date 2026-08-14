"""Fabrica de la aplicacion reconstruida."""

from __future__ import annotations

from collections.abc import Mapping

from flask import Flask

from app_scheduler.compartido.logging import configurar_logging
from app_scheduler.configuracion import ConfiguracionAplicacion
from app_scheduler.extensiones import iniciar_extensiones


def crear_aplicacion(
    configuracion: ConfiguracionAplicacion | None = None,
    *,
    validar_capacidad: str = "web",
    ajustes: Mapping[str, object] | None = None,
) -> Flask:
    """Crea un runtime aislado y testeable sin registrar modulos historicos."""
    configuracion = configuracion or ConfiguracionAplicacion.desde_entorno()
    configuracion.validar(validar_capacidad)

    app = Flask(
        __name__,
        template_folder="presentacion/templates",
        static_folder="presentacion/static",
        static_url_path="/static-reconstruccion",
    )
    app.config.update(configuracion.como_config_flask())
    if ajustes:
        app.config.update(ajustes)

    logger = configurar_logging(
        "app_scheduler.web",
        configuracion.log_level,
        configuracion.secretos_conocidos(),
    )
    app.logger.handlers.clear()
    app.logger.handlers.extend(logger.handlers)
    app.logger.setLevel(logger.level)
    app.logger.propagate = False

    iniciar_extensiones(app)

    from app_scheduler.modulos.base.rutas import bp_base

    app.register_blueprint(bp_base)
    app.logger.info(
        "Runtime base creado para ambiente %s",
        configuracion.app_env,
        extra={"evento": "APLICACION_INICIADA"},
    )
    return app
