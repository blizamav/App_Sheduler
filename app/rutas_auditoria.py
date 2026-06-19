from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.seguridad import permiso_requerido
from app.servicios.servicio_auditoria import listar_auditoria_admin, obtener_detalle_auditoria


bp_auditoria = Blueprint("auditoria", __name__, url_prefix="/auditoria")


@bp_auditoria.route("/")
@permiso_requerido("AUDITORIA_VER")
def listado():
    try:
        contexto = listar_auditoria_admin(request.args)
    except Exception:
        flash("No fue posible cargar la auditoria.", "error")
        contexto = {
            "registros": [],
            "filtros": {},
            "page": 1,
            "per_page": 25,
            "per_page_opciones": (10, 25, 50, 100),
            "total": 0,
            "total_paginas": 1,
        }
    return render_template("auditoria/listado.html", **contexto)


@bp_auditoria.route("/<int:id_auditoria>")
@permiso_requerido("AUDITORIA_DETALLE")
def detalle(id_auditoria):
    registro = obtener_detalle_auditoria(id_auditoria)
    if not registro:
        flash("Registro de auditoria no encontrado.", "error")
        return redirect(url_for("auditoria.listado"))
    return render_template("auditoria/detalle.html", registro=registro)
