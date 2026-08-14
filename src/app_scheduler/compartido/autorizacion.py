"""Fundamentos de identidad y autorizacion para los modulos futuros."""

from __future__ import annotations

from dataclasses import dataclass
from functools import wraps

from flask import redirect, session, url_for

from app_scheduler.compartido.errores import ErrorAutorizacion


@dataclass(frozen=True, slots=True)
class IdentidadSesion:
    usuario: str
    nombre: str
    roles: frozenset[str]
    permisos: frozenset[str]
    es_super_admin_env: bool = False

    def tiene_permiso(self, codigo: str) -> bool:
        return (
            self.es_super_admin_env
            or "*" in self.permisos
            or "SUPER_ADMIN" in self.roles
            or codigo in self.permisos
        )


def identidad_actual() -> IdentidadSesion | None:
    usuario = str(session.get("usuario") or "").strip()
    if not usuario:
        return None
    return IdentidadSesion(
        usuario=usuario,
        nombre=str(session.get("usuario_nombre") or usuario),
        roles=frozenset(session.get("roles") or ()),
        permisos=frozenset(session.get("permisos") or ()),
        es_super_admin_env=bool(session.get("es_admin_env")),
    )


def sesion_requerida(vista):
    @wraps(vista)
    def wrapper(*args, **kwargs):
        if identidad_actual() is None:
            return redirect(url_for("base.inicio"))
        return vista(*args, **kwargs)

    return wrapper


def permiso_requerido(codigo: str):
    def decorador(vista):
        @wraps(vista)
        def wrapper(*args, **kwargs):
            identidad = identidad_actual()
            if identidad is None or not identidad.tiene_permiso(codigo):
                raise ErrorAutorizacion()
            return vista(*args, **kwargs)

        return wrapper

    return decorador
