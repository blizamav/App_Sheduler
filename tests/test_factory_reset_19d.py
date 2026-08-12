import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from app import crear_app
from app.servicios.servicio_control_runtime import (
    adquirir_lock_factory_reset,
    liberar_lock_factory_reset,
    obtener_estado_factory_reset,
    registrar_marca_factory_reset_completado,
    actualizar_lock_factory_reset,
)
from app.servicios.servicio_factory_reset import validar_manifiesto_bootstrap
from app.servicios.servicio_factory_reset_filesystem import (
    ErrorFactoryResetFilesystem,
    limpiar_roots_factory_reset,
    preparar_roots_factory_reset,
)
from app.servicios.servicio_orquestador_factory_reset import ejecutar_factory_reset
from app.servicios.servicio_factory_reset_sql import EjecutorSQLFactoryReset, ErrorFactoryResetSQL
from app.servicios.servicio_scheduler_worker import ejecutar_ciclo_worker


class MotorSQLSimulado:
    def __init__(self, actual="APP_SCHEDULER_FACTORY_SOURCE_TEST", fallo=None):
        self.bases = {actual}
        self.actual = actual
        self.fallo = fallo
        self.auditoria = False
        self.rollback_ejecutado = False

    def existe_base(self, nombre):
        return nombre in self.bases

    def ejecutar_bootstrap(self, nombre, _manifiesto):
        if self.fallo == "bootstrap":
            raise RuntimeError("fallo simulado")
        self.bases.add(nombre)

    def validar_bootstrap(self, _nombre, _ruta):
        if self.fallo == "validacion":
            raise RuntimeError("fallo simulado")
        return True

    def listar_sesiones(self, _nombre):
        return []

    def intercambiar_bases(self, actual, nueva, anterior):
        self.bases.remove(actual)
        self.bases.add(anterior)
        if self.fallo == "intercambio":
            raise RuntimeError("fallo simulado")
        self.bases.remove(nueva)
        self.bases.add(actual)

    def rollback_intercambio(self, actual, _nueva, anterior, fallida):
        self.rollback_ejecutado = True
        if actual in self.bases:
            self.bases.remove(actual)
            self.bases.add(fallida)
        if anterior in self.bases:
            self.bases.remove(anterior)
            self.bases.add(actual)

    def registrar_reset_completado(self, _nombre, _usuario, _operacion, _version):
        self.auditoria = True

    def validar_resultado_final(self, _nombre, _operacion):
        if not self.auditoria:
            raise RuntimeError("auditoria ausente")


class FactoryReset19DTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="factory-reset-19d-")
        base = Path(self.temp.name)
        self.app = crear_app()
        self.app.config.update(
            TESTING=True,
            SECRET_KEY="test-factory-reset-secret",
            DB_DATABASE="APP_SCHEDULER_FACTORY_SOURCE_TEST",
            FACTORY_RESET_DB_TARGET="APP_SCHEDULER_FACTORY_SOURCE_TEST",
            FACTORY_RESET_HABILITADO=True,
            FACTORY_RESET_DB_SERVER="sql-test",
            FACTORY_RESET_DB_USER="admin-test",
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
            (root / "dato.test").write_text("temporal", encoding="utf-8")

    def tearDown(self):
        with self.app.app_context():
            lock = obtener_estado_factory_reset()
            if lock.get("id_operacion"):
                liberar_lock_factory_reset(lock["id_operacion"])
        self.temp.cleanup()

    def _preview(self):
        manifiesto = validar_manifiesto_bootstrap()
        return {
            "id_operacion": str(uuid4()),
            "manifest_hash": manifiesto["hash_conjunto"],
            "estado_lock": "NORMAL",
        }

    def _parches_precheck(self, diagnostico=None):
        diagnostico = diagnostico or {
            "total_ejecuciones_activas": 0,
            "pids_vivos_registrados": 0,
            "procesos_hijos_conocidos": 0,
        }
        return (
            patch("app.servicios.servicio_orquestador_factory_reset.validar_configuracion_factory_reset_sql", return_value={"disponible": True, "bloqueos": []}),
            patch("app.servicios.servicio_orquestador_factory_reset.validar_super_admin_env", return_value={"disponible": True}),
            patch("app.servicios.servicio_orquestador_factory_reset.diagnosticar_operacion_factory_reset", return_value=diagnostico),
        )

    def test_reset_completo_y_segundo_reset(self):
        with self.app.app_context():
            motor = MotorSQLSimulado()
            parches = self._parches_precheck()
            with parches[0], parches[1], parches[2]:
                primero = ejecutar_factory_reset(self._preview(), "admin", "ENV", motor)
                segundo = ejecutar_factory_reset(self._preview(), "admin", "ENV", motor)
            self.assertTrue(primero["ok"])
            self.assertTrue(segundo["ok"])
            self.assertTrue(motor.auditoria)
            self.assertEqual(obtener_estado_factory_reset()["estado"], "NORMAL")
            for clave in ("RUTA_BASE_SCRIPTS", "RUTA_BASE_ENV_SCRIPTS", "RUTA_BASE_LOGS_TAREAS", "RUTA_BASE_LOGS_SISTEMA", "RUTA_BASE_LOGS_WORKER"):
                self.assertEqual(list(Path(self.app.config[clave]).iterdir()), [])

    def test_ejecucion_activa_rechaza_antes_del_lock(self):
        with self.app.app_context():
            diagnostico = {"total_ejecuciones_activas": 1, "pids_vivos_registrados": 1, "procesos_hijos_conocidos": 0}
            parches = self._parches_precheck(diagnostico)
            with parches[0], parches[1], parches[2]:
                resultado = ejecutar_factory_reset(self._preview(), "admin", "ENV", MotorSQLSimulado())
            self.assertFalse(resultado["ok"])
            self.assertEqual(obtener_estado_factory_reset()["estado"], "NORMAL")

    def test_segundo_reset_simultaneo_rechazado(self):
        with self.app.app_context():
            preview = self._preview()
            adquirido, _ = adquirir_lock_factory_reset("FACTORY_RESET_PREPARANDO", "test", "otra-operacion-123")
            self.assertTrue(adquirido)
            parches = self._parches_precheck()
            with parches[0], parches[1], parches[2]:
                resultado = ejecutar_factory_reset(preview, "admin", "ENV", MotorSQLSimulado())
            self.assertFalse(resultado["ok"])

    def test_fallo_bootstrap_conserva_original(self):
        with self.app.app_context():
            motor = MotorSQLSimulado(fallo="bootstrap")
            parches = self._parches_precheck()
            with parches[0], parches[1], parches[2]:
                resultado = ejecutar_factory_reset(self._preview(), "admin", "ENV", motor)
            self.assertFalse(resultado["ok"])
            self.assertIn(motor.actual, motor.bases)
            self.assertEqual(obtener_estado_factory_reset()["estado"], "FACTORY_RESET_ERROR")

    def test_fallo_intercambio_ejecuta_rollback(self):
        with self.app.app_context():
            motor = MotorSQLSimulado(fallo="intercambio")
            parches = self._parches_precheck()
            with parches[0], parches[1], parches[2]:
                resultado = ejecutar_factory_reset(self._preview(), "admin", "ENV", motor)
            self.assertFalse(resultado["ok"])
            self.assertTrue(motor.rollback_ejecutado)
            self.assertIn(motor.actual, motor.bases)

    def test_fallo_filesystem_ejecuta_rollback_sql(self):
        with self.app.app_context():
            motor = MotorSQLSimulado()
            parches = self._parches_precheck()
            with parches[0], parches[1], parches[2], patch(
                "app.servicios.servicio_orquestador_factory_reset.limpiar_roots_factory_reset",
                side_effect=ErrorFactoryResetFilesystem("fallo simulado"),
            ):
                resultado = ejecutar_factory_reset(self._preview(), "admin", "ENV", motor)
            self.assertFalse(resultado["ok"])
            self.assertTrue(motor.rollback_ejecutado)
            self.assertIn(motor.actual, motor.bases)

    def test_path_traversal_rechazado(self):
        with self.app.app_context():
            self.app.config["RUTA_BASE_SCRIPTS"] = "../ruta_maliciosa"
            with self.assertRaises(ErrorFactoryResetFilesystem):
                preparar_roots_factory_reset(str(uuid4()))

    def test_limpieza_parcial_restaura_desde_cuarentena(self):
        from app.servicios import servicio_factory_reset_filesystem as servicio_fs

        with self.app.app_context():
            operaciones = preparar_roots_factory_reset(str(uuid4()))
            limpiar_real = servicio_fs._limpiar_contenido_root
            llamadas = {"total": 0}

            def limpiar_y_fallar(root):
                limpiar_real(root)
                llamadas["total"] += 1
                if llamadas["total"] == 1:
                    raise OSError("fallo simulado")

            with patch.object(servicio_fs, "_limpiar_contenido_root", side_effect=limpiar_y_fallar):
                with self.assertRaises(ErrorFactoryResetFilesystem):
                    limpiar_roots_factory_reset(operaciones)
            self.assertEqual(
                (Path(self.app.config["RUTA_BASE_SCRIPTS"]) / "dato.test").read_text(encoding="utf-8"),
                "temporal",
            )

    def test_rutas_autorizacion_csrf_frase_y_token(self):
        client = self.app.test_client()
        with client.session_transaction() as sesion:
            sesion.update(usuario="normal", roles=["OPERADOR"], permisos=["FACTORY_RESET_EJECUTAR"], es_admin_env=False)
        self.assertEqual(client.get("/administracion/factory-reset").status_code, 403)

        with client.session_transaction() as sesion:
            sesion.update(usuario="admin", roles=["SUPER_ADMIN_ENV"], permisos=["*"], es_admin_env=True)
        self.assertEqual(client.get("/administracion/factory-reset").status_code, 200)
        self.assertEqual(client.post("/administracion/factory-reset/ejecutar", data={"csrf_token": "invalido"}).status_code, 403)

        with client.session_transaction() as sesion:
            token_csrf = "csrf-test"
            sesion["csrf_factory_reset"] = {"token": token_csrf, "creado": time.time()}
        respuesta = client.post(
            "/administracion/factory-reset/ejecutar",
            data={"csrf_token": token_csrf, "confirmacion": "frase incorrecta"},
        )
        self.assertEqual(respuesta.status_code, 302)

    def test_worker_no_accede_bd_en_intercambio(self):
        with self.app.app_context():
            operacion = str(uuid4())
            adquirir_lock_factory_reset("FACTORY_RESET_PREPARANDO", "test", operacion)
            actualizar_lock_factory_reset(
                operacion,
                "FACTORY_RESET_EN_PROGRESO",
                fase="INTERCAMBIANDO_BD",
                progreso=65,
                mensaje="test",
            )
            with patch("app.servicios.servicio_scheduler_worker._registrar_estado_unico"), patch(
                "app.servicios.servicio_scheduler_worker.registrar_inicio_ciclo",
                side_effect=AssertionError("No debe acceder a heartbeat SQL"),
            ):
                self.assertEqual(ejecutar_ciclo_worker(nombre_worker="test"), 60)

    def test_sqlcmd_no_expone_password_en_argumentos_y_rechaza_sesion_ajena(self):
        class Resultado:
            returncode = 0
            stdout = "FACTORY_EXISTS|1\n"
            stderr = ""

        captura = {}

        def ejecutar_simulado(comando, **kwargs):
            captura["comando"] = list(comando)
            captura["entorno"] = dict(kwargs["env"])
            return Resultado()

        with self.app.app_context(), patch(
            "app.servicios.servicio_factory_reset_sql._resolver_sqlcmd", return_value="sqlcmd-test"
        ), patch("app.servicios.servicio_factory_reset_sql.subprocess.run", side_effect=ejecutar_simulado):
            motor = EjecutorSQLFactoryReset()
            self.assertTrue(motor.existe_base("APP_SCHEDULER_FACTORY_SOURCE_TEST"))
            comando = captura["comando"]
            entorno = captura["entorno"]
            self.assertNotIn("secret-test", " ".join(comando))
            self.assertEqual(entorno["SQLCMDPASSWORD"], "secret-test")
            with patch.object(
                motor,
                "listar_sesiones",
                return_value=[{"session_id": 22, "program_name": "SSMS", "host_name": "otro"}],
            ):
                with self.assertRaises(ErrorFactoryResetSQL):
                    motor.intercambiar_bases("APP_SCHEDULER_FACTORY_SOURCE_TEST", "TEMP_TEST", "OLD_TEST")

    def test_lock_bloquea_web_e_invalida_sesion_anterior(self):
        client = self.app.test_client()
        with client.session_transaction() as sesion:
            sesion.update(
                usuario="admin",
                roles=["SUPER_ADMIN_ENV"],
                permisos=["*"],
                es_admin_env=True,
                sesion_iniciada_epoch=time.time(),
            )
        with self.app.app_context():
            operacion = str(uuid4())
            adquirir_lock_factory_reset("FACTORY_RESET_PREPARANDO", "test", operacion)
        self.assertEqual(client.get("/panel").status_code, 503)
        with self.app.app_context():
            liberar_lock_factory_reset(operacion)
            registrar_marca_factory_reset_completado(str(uuid4()))
        respuesta = client.get("/panel")
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("/login", respuesta.headers["Location"])

    def test_endpoint_estado_lee_log_externo(self):
        client = self.app.test_client()
        with client.session_transaction() as sesion:
            sesion.update(
                usuario="admin",
                roles=["SUPER_ADMIN_ENV"],
                permisos=["*"],
                es_admin_env=True,
                sesion_iniciada_epoch=time.time(),
            )
        with self.app.app_context():
            operacion = str(uuid4())
            adquirir_lock_factory_reset("FACTORY_RESET_PREPARANDO", "test", operacion)
            actualizar_lock_factory_reset(
                operacion,
                "FACTORY_RESET_EN_PROGRESO",
                fase="EJECUTANDO_BOOTSTRAP",
                progreso=30,
                mensaje="Prueba de estado.",
            )
        respuesta = client.get(f"/administracion/factory-reset/estado?operacion={operacion}")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.get_json()["fase"], "EJECUTANDO_BOOTSTRAP")
        self.assertEqual(respuesta.get_json()["progreso"], 30)

    def test_endpoint_ejecutar_solo_post_e_invalida_sesion_al_completar(self):
        client = self.app.test_client()
        with client.session_transaction() as sesion:
            sesion.update(
                usuario="admin",
                roles=["SUPER_ADMIN_ENV"],
                permisos=["*"],
                es_admin_env=True,
                sesion_iniciada_epoch=time.time(),
                csrf_factory_reset={"token": "csrf-ok", "creado": time.time()},
            )
        self.assertEqual(client.get("/administracion/factory-reset/ejecutar").status_code, 405)
        with patch(
            "app.rutas_factory_reset.validar_token_preview",
            return_value=(True, "OK", {"estado_lock": "NORMAL", "id_operacion": str(uuid4())}),
        ), patch(
            "app.rutas_factory_reset.ejecutar_factory_reset",
            return_value={"ok": True, "mensaje": "OK", "id_operacion": str(uuid4())},
        ):
            respuesta = client.post(
                "/administracion/factory-reset/ejecutar",
                data={
                    "csrf_token": "csrf-ok",
                    "confirmacion": "RESTABLECER APP SCHEDULER",
                    "token_preview": "firmado",
                    "resumen_hash": "hash",
                },
            )
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("/login", respuesta.headers["Location"])
        with client.session_transaction() as sesion:
            self.assertNotIn("usuario", sesion)

        with client.session_transaction() as sesion:
            sesion["csrf_factory_reset"] = {"token": "csrf-expirado", "creado": time.time()}
        with patch("app.rutas_factory_reset.validar_token_preview", return_value=(False, "El preview expiro.", None)):
            respuesta = client.post(
                "/administracion/factory-reset/ejecutar",
                data={"csrf_token": "csrf-expirado", "confirmacion": "RESTABLECER APP SCHEDULER", "token_preview": "x"},
            )
        self.assertEqual(respuesta.status_code, 302)


if __name__ == "__main__":
    unittest.main()
