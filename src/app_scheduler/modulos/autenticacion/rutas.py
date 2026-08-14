"""Rutas web de autenticacion del runtime reconstruido."""

from __future__ import annotations

from urllib.parse import urlsplit

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from app_scheduler.compartido.auditoria import ContextoAuditoria
from app_scheduler.compartido.autorizacion import (
    establecer_sesion,
    identidad_actual,
    limpiar_sesion,
)


bp_autenticacion = Blueprint("autenticacion", __name__)


def _servicio():
    return current_app.extensions["servicio_autenticacion"]


def _contexto() -> ContextoAuditoria:
    return ContextoAuditoria(
        ip_origen=request.remote_addr,
        user_agent=request.user_agent.string[:500] or None,
        ruta=request.path,
        metodo_http=request.method,
    )


def _destino_local(valor: str | None) -> str | None:
    if not valor:
        return None
    partes = urlsplit(valor)
    if partes.scheme or partes.netloc or not partes.path.startswith("/"):
        return None
    if partes.path.startswith("//"):
        return None
    return valor


@bp_autenticacion.route("/login", methods=["GET", "POST"])
def login():
    if identidad_actual() is not None:
        return redirect(url_for("base.inicio"))
    siguiente = _destino_local(request.values.get("next"))
    if request.method == "POST":
        resultado = _servicio().autenticar(
            request.form.get("usuario", ""),
            request.form.get("password", ""),
            _contexto(),
        )
        if resultado.exito and resultado.identidad is not None:
            establecer_sesion(resultado.identidad)
            flash(resultado.mensaje, "success")
            return redirect(siguiente or url_for("base.inicio"))
        current_app.logger.warning(
            "Intento de autenticacion rechazado.",
            extra={"evento": "LOGIN_FALLIDO"},
        )
        flash(resultado.mensaje, "error")
    return render_template("autenticacion/login.html", siguiente=siguiente or "")


@bp_autenticacion.post("/logout")
def logout():
    identidad = identidad_actual()
    if identidad is not None:
        _servicio().registrar_logout(identidad, _contexto())
    limpiar_sesion()
    flash("Sesion cerrada correctamente.", "success")
    return redirect(url_for("autenticacion.login"))
