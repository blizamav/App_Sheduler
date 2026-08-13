import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from app import crear_app
from app.config import BASE_DIR
from app.servicios.servicio_control_runtime import liberar_lock_factory_reset, obtener_estado_factory_reset
from app.servicios.servicio_control_runtime import FASES_OPERACION
from app.servicios.servicio_factory_reset import validar_manifiesto_bootstrap
from app.servicios.servicio_factory_reset_filesystem import (
    eliminar_cuarentena_factory_reset,
    limpiar_roots_factory_reset,
    preparar_roots_factory_reset,
    rollback_roots_factory_reset,
    validar_roots_vacios,
)
from app.servicios.servicio_factory_reset_sql import EjecutorSQLFactoryReset, ErrorFactoryResetSQL
from app.servicios.servicio_orquestador_factory_reset import ejecutar_factory_reset


class MotorSQLSimulado:
    def __init__(self, fallo=None, db_owner=True):
        self.fallo = fallo
        self.db_owner = db_owner
        self.reset_ejecutado = False

    def validar_entorno_in_place(self):
        return {
            "disponible": self.db_owner,
            "contexto_correcto": True,
            "lectura_escritura": True,
            "db_owner": self.db_owner,
            "mensaje": "Entorno disponible." if self.db_owner else "FACTORY_RESET_DB_USER requiere db_owner.",
        }

    def ejecutar_reset_in_place(self, _operacion, _usuario, _version):
        if self.fallo == "sql":
            raise ErrorFactoryResetSQL("SCRIPT: 004_seed_catalogos_base.sql; RETURNCODE: 1; ERROR: fallo SQL simulado")
        self.reset_ejecutado = True
        return True

    def validar_resultado_final(self, _operacion):
        if self.fallo == "post_commit":
            raise RuntimeError("validacion final simulada")
        return True


class FactoryResetInPlaceTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="factory-reset-in-place-")
        base = Path(self.temp.name)
        self.app = crear_app()
        self.app.config.update(
            TESTING=True,
            SECRET_KEY="test-factory-reset-secret",
            DB_DATABASE="APP_SCHEDULER_QA",
            FACTORY_RESET_DB_TARGET="APP_SCHEDULER_QA",
            FACTORY_RESET_DB_ALLOWED_TARGETS="APP_SCHEDULER_QA",
            FACTORY_RESET_HABILITADO=True,
            FACTORY_RESET_DB_SERVER="sql-test",
            FACTORY_RESET_DB_USER="user_scheduler_mantenimiento",
            FACTORY_RESET_DB_PASSWORD="secret-test",
            RUTA_CONTROL_RUNTIME=str(base / "control"),
            RUTA_BASE_SCRIPTS=str(base / "scripts"),
            RUTA_BASE_ENV_SCRIPTS=str(base / "env_scripts"),
            RUTA_BASE_LOGS_TAREAS=str(base / "logs_tareas"),
            RUTA_BASE_LOGS_SISTEMA=str(base / "logs_sistema"),
            RUTA_BASE_LOGS_WORKER=str(base / "logs"),
        )
        for clave in (
            "RUTA_BASE_SCRIPTS",
            "RUTA_BASE_ENV_SCRIPTS",
            "RUTA_BASE_LOGS_TAREAS",
            "RUTA_BASE_LOGS_SISTEMA",
            "RUTA_BASE_LOGS_WORKER",
        ):
            root = Path(self.app.config[clave])
            root.mkdir(parents=True)
            (root / "dato.test").write_text("estado-anterior", encoding="utf-8")

    def tearDown(self):
        with self.app.app_context():
            lock = obtener_estado_factory_reset()
            if lock.get("id_operacion"):
                liberar_lock_factory_reset(lock["id_operacion"])
        self.temp.cleanup()

    def _preview(self):
        manifiesto = validar_manifiesto_bootstrap()
        return {"id_operacion": str(uuid4()), "manifest_hash": manifiesto["hash_conjunto"]}

    def _parches_precheck(self):
        diagnostico = {
            "total_ejecuciones_activas": 0,
            "pids_vivos_registrados": 0,
            "procesos_hijos_conocidos": 0,
        }
        return (
            patch("app.servicios.servicio_orquestador_factory_reset.validar_configuracion_factory_reset_sql", return_value={"disponible": True, "bloqueos": []}),
            patch("app.servicios.servicio_orquestador_factory_reset.validar_super_admin_env", return_value={"disponible": True}),
            patch("app.servicios.servicio_orquestador_factory_reset.diagnosticar_operacion_factory_reset", return_value=diagnostico),
        )

    def test_manifiesto_in_place_excluye_creacion_de_base(self):
        with self.app.app_context():
            manifiesto = validar_manifiesto_bootstrap()
        self.assertTrue(manifiesto["valido"])
        self.assertEqual(manifiesto["modo"], "IN_PLACE")
        self.assertEqual(manifiesto["orden"], [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 100])
        self.assertFalse(any(Path(item["file"]).name.startswith("001_") for item in manifiesto["scripts"]))

    def test_runner_usa_transaccion_applock_y_un_solo_target(self):
        contenido = (BASE_DIR / "database/factory_reset/000_reset_in_place.sql").read_text(encoding="utf-8").upper()
        self.assertIn("BEGIN TRANSACTION", contenido)
        self.assertIn("SP_GETAPPLOCK", contenido)
        self.assertIn("COMMIT TRANSACTION", contenido)
        self.assertIn("USE [$(DB_NAME)]", contenido)
        self.assertNotIn("CREATE DATABASE", contenido)
        self.assertNotIn("DROP DATABASE", contenido)
        self.assertNotIn("ALTER DATABASE", contenido)

    def test_limpieza_sql_declara_33_tablas_y_no_borra_base(self):
        contenido = (BASE_DIR / "database/factory_reset/001_eliminar_esquema_aplicativo.sql").read_text(encoding="utf-8")
        self.assertEqual(contenido.count("DROP TABLE IF EXISTS dbo."), 33)
        self.assertNotIn("DROP DATABASE", contenido.upper())
        self.assertNotIn("TRUNCATE", contenido.upper())
        self.assertIn("tablas dbo desconocidas", contenido)

    def test_db_owner_habilita_entorno_sin_permisos_de_servidor(self):
        motor = EjecutorSQLFactoryReset.__new__(EjecutorSQLFactoryReset)
        motor.target = "APP_SCHEDULER_QA"
        consultas = []
        motor.ejecutar_consulta = lambda sql: consultas.append(sql) or "FACTORY_INPLACE_ENV|1|1|1"
        resultado = motor.validar_entorno_in_place()
        self.assertTrue(resultado["disponible"])
        self.assertNotIn("CREATE ANY DATABASE", consultas[0].upper())
        self.assertNotIn("ALTER ANY DATABASE", consultas[0].upper())
        self.assertNotIn("VIEW SERVER STATE", consultas[0].upper())
        self.assertNotIn("PROCESSADMIN", consultas[0].upper())

    def test_sin_db_owner_bloquea_entorno(self):
        motor = EjecutorSQLFactoryReset.__new__(EjecutorSQLFactoryReset)
        motor.target = "APP_SCHEDULER_QA"
        motor.ejecutar_consulta = lambda _sql: "FACTORY_INPLACE_ENV|1|1|0"
        resultado = motor.validar_entorno_in_place()
        self.assertFalse(resultado["disponible"])
        self.assertIn("db_owner", resultado["mensaje"])

    def test_precheck_sin_db_owner_no_adquiere_lock(self):
        with self.app.app_context():
            parches = self._parches_precheck()
            with parches[0], parches[1], parches[2]:
                resultado = ejecutar_factory_reset(self._preview(), "admin", ejecutor=MotorSQLSimulado(db_owner=False))
            self.assertFalse(resultado["ok"])
            self.assertEqual(obtener_estado_factory_reset()["estado"], "NORMAL")

    def test_reset_exitoso_deja_roots_vacios_y_elimina_cuarentena(self):
        with self.app.app_context():
            preview = self._preview()
            parches = self._parches_precheck()
            with parches[0], parches[1], parches[2]:
                resultado = ejecutar_factory_reset(preview, "admin", ejecutor=MotorSQLSimulado())
            self.assertTrue(resultado["ok"])
            for clave in ("RUTA_BASE_SCRIPTS", "RUTA_BASE_ENV_SCRIPTS", "RUTA_BASE_LOGS_TAREAS", "RUTA_BASE_LOGS_SISTEMA", "RUTA_BASE_LOGS_WORKER"):
                self.assertEqual(list(Path(self.app.config[clave]).iterdir()), [])
            backups = Path(self.app.config["RUTA_CONTROL_RUNTIME"]) / "factory_backups"
            self.assertFalse(backups.exists() and any(backups.iterdir()))

    def test_fallo_sql_restaura_filesystem_anterior(self):
        with self.app.app_context():
            parches = self._parches_precheck()
            with parches[0], parches[1], parches[2]:
                resultado = ejecutar_factory_reset(self._preview(), "admin", ejecutor=MotorSQLSimulado(fallo="sql"))
            self.assertFalse(resultado["ok"])
            self.assertFalse(resultado["commit_sql_confirmado"])
            self.assertEqual(Path(self.app.config["RUTA_BASE_SCRIPTS"]).joinpath("dato.test").read_text(), "estado-anterior")

    def test_fallo_post_commit_no_reintroduce_filesystem_anterior(self):
        with self.app.app_context():
            parches = self._parches_precheck()
            with parches[0], parches[1], parches[2]:
                resultado = ejecutar_factory_reset(self._preview(), "admin", ejecutor=MotorSQLSimulado(fallo="post_commit"))
            self.assertFalse(resultado["ok"])
            self.assertTrue(resultado["commit_sql_confirmado"])
            self.assertFalse(Path(self.app.config["RUTA_BASE_SCRIPTS"]).joinpath("dato.test").exists())

    def test_filesystem_cuarentena_puede_restaurarse_y_eliminarse(self):
        with self.app.app_context():
            operaciones = preparar_roots_factory_reset(str(uuid4()))
            limpiar_roots_factory_reset(operaciones)
            self.assertTrue(validar_roots_vacios(operaciones))
            self.assertTrue(rollback_roots_factory_reset(operaciones)["ok"])
            self.assertTrue(eliminar_cuarentena_factory_reset(operaciones)["ok"])

    def test_sqlcmd_fallido_informa_script_y_sanitiza_secretos(self):
        motor = EjecutorSQLFactoryReset.__new__(EjecutorSQLFactoryReset)
        motor.password = "clave-super-secreta"
        motor.usuario = "usuario-secreto"
        motor.servidor = "servidor-secreto"
        motor.timeout = 10
        resultado = subprocess.CompletedProcess(
            args=["sqlcmd"],
            returncode=1,
            stdout="FACTORY_SCRIPT|004_seed_catalogos_base.sql\n",
            stderr="password=clave-super-secreta login failed for user 'usuario-secreto'",
        )
        with patch("app.servicios.servicio_factory_reset_sql.subprocess.run", return_value=resultado):
            with self.assertRaises(ErrorFactoryResetSQL) as contexto:
                motor._ejecutar(["sqlcmd"])
        mensaje = str(contexto.exception)
        self.assertIn("004_seed_catalogos_base.sql", mensaje)
        self.assertNotIn("clave-super-secreta", mensaje)
        self.assertNotIn("usuario-secreto", mensaje)

    def test_motor_invoca_runner_una_sola_vez(self):
        motor = EjecutorSQLFactoryReset.__new__(EjecutorSQLFactoryReset)
        motor.target = "APP_SCHEDULER_QA"
        motor.timeout = 900
        motor._comando_base = lambda _db: ["sqlcmd"]
        comandos = []

        def ejecutar(comando, script=None):
            comandos.append((comando, script))
            return "FACTORY_IN_PLACE_COMMIT_OK"

        motor._ejecutar = ejecutar
        motor.ejecutar_reset_in_place(str(uuid4()), "admin", "test")
        self.assertEqual(len(comandos), 1)
        self.assertIn("000_reset_in_place.sql", comandos[0][0][-1])

    def test_bootstrap_deja_marca_19c(self):
        seed = (BASE_DIR / "database/bootstrap/011_seed_permiso_factory_reset.sql").read_text(encoding="utf-8")
        validacion = (BASE_DIR / "database/bootstrap/100_validacion_bootstrap_actual.sql").read_text(encoding="utf-8")
        self.assertIn("N'19C.0'", seed)
        self.assertIn("N'19C.0'", validacion)

    def test_runtime_declara_solo_fases_in_place(self):
        esperadas = {
            "CUARENTENA_FILESYSTEM",
            "ADQUIRIENDO_APPLOCK",
            "EJECUTANDO_RESET_IN_PLACE",
            "CONFIRMANDO_COMMIT",
            "VALIDANDO_RESULTADO",
            "LIMPIANDO_CUARENTENA",
            "ROLLBACK_FILESYSTEM",
        }
        self.assertTrue(esperadas.issubset(FASES_OPERACION))
        self.assertFalse({"CREANDO_BD_TEMPORAL", "INTERCAMBIANDO_BD", "ROLLBACK"} & FASES_OPERACION)

    def test_codigo_operativo_no_conserva_blue_green(self):
        archivos = (
            BASE_DIR / "app/servicios/servicio_factory_reset_sql.py",
            BASE_DIR / "app/servicios/servicio_orquestador_factory_reset.py",
            BASE_DIR / "database/factory_reset/000_reset_in_place.sql",
        )
        contenido = "\n".join(archivo.read_text(encoding="utf-8") for archivo in archivos).upper()
        for texto in ("__FACTORY_NEW_", "__FACTORY_OLD_", "__FACTORY_FAILED_", "INTERCAMBIAR_BASES", "ROLLBACK_INTERCAMBIO"):
            self.assertNotIn(texto, contenido)


if __name__ == "__main__":
    unittest.main()
