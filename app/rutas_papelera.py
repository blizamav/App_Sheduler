from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.seguridad import permiso_requerido
from app.servicios.servicio_papelera import (
    eliminar_registro_permanente,
    listar_papelera,
    restaurar_registro,
)


bp_papelera = Blueprint("papelera", __name__, url_prefix="/papelera")


@bp_papelera.route("/")
@permiso_requerido("PAPELERA_VER")
def listado():
    filtros = {
        "entidad": request.args.get("entidad", "").strip(),
        "buscar": request.args.get("buscar", "").strip(),
        "usuario": request.args.get("usuario", "").strip(),
        "fecha_desde": request.args.get("fecha_desde", "").strip(),
        "fecha_hasta": request.args.get("fecha_hasta", "").strip(),
        "page": request.args.get("page", "1").strip(),
        "per_page": request.args.get("per_page", "25").strip(),
    }
    contexto = listar_papelera(filtros)
    return render_template("papelera/listado.html", filtros=filtros, **contexto)


@bp_papelera.route("/<entidad>/<int:id_registro>/restaurar", methods=["POST"])
@permiso_requerido("PAPELERA_RESTAURAR")
def restaurar(entidad, id_registro):
    ok, mensaje = restaurar_registro(entidad, id_registro, session.get("usuario"))
    flash(mensaje, "success" if ok else "error")
    return redirect(_volver())


@bp_papelera.route("/<entidad>/<int:id_registro>/eliminar-permanente", methods=["POST"])
@permiso_requerido("PAPELERA_ELIMINAR_PERMANENTE")
def eliminar_permanente(entidad, id_registro):
    ok, mensaje = eliminar_registro_permanente(
        entidad,
        id_registro,
        session.get("usuario"),
        session.get("id_usuario"),
    )
    flash(mensaje, "success" if ok else "error")
    return redirect(_volver())


def _volver():
    return request.form.get("volver") or url_for("papelera.listado")
