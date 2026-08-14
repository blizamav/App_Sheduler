"""Dobles de DB-API que conservan SQL, parametros y limites transaccionales."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ResultadoSQL:
    fila: Any = None
    filas: list[Any] = field(default_factory=list)
    rowcount: int = 0
    error: Exception | None = None


class CursorProgramado:
    def __init__(self, conexion: "ConexionProgramada", resultado: ResultadoSQL):
        self._conexion = conexion
        self._resultado = resultado
        self.cerrado = False
        self.rowcount = resultado.rowcount

    def execute(self, sql, parametros=()):
        self._conexion.ejecuciones.append((sql, tuple(parametros)))
        if self._resultado.error is not None:
            raise self._resultado.error
        return self

    def fetchone(self):
        return self._resultado.fila

    def fetchall(self):
        return list(self._resultado.filas)

    def close(self):
        self.cerrado = True


class ConexionProgramada:
    def __init__(self, *resultados: ResultadoSQL):
        self._resultados = list(resultados)
        self.ejecuciones: list[tuple[str, tuple[Any, ...]]] = []
        self.cursores: list[CursorProgramado] = []
        self.commits = 0
        self.rollbacks = 0
        self.cerrada = False

    def cursor(self):
        if not self._resultados:
            raise AssertionError("No existe un resultado SQL programado para este cursor.")
        cursor = CursorProgramado(self, self._resultados.pop(0))
        self.cursores.append(cursor)
        return cursor

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.cerrada = True


class ProveedorProgramado:
    def __init__(self, conexion: ConexionProgramada):
        self.conexion = conexion
        self.aperturas = 0

    def abrir(self):
        self.aperturas += 1
        return self.conexion
