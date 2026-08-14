"""Repositorios de lectura para clientes, categorias y tipos."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Sequence
from typing import Any, Callable, Generic, TypeVar

from app_scheduler.compartido.base_datos import ConexionDBAPI
from app_scheduler.persistencia.mapeadores import (
    mapear_categoria,
    mapear_cliente,
    mapear_tipo,
)
from app_scheduler.persistencia.modelos import Categoria, Cliente, Tipo
from app_scheduler.persistencia.repositorio import RepositorioSQL


T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class _EspecificacionCatalogo(Generic[T]):
    tabla: str
    columna_id: str
    columna_nombre: str
    mapeador: Callable[[Sequence[Any]], T]


_CLIENTES = _EspecificacionCatalogo(
    tabla="clientes",
    columna_id="id_cliente",
    columna_nombre="nombre_cliente",
    mapeador=mapear_cliente,
)
_CATEGORIAS = _EspecificacionCatalogo(
    tabla="categorias",
    columna_id="id_categoria",
    columna_nombre="nombre_categoria",
    mapeador=mapear_categoria,
)
_TIPOS = _EspecificacionCatalogo(
    tabla="tipos",
    columna_id="id_tipo",
    columna_nombre="nombre_tipo",
    mapeador=mapear_tipo,
)
_ESPECIFICACIONES_PERMITIDAS = {
    ("clientes", "id_cliente", "nombre_cliente"),
    ("categorias", "id_categoria", "nombre_categoria"),
    ("tipos", "id_tipo", "nombre_tipo"),
}


class _RepositorioCatalogo(RepositorioSQL, Generic[T]):
    """Comparte consultas solo entre tres especificaciones internas e inmutables."""

    def __init__(
        self,
        conexion: ConexionDBAPI,
        especificacion: _EspecificacionCatalogo[T],
    ):
        super().__init__(conexion)
        clave = (
            especificacion.tabla,
            especificacion.columna_id,
            especificacion.columna_nombre,
        )
        if clave not in _ESPECIFICACIONES_PERMITIDAS:
            raise ValueError("Especificacion de catalogo no permitida.")
        self._especificacion = especificacion

    def _seleccion(self) -> str:
        e = self._especificacion
        return f"""c.{e.columna_id} AS id,
    c.{e.columna_nombre} AS nombre,
    c.nombre_normalizado,
    c.descripcion,
    c.eliminado_operativo,
    c.fecha_creacion,
    c.fecha_actualizacion,
    c.activo"""

    def obtener_por_id(self, identificador: int) -> T | None:
        e = self._especificacion
        sql = f"""SELECT {self._seleccion()}
FROM dbo.{e.tabla} c
WHERE c.{e.columna_id} = ?
  AND c.eliminado_operativo = 0"""
        fila = self.ejecutar_uno(
            sql,
            (identificador,),
            operacion=f"obtener_{e.tabla}_por_id",
        )
        return None if fila is None else e.mapeador(fila)

    def buscar_por_clave(self, nombre_normalizado: str) -> T | None:
        e = self._especificacion
        sql = f"""SELECT {self._seleccion()}
FROM dbo.{e.tabla} c
WHERE c.nombre_normalizado = ?"""
        fila = self.ejecutar_uno(
            sql,
            (nombre_normalizado,),
            operacion=f"buscar_{e.tabla}_por_clave",
        )
        return None if fila is None else e.mapeador(fila)

    def listar(
        self,
        *,
        solo_activos: bool = False,
        incluir_eliminados: bool = False,
    ) -> tuple[T, ...]:
        e = self._especificacion
        filtros: list[str] = []
        if not incluir_eliminados:
            filtros.append("c.eliminado_operativo = 0")
        if solo_activos:
            filtros.append("c.activo = 1")
        where = f"WHERE {' AND '.join(filtros)}" if filtros else ""
        sql = f"""SELECT {self._seleccion()}
FROM dbo.{e.tabla} c
{where}
ORDER BY c.{e.columna_nombre}, c.{e.columna_id}"""
        filas = self.ejecutar_lista(sql, operacion=f"listar_{e.tabla}")
        return tuple(e.mapeador(fila) for fila in filas)


class RepositorioClientes(_RepositorioCatalogo[Cliente]):
    def __init__(self, conexion: ConexionDBAPI):
        super().__init__(conexion, _CLIENTES)


class RepositorioCategorias(_RepositorioCatalogo[Categoria]):
    def __init__(self, conexion: ConexionDBAPI):
        super().__init__(conexion, _CATEGORIAS)


class RepositorioTipos(_RepositorioCatalogo[Tipo]):
    def __init__(self, conexion: ConexionDBAPI):
        super().__init__(conexion, _TIPOS)
