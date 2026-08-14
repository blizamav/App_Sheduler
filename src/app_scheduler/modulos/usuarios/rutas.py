"""Rutas del modulo reconstruido de usuarios."""

from __future__ import annotations

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from app_scheduler.compartido.auditoria import ContextoAuditoria
from app_scheduler.compartido.autorizacion import identidad_actual, permiso_requerido
from app_scheduler.compartido.errores import ErrorValidacion


bp_usuarios = Blueprint("usuarios", __name__, url_prefix="/usuarios")


def _servicio():
    return current_app.extensions["servicio_usuarios"]


def _contexto() -> ContextoAuditoria:
    return ContextoAuditoria(
        ip_origen=request.remote_addr,
        user_agent=request.user_agent.string[:500] or None,
        ruta=request.path,
        metodo_http=request.method,
    )


def _entero(valor, default=None):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return default


@bp_usuarios.get("/")
@permiso_requerido("USUARIOS_ADMIN")
def listado():
    estado = request.args.get("estado", "").strip()
    activo = {"activo": True, "inactivo": False}.get(estado)
    pagina = max(1, _entero(request.args.get("pagina"), 1))
    id_rol = _entero(request.args.get("rol"))
    resultado = _servicio().listar(
        pagina=pagina,
        activo=activo,
        busqueda=request.args.get("buscar", "").strip() or None,
        id_rol=id_rol,
    )
    return render_template(
        "usuarios/listado.html",
        resultado=resultado,
        roles=_servicio().roles_disponibles(identidad_actual()),
        filtros={"estado": estado, "rol": id_rol, "buscar": request.args.get("buscar", "")},
    )


@bp_usuarios.route("/nuevo", methods=["GET", "POST"])
@permiso_requerido("USUARIOS_ADMIN")
def nuevo():
    actor = identidad_actual()
    datos = {"activo": "1"}
    if request.method == "POST":
        datos = request.form.to_dict()
        try:
            id_usuario = _servicio().crear(datos, actor, _contexto())
        except ErrorValidacion as error:
            flash(error.mensaje, "error")
        else:
            flash("Usuario creado correctamente.", "success")
            return redirect(url_for("usuarios.editar", id_usuario=id_usuario))
    return render_template(
        "usuarios/formulario.html",
        modo="crear",
        datos=datos,
        roles=_servicio().roles_disponibles(actor),
    )


@bp_usuarios.route("/<int:id_usuario>/editar", methods=["GET", "POST"])
@permiso_requerido("USUARIOS_ADMIN")
def editar(id_usuario: int):
    actor = identidad_actual()
    detalle = _servicio().obtener(id_usuario)
    if detalle is None:
        flash("Usuario no encontrado.", "error")
        return redirect(url_for("usuarios.listado"))
    datos = {
        "usuario": detalle.usuario.usuario,
        "nombre_completo": detalle.usuario.nombre_completo,
        "email": detalle.usuario.email or "",
        "id_rol": detalle.rol_principal.id_rol if detalle.rol_principal else "",
        "activo": "1" if detalle.usuario.activo else "",
    }
    if request.method == "POST":
        datos.update(request.form.to_dict())
        try:
            _servicio().actualizar(id_usuario, datos, actor, _contexto())
        except ErrorValidacion as error:
            flash(error.mensaje, "error")
        else:
            flash("Usuario actualizado correctamente.", "success")
            return redirect(url_for("usuarios.listado"))
    return render_template(
        "usuarios/formulario.html",
        modo="editar",
        datos=datos,
        detalle=detalle,
        roles=_servicio().roles_disponibles(actor),
    )


@bp_usuarios.post("/<int:id_usuario>/estado")
@permiso_requerido("USUARIOS_ADMIN")
def estado(id_usuario: int):
    activo = request.form.get("activo") == "1"
    try:
        _servicio().cambiar_estado(id_usuario, activo, identidad_actual(), _contexto())
    except ErrorValidacion as error:
        flash(error.mensaje, "error")
    else:
        flash("Usuario activado correctamente." if activo else "Usuario desactivado correctamente.", "success")
    return redirect(url_for("usuarios.listado"))
