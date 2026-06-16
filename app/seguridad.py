from functools import wraps

from flask import abort, flash, redirect, session, url_for


def login_requerido(vista):
    """Protege rutas internas validando que exista usuario en sesion."""

    @wraps(vista)
    def wrapper(*args, **kwargs):
        if not session.get("usuario"):
            return redirect(url_for("principal.login"))
        return vista(*args, **kwargs)

    return wrapper


def usuario_env_admin():
    """Indica si la sesion corresponde al administrador inicial desde .env."""
    return bool(session.get("es_admin_env"))


def usuario_tiene_permiso(codigo_permiso):
    """Valida permisos guardados en sesion sin consultar base de datos."""
    permisos = session.get("permisos", [])
    roles = session.get("roles", [])

    if usuario_env_admin() or "*" in permisos or "SUPER_ADMIN" in roles:
        return True

    if codigo_permiso in permisos:
        return True

    if codigo_permiso.startswith("USUARIOS_") and "USUARIOS_ADMIN" in permisos:
        return True

    for prefijo in ("CLIENTES_", "CATEGORIAS_", "TIPOS_", "SCRIPTS_", "EJECUCIONES_", "SCHEDULER_"):
        if codigo_permiso.startswith(prefijo) and f"{prefijo}ADMIN" in permisos:
            return True

    if codigo_permiso == "TAREAS_ESTADO" and (
        "TAREAS_ACTIVAR" in permisos or "TAREAS_SUSPENDER" in permisos
    ):
        return True

    return False


def permiso_requerido(codigo_permiso):
    """Protege rutas por permiso funcional."""

    def decorador(vista):
        @wraps(vista)
        def wrapper(*args, **kwargs):
            if not session.get("usuario"):
                return redirect(url_for("principal.login"))

            if not usuario_tiene_permiso(codigo_permiso):
                flash("No tienes permisos suficientes para acceder a esta seccion.", "error")
                return abort(403)

            return vista(*args, **kwargs)

        return wrapper

    return decorador
