"""Identidad de sesion y autorizacion backend compartida."""

from __future__ import annotations

from dataclasses import dataclass
from functools import wraps
from typing import Callable

from flask import current_app, g, redirect, request, session, url_for

from app_scheduler.compartido.errores import ErrorAutorizacion


CLAVE_IDENTIDAD = "_identidad"
TIPO_BASE_DATOS = "BASE_DATOS"
TIPO_SUPER_ADMIN_ENV = "SUPER_ADMIN_ENV"


@dataclass(frozen=True, slots=True)
class IdentidadSesion:
    id_usuario: int | None
    usuario: str
    nombre: str
    tipo_identidad: str
    roles: frozenset[str]
    permisos: frozenset[str]

    @property
    def es_super_admin_env(self) -> bool:
        return self.tipo_identidad == TIPO_SUPER_ADMIN_ENV

    def tiene_permiso(self, codigo: str) -> bool:
        return self.es_super_admin_env or "*" in self.permisos or codigo in self.permisos


def iniciar_autorizacion(
    app,
    cargador: Callable[[dict[str, object]], IdentidadSesion | None],
) -> None:
    app.extensions["cargador_identidad"] = cargador
    app.jinja_env.globals["identidad_actual"] = identidad_actual


def establecer_sesion(identidad: IdentidadSesion) -> None:
    session.clear()
    session[CLAVE_IDENTIDAD] = {
        "tipo": identidad.tipo_identidad,
        "id_usuario": identidad.id_usuario,
        "usuario": identidad.usuario,
    }
    session.modified = True
    g.identidad_actual = identidad


def limpiar_sesion() -> None:
    session.clear()
    g.pop("identidad_actual", None)


def identidad_actual() -> IdentidadSesion | None:
    if "identidad_actual" in g:
        return g.identidad_actual
    datos = session.get(CLAVE_IDENTIDAD)
    if not isinstance(datos, dict):
        g.identidad_actual = None
        return None
    cargador = current_app.extensions.get("cargador_identidad")
    identidad = cargador(datos) if cargador else None
    if identidad is None:
        limpiar_sesion()
    g.identidad_actual = identidad
    return identidad


def _redireccion_login():
    siguiente = request.full_path.rstrip("?")
    return redirect(url_for("autenticacion.login", next=siguiente))


def sesion_requerida(vista):
    @wraps(vista)
    def wrapper(*args, **kwargs):
        if identidad_actual() is None:
            return _redireccion_login()
        return vista(*args, **kwargs)

    return wrapper


def permiso_requerido(codigo: str):
    def decorador(vista):
        @wraps(vista)
        def wrapper(*args, **kwargs):
            identidad = identidad_actual()
            if identidad is None:
                return _redireccion_login()
            if not identidad.tiene_permiso(codigo):
                raise ErrorAutorizacion()
            return vista(*args, **kwargs)

        return wrapper

    return decorador
