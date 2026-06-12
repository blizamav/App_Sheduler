from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, session, url_for

from app.seguridad import login_requerido
from app.servicios.servicio_logs_sistema import registrar_log_sistema

bp_principal = Blueprint("principal", __name__)


@bp_principal.route("/")
def inicio():
    if session.get("usuario"):
        return redirect(url_for("principal.panel"))
    return redirect(url_for("principal.login"))


@bp_principal.route("/login", methods=["GET", "POST"])
def login():
    """Valida primero el usuario .env y luego usuarios activos de base de datos."""
    if session.get("usuario"):
        return redirect(url_for("principal.panel"))

    advertencias_configuracion = current_app.config.get("ADVERTENCIAS_CONFIGURACION", [])

    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        password = request.form.get("password", "")
        usuario_esperado = current_app.config["USUARIO_ADMIN_DEFECTO"]
        password_esperado = current_app.config["PASSWORD_ADMIN_DEFECTO"]

        if usuario == usuario_esperado and password and password == password_esperado:
            session.clear()
            session["usuario"] = usuario
            session["usuario_nombre"] = usuario
            session["id_usuario"] = None
            session["roles"] = ["SUPER_ADMIN_ENV"]
            session["permisos"] = ["*"]
            session["es_admin_env"] = True
            registrar_log_sistema(
                "LOGIN_EXITOSO",
                "AUTH",
                "Login correcto con administrador inicial desde .env.",
                usuario=usuario,
            )
            flash("Sesion iniciada correctamente.", "success")
            return redirect(url_for("principal.panel"))

        try:
            from app.servicios.servicio_usuarios import autenticar_usuario_bd

            ok, mensaje, datos_usuario = autenticar_usuario_bd(usuario, password)
        except Exception:
            ok = False
            mensaje = "No fue posible validar el usuario en este momento. Revisa la conexion."
            datos_usuario = None
            registrar_log_sistema(
                "LOGIN_ERROR",
                "AUTH",
                "Error al intentar validar usuario de base de datos.",
                usuario=usuario,
                nivel="ERROR",
            )

        if ok:
            session.clear()
            session["usuario"] = datos_usuario["usuario"]
            session["usuario_nombre"] = datos_usuario["nombre_completo"]
            session["id_usuario"] = datos_usuario["id_usuario"]
            session["roles"] = datos_usuario["roles"]
            session["permisos"] = datos_usuario["permisos"]
            session["es_admin_env"] = False
            flash(mensaje, "success")
            return redirect(url_for("principal.panel"))

        flash(mensaje, "error")

    return render_template("login.html", advertencias_configuracion=advertencias_configuracion)


@bp_principal.route("/panel")
@login_requerido
def panel():
    resumen = {
        "total_tareas": 0,
        "tareas_activas": 0,
        "tareas_inactivas": 0,
        "estado_scheduler": "Pendiente de implementar",
    }
    return render_template("panel.html", resumen=resumen)


@bp_principal.route("/diagnostico/bd")
@login_requerido
def diagnostico_bd():
    """Muestra diagnostico controlado de conexion a base de datos en LOCAL/QA."""
    ambiente = current_app.config.get("APP_ENV", "LOCAL").upper()
    if ambiente not in {"LOCAL", "QA"}:
        abort(404)

    from app.database.conexion import probar_conexion_bd

    resultado = probar_conexion_bd()
    return render_template("diagnostico_bd.html", resultado=resultado, ambiente=ambiente)


@bp_principal.route("/logout", methods=["POST"])
@login_requerido
def logout():
    session.clear()
    flash("Sesion cerrada.", "success")
    return redirect(url_for("principal.login"))
