from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.seguridad import permiso_requerido
from app.servicios.servicio_roles import obtener_roles_para_formulario
from app.servicios.servicio_usuarios import (
    actualizar_usuario_admin,
    cambiar_estado_usuario_admin,
    crear_usuario_admin,
    listar_usuarios_admin,
    obtener_usuario_admin,
)


bp_usuarios = Blueprint("usuarios", __name__, url_prefix="/usuarios")


@bp_usuarios.route("/")
@permiso_requerido("USUARIOS_ADMIN")
def listado():
    filtros = {
        "estado": request.args.get("estado", "").strip(),
        "rol": request.args.get("rol", "").strip(),
        "buscar": request.args.get("buscar", "").strip(),
    }
    filtros = {clave: valor for clave, valor in filtros.items() if valor}
    roles = _cargar_roles()

    try:
        usuarios = listar_usuarios_admin(filtros)
    except Exception:
        usuarios = []
        flash("No fue posible consultar usuarios en este momento.", "error")

    return render_template(
        "usuarios/listado.html",
        usuarios=usuarios,
        roles=roles,
        filtros=filtros,
        total_usuarios=len(usuarios),
    )


@bp_usuarios.route("/nuevo", methods=["GET", "POST"])
@permiso_requerido("USUARIOS_ADMIN")
def nuevo():
    roles = _cargar_roles()
    datos = {"activo": "1"}

    if request.method == "POST":
        datos = request.form.to_dict()
        datos["activo"] = request.form.get("activo")
        ok, mensajes, id_usuario = crear_usuario_admin(datos, session.get("usuario"))
        if ok:
            flash(mensajes[0], "success")
            return redirect(url_for("usuarios.editar", id_usuario=id_usuario))

        for mensaje in mensajes:
            flash(mensaje, "error")

    return render_template("usuarios/formulario.html", modo="crear", usuario=datos, roles=roles)


@bp_usuarios.route("/<int:id_usuario>/editar", methods=["GET", "POST"])
@permiso_requerido("USUARIOS_ADMIN")
def editar(id_usuario):
    roles = _cargar_roles()
    usuario = obtener_usuario_admin(id_usuario)
    if not usuario:
        flash("Usuario no encontrado.", "error")
        return redirect(url_for("usuarios.listado"))

    if request.method == "POST":
        datos = request.form.to_dict()
        datos["activo"] = request.form.get("activo")
        ok, mensajes = actualizar_usuario_admin(id_usuario, datos, session.get("usuario"))
        if ok:
            for mensaje in mensajes:
                flash(mensaje, "success")
            return redirect(url_for("usuarios.listado"))

        for mensaje in mensajes:
            flash(mensaje, "error")
        usuario.update(datos)

    return render_template("usuarios/formulario.html", modo="editar", usuario=usuario, roles=roles)


@bp_usuarios.route("/<int:id_usuario>/estado", methods=["POST"])
@permiso_requerido("USUARIOS_ADMIN")
def estado(id_usuario):
    activo = request.form.get("activo") == "1"
    ok, mensaje = cambiar_estado_usuario_admin(id_usuario, activo, session.get("usuario"))
    flash(mensaje, "success" if ok else "error")
    return redirect(url_for("usuarios.listado"))


def _cargar_roles():
    try:
        return obtener_roles_para_formulario()
    except Exception:
        flash("No fue posible cargar roles. Revisa la conexion a base de datos.", "error")
        return []
