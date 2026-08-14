from __future__ import annotations

from datetime import datetime

import pytest

from app_scheduler.compartido.errores import ErrorPersistencia
from app_scheduler.persistencia.mapeadores import (
    mapear_cliente,
    mapear_credencial_usuario,
    mapear_permiso,
    mapear_rol,
    mapear_usuario,
)


FECHA = datetime(2026, 8, 14, 10, 30)


def fila_usuario(*, activo=1):
    return (
        7,
        "operador",
        "Usuario Operador",
        "operador@example.invalid",
        0,
        None,
        2,
        0,
        0,
        None,
        FECHA,
        None,
        activo,
    )


def test_mapea_usuario_por_contrato_y_conserva_datetime():
    usuario = mapear_usuario(fila_usuario())

    assert usuario.id_usuario == 7
    assert usuario.ultimo_login is None
    assert usuario.fecha_creacion is FECHA
    assert usuario.activo is True
    assert usuario.bloqueado is False


def test_credencial_separa_hash_del_usuario_y_no_lo_representa():
    credencial = mapear_credencial_usuario((*fila_usuario(), "hash-no-real"))

    assert credencial.usuario.usuario == "operador"
    assert credencial.password_hash == "hash-no-real"
    assert "hash-no-real" not in repr(credencial)


def test_mapeo_rechaza_fila_con_columnas_incompletas():
    with pytest.raises(ErrorPersistencia, match="contrato de columnas"):
        mapear_usuario((1, "incompleto"))


def test_mapea_roles_permisos_y_catalogos():
    rol = mapear_rol((2, "TI", "Tecnologia", None, 1, 1))
    permiso = mapear_permiso((3, "TAREAS_VER", "Tareas", "Ver", None, 1))
    cliente = mapear_cliente((4, "Cliente", "CLIENTE", None, 0, FECHA, None, 1))

    assert rol.codigo_rol == "TI" and rol.es_sistema is True
    assert permiso.codigo_permiso == "TAREAS_VER" and permiso.activo is True
    assert cliente.id_cliente == 4 and cliente.eliminado_operativo is False
