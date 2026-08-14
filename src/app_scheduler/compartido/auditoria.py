"""Construccion segura de eventos de auditoria funcional."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping

from app_scheduler.persistencia.modelos import EventoAuditoria


CLAVES_SENSIBLES = (
    "password",
    "contrasena",
    "hash",
    "secret",
    "token",
    "cookie",
    "connection",
    "cadena_conexion",
)


@dataclass(frozen=True, slots=True)
class ContextoAuditoria:
    ip_origen: str | None = None
    user_agent: str | None = None
    ruta: str | None = None
    metodo_http: str | None = None


def _es_sensible(clave: object) -> bool:
    texto = str(clave).lower()
    return any(fragmento in texto for fragmento in CLAVES_SENSIBLES)


def sanitizar_valores(valor: Any) -> Any:
    if isinstance(valor, Mapping):
        return {
            str(clave): "[PROTEGIDO]" if _es_sensible(clave) else sanitizar_valores(contenido)
            for clave, contenido in valor.items()
        }
    if isinstance(valor, (list, tuple, set, frozenset)):
        return [sanitizar_valores(item) for item in valor]
    if valor is None or isinstance(valor, (str, int, float, bool)):
        return valor
    return str(valor)


def serializar_valores(valor: Any) -> str | None:
    if valor is None:
        return None
    return json.dumps(sanitizar_valores(valor), ensure_ascii=True, sort_keys=True)


def crear_evento_auditoria(
    *,
    usuario: str,
    accion: str,
    entidad: str,
    contexto: ContextoAuditoria | None = None,
    id_usuario: int | None = None,
    id_entidad: object | None = None,
    nombre_entidad: str | None = None,
    descripcion: str | None = None,
    valores_antes: Any = None,
    valores_despues: Any = None,
    resultado: str = "OK",
    modulo: str = "SEGURIDAD",
) -> EventoAuditoria:
    contexto = contexto or ContextoAuditoria()
    return EventoAuditoria(
        usuario=usuario or "sistema",
        id_usuario=id_usuario,
        accion=accion,
        entidad=entidad,
        id_entidad=None if id_entidad is None else str(id_entidad),
        nombre_entidad=nombre_entidad,
        descripcion=descripcion,
        valores_antes=serializar_valores(valores_antes),
        valores_despues=serializar_valores(valores_despues),
        ip_origen=contexto.ip_origen,
        user_agent=contexto.user_agent,
        resultado=resultado,
        modulo=modulo,
        ruta=contexto.ruta,
        metodo_http=contexto.metodo_http,
    )
