"""Rutas web autorizadas para scripts versionados."""

from flask import Blueprint, current_app, flash, redirect, render_template, request, send_file, url_for

from app_scheduler.compartido.auditoria import ContextoAuditoria
from app_scheduler.compartido.autorizacion import identidad_actual, permiso_requerido
from app_scheduler.compartido.errores import ErrorValidacion


bp_scripts = Blueprint("scripts", __name__)


def _servicio(): return current_app.extensions["servicio_scripts"]
def _contexto(): return ContextoAuditoria(request.remote_addr, request.user_agent.string[:500] or None, request.path, request.method)
def _entero(valor, default=None):
    try: return int(valor)
    except (TypeError, ValueError): return default
def _origen_scripts(): return request.values.get("origen") == "scripts"
def _volver(id_tarea):
    parametros = {"id_tarea": id_tarea}
    if _origen_scripts(): parametros["origen"] = "scripts"
    return redirect(url_for("scripts.detalle", **parametros))
def _archivo(campo="archivo_script"):
    archivo = request.files.get(campo)
    if archivo is None or not archivo.filename: raise ErrorValidacion("Selecciona un archivo.")
    limite = current_app.config["CONFIGURACION_APLICACION"].max_script_size_mb * 1024 * 1024
    return archivo.filename, archivo.stream.read(limite + 1)


@bp_scripts.get("/scripts")
@permiso_requerido("SCRIPTS_VER")
def listado():
    estado = request.args.get("estado", "").strip().upper() or None
    version_activa = request.args.get("version_activa", "").strip() or None
    try:
        resultado = _servicio().listar(
            pagina=max(1, _entero(request.args.get("pagina"), 1)),
            busqueda=request.args.get("buscar", "").strip() or None,
            estado=estado,
            version_activa=version_activa,
        )
    except ErrorValidacion as error:
        flash(error.mensaje, "error"); return redirect(url_for("scripts.listado"))
    return render_template(
        "scripts/listado.html",
        resultado=resultado,
        filtros={
            "buscar": request.args.get("buscar", ""),
            "estado": estado or "",
            "version_activa": version_activa or "",
        },
    )


@bp_scripts.get("/tareas/<int:id_tarea>/scripts")
@permiso_requerido("SCRIPTS_VER")
def detalle(id_tarea):
    try: datos = _servicio().detalle(id_tarea)
    except ErrorValidacion as error:
        flash(error.mensaje, "error"); return redirect(url_for("tareas.listado"))
    return render_template(
        "scripts/detalle.html", origen_scripts=_origen_scripts(), **datos
    )


@bp_scripts.post("/tareas/<int:id_tarea>/scripts/versiones")
@permiso_requerido("SCRIPTS_VERSIONAR")
def subir(id_tarea):
    try:
        nombre, contenido = _archivo()
        _servicio().subir_version(id_tarea, nombre, contenido, request.form.get("observacion"), identidad_actual(), _contexto())
    except ErrorValidacion as error: flash(error.mensaje, "error")
    else: flash("Version cargada correctamente.", "success")
    return _volver(id_tarea)


@bp_scripts.post("/tareas/<int:id_tarea>/scripts/versiones/<int:id_version>/reemplazar")
@permiso_requerido("SCRIPTS_REEMPLAZAR")
def reemplazar(id_tarea, id_version):
    try:
        nombre, contenido = _archivo()
        _servicio().reemplazar(id_tarea, id_version, nombre, contenido, request.form.get("observacion"), identidad_actual(), _contexto())
    except ErrorValidacion as error: flash(error.mensaje, "error")
    else: flash("Slot reemplazado correctamente.", "success")
    return _volver(id_tarea)


@bp_scripts.post("/tareas/<int:id_tarea>/scripts/versiones/<int:id_version>/activar")
@permiso_requerido("SCRIPTS_ACTIVAR_VERSION")
def activar(id_tarea, id_version):
    try: _servicio().activar(id_tarea, id_version, identidad_actual(), _contexto())
    except ErrorValidacion as error: flash(error.mensaje, "error")
    else: flash("Version activa actualizada.", "success")
    return _volver(id_tarea)


@bp_scripts.post("/tareas/<int:id_tarea>/scripts/versiones/<int:id_version>/desactivar")
@permiso_requerido("SCRIPTS_DESACTIVAR")
def desactivar(id_tarea, id_version):
    try: _servicio().desactivar(id_tarea, id_version, identidad_actual(), _contexto())
    except ErrorValidacion as error: flash(error.mensaje, "error")
    else: flash("Version desactivada.", "success")
    return _volver(id_tarea)


@bp_scripts.post("/tareas/<int:id_tarea>/scripts/versiones/<int:id_version>/env")
@permiso_requerido("SCRIPTS_ENV_GESTIONAR")
def guardar_env(id_tarea, id_version):
    archivo = request.files.get("archivo_env")
    texto = request.form.get("contenido_env", "")
    try:
        if archivo and archivo.filename and texto.strip(): raise ErrorValidacion("Usa archivo o texto .env, no ambos.")
        contenido = archivo.stream.read(current_app.config["CONFIGURACION_APLICACION"].max_env_size_kb * 1024 + 1) if archivo and archivo.filename else texto.encode("utf-8")
        _servicio().guardar_env(id_tarea, id_version, contenido, identidad_actual(), _contexto())
    except ErrorValidacion as error: flash(error.mensaje, "error")
    else: flash("Configuracion .env guardada sin exponer su contenido.", "success")
    return _volver(id_tarea)


@bp_scripts.post("/tareas/<int:id_tarea>/scripts/versiones/<int:id_version>/env/quitar")
@permiso_requerido("SCRIPTS_ENV_GESTIONAR")
def quitar_env(id_tarea, id_version):
    try: _servicio().quitar_env(id_tarea, id_version, identidad_actual(), _contexto())
    except ErrorValidacion as error: flash(error.mensaje, "error")
    else: flash("Configuracion .env retirada.", "success")
    return _volver(id_tarea)


@bp_scripts.get("/tareas/<int:id_tarea>/scripts/versiones/<int:id_version>/descargar")
@permiso_requerido("SCRIPTS_VER")
def descargar(id_tarea, id_version):
    try: ruta, nombre = _servicio().obtener_descarga(id_tarea, id_version)
    except ErrorValidacion as error:
        flash(error.mensaje, "error"); return _volver(id_tarea)
    return send_file(ruta, as_attachment=True, download_name=nombre, mimetype="text/x-python")
