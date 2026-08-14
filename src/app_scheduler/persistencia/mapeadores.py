"""Conversion explicita de filas SQL a DTO de persistencia."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from app_scheduler.compartido.errores import ErrorPersistencia
from app_scheduler.persistencia.modelos import (
    Categoria,
    Cliente,
    CredencialUsuario,
    Permiso,
    Rol,
    Tipo,
    Usuario,
)


COLUMNAS_USUARIO = (
    "id_usuario",
    "usuario",
    "nombre_completo",
    "email",
    "debe_cambiar_password",
    "ultimo_login",
    "intentos_fallidos",
    "bloqueado",
    "eliminado_operativo",
    "fecha_eliminado_operativo",
    "fecha_creacion",
    "fecha_actualizacion",
    "activo",
)
COLUMNAS_CREDENCIAL_USUARIO = COLUMNAS_USUARIO + ("password_hash",)
COLUMNAS_ROL = (
    "id_rol",
    "codigo_rol",
    "nombre_rol",
    "descripcion",
    "es_sistema",
    "activo",
)
COLUMNAS_PERMISO = (
    "id_permiso",
    "codigo_permiso",
    "modulo",
    "accion",
    "descripcion",
    "activo",
)
COLUMNAS_CATALOGO = (
    "id",
    "nombre",
    "nombre_normalizado",
    "descripcion",
    "eliminado_operativo",
    "fecha_creacion",
    "fecha_actualizacion",
    "activo",
)


def fila_como_diccionario(
    fila: Sequence[Any], columnas: Sequence[str]
) -> dict[str, Any]:
    if len(fila) != len(columnas):
        raise ErrorPersistencia(
            detalle_tecnico=(
                "El resultado SQL no coincide con el contrato de columnas: "
                f"esperadas={len(columnas)}, recibidas={len(fila)}."
            )
        )
    return dict(zip(columnas, fila, strict=True))


def mapear_usuario(fila: Sequence[Any]) -> Usuario:
    datos = fila_como_diccionario(fila, COLUMNAS_USUARIO)
    return Usuario(
        id_usuario=datos["id_usuario"],
        usuario=datos["usuario"],
        nombre_completo=datos["nombre_completo"],
        email=datos["email"],
        debe_cambiar_password=bool(datos["debe_cambiar_password"]),
        ultimo_login=datos["ultimo_login"],
        intentos_fallidos=datos["intentos_fallidos"],
        bloqueado=bool(datos["bloqueado"]),
        eliminado_operativo=bool(datos["eliminado_operativo"]),
        fecha_eliminado_operativo=datos["fecha_eliminado_operativo"],
        fecha_creacion=datos["fecha_creacion"],
        fecha_actualizacion=datos["fecha_actualizacion"],
        activo=bool(datos["activo"]),
    )


def mapear_credencial_usuario(fila: Sequence[Any]) -> CredencialUsuario:
    datos = fila_como_diccionario(fila, COLUMNAS_CREDENCIAL_USUARIO)
    return CredencialUsuario(
        usuario=mapear_usuario(tuple(datos[columna] for columna in COLUMNAS_USUARIO)),
        password_hash=datos["password_hash"],
    )


def mapear_rol(fila: Sequence[Any]) -> Rol:
    datos = fila_como_diccionario(fila, COLUMNAS_ROL)
    return Rol(
        id_rol=datos["id_rol"],
        codigo_rol=datos["codigo_rol"],
        nombre_rol=datos["nombre_rol"],
        descripcion=datos["descripcion"],
        es_sistema=bool(datos["es_sistema"]),
        activo=bool(datos["activo"]),
    )


def mapear_permiso(fila: Sequence[Any]) -> Permiso:
    datos = fila_como_diccionario(fila, COLUMNAS_PERMISO)
    return Permiso(
        id_permiso=datos["id_permiso"],
        codigo_permiso=datos["codigo_permiso"],
        modulo=datos["modulo"],
        accion=datos["accion"],
        descripcion=datos["descripcion"],
        activo=bool(datos["activo"]),
    )


def _datos_catalogo(fila: Sequence[Any]) -> dict[str, Any]:
    return fila_como_diccionario(fila, COLUMNAS_CATALOGO)


def mapear_cliente(fila: Sequence[Any]) -> Cliente:
    datos = _datos_catalogo(fila)
    return Cliente(
        id_cliente=datos["id"],
        nombre=datos["nombre"],
        nombre_normalizado=datos["nombre_normalizado"],
        descripcion=datos["descripcion"],
        eliminado_operativo=bool(datos["eliminado_operativo"]),
        fecha_creacion=datos["fecha_creacion"],
        fecha_actualizacion=datos["fecha_actualizacion"],
        activo=bool(datos["activo"]),
    )


def mapear_categoria(fila: Sequence[Any]) -> Categoria:
    datos = _datos_catalogo(fila)
    return Categoria(
        id_categoria=datos["id"],
        nombre=datos["nombre"],
        nombre_normalizado=datos["nombre_normalizado"],
        descripcion=datos["descripcion"],
        eliminado_operativo=bool(datos["eliminado_operativo"]),
        fecha_creacion=datos["fecha_creacion"],
        fecha_actualizacion=datos["fecha_actualizacion"],
        activo=bool(datos["activo"]),
    )


def mapear_tipo(fila: Sequence[Any]) -> Tipo:
    datos = _datos_catalogo(fila)
    return Tipo(
        id_tipo=datos["id"],
        nombre=datos["nombre"],
        nombre_normalizado=datos["nombre_normalizado"],
        descripcion=datos["descripcion"],
        eliminado_operativo=bool(datos["eliminado_operativo"]),
        fecha_creacion=datos["fecha_creacion"],
        fecha_actualizacion=datos["fecha_actualizacion"],
        activo=bool(datos["activo"]),
    )
