from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.seguridad import permiso_requerido
from app.servicios.servicio_mantenedores import (
    actualizar_mantenedor,
    cambiar_estado_mantenedor,
    crear_mantenedor,
    eliminar_mantenedor,
    listar_mantenedor,
    obtener_config_mantenedor,
    obtener_mantenedor,
)


bp_mantenedores = Blueprint("mantenedores", __name__)


ENTIDADES = {
    "clientes": {"url": "/clientes", "endpoint": "clientes", "permiso": "CLIENTES"},
    "categorias": {"url": "/categorias", "endpoint": "categorias", "permiso": "CATEGORIAS"},
    "tipos": {"url": "/tipos", "endpoint": "tipos", "permiso": "TIPOS"},
}


def _filtros_request():
    filtros = {
        "estado": request.args.get("estado", "").strip(),
        "buscar": request.args.get("buscar", "").strip(),
    }
    return {clave: valor for clave, valor in filtros.items() if valor}


def _registrar_rutas(entidad, datos):
    permiso_base = datos["permiso"]

    @bp_mantenedores.route(datos["url"] + "/", endpoint=f"{datos['endpoint']}_listado")
    @permiso_requerido(f"{permiso_base}_VER")
    def listado(entidad=entidad):
        config = obtener_config_mantenedor(entidad)
        filtros = _filtros_request()
        try:
            registros = listar_mantenedor(entidad, filtros)
        except Exception:
            registros = []
            flash("No fue posible consultar registros en este momento.", "error")

        return render_template(
            "mantenedores/listado.html",
            entidad=entidad,
            config=config,
            registros=registros,
            filtros=filtros,
            total_registros=len(registros),
        )

    @bp_mantenedores.route(datos["url"] + "/nuevo", methods=["GET", "POST"], endpoint=f"{datos['endpoint']}_nuevo")
    @permiso_requerido(f"{permiso_base}_CREAR")
    def nuevo(entidad=entidad):
        config = obtener_config_mantenedor(entidad)
        registro = {}
        if request.method == "POST":
            registro = request.form.to_dict()
            ok, mensajes, id_registro = crear_mantenedor(entidad, registro, session.get("usuario"))
            if ok:
                flash(mensajes[0], "success")
                return redirect(url_for(f"mantenedores.{ENTIDADES[entidad]['endpoint']}_editar", id_registro=id_registro))

            for mensaje in mensajes:
                flash(mensaje, "error")

        return render_template("mantenedores/formulario.html", entidad=entidad, config=config, modo="crear", registro=registro)

    @bp_mantenedores.route(
        datos["url"] + "/<int:id_registro>/editar",
        methods=["GET", "POST"],
        endpoint=f"{datos['endpoint']}_editar",
    )
    @permiso_requerido(f"{permiso_base}_EDITAR")
    def editar(id_registro, entidad=entidad):
        config = obtener_config_mantenedor(entidad)
        registro = obtener_mantenedor(entidad, id_registro)
        if not registro:
            flash("Registro no encontrado.", "error")
            return redirect(url_for(f"mantenedores.{ENTIDADES[entidad]['endpoint']}_listado"))

        if request.method == "POST":
            datos_formulario = request.form.to_dict()
            ok, mensajes = actualizar_mantenedor(entidad, id_registro, datos_formulario, session.get("usuario"))
            if ok:
                for mensaje in mensajes:
                    flash(mensaje, "success")
                return redirect(url_for(f"mantenedores.{ENTIDADES[entidad]['endpoint']}_listado"))

            for mensaje in mensajes:
                flash(mensaje, "error")
            registro.update(datos_formulario)

        return render_template("mantenedores/formulario.html", entidad=entidad, config=config, modo="editar", registro=registro)

    @bp_mantenedores.route(datos["url"] + "/<int:id_registro>/estado", methods=["POST"], endpoint=f"{datos['endpoint']}_estado")
    @permiso_requerido(f"{permiso_base}_ESTADO")
    def estado(id_registro, entidad=entidad):
        activo = request.form.get("activo") == "1"
        ok, mensaje = cambiar_estado_mantenedor(entidad, id_registro, activo, session.get("usuario"))
        flash(mensaje, "success" if ok else "error")
        return redirect(url_for(f"mantenedores.{ENTIDADES[entidad]['endpoint']}_listado"))

    @bp_mantenedores.route(datos["url"] + "/<int:id_registro>/eliminar", methods=["POST"], endpoint=f"{datos['endpoint']}_eliminar")
    @permiso_requerido(f"{permiso_base}_ESTADO")
    def eliminar_registro(id_registro, entidad=entidad):
        ok, mensaje = eliminar_mantenedor(entidad, id_registro, session.get("usuario"))
        flash(mensaje, "success" if ok else "error")
        return redirect(url_for(f"mantenedores.{ENTIDADES[entidad]['endpoint']}_listado"))


for nombre_entidad, datos_entidad in ENTIDADES.items():
    _registrar_rutas(nombre_entidad, datos_entidad)
