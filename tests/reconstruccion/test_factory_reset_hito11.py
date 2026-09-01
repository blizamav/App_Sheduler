from __future__ import annotations

import sys
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path

import pytest

from app_scheduler import crear_aplicacion
from app_scheduler.compartido.autorizacion import (
    CLAVE_IDENTIDAD,
    IdentidadSesion,
    TIPO_BASE_DATOS,
)
from app_scheduler.compartido.control_runtime import (
    adquirir_lock_factory_reset,
    liberar_lock_factory_reset,
    obtener_estado_factory_reset,
)
from app_scheduler.modulos.factory_reset.casos_uso import (
    ServicioFactoryReset,
    validar_manifiesto_factory_reset,
)
from app_scheduler.modulos.factory_reset.sql import ErrorFactoryResetSQL


class ProveedorFactoryFake:
    @contextmanager
    def conexion_lectura(self):
        yield object()


class RepoFactoryFake:
    activas = ()

    def __init__(self, _conexion):
        pass

    def obtener_conteos(self):
        return {"tareas": 2, "ejecuciones": 4}

    def obtener_version_bootstrap(self):
        return "19C.1"

    def listar_ejecuciones_activas(self):
        return self.activas


class MotorFactoryFake:
    def __init__(self, fallo=None):
        self.fallo = fallo
        self.ejecuciones = 0
        self.validaciones = 0

    def validar_entorno_in_place(self):
        return {"disponible": True, "contexto_correcto": True,
                "lectura_escritura": True, "db_owner": True,
                "mensaje": "Entorno correcto."}

    def ejecutar_reset_in_place(self, *_argumentos):
        self.ejecuciones += 1
        if self.fallo == "sql":
            raise ErrorFactoryResetSQL("SCRIPT: 002_schema_final.sql | ERROR: fallo controlado")

    def validar_resultado_final(self, *_argumentos):
        self.validaciones += 1
        if self.fallo == "post_commit":
            raise ErrorFactoryResetSQL("Validacion final controlada")


@pytest.fixture
def configuracion_factory(configuracion, tmp_path):
    roots = {
        "ruta_base_scripts": tmp_path / "scripts",
        "ruta_base_env_scripts": tmp_path / "env_scripts",
        "ruta_base_logs_tareas": tmp_path / "logs_tareas",
        "ruta_base_logs_sistema": tmp_path / "logs_sistema",
        "ruta_base_logs_worker": tmp_path / "logs",
        "ruta_control_runtime": tmp_path / "runtime_control",
    }
    for ruta in roots.values():
        ruta.mkdir(parents=True)
    return replace(
        configuracion, **roots, factory_reset_habilitado=True,
        factory_reset_db_target="APP_SCHEDULER_QA",
        factory_reset_db_allowed_targets="APP_SCHEDULER_QA",
        factory_reset_db_server="sql-test", factory_reset_db_user="maintainer-test",
        factory_reset_db_password="password-maintainer-test-no-real",
        factory_reset_sqlcmd=sys.executable,
    )


def _app(configuracion):
    return crear_aplicacion(
        configuracion, ajustes={"TESTING": True}, proveedor_sql=ProveedorFactoryFake()
    )


def _actor(permisos=frozenset({"FACTORY_RESET_EJECUTAR"})):
    return IdentidadSesion(
        7, "operador", "Operador TI", TIPO_BASE_DATOS,
        frozenset({"ADMIN"}), frozenset(permisos),
    )


def _sesion(cliente, actor):
    with cliente.session_transaction() as datos:
        datos[CLAVE_IDENTIDAD] = {
            "tipo": actor.tipo_identidad, "id_usuario": actor.id_usuario,
            "usuario": actor.usuario,
        }


def _servicio(configuracion, motor):
    return ServicioFactoryReset(
        ProveedorFactoryFake(), configuracion, repositorio=RepoFactoryFake,
        fabrica_motor=lambda: motor,
    )


def test_manifiesto_in_place_excluye_creacion_y_operaciones_de_base():
    manifiesto = validar_manifiesto_factory_reset()
    runner = Path(manifiesto["runner"]).name
    contenido = Path("database/factory_reset/000_reset_in_place.sql").read_text(encoding="utf-8").upper()

    assert manifiesto["valido"] and manifiesto["orden"] == (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 100)
    assert runner == "000_reset_in_place.sql"
    assert "CREATE DATABASE" not in contenido
    assert "DROP DATABASE" not in contenido
    assert "ALTER DATABASE" not in contenido
    assert "USE [MASTER]" not in contenido


def test_runner_configura_opciones_requeridas_por_indices_filtrados():
    contenido = Path("database/factory_reset/000_reset_in_place.sql").read_text(
        encoding="utf-8"
    ).upper()

    for sentencia in (
        "SET QUOTED_IDENTIFIER ON;",
        "SET ANSI_NULLS ON;",
        "SET ANSI_PADDING ON;",
        "SET ANSI_WARNINGS ON;",
        "SET CONCAT_NULL_YIELDS_NULL ON;",
        "SET ARITHABORT ON;",
        "SET NUMERIC_ROUNDABORT OFF;",
    ):
        assert sentencia in contenido


def test_factory_reset_happy_path_simulado_limpia_roots_y_lock(configuracion_factory):
    motor = MotorFactoryFake()
    servicio = _servicio(configuracion_factory, motor)
    archivo = configuracion_factory.ruta_base_scripts / "proceso.py"
    archivo.write_text("print('custodiado')", encoding="utf-8")
    app = _app(configuracion_factory)

    with app.app_context():
        manifiesto = validar_manifiesto_factory_reset()
        resultado = servicio.ejecutar(
            {"id_operacion": "operacion-happy", "manifest_hash": manifiesto["hash_conjunto"]},
            _actor(), motor=motor,
        )

    assert resultado["ok"] and motor.ejecuciones == 1 and motor.validaciones == 1
    assert not archivo.exists()
    assert not (configuracion_factory.ruta_control_runtime / "factory_reset.lock").exists()
    assert not (configuracion_factory.ruta_control_runtime / "factory_backups").exists()


def test_fallo_sql_revierte_filesystem_y_conserva_lock_error(configuracion_factory):
    motor = MotorFactoryFake("sql")
    servicio = _servicio(configuracion_factory, motor)
    archivo = configuracion_factory.ruta_base_scripts / "proceso.py"
    archivo.write_text("contenido", encoding="utf-8")
    app = _app(configuracion_factory)

    with app.app_context():
        manifiesto = validar_manifiesto_factory_reset()
        resultado = servicio.ejecutar(
            {"id_operacion": "operacion-error", "manifest_hash": manifiesto["hash_conjunto"]},
            _actor(), motor=motor,
        )
        estado = servicio.estado_lock()

    assert not resultado["ok"] and resultado["commit_sql_confirmado"] is False
    assert archivo.read_text(encoding="utf-8") == "contenido"
    assert estado["estado"] == "FACTORY_RESET_ERROR" and estado["bloquea"]


def test_fallo_post_commit_no_reintroduce_archivos(configuracion_factory):
    motor = MotorFactoryFake("post_commit")
    servicio = _servicio(configuracion_factory, motor)
    archivo = configuracion_factory.ruta_base_scripts / "proceso.py"
    archivo.write_text("contenido", encoding="utf-8")
    app = _app(configuracion_factory)

    with app.app_context():
        manifiesto = validar_manifiesto_factory_reset()
        resultado = servicio.ejecutar(
            {"id_operacion": "operacion-post-commit", "manifest_hash": manifiesto["hash_conjunto"]},
            _actor(), motor=motor,
        )

    assert not resultado["ok"] and resultado["commit_sql_confirmado"] is True
    assert not archivo.exists()


def test_lock_exclusivo_impide_dos_factory_reset(configuracion_factory):
    root = configuracion_factory.ruta_control_runtime
    primero, _ = adquirir_lock_factory_reset(root, "FACTORY_RESET_PREPARANDO", "TEST", id_operacion="uno")
    segundo, estado = adquirir_lock_factory_reset(root, "FACTORY_RESET_PREPARANDO", "TEST", id_operacion="dos")

    assert primero is True and segundo is False
    assert estado["id_operacion"] == "uno"
    assert liberar_lock_factory_reset(root, "uno") is True


def test_rutas_exigen_permiso_dedicado_y_csrf(configuracion):
    app = _app(configuracion)
    cliente = app.test_client()
    sin_permiso = _actor(frozenset())
    app.extensions["cargador_identidad"] = lambda _: sin_permiso
    _sesion(cliente, sin_permiso)

    assert cliente.get("/administracion/factory-reset").status_code == 403

    con_permiso = _actor()
    app.extensions["cargador_identidad"] = lambda _: con_permiso
    _sesion(cliente, con_permiso)
    assert cliente.get("/administracion/factory-reset").status_code == 200
    assert cliente.post("/administracion/factory-reset/preview").status_code == 403


def test_preview_bloquea_con_kill_switch_apagado(configuracion):
    app = _app(configuracion)
    servicio = ServicioFactoryReset(
        ProveedorFactoryFake(), configuracion, repositorio=RepoFactoryFake,
        fabrica_motor=MotorFactoryFake,
    )
    with app.app_context():
        preview = servicio.generar_preview(_actor())

    assert preview["estado"] == "BLOQUEADO"
    assert any("deshabilitado" in item.lower() for item in preview["bloqueos"])
    assert preview["bootstrap"]["valido"]


def test_sql_y_servicios_no_importan_runtime_historico():
    archivos = tuple(Path("src/app_scheduler/modulos/factory_reset").glob("*.py"))
    contenido = "\n".join(archivo.read_text(encoding="utf-8") for archivo in archivos)

    assert "from app." not in contenido
    assert "import app." not in contenido
    assert "BEGIN ;THROW" not in contenido.upper()
