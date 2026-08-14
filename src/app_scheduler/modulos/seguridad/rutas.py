"""Consulta de la matriz vigente de roles y permisos."""

from flask import Blueprint, current_app, render_template

from app_scheduler.compartido.autorizacion import permiso_requerido


bp_seguridad = Blueprint("seguridad", __name__, url_prefix="/seguridad")


@bp_seguridad.get("/roles-permisos")
@permiso_requerido("USUARIOS_ADMIN")
def roles_permisos():
    resumen = current_app.extensions["servicio_usuarios"].resumen_seguridad()
    permisos_por_modulo: dict[str, list] = {}
    for permiso in resumen.permisos:
        permisos_por_modulo.setdefault(permiso.modulo, []).append(permiso)
    return render_template(
        "seguridad/roles_permisos.html",
        resumen=resumen,
        permisos_por_modulo=permisos_por_modulo,
    )
