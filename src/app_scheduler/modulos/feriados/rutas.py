"""Rutas protegidas del calendario local y su sincronizacion manual."""

from __future__ import annotations

from datetime import date

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for

from app_scheduler.compartido.auditoria import ContextoAuditoria
from app_scheduler.compartido.autorizacion import identidad_actual, permiso_requerido
from app_scheduler.compartido.errores import ErrorValidacion


bp_feriados = Blueprint("feriados", __name__, url_prefix="/feriados")


def _servicio():
    return current_app.extensions["servicio_feriados"]


def _contexto():
    return ContextoAuditoria(
        request.remote_addr, request.user_agent.string[:500] or None,
        request.path, request.method,
    )


def _entero(valor, defecto=1):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return defecto


def _datos():
    return {clave: request.form.get(clave, "") for clave in (
        "fecha", "nombre", "tipo", "pais", "irrenunciable", "observacion"
    )}


@bp_feriados.get("/")
@permiso_requerido("FERIADOS_VER")
def listado():
    estado = request.args.get("estado", "").strip()
    activo = {"activo": True, "inactivo": False}.get(estado)
    try:
        resultado = _servicio().listar(
            pagina=max(1, _entero(request.args.get("pagina"))),
            anio=request.args.get("anio"), pais=request.args.get("pais"),
            origen=request.args.get("origen"), activo=activo,
            busqueda=request.args.get("buscar"),
        )
    except ErrorValidacion as error:
        flash(error.mensaje, "error")
        return redirect(url_for("feriados.listado"))
    return render_template(
        "feriados/listado.html", resultado=resultado,
        filtros={"anio": request.args.get("anio", ""), "pais": request.args.get("pais", ""),
                 "origen": request.args.get("origen", ""), "estado": estado,
                 "buscar": request.args.get("buscar", "")},
    )


@bp_feriados.route("/nuevo", methods=["GET", "POST"])
@permiso_requerido("FERIADOS_CREAR")
def nuevo():
    datos = {"fecha": "", "nombre": "", "tipo": "", "pais": "CL",
             "irrenunciable": "", "observacion": ""}
    if request.method == "POST":
        datos = _datos()
        try:
            _servicio().crear(datos, identidad_actual(), _contexto())
        except ErrorValidacion as error:
            flash(error.mensaje, "error")
        else:
            flash("Feriado manual creado correctamente.", "success")
            return redirect(url_for("feriados.listado"))
    return render_template("feriados/formulario.html", modo="crear", datos=datos)


@bp_feriados.route("/<int:id_feriado>/editar", methods=["GET", "POST"])
@permiso_requerido("FERIADOS_EDITAR")
def editar(id_feriado):
    actual = _servicio().obtener(id_feriado)
    if actual is None:
        abort(404)
    datos = {"fecha": actual.fecha.isoformat(), "nombre": actual.nombre,
             "tipo": actual.tipo or "", "pais": actual.pais,
             "irrenunciable": "1" if actual.irrenunciable else "",
             "observacion": actual.observacion or ""}
    if request.method == "POST":
        datos = _datos()
        try:
            _servicio().actualizar(id_feriado, datos, identidad_actual(), _contexto())
        except ErrorValidacion as error:
            flash(error.mensaje, "error")
        else:
            flash("Feriado actualizado correctamente.", "success")
            return redirect(url_for("feriados.listado"))
    return render_template("feriados/formulario.html", modo="editar", datos=datos, actual=actual)


@bp_feriados.post("/<int:id_feriado>/estado")
@permiso_requerido("FERIADOS_ESTADO")
def estado(id_feriado):
    valor = request.form.get("activo")
    if valor not in {"0", "1"}:
        flash("El estado solicitado no es valido.", "error")
    else:
        try:
            _servicio().cambiar_estado(id_feriado, valor == "1", identidad_actual(), _contexto())
        except ErrorValidacion as error:
            flash(error.mensaje, "error")
        else:
            flash("Estado del feriado actualizado.", "success")
    return redirect(url_for("feriados.listado"))


@bp_feriados.post("/<int:id_feriado>/eliminar")
@permiso_requerido("FERIADOS_ELIMINAR")
def eliminar(id_feriado):
    try:
        _servicio().eliminar(id_feriado, identidad_actual(), _contexto())
    except ErrorValidacion as error:
        flash(error.mensaje, "error")
    else:
        flash("Feriado manual eliminado definitivamente.", "success")
    return redirect(url_for("feriados.listado"))


@bp_feriados.get("/sincronizar")
@permiso_requerido("FERIADOS_SINCRONIZAR")
def sincronizar():
    return render_template("feriados/sincronizar.html", anio=date.today().year, pais="CL")


@bp_feriados.post("/sincronizar/preview")
@permiso_requerido("FERIADOS_SINCRONIZAR")
def preview_sincronizacion():
    try:
        preview = _servicio().previsualizar(
            request.form.get("anio"), request.form.get("pais"),
            identidad_actual(), _contexto(),
        )
    except ErrorValidacion as error:
        flash(error.mensaje, "error")
        return redirect(url_for("feriados.sincronizar"))
    return render_template("feriados/sincronizar.html", preview=preview,
                           anio=preview["anio"], pais=preview["pais"])


@bp_feriados.post("/sincronizar/aplicar")
@permiso_requerido("FERIADOS_SINCRONIZAR")
def aplicar_sincronizacion():
    try:
        resumen = _servicio().sincronizar(
            request.form.get("anio"), request.form.get("pais"),
            identidad_actual(), _contexto(),
        )
    except ErrorValidacion as error:
        flash(error.mensaje, "error")
        return redirect(url_for("feriados.sincronizar"))
    flash(
        "Sincronizacion completada: "
        f"{resumen['insertados']} insertados, {resumen['actualizados']} actualizados y "
        f"{resumen['sin_cambios']} sin cambios.",
        "success",
    )
    return redirect(url_for("feriados.listado", anio=request.form.get("anio"), pais=request.form.get("pais")))
