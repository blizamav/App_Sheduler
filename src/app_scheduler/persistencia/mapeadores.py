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
    Tarea,
    Script,
    VersionScript,
    Programacion,
    Usuario,
)

COLUMNAS_TAREA = (
    "id_tarea", "nombre_tarea", "descripcion", "observacion_tecnica",
    "id_cliente", "cliente", "id_categoria", "categoria", "id_tipo", "tipo",
    "tipo_tarea", "estado_tarea", "permite_ejecucion_manual", "fecha_creacion",
    "fecha_actualizacion", "activo",
)
COLUMNAS_SCRIPT = (
    "id_script", "id_tarea", "nombre_script", "descripcion", "id_version_activa",
    "fecha_creacion", "fecha_actualizacion", "activo",
)
COLUMNAS_VERSION_SCRIPT = (
    "id_version", "id_script", "numero_version", "nombre_archivo", "ruta_fisica",
    "ruta_relativa", "hash_archivo", "estado_version", "es_activa", "requiere_env",
    "ruta_env_fisica", "ruta_env_relativa", "usuario_carga", "fecha_carga",
    "observacion", "fecha_creacion", "fecha_actualizacion",
)
COLUMNAS_PROGRAMACION = (
    "id_programacion", "id_tarea", "nombre_tarea", "estado_tarea",
    "tipo_programacion", "modo_ejecucion_dia", "hora_inicio", "hora_termino",
    "hora_ejecucion", "intervalo_minutos", "dias_semana", "dia_mes",
    "fecha_especifica", "fechas_especificas", "ejecutar_en_feriados",
    "zona_horaria", "fecha_inicio_vigencia", "fecha_fin_vigencia",
    "fecha_creacion", "fecha_actualizacion", "activo",
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


def mapear_tarea(fila: Sequence[Any]) -> Tarea:
    datos = fila_como_diccionario(fila, COLUMNAS_TAREA)
    return Tarea(
        id_tarea=datos["id_tarea"], nombre_tarea=datos["nombre_tarea"],
        descripcion=datos["descripcion"], observacion_tecnica=datos["observacion_tecnica"],
        id_cliente=datos["id_cliente"], cliente=datos["cliente"],
        id_categoria=datos["id_categoria"], categoria=datos["categoria"],
        id_tipo=datos["id_tipo"], tipo=datos["tipo"], tipo_tarea=datos["tipo_tarea"],
        estado_tarea=datos["estado_tarea"],
        permite_ejecucion_manual=bool(datos["permite_ejecucion_manual"]),
        fecha_creacion=datos["fecha_creacion"], fecha_actualizacion=datos["fecha_actualizacion"],
        activo=bool(datos["activo"]),
    )


def mapear_script(fila: Sequence[Any]) -> Script:
    datos = fila_como_diccionario(fila, COLUMNAS_SCRIPT)
    return Script(
        id_script=datos["id_script"], id_tarea=datos["id_tarea"],
        nombre_script=datos["nombre_script"], descripcion=datos["descripcion"],
        id_version_activa=datos["id_version_activa"], fecha_creacion=datos["fecha_creacion"],
        fecha_actualizacion=datos["fecha_actualizacion"], activo=bool(datos["activo"]),
    )


def mapear_version_script(fila: Sequence[Any]) -> VersionScript:
    datos = fila_como_diccionario(fila, COLUMNAS_VERSION_SCRIPT)
    return VersionScript(
        id_version=datos["id_version"], id_script=datos["id_script"],
        numero_version=datos["numero_version"], nombre_archivo=datos["nombre_archivo"],
        ruta_fisica=datos["ruta_fisica"], ruta_relativa=datos["ruta_relativa"],
        hash_archivo=datos["hash_archivo"], estado_version=datos["estado_version"],
        es_activa=bool(datos["es_activa"]), requiere_env=bool(datos["requiere_env"]),
        ruta_env_fisica=datos["ruta_env_fisica"], ruta_env_relativa=datos["ruta_env_relativa"],
        usuario_carga=datos["usuario_carga"], fecha_carga=datos["fecha_carga"],
        observacion=datos["observacion"], fecha_creacion=datos["fecha_creacion"],
        fecha_actualizacion=datos["fecha_actualizacion"],
    )


def mapear_programacion(fila: Sequence[Any]) -> Programacion:
    columnas = COLUMNAS_PROGRAMACION
    if len(fila) == len(COLUMNAS_PROGRAMACION) + 1:
        columnas += ("proxima_ejecucion",)
    datos = fila_como_diccionario(fila, columnas)
    return Programacion(
        id_programacion=datos["id_programacion"], id_tarea=datos["id_tarea"],
        nombre_tarea=datos["nombre_tarea"], estado_tarea=datos["estado_tarea"],
        tipo_programacion=datos["tipo_programacion"],
        modo_ejecucion_dia=datos["modo_ejecucion_dia"], hora_inicio=datos["hora_inicio"],
        hora_termino=datos["hora_termino"], hora_ejecucion=datos["hora_ejecucion"],
        intervalo_minutos=datos["intervalo_minutos"], dias_semana=datos["dias_semana"],
        dia_mes=datos["dia_mes"], fecha_especifica=datos["fecha_especifica"],
        fechas_especificas=datos["fechas_especificas"],
        ejecutar_en_feriados=bool(datos["ejecutar_en_feriados"]),
        zona_horaria=datos["zona_horaria"],
        fecha_inicio_vigencia=datos["fecha_inicio_vigencia"],
        fecha_fin_vigencia=datos["fecha_fin_vigencia"],
        fecha_creacion=datos["fecha_creacion"],
        fecha_actualizacion=datos["fecha_actualizacion"], activo=bool(datos["activo"]),
        proxima_ejecucion=datos.get("proxima_ejecucion"),
    )
