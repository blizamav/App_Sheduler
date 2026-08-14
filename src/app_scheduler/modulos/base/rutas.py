"""Rutas tecnicas minimas del runtime reconstruido."""

from flask import Blueprint, current_app, jsonify, render_template

from app_scheduler.compartido.autorizacion import identidad_actual, permiso_requerido


bp_base = Blueprint("base", __name__)


@bp_base.get("/")
@permiso_requerido("PANEL_VER")
def inicio():
    return render_template(
        "base/inicio.html",
        ambiente=current_app.config["APP_ENV"],
        version=current_app.config["APP_VERSION"],
        identidad=identidad_actual(),
    )


@bp_base.get("/salud")
def salud():
    """Healthcheck de proceso; no abre conexiones SQL."""
    return jsonify(
        {
            "estado": "OK",
            "servicio": "web",
            "ambiente": current_app.config["APP_ENV"],
            "version": current_app.config["APP_VERSION"],
        }
    )
