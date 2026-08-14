"""Persistencia acotada para clientes, categorias y tipos."""

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
from app_scheduler.persistencia.modelos import Categoria, Cliente, Pagina, Paginacion, Tipo
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

    def listar_paginado(
        self,
        paginacion: Paginacion,
        *,
        activo: bool | None = None,
        busqueda: str | None = None,
    ) -> Pagina[T]:
        e = self._especificacion
        filtros = ["c.eliminado_operativo = 0"]
        parametros: list[object] = []
        if activo is not None:
            filtros.append("c.activo = ?")
            parametros.append(int(activo))
        if busqueda and busqueda.strip():
            filtros.append(
                f"(c.{e.columna_nombre} LIKE ? ESCAPE '~' "
                "OR c.descripcion LIKE ? ESCAPE '~')"
            )
            patron = _patron_like_literal(busqueda.strip())
            parametros.extend((patron, patron))

        where = " AND ".join(filtros)
        total = int(
            self.ejecutar_escalar(
                f"SELECT COUNT(1) FROM dbo.{e.tabla} c WHERE {where}",
                parametros,
                operacion=f"contar_{e.tabla}",
            )
            or 0
        )
        filas = self.ejecutar_lista(
            f"""SELECT {self._seleccion()}
FROM dbo.{e.tabla} c
WHERE {where}
ORDER BY c.{e.columna_nombre}, c.{e.columna_id}
OFFSET ? ROWS FETCH NEXT ? ROWS ONLY""",
            (*parametros, paginacion.desplazamiento, paginacion.por_pagina),
            operacion=f"listar_{e.tabla}_paginado",
        )
        return Pagina(
            elementos=tuple(e.mapeador(fila) for fila in filas),
            total=total,
            pagina=paginacion.pagina,
            por_pagina=paginacion.por_pagina,
        )

    def crear(
        self,
        nombre: str,
        nombre_normalizado: str,
        descripcion: str | None,
        actor: str,
    ) -> int:
        e = self._especificacion
        fila = self.ejecutar_uno(
            f"""INSERT INTO dbo.{e.tabla}
    ({e.columna_nombre}, nombre_normalizado, descripcion, usuario_creacion, activo)
OUTPUT INSERTED.{e.columna_id}
VALUES (?, ?, ?, ?, 1)""",
            (nombre, nombre_normalizado, descripcion, actor),
            operacion=f"crear_{e.tabla}",
        )
        return int(fila[0])

    def actualizar(
        self,
        identificador: int,
        nombre: str,
        nombre_normalizado: str,
        descripcion: str | None,
        actor: str,
    ) -> bool:
        e = self._especificacion
        return self.ejecutar(
            f"""UPDATE dbo.{e.tabla}
SET {e.columna_nombre} = ?,
    nombre_normalizado = ?,
    descripcion = ?,
    usuario_actualizacion = ?,
    fecha_actualizacion = SYSDATETIME()
WHERE {e.columna_id} = ?
  AND eliminado_operativo = 0""",
            (nombre, nombre_normalizado, descripcion, actor, identificador),
            operacion=f"actualizar_{e.tabla}",
        ) > 0

    def cambiar_estado(self, identificador: int, activo: bool, actor: str) -> bool:
        e = self._especificacion
        return self.ejecutar(
            f"""UPDATE dbo.{e.tabla}
SET activo = ?,
    usuario_actualizacion = ?,
    fecha_actualizacion = SYSDATETIME()
WHERE {e.columna_id} = ?
  AND eliminado_operativo = 0""",
            (int(activo), actor, identificador),
            operacion=f"cambiar_estado_{e.tabla}",
        ) > 0


class RepositorioClientes(_RepositorioCatalogo[Cliente]):
    def __init__(self, conexion: ConexionDBAPI):
        super().__init__(conexion, _CLIENTES)


class RepositorioCategorias(_RepositorioCatalogo[Categoria]):
    def __init__(self, conexion: ConexionDBAPI):
        super().__init__(conexion, _CATEGORIAS)


class RepositorioTipos(_RepositorioCatalogo[Tipo]):
    def __init__(self, conexion: ConexionDBAPI):
        super().__init__(conexion, _TIPOS)


def _patron_like_literal(valor: str) -> str:
    escapado = valor.replace("~", "~~").replace("%", "~%").replace("_", "~_")
    return f"%{escapado}%"
