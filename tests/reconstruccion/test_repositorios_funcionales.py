from __future__ import annotations

from datetime import datetime

import pytest

from app_scheduler.compartido.errores import ErrorPersistencia
from app_scheduler.compartido.unidad_trabajo import UnidadTrabajoSQL
from app_scheduler.persistencia.modelos import Paginacion
from app_scheduler.persistencia.repositorio_catalogos import (
    RepositorioCategorias,
    RepositorioClientes,
    RepositorioTipos,
)
from app_scheduler.persistencia.repositorio_seguridad import RepositorioSeguridad
from app_scheduler.persistencia.repositorio_usuarios import RepositorioUsuarios
from tests.reconstruccion.fakes_sql import (
    ConexionProgramada,
    ProveedorProgramado,
    ResultadoSQL,
)


FECHA = datetime(2026, 8, 14, 11, 0)
FILA_USUARIO = (
    7,
    "operador",
    "Usuario Operador",
    None,
    0,
    None,
    0,
    0,
    0,
    None,
    FECHA,
    None,
    1,
)


def test_usuario_por_id_usa_columnas_explicitas_y_parametro():
    conexion = ConexionProgramada(ResultadoSQL(fila=FILA_USUARIO))

    usuario = RepositorioUsuarios(conexion).obtener_por_id(7)

    sql, parametros = conexion.ejecuciones[0]
    assert usuario is not None and usuario.id_usuario == 7
    assert "SELECT *" not in sql.upper()
    assert "WHERE u.id_usuario = ?" in sql
    assert parametros == (7,)
    assert conexion.cursores[0].cerrado is True


def test_listado_usuarios_parametriza_filtros_busqueda_y_paginacion():
    conexion = ConexionProgramada(
        ResultadoSQL(fila=(1,)),
        ResultadoSQL(filas=[FILA_USUARIO]),
    )

    pagina = RepositorioUsuarios(conexion).listar(
        Paginacion(pagina=2, por_pagina=25),
        activo=True,
        busqueda="op%_",
    )

    sql_total, parametros_total = conexion.ejecuciones[0]
    sql_listado, parametros_listado = conexion.ejecuciones[1]
    assert pagina.total == 1 and pagina.pagina == 2
    assert "op%_" not in sql_total and "op%_" not in sql_listado
    assert parametros_total == (1, "%op~%~_%", "%op~%~_%", "%op~%~_%")
    assert parametros_listado == (*parametros_total, 25, 25)
    assert "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY" in sql_listado
    assert all(cursor.cerrado for cursor in conexion.cursores)


def test_permisos_efectivos_se_resuelven_en_una_consulta_sin_n_mas_uno():
    conexion = ConexionProgramada(
        ResultadoSQL(filas=[(3, "TAREAS_VER", "Tareas", "Ver", None, 1)])
    )

    permisos = RepositorioSeguridad(conexion).obtener_permisos_efectivos(7)

    sql, parametros = conexion.ejecuciones[0]
    assert tuple(permiso.codigo_permiso for permiso in permisos) == ("TAREAS_VER",)
    assert len(conexion.ejecuciones) == 1
    assert "INNER JOIN dbo.roles_permisos" in sql
    assert "rp.permitido = 1" in sql
    assert parametros == (7,)


def test_roles_de_usuario_respetan_asociaciones_y_estados_activos():
    conexion = ConexionProgramada(
        ResultadoSQL(filas=[(2, "TI", "Tecnologia", None, 1, 1)])
    )

    roles = RepositorioSeguridad(conexion).obtener_roles_usuario(7)

    sql, parametros = conexion.ejecuciones[0]
    assert tuple(rol.codigo_rol for rol in roles) == ("TI",)
    assert "FROM dbo.usuarios_roles" in sql
    assert "ur.activo = 1" in sql and "r.activo = 1" in sql
    assert parametros == (7,)


@pytest.mark.parametrize(
    ("repositorio", "tabla", "campo_id"),
    [
        (RepositorioClientes, "clientes", "id_cliente"),
        (RepositorioCategorias, "categorias", "id_categoria"),
        (RepositorioTipos, "tipos", "id_tipo"),
    ],
)
def test_catalogos_buscan_clave_fisica_incluyendo_papelera(
    repositorio, tabla, campo_id
):
    conexion = ConexionProgramada(
        ResultadoSQL(fila=(9, "Registro", "REGISTRO", None, 1, FECHA, None, 0))
    )

    resultado = repositorio(conexion).buscar_por_clave("REGISTRO")

    sql, parametros = conexion.ejecuciones[0]
    assert getattr(resultado, campo_id) == 9
    assert f"FROM dbo.{tabla}" in sql
    assert "eliminado_operativo = 0" not in sql
    assert parametros == ("REGISTRO",)


def test_repositorio_no_confirma_y_uow_coordina_commit():
    conexion = ConexionProgramada(ResultadoSQL(rowcount=1))
    proveedor = ProveedorProgramado(conexion)

    with UnidadTrabajoSQL(proveedor) as unidad:
        actualizado = RepositorioUsuarios(
            unidad.obtener_conexion()
        ).actualizar_ultimo_login(7, FECHA, "sistema")
        assert actualizado is True
        assert conexion.commits == 0
        unidad.confirmar()

    assert conexion.commits == 1
    assert conexion.rollbacks == 0
    assert conexion.cerrada is True


def test_error_sql_revierte_cierra_y_no_expone_detalle_del_driver():
    error_driver = RuntimeError("detalle-driver-no-publicable-4711")
    conexion = ConexionProgramada(ResultadoSQL(error=error_driver))
    proveedor = ProveedorProgramado(conexion)

    with pytest.raises(ErrorPersistencia) as capturado:
        with UnidadTrabajoSQL(proveedor) as unidad:
            RepositorioUsuarios(unidad.obtener_conexion()).actualizar_ultimo_login(
                7, FECHA, "sistema"
            )

    assert "detalle-driver-no-publicable-4711" not in str(capturado.value)
    assert "actualizar_ultimo_login" in capturado.value.detalle_tecnico
    assert conexion.rollbacks == 1
    assert conexion.cerrada is True


def test_error_sql_conserva_solo_sqlstate_seguro():
    class ErrorODBC(Exception):
        pass

    error_driver = ErrorODBC("23000", "detalle-driver-no-publicable-8192")
    conexion = ConexionProgramada(ResultadoSQL(error=error_driver))

    with pytest.raises(ErrorPersistencia) as capturado:
        RepositorioUsuarios(conexion).obtener_por_id(7)

    assert "SQLSTATE=23000" in capturado.value.detalle_tecnico
    assert "detalle-driver-no-publicable-8192" not in capturado.value.detalle_tecnico
    assert conexion.cursores[0].cerrado is True
