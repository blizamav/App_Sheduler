from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.seguridad import permiso_requerido
from app.servicios.servicio_calendario import (
    cambiar_estado_feriado_admin,
    eliminar_feriado_admin,
    guardar_feriado,
    listar_feriados,
    obtener_feriado_admin,
)


bp_feriados = Blueprint("feriados", __name__, url_prefix="/feriados")


def _filtros_request():
    filtros = {
        "anio": request.args.get("anio", "").strip(),
        "mes": request.args.get("mes", "").strip(),
        "pais": request.args.get("pais", "").strip().upper(),
        "activo": request.args.get("activo", "").strip(),
    }
    normalizados = {}
    for clave, valor in filtros.items():
        if not valor:
            continue
        if clave == "anio":
            try:
                anio = int(valor)
                if 2000 <= anio <= 2100:
                    normalizados[clave] = anio
            except ValueError:
                flash("El ano informado no es valido.", "advertencia")
        elif clave == "mes":
            try:
                mes = int(valor)
                if 1 <= mes <= 12:
                    normalizados[clave] = mes
            except ValueError:
                flash("El mes informado no es valido.", "advertencia")
        elif clave == "activo" and valor in ("activo", "inactivo"):
            normalizados[clave] = valor
        elif clave == "pais":
            normalizados[clave] = valor[:10]
    return normalizados


@bp_feriados.route("/")
@permiso_requerido("FERIADOS_VER")
def listado():
    filtros = _filtros_request()
    try:
        registros = listar_feriados(filtros)
    except Exception:
        registros = []
        flash("No fue posible consultar feriados. Verifica que la migracion 012 este ejecutada.", "error")
    return render_template("feriados/listado.html", registros=registros, filtros=filtros, total_registros=len(registros))


@bp_feriados.route("/nuevo", methods=["GET", "POST"])
@permiso_requerido("FERIADOS_CREAR")
def nuevo():
    registro = {"pais": "CL", "activo": True}
    if request.method == "POST":
        registro = request.form.to_dict()
        ok, mensajes, feriado = guardar_feriado(request.form, session.get("usuario"))
        if ok:
            flash(mensajes[0], "success")
            return redirect(url_for("feriados.editar", id_feriado=feriado["id_feriado"]))
        for mensaje in mensajes:
            flash(mensaje, "info" if mensaje == "No hay cambios para guardar." else "error")
    return render_template("feriados/formulario.html", modo="crear", registro=registro)


@bp_feriados.route("/<int:id_feriado>/editar", methods=["GET", "POST"])
@permiso_requerido("FERIADOS_EDITAR")
def editar(id_feriado):
    registro = obtener_feriado_admin(id_feriado)
    if not registro:
        flash("Feriado no encontrado.", "error")
        return redirect(url_for("feriados.listado"))
    if request.method == "POST":
        datos = request.form.to_dict()
        ok, mensajes, actualizado = guardar_feriado(request.form, session.get("usuario"), id_feriado)
        if ok:
            flash(mensajes[0], "success")
            return redirect(url_for("feriados.listado"))
        for mensaje in mensajes:
            flash(mensaje, "info" if mensaje == "No hay cambios para guardar." else "error")
        registro.update(datos)
    return render_template("feriados/formulario.html", modo="editar", registro=registro)


@bp_feriados.route("/<int:id_feriado>/estado", methods=["POST"])
@permiso_requerido("FERIADOS_ESTADO")
def estado(id_feriado):
    activo = request.form.get("activo") == "1"
    ok, mensaje = cambiar_estado_feriado_admin(id_feriado, activo, session.get("usuario"))
    flash(mensaje, "success" if ok else "error")
    return redirect(url_for("feriados.listado"))


@bp_feriados.route("/<int:id_feriado>/eliminar", methods=["POST"])
@permiso_requerido("FERIADOS_ELIMINAR")
def eliminar(id_feriado):
    ok, mensaje = eliminar_feriado_admin(id_feriado, session.get("usuario"))
    flash(mensaje, "success" if ok else "error")
    return redirect(url_for("feriados.listado"))
