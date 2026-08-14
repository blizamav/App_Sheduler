"""Rutas autorizadas de clientes, categorias y tipos."""

from __future__ import annotations

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from app_scheduler.compartido.auditoria import ContextoAuditoria
from app_scheduler.compartido.autorizacion import identidad_actual, permiso_requerido
from app_scheduler.compartido.errores import ErrorValidacion
from app_scheduler.modulos.catalogos.casos_uso import CATALOGOS, DefinicionCatalogo


bp_catalogos = Blueprint("catalogos", __name__)


def _servicio():
    return current_app.extensions["servicio_catalogos"]


def _contexto() -> ContextoAuditoria:
    return ContextoAuditoria(
        ip_origen=request.remote_addr,
        user_agent=request.user_agent.string[:500] or None,
        ruta=request.path,
        metodo_http=request.method,
    )


def _entero(valor, default=1):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return default


def _datos_formulario() -> dict[str, str]:
    return {
        "nombre": request.form.get("nombre", ""),
        "descripcion": request.form.get("descripcion", ""),
    }


def _registrar_rutas(definicion: DefinicionCatalogo) -> None:
    clave = definicion.clave

    def listado():
        estado = request.args.get("estado", "").strip()
        activo = {"activo": True, "inactivo": False}.get(estado)
        pagina = max(1, _entero(request.args.get("pagina"), 1))
        resultado = _servicio().listar(
            clave,
            pagina=pagina,
            activo=activo,
            busqueda=request.args.get("buscar", "").strip() or None,
        )
        return render_template(
            "catalogos/listado.html",
            config=definicion,
            resultado=resultado,
            filtros={"estado": estado, "buscar": request.args.get("buscar", "")},
        )

    def nuevo():
        datos = {"nombre": "", "descripcion": ""}
        if request.method == "POST":
            datos = _datos_formulario()
            try:
                identificador = _servicio().crear(
                    clave, datos, identidad_actual(), _contexto()
                )
            except ErrorValidacion as error:
                flash(error.mensaje, "error")
            else:
                flash(f"{definicion.singular.capitalize()} creado correctamente.", "success")
                return redirect(
                    url_for(f"catalogos.{clave}_editar", id_registro=identificador)
                )
        return render_template(
            "catalogos/formulario.html", config=definicion, modo="crear", datos=datos
        )

    def editar(id_registro: int):
        actual = _servicio().obtener(clave, id_registro)
        if actual is None:
            flash(f"{definicion.singular.capitalize()} no encontrado.", "error")
            return redirect(url_for(f"catalogos.{clave}_listado"))
        datos = {"nombre": actual.nombre, "descripcion": actual.descripcion or ""}
        if request.method == "POST":
            datos = _datos_formulario()
            try:
                _servicio().actualizar(
                    clave, id_registro, datos, identidad_actual(), _contexto()
                )
            except ErrorValidacion as error:
                flash(error.mensaje, "error")
            else:
                flash(f"{definicion.singular.capitalize()} actualizado correctamente.", "success")
                return redirect(url_for(f"catalogos.{clave}_listado"))
        return render_template(
            "catalogos/formulario.html",
            config=definicion,
            modo="editar",
            datos=datos,
            actual=actual,
        )

    def estado(id_registro: int):
        valor = request.form.get("activo")
        if valor not in {"0", "1"}:
            flash("El estado solicitado no es valido.", "error")
            return redirect(url_for(f"catalogos.{clave}_listado"))
        activo = valor == "1"
        try:
            _servicio().cambiar_estado(
                clave, id_registro, activo, identidad_actual(), _contexto()
            )
        except ErrorValidacion as error:
            flash(error.mensaje, "error")
        else:
            texto = "activado" if activo else "desactivado"
            flash(f"{definicion.singular.capitalize()} {texto} correctamente.", "success")
        return redirect(url_for(f"catalogos.{clave}_listado"))

    bp_catalogos.add_url_rule(
        f"/{clave}/",
        endpoint=f"{clave}_listado",
        view_func=permiso_requerido(definicion.permiso_ver)(listado),
        methods=["GET"],
    )
    bp_catalogos.add_url_rule(
        f"/{clave}/nuevo",
        endpoint=f"{clave}_nuevo",
        view_func=permiso_requerido(definicion.permiso_crear)(nuevo),
        methods=["GET", "POST"],
    )
    bp_catalogos.add_url_rule(
        f"/{clave}/<int:id_registro>/editar",
        endpoint=f"{clave}_editar",
        view_func=permiso_requerido(definicion.permiso_editar)(editar),
        methods=["GET", "POST"],
    )
    bp_catalogos.add_url_rule(
        f"/{clave}/<int:id_registro>/estado",
        endpoint=f"{clave}_estado",
        view_func=permiso_requerido(definicion.permiso_estado)(estado),
        methods=["POST"],
    )


for _definicion in CATALOGOS.values():
    _registrar_rutas(_definicion)
