from functools import wraps

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, session, url_for


bp_principal = Blueprint("principal", __name__)


def login_requerido(vista):
    """Protege rutas internas validando que exista usuario en sesion."""

    @wraps(vista)
    def wrapper(*args, **kwargs):
        if not session.get("usuario"):
            return redirect(url_for("principal.login"))
        return vista(*args, **kwargs)

    return wrapper


@bp_principal.route("/")
def inicio():
    if session.get("usuario"):
        return redirect(url_for("principal.panel"))
    return redirect(url_for("principal.login"))


@bp_principal.route("/login", methods=["GET", "POST"])
def login():
    """Valida el usuario inicial desde .env y abre una sesion local."""
    if session.get("usuario"):
        return redirect(url_for("principal.panel"))

    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        password = request.form.get("password", "")
        usuario_esperado = current_app.config["USUARIO_ADMIN_DEFECTO"]
        password_esperado = current_app.config["PASSWORD_ADMIN_DEFECTO"]

        if usuario == usuario_esperado and password and password == password_esperado:
            session["usuario"] = usuario
            flash("Sesion iniciada correctamente.", "success")
            return redirect(url_for("principal.panel"))

        flash("Usuario o contrasena no validos.", "error")

    return render_template("login.html")


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
