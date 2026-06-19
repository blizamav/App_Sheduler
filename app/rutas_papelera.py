from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.seguridad import permiso_requerido
from app.servicios.servicio_papelera import (
    eliminar_registro_permanente,
    eliminar_todo_permanente,
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
    resultado_masivo = session.pop("papelera_resultado_masivo", None)
    return render_template("papelera/listado.html", filtros=filtros, resultado_masivo=resultado_masivo, **contexto)


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


@bp_papelera.route("/eliminar-permanente-todo", methods=["POST"])
@permiso_requerido("PAPELERA_ELIMINAR_PERMANENTE")
def eliminar_permanente_todo():
    resumen = eliminar_todo_permanente(session.get("usuario"), session.get("id_usuario"))
    session["papelera_resultado_masivo"] = _resumen_para_sesion(resumen)
    mensaje = (
        f"Proceso finalizado. Eliminados permanentemente: {resumen['eliminados']}. "
        f"No eliminados: {resumen['no_eliminados']}. Errores: {resumen['errores']}."
    )
    categoria = "success" if resumen["errores"] == 0 else "advertencia"
    flash(mensaje, categoria)
    return redirect(url_for("papelera.listado"))


def _volver():
    return request.form.get("volver") or url_for("papelera.listado")


def _resumen_para_sesion(resumen):
    detalles = [
        {
            "entidad_label": item.get("entidad_label"),
            "id_registro": item.get("id_registro"),
            "nombre": item.get("nombre"),
            "motivo": item.get("motivo"),
        }
        for item in resumen.get("detalles_no_eliminados", [])[:20]
    ]
    return {
        "total": resumen.get("total", 0),
        "eliminados": resumen.get("eliminados", 0),
        "no_eliminados": resumen.get("no_eliminados", 0),
        "errores": resumen.get("errores", 0),
        "por_entidad": resumen.get("por_entidad", {}),
        "detalles_no_eliminados": detalles,
        "error_global": resumen.get("error_global"),
    }
