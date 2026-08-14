"""Ayudas SQL acotadas; no implementan un CRUD generico."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from app_scheduler.compartido.base_datos import ConexionDBAPI


class RepositorioSQL:
    def __init__(self, conexion: ConexionDBAPI):
        self.conexion = conexion

    def ejecutar_uno(self, sql: str, parametros: Sequence[Any] = ()):
        cursor = self.conexion.cursor()
        try:
            cursor.execute(sql, tuple(parametros))
            return cursor.fetchone()
        finally:
            cursor.close()

    def ejecutar_lista(self, sql: str, parametros: Sequence[Any] = ()) -> list[Any]:
        cursor = self.conexion.cursor()
        try:
            cursor.execute(sql, tuple(parametros))
            return list(cursor.fetchall())
        finally:
            cursor.close()


class RepositorioDiagnosticoSQL(RepositorioSQL):
    """Ejemplo tecnico minimo; no consulta tablas funcionales."""

    def conexion_responde(self) -> bool:
        fila = self.ejecutar_uno("SELECT CAST(1 AS int)")
        return bool(fila and fila[0] == 1)
