"""Conexion centralizada y testeable a SQL Server."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator, Protocol

from app_scheduler.compartido.errores import ErrorPersistencia
from app_scheduler.configuracion import ConfiguracionAplicacion


class ConexionDBAPI(Protocol):
    def cursor(self): ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
    def close(self) -> None: ...


class DriverODBC(Protocol):
    def connect(self, cadena: str, **opciones: Any) -> ConexionDBAPI: ...


def _valor_odbc(valor: object, nombre: str) -> str:
    texto = str(valor or "")
    if ";" in texto or "\x00" in texto:
        raise ErrorPersistencia(
            "La configuracion de base de datos no es valida.",
            detalle_tecnico=f"{nombre} contiene caracteres no permitidos.",
        )
    return texto


def _driver_odbc(valor: object) -> str:
    return "{" + str(valor or "").replace("}", "}}") + "}"


def construir_cadena_odbc(configuracion: ConfiguracionAplicacion) -> str:
    """Construye la cadena solo desde configuracion validada."""
    return (
        f"DRIVER={_driver_odbc(configuracion.db_driver)};"
        f"SERVER={_valor_odbc(configuracion.db_server, 'DB_SERVER')};"
        f"DATABASE={_valor_odbc(configuracion.db_database, 'DB_DATABASE')};"
        f"UID={_valor_odbc(configuracion.db_user, 'DB_USER')};"
        f"PWD={_valor_odbc(configuracion.db_password, 'DB_PASSWORD')};"
        f"Encrypt={_valor_odbc(configuracion.db_encrypt, 'DB_ENCRYPT')};"
        "TrustServerCertificate="
        f"{_valor_odbc(configuracion.db_trust_server_certificate, 'DB_TRUST_SERVER_CERTIFICATE')};"
        f"Connection Timeout={configuracion.db_timeout};"
        f"APP={_valor_odbc(configuracion.db_application_name, 'DB_APPLICATION_NAME')};"
    )


class ProveedorConexionesSQLServer:
    """Abre conexiones cortas; no conserva estado global entre requests."""

    def __init__(
        self,
        configuracion: ConfiguracionAplicacion,
        driver: DriverODBC | None = None,
    ):
        self.configuracion = configuracion
        self._driver = driver

    def abrir(self) -> ConexionDBAPI:
        driver = self._driver
        if driver is None:
            try:
                import pyodbc as driver
            except ImportError as error:
                raise ErrorPersistencia(
                    "El servicio de datos no esta disponible.",
                    detalle_tecnico="pyodbc no esta instalado.",
                ) from error
        try:
            return driver.connect(
                construir_cadena_odbc(self.configuracion),
                autocommit=False,
                timeout=self.configuracion.db_timeout,
            )
        except ErrorPersistencia:
            raise
        except Exception as error:
            raise ErrorPersistencia(
                detalle_tecnico=f"Fallo al abrir SQL Server: {error.__class__.__name__}."
            ) from error

    @contextmanager
    def conexion_lectura(self) -> Iterator[ConexionDBAPI]:
        conexion = self.abrir()
        try:
            yield conexion
        finally:
            conexion.close()
