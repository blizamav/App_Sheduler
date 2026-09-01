"""Ayudas SQL acotadas; no implementan un CRUD generico."""

from __future__ import annotations

from collections.abc import Sequence
import re
from typing import Any

from app_scheduler.compartido.base_datos import ConexionDBAPI
from app_scheduler.compartido.errores import ErrorPersistencia


def _codigo_sql_seguro(error: Exception) -> str | None:
    """Extrae solo SQLSTATE; nunca serializa argumentos completos del driver."""
    if not getattr(error, "args", None):
        return None
    codigo = str(error.args[0]).strip().upper()
    if len(codigo) == 5 and codigo.isalnum():
        return codigo
    return None


def _diagnostico_sql_server_seguro(error: Exception) -> tuple[str | None, str | None]:
    """Extrae numero nativo y objeto SQL sin conservar valores del mensaje."""
    argumentos = getattr(error, "args", ())
    if len(argumentos) < 2:
        return None, None
    detalle = str(argumentos[1])
    numeros = re.findall(r"\((\d{3,6})\)\s*(?=\(|$)", detalle)
    numero = numeros[-1] if numeros else None
    objeto = None
    coincidencia = re.search(
        r"[\"']((?:CK|FK|PK|UQ|UX|IX)_[A-Za-z0-9_]{1,125})[\"']",
        detalle,
        flags=re.IGNORECASE,
    )
    if coincidencia:
        objeto = coincidencia.group(1)
    return numero, objeto


class RepositorioSQL:
    def __init__(self, conexion: ConexionDBAPI):
        self.conexion = conexion

    def _error(self, error: Exception, operacion: str) -> ErrorPersistencia:
        codigo = _codigo_sql_seguro(error)
        numero, objeto = _diagnostico_sql_server_seguro(error)
        diagnostico = []
        if codigo:
            diagnostico.append(f"SQLSTATE={codigo}")
        if numero:
            diagnostico.append(f"SQLSERVER={numero}")
        if objeto:
            diagnostico.append(f"OBJETO={objeto}")
        sufijo = f" {' '.join(diagnostico)}." if diagnostico else "."
        return ErrorPersistencia(
            detalle_tecnico=(
                f"Fallo de persistencia en {operacion}: "
                f"{error.__class__.__name__}{sufijo}"
            )
        )

    def ejecutar_uno(
        self,
        sql: str,
        parametros: Sequence[Any] = (),
        *,
        operacion: str = "consulta_unica",
    ):
        cursor = None
        try:
            cursor = self.conexion.cursor()
            cursor.execute(sql, tuple(parametros))
            return cursor.fetchone()
        except ErrorPersistencia:
            raise
        except Exception as error:
            raise self._error(error, operacion) from error
        finally:
            if cursor is not None:
                cursor.close()

    def ejecutar_lista(
        self,
        sql: str,
        parametros: Sequence[Any] = (),
        *,
        operacion: str = "consulta_lista",
    ) -> list[Any]:
        cursor = None
        try:
            cursor = self.conexion.cursor()
            cursor.execute(sql, tuple(parametros))
            return list(cursor.fetchall())
        except ErrorPersistencia:
            raise
        except Exception as error:
            raise self._error(error, operacion) from error
        finally:
            if cursor is not None:
                cursor.close()

    def ejecutar_escalar(
        self,
        sql: str,
        parametros: Sequence[Any] = (),
        *,
        operacion: str = "consulta_escalar",
    ) -> Any:
        fila = self.ejecutar_uno(sql, parametros, operacion=operacion)
        return None if fila is None else fila[0]

    def ejecutar(
        self,
        sql: str,
        parametros: Sequence[Any] = (),
        *,
        operacion: str = "escritura",
    ) -> int:
        cursor = None
        try:
            cursor = self.conexion.cursor()
            cursor.execute(sql, tuple(parametros))
            return int(cursor.rowcount)
        except ErrorPersistencia:
            raise
        except Exception as error:
            raise self._error(error, operacion) from error
        finally:
            if cursor is not None:
                cursor.close()


class RepositorioDiagnosticoSQL(RepositorioSQL):
    """Ejemplo tecnico minimo; no consulta tablas funcionales."""

    def conexion_responde(self) -> bool:
        fila = self.ejecutar_uno("SELECT CAST(1 AS int)")
        return bool(fila and fila[0] == 1)
