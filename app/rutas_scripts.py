from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.seguridad import permiso_requerido
from app.servicios.servicio_scripts import (
    activar_version_script,
    desactivar_version_script,
    desactivar_script_logico,
    eliminar_env_version,
    eliminar_script_logico,
    eliminar_version_script,
    guardar_env_version,
    obtener_vista_scripts_tarea,
    reemplazar_version_script,
    subir_version,
)


bp_scripts = Blueprint("scripts", __name__)


@bp_scripts.route("/tareas/<int:id_tarea>/scripts")
@permiso_requerido("SCRIPTS_VER")
def por_tarea(id_tarea):
    vista = obtener_vista_scripts_tarea(id_tarea)
    if not vista:
        flash("Tarea no encontrada.", "error")
        return redirect(url_for("tareas.listado"))
    return render_template("scripts/listado.html", **vista)


@bp_scripts.route("/tareas/<int:id_tarea>/scripts/versiones/nueva", methods=["POST"])
@permiso_requerido("SCRIPTS_VERSIONAR")
def nueva_version(id_tarea):
    ok, mensaje = subir_version(
        id_tarea,
        request.files.get("archivo_script"),
        request.form.get("observacion", "").strip(),
        request.form.get("requiere_env") == "1",
        session.get("usuario"),
    )
    flash(mensaje, "success" if ok else "error")
    return redirect(url_for("scripts.por_tarea", id_tarea=id_tarea))


@bp_scripts.route("/scripts/versiones/<int:id_version>/reemplazar", methods=["POST"])
@permiso_requerido("SCRIPTS_VERSIONAR")
def reemplazar_version(id_version):
    ok, mensaje = reemplazar_version_script(
        id_version,
        request.files.get("archivo_script"),
        request.form.get("observacion", "").strip(),
        session.get("usuario"),
    )
    flash(mensaje, "success" if ok else "error")
    return _volver_a_tarea(id_version)


@bp_scripts.route("/scripts/versiones/<int:id_version>/activar", methods=["POST"])
@permiso_requerido("SCRIPTS_ACTIVAR_VERSION")
def activar_version(id_version):
    ok, mensaje = activar_version_script(id_version, session.get("usuario"))
    flash(mensaje, "success" if ok else "error")
    return _volver_a_tarea(id_version)


@bp_scripts.route("/scripts/versiones/<int:id_version>/desactivar", methods=["POST"])
@permiso_requerido("SCRIPTS_DESACTIVAR")
def desactivar_version(id_version):
    ok, mensaje = desactivar_version_script(id_version, session.get("usuario"))
    flash(mensaje, "success" if ok else "error")
    return _volver_a_tarea(id_version)


@bp_scripts.route("/scripts/versiones/<int:id_version>/eliminar", methods=["POST"])
@permiso_requerido("SCRIPTS_ELIMINAR")
def eliminar_version(id_version):
    ok, mensaje = eliminar_version_script(id_version, session.get("usuario"))
    flash(mensaje, "success" if ok else "error")
    return redirect(request.form.get("volver") or url_for("tareas.listado"))


@bp_scripts.route("/scripts/versiones/<int:id_version>/env", methods=["POST"])
@permiso_requerido("SCRIPTS_ENV_GESTIONAR")
def guardar_env(id_version):
    ok, mensaje = guardar_env_version(
        id_version,
        request.files.get("archivo_env"),
        request.form.get("requiere_env") == "1",
        session.get("usuario"),
        request.form.get("contenido_env"),
    )
    flash(mensaje, "success" if ok else "error")
    return _volver_a_tarea(id_version)


@bp_scripts.route("/scripts/versiones/<int:id_version>/env/eliminar", methods=["POST"])
@permiso_requerido("SCRIPTS_ENV_GESTIONAR")
def eliminar_env(id_version):
    ok, mensaje = eliminar_env_version(id_version, session.get("usuario"))
    flash(mensaje, "success" if ok else "error")
    return _volver_a_tarea(id_version)


@bp_scripts.route("/scripts/<int:id_script>/desactivar", methods=["POST"])
@permiso_requerido("SCRIPTS_DESACTIVAR")
def desactivar_script(id_script):
    ok, mensaje, id_tarea = desactivar_script_logico(id_script, session.get("usuario"))
    flash(mensaje, "success" if ok else "error")
    return redirect(url_for("scripts.por_tarea", id_tarea=id_tarea) if id_tarea else url_for("tareas.listado"))


@bp_scripts.route("/scripts/<int:id_script>/eliminar", methods=["POST"])
@permiso_requerido("SCRIPTS_ELIMINAR")
def eliminar_script(id_script):
    ok, mensaje, id_tarea = eliminar_script_logico(id_script, session.get("usuario"))
    flash(mensaje, "success" if ok else "error")
    return redirect(url_for("scripts.por_tarea", id_tarea=id_tarea) if id_tarea and not ok else url_for("tareas.listado"))


def _volver_a_tarea(id_version):
    vista = request.form.get("volver")
    if vista:
        return redirect(vista)
    from app.repositorios.repositorio_scripts import obtener_version

    version = obtener_version(id_version)
    if version:
        return redirect(url_for("scripts.por_tarea", id_tarea=version["id_tarea"]))
    return redirect(url_for("tareas.listado"))
