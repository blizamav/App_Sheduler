"""Fabrica de la aplicacion reconstruida."""

from __future__ import annotations

from collections.abc import Mapping

from flask import Flask

from app_scheduler.compartido.autorizacion import iniciar_autorizacion
from app_scheduler.compartido.base_datos import ProveedorConexionesSQLServer
from app_scheduler.compartido.logging import configurar_logging
from app_scheduler.configuracion import ConfiguracionAplicacion
from app_scheduler.extensiones import iniciar_extensiones


def crear_aplicacion(
    configuracion: ConfiguracionAplicacion | None = None,
    *,
    validar_capacidad: str = "autenticacion",
    ajustes: Mapping[str, object] | None = None,
    proveedor_sql=None,
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

    proveedor_sql = proveedor_sql or ProveedorConexionesSQLServer(configuracion)
    from app_scheduler.modulos.autenticacion.casos_uso import ServicioAutenticacion
    from app_scheduler.modulos.catalogos.casos_uso import ServicioCatalogos
    from app_scheduler.modulos.usuarios.casos_uso import ServicioUsuarios
    from app_scheduler.modulos.tareas.casos_uso import ServicioTareas
    from app_scheduler.modulos.scripts.casos_uso import ServicioScripts

    servicio_autenticacion = ServicioAutenticacion(
        configuracion,
        proveedor_sql,
        logger=app.logger,
    )
    app.extensions["proveedor_sql"] = proveedor_sql
    app.extensions["servicio_autenticacion"] = servicio_autenticacion
    app.extensions["servicio_catalogos"] = ServicioCatalogos(proveedor_sql)
    app.extensions["servicio_usuarios"] = ServicioUsuarios(proveedor_sql)
    app.extensions["servicio_tareas"] = ServicioTareas(proveedor_sql)
    app.extensions["servicio_scripts"] = ServicioScripts(proveedor_sql, configuracion)
    iniciar_autorizacion(app, servicio_autenticacion.cargar_identidad)

    from app_scheduler.modulos.base.rutas import bp_base
    from app_scheduler.modulos.autenticacion.rutas import bp_autenticacion
    from app_scheduler.modulos.catalogos.rutas import bp_catalogos
    from app_scheduler.modulos.seguridad.rutas import bp_seguridad
    from app_scheduler.modulos.usuarios.rutas import bp_usuarios
    from app_scheduler.modulos.tareas.rutas import bp_tareas
    from app_scheduler.modulos.scripts.rutas import bp_scripts

    app.register_blueprint(bp_base)
    app.register_blueprint(bp_autenticacion)
    app.register_blueprint(bp_catalogos)
    app.register_blueprint(bp_usuarios)
    app.register_blueprint(bp_seguridad)
    app.register_blueprint(bp_tareas)
    app.register_blueprint(bp_scripts)
    app.logger.info(
        "Runtime base creado para ambiente %s",
        configuracion.app_env,
        extra={"evento": "APLICACION_INICIADA"},
    )
    return app
