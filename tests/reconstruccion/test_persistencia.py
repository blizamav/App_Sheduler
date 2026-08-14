from __future__ import annotations

import pytest

from app_scheduler.compartido.base_datos import (
    ProveedorConexionesSQLServer,
    construir_cadena_odbc,
)
from app_scheduler.compartido.errores import ErrorPersistencia
from app_scheduler.compartido.unidad_trabajo import UnidadTrabajoSQL
from app_scheduler.persistencia.repositorio import RepositorioDiagnosticoSQL


class CursorFalso:
    def __init__(self):
        self.cerrado = False
        self.sql = None
        self.parametros = None

    def execute(self, sql, parametros=()):
        self.sql = sql
        self.parametros = parametros
        return self

    def fetchone(self):
        return (1,)

    def fetchall(self):
        return [(1,)]

    def close(self):
        self.cerrado = True


class ConexionFalsa:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0
        self.cerrada = False
        self.ultimo_cursor = None

    def cursor(self):
        self.ultimo_cursor = CursorFalso()
        return self.ultimo_cursor

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.cerrada = True


class DriverFalso:
    def __init__(self, conexion):
        self.conexion = conexion
        self.cadena = None
        self.opciones = None

    def connect(self, cadena, **opciones):
        self.cadena = cadena
        self.opciones = opciones
        return self.conexion


def test_proveedor_configura_conexion_sin_autocommit(configuracion):
    conexion = ConexionFalsa()
    driver = DriverFalso(conexion)

    resultado = ProveedorConexionesSQLServer(configuracion, driver).abrir()

    assert resultado is conexion
    assert driver.opciones == {"autocommit": False, "timeout": 5}
    assert "DATABASE=APP_SCHEDULER_QA" in driver.cadena


def test_cadena_rechaza_separador_inyectado(configuracion):
    configuracion_maliciosa = object.__new__(type(configuracion))
    for campo in configuracion.__dataclass_fields__:
        object.__setattr__(configuracion_maliciosa, campo, getattr(configuracion, campo))
    object.__setattr__(configuracion_maliciosa, "db_server", "servidor;Trusted_Connection=yes")

    with pytest.raises(ErrorPersistencia, match="caracteres no permitidos"):
        construir_cadena_odbc(configuracion_maliciosa)


def test_unidad_trabajo_confirma_y_cierra(configuracion):
    conexion = ConexionFalsa()
    proveedor = ProveedorConexionesSQLServer(configuracion, DriverFalso(conexion))

    with UnidadTrabajoSQL(proveedor) as unidad:
        unidad.confirmar()

    assert conexion.commits == 1
    assert conexion.rollbacks == 0
    assert conexion.cerrada is True


def test_unidad_trabajo_revierte_si_no_se_confirma(configuracion):
    conexion = ConexionFalsa()
    proveedor = ProveedorConexionesSQLServer(configuracion, DriverFalso(conexion))

    with UnidadTrabajoSQL(proveedor):
        pass

    assert conexion.commits == 0
    assert conexion.rollbacks == 1
    assert conexion.cerrada is True


def test_unidad_trabajo_revierte_ante_error(configuracion):
    conexion = ConexionFalsa()
    proveedor = ProveedorConexionesSQLServer(configuracion, DriverFalso(conexion))

    with pytest.raises(RuntimeError):
        with UnidadTrabajoSQL(proveedor):
            raise RuntimeError("fallo controlado")

    assert conexion.rollbacks == 1
    assert conexion.cerrada is True


def test_repositorio_diagnostico_cierra_cursor():
    conexion = ConexionFalsa()

    assert RepositorioDiagnosticoSQL(conexion).conexion_responde() is True
    assert conexion.ultimo_cursor.sql == "SELECT CAST(1 AS int)"
    assert conexion.ultimo_cursor.parametros == ()
    assert conexion.ultimo_cursor.cerrado is True
