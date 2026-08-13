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
from app.servicios.servicio_factory_reset import generar_preview_factory_reset, validar_manifiesto_bootstrap
from app.servicios.servicio_factory_reset_filesystem import (
    ErrorFactoryResetFilesystem,
    limpiar_roots_factory_reset,
    preparar_roots_factory_reset,
)
from app.servicios.servicio_orquestador_factory_reset import ejecutar_factory_reset
from app.servicios.servicio_factory_reset_sql import (
    EjecutorSQLFactoryReset,
    ErrorFactoryResetSQL,
    derivar_bases_temporales_factory_reset,
)
from app.servicios.servicio_scheduler_worker import ejecutar_ciclo_worker


class MotorSQLSimulado:
    def __init__(self, actual="APP_SCHEDULER_FACTORY_SOURCE_TEST", fallo=None, permisos=True):
        self.bases = {actual}
        self.actual = actual
        self.fallo = fallo
        self.auditoria = False
        self.rollback_ejecutado = False
        self.bases_eliminadas = []
        self.permisos = permisos

    def existe_base(self, nombre):
        return nombre in self.bases

    def validar_permisos_administrativos(self):
        return {
            "disponible": self.permisos,
            "mensaje": (
                "Privilegios suficientes."
                if self.permisos
                else "La credencial administrativa no tiene privilegios suficientes."
            ),
        }

    def ejecutar_bootstrap(self, nombre, _manifiesto):
        self.bases.add(nombre)
        if self.fallo == "bootstrap_sql":
            raise ErrorFactoryResetSQL(
                "SCRIPT: 001_crear_base_datos.sql; RETURNCODE: 1; "
                "ERROR: CREATE DATABASE permission denied in database 'master'."
            )
        if self.fallo == "bootstrap":
            raise RuntimeError("fallo simulado")

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
        if self.fallo == "rollback":
            raise RuntimeError("rollback no confirmable")
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
        if self.fallo in {"post_intercambio", "rollback"}:
            raise RuntimeError("fallo posterior simulado")

    def listar_bases_residuales(self, base_actual):
        prefijo = f"{base_actual}__FACTORY_".upper()
        return sorted(nombre for nombre in self.bases if nombre.upper().startswith(prefijo))

    def eliminar_base_temporal_operacion(self, nombre, base_actual, id_operacion):
        permitidas = set(derivar_bases_temporales_factory_reset(base_actual, id_operacion).values())
        if nombre == base_actual or nombre not in permitidas:
            raise ErrorFactoryResetSQL("base no permitida")
        if self.fallo == "cleanup":
            return False
        if nombre in self.bases:
            self.bases.remove(nombre)
            self.bases_eliminadas.append(nombre)
            return True
        return False


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
            FACTORY_RESET_DB_ALLOWED_TARGETS="APP_SCHEDULER_FACTORY_SOURCE_TEST",
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
            self.assertEqual(motor.bases, {motor.actual})
            self.assertTrue(any("__FACTORY_OLD_" in nombre for nombre in motor.bases_eliminadas))
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

    def test_credencial_sin_create_alter_bloquea_antes_del_lock(self):
        with self.app.app_context():
            parches = self._parches_precheck()
            with parches[0], parches[1], parches[2]:
                resultado = ejecutar_factory_reset(
                    self._preview(),
                    "admin",
                    "ENV",
                    MotorSQLSimulado(permisos=False),
                )
            self.assertFalse(resultado["ok"])
            self.assertIn("privilegios suficientes", resultado["mensaje"])
            self.assertEqual(obtener_estado_factory_reset()["estado"], "NORMAL")

    def test_preview_bloqueado_por_privilegios_administrativos_insuficientes(self):
        permisos = {
            "disponible": False,
            "mensaje": "La credencial administrativa no tiene privilegios suficientes.",
        }
        motor = MotorSQLSimulado(permisos=False)
        with self.app.app_context(), patch(
            "app.servicios.servicio_factory_reset.obtener_conteos_factory_reset", return_value={}
        ), patch(
            "app.servicios.servicio_factory_reset.obtener_version_bootstrap_sql", return_value=None
        ), patch(
            "app.servicios.servicio_factory_reset._diagnosticar_operacion",
            return_value={
                "ejecuciones_activas": [],
                "total_ejecuciones_activas": 0,
                "pids_vivos_registrados": 0,
                "procesos_hijos_conocidos": 0,
                "worker": {"detectado": True, "estado": "ACTIVO", "activo": True},
                "tareas_candidatas": 0,
            },
        ), patch(
            "app.servicios.servicio_factory_reset.validar_super_admin_env", return_value={"disponible": True}
        ), patch(
            "app.servicios.servicio_factory_reset_sql.validar_configuracion_factory_reset_sql",
            return_value={"disponible": True, "bloqueos": [], "target_configurado": motor.actual},
        ), patch(
            "app.servicios.servicio_factory_reset_sql.EjecutorSQLFactoryReset", return_value=motor
        ), patch.object(
            motor, "validar_permisos_administrativos", return_value=permisos
        ):
            preview = generar_preview_factory_reset("admin")
        self.assertEqual(preview["estado"], "BLOQUEADO")
        self.assertFalse(preview["reset_destructivo_habilitado"])
        self.assertIn(permisos["mensaje"], preview["bloqueos"])

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
            self.assertEqual(motor.listar_bases_residuales(motor.actual), [])
            self.assertEqual(obtener_estado_factory_reset()["estado"], "FACTORY_RESET_ERROR")

    def test_error_sqlcmd_sanitizado_llega_al_log_externo(self):
        with self.app.app_context():
            motor = MotorSQLSimulado(fallo="bootstrap_sql")
            parches = self._parches_precheck()
            with parches[0], parches[1], parches[2], patch(
                "app.servicios.servicio_orquestador_factory_reset.registrar_evento_factory_reset"
            ) as registrar:
                resultado = ejecutar_factory_reset(self._preview(), "admin", "ENV", motor)
            self.assertFalse(resultado["ok"])
            mensajes = " ".join(str(llamada) for llamada in registrar.call_args_list)
            self.assertIn("SCRIPT: 001_crear_base_datos.sql", mensajes)
            self.assertIn("CREATE DATABASE permission denied", mensajes)
            self.assertNotIn("secret-test", mensajes)
            self.assertNotIn("admin-test", mensajes)

    def test_fallo_intercambio_ejecuta_rollback(self):
        with self.app.app_context():
            motor = MotorSQLSimulado(fallo="intercambio")
            parches = self._parches_precheck()
            with parches[0], parches[1], parches[2]:
                resultado = ejecutar_factory_reset(self._preview(), "admin", "ENV", motor)
            self.assertFalse(resultado["ok"])
            self.assertTrue(motor.rollback_ejecutado)
            self.assertIn(motor.actual, motor.bases)
            self.assertEqual(motor.listar_bases_residuales(motor.actual), [])

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
            self.assertEqual(motor.listar_bases_residuales(motor.actual), [])

    def test_fallo_posterior_con_rollback_exitoso_elimina_failed_y_new(self):
        with self.app.app_context():
            motor = MotorSQLSimulado(fallo="post_intercambio")
            parches = self._parches_precheck()
            with parches[0], parches[1], parches[2]:
                resultado = ejecutar_factory_reset(self._preview(), "admin", "ENV", motor)
            self.assertFalse(resultado["ok"])
            self.assertTrue(motor.rollback_ejecutado)
            self.assertEqual(motor.bases, {motor.actual})

    def test_rollback_fallido_conserva_recursos_de_recuperacion(self):
        with self.app.app_context():
            motor = MotorSQLSimulado(fallo="rollback")
            parches = self._parches_precheck()
            with parches[0], parches[1], parches[2]:
                resultado = ejecutar_factory_reset(self._preview(), "admin", "ENV", motor)
            self.assertFalse(resultado["ok"])
            self.assertTrue(resultado["requiere_revision_manual"])
            self.assertTrue(motor.listar_bases_residuales(motor.actual))
            self.assertEqual(obtener_estado_factory_reset()["estado"], "FACTORY_RESET_ERROR")

    def test_residuo_anterior_bloquea_nuevo_reset(self):
        with self.app.app_context():
            motor = MotorSQLSimulado()
            motor.bases.add(f"{motor.actual}__FACTORY_OLD_OPERACIONVIEJA")
            parches = self._parches_precheck()
            with parches[0], parches[1], parches[2]:
                resultado = ejecutar_factory_reset(self._preview(), "admin", "ENV", motor)
            self.assertFalse(resultado["ok"])
            self.assertIn("residuales", resultado["mensaje"])

    def test_exito_requiere_cero_temporales(self):
        with self.app.app_context():
            motor = MotorSQLSimulado(fallo="cleanup")
            parches = self._parches_precheck()
            with parches[0], parches[1], parches[2]:
                resultado = ejecutar_factory_reset(self._preview(), "admin", "ENV", motor)
            self.assertFalse(resultado["ok"])
            self.assertTrue(motor.listar_bases_residuales(motor.actual))

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

    def test_pantalla_expone_flujo_estado_base_y_monitor_real(self):
        client = self.app.test_client()
        with client.session_transaction() as sesion:
            sesion.update(
                usuario="admin",
                roles=["SUPER_ADMIN_ENV"],
                permisos=["*"],
                es_admin_env=True,
                sesion_iniciada_epoch=time.time(),
            )
        respuesta = client.get("/administracion/factory-reset")
        html = respuesta.get_data(as_text=True)
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("Restablecer APP Scheduler a estado base", html)
        self.assertIn('data-factory-reset-status-url="/administracion/factory-reset/estado"', html)
        self.assertIn("No cierres esta ventana", html)
        self.assertIn('class="factory-reset-ejecutando"', html)
        self.assertIn('aria-hidden="true"', html)

    def test_pantalla_recupera_operacion_en_curso_sin_ejecutar_reset(self):
        operacion = str(uuid4())
        with self.app.app_context():
            adquirir_lock_factory_reset("FACTORY_RESET_PREPARANDO", "test", operacion)
            actualizar_lock_factory_reset(
                operacion,
                "FACTORY_RESET_EN_PROGRESO",
                fase="EJECUTANDO_BOOTSTRAP",
                progreso=30,
                mensaje="Instalando estado base.",
            )
        client = self.app.test_client()
        with client.session_transaction() as sesion:
            sesion.update(
                usuario="admin",
                roles=["SUPER_ADMIN_ENV"],
                permisos=["*"],
                es_admin_env=True,
                sesion_iniciada_epoch=time.time(),
            )
        respuesta = client.get("/administracion/factory-reset")
        html = respuesta.get_data(as_text=True)
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("factory-reset-ejecutando visible", html)
        self.assertIn(f'data-factory-reset-operation="{operacion}"', html)
        self.assertIn('data-factory-reset-initial-phase="EJECUTANDO_BOOTSTRAP"', html)
        self.assertIn('aria-valuenow="30"', html)

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

    def test_permisos_sysadmin_habilitan_factory_reset(self):
        with self.app.app_context(), patch(
            "app.servicios.servicio_factory_reset_sql._resolver_sqlcmd", return_value="sqlcmd-test"
        ):
            motor = EjecutorSQLFactoryReset()
            with patch.object(motor, "ejecutar_consulta", return_value="FACTORY_PERMISSIONS|1|0|0|0|0|0"):
                permisos = motor.validar_permisos_administrativos()
            self.assertTrue(permisos["disponible"])
            self.assertTrue(permisos["sysadmin"])

    def test_permisos_equivalentes_habilitan_factory_reset(self):
        with self.app.app_context(), patch(
            "app.servicios.servicio_factory_reset_sql._resolver_sqlcmd", return_value="sqlcmd-test"
        ):
            motor = EjecutorSQLFactoryReset()
            with patch.object(motor, "ejecutar_consulta", return_value="FACTORY_PERMISSIONS|0|1|1|1|1|0"):
                permisos = motor.validar_permisos_administrativos()
            self.assertTrue(permisos["disponible"])
            self.assertTrue(permisos["gestionar_sesiones"])

    def test_permisos_incompletos_bloquean_factory_reset(self):
        with self.app.app_context(), patch(
            "app.servicios.servicio_factory_reset_sql._resolver_sqlcmd", return_value="sqlcmd-test"
        ):
            motor = EjecutorSQLFactoryReset()
            with patch.object(motor, "ejecutar_consulta", return_value="FACTORY_PERMISSIONS|0|0|0|1|0|0"):
                permisos = motor.validar_permisos_administrativos()
            self.assertFalse(permisos["disponible"])
            self.assertNotIn("admin-test", permisos["mensaje"])

    def test_fallo_sqlcmd_informa_script_y_sanitiza_salida(self):
        class ResultadoError:
            returncode = 1
            stdout = "password=secret-test usuario=admin-test servidor=sql-test\n"
            stderr = "CREATE DATABASE permission denied in database 'master'.\n"

        with self.app.app_context(), patch(
            "app.servicios.servicio_factory_reset_sql._resolver_sqlcmd", return_value="sqlcmd-test"
        ), patch(
            "app.servicios.servicio_factory_reset_sql.subprocess.run", return_value=ResultadoError()
        ):
            motor = EjecutorSQLFactoryReset()
            with self.assertRaises(ErrorFactoryResetSQL) as contexto:
                motor.ejecutar_archivo(
                    Path("database/release/001_crear_base_datos.sql"),
                    self.app.config["DB_DATABASE"],
                )
        mensaje = str(contexto.exception)
        self.assertIn("SCRIPT: 001_crear_base_datos.sql", mensaje)
        self.assertIn("RETURNCODE: 1", mensaje)
        self.assertIn("CREATE DATABASE permission denied", mensaje)
        self.assertNotIn("secret-test", mensaje)
        self.assertNotIn("admin-test", mensaje)
        self.assertNotIn("sql-test", mensaje)

    def test_drop_temporal_rechaza_base_operativa_y_nombre_ajeno(self):
        with self.app.app_context(), patch(
            "app.servicios.servicio_factory_reset_sql._resolver_sqlcmd", return_value="sqlcmd-test"
        ):
            motor = EjecutorSQLFactoryReset()
            operacion = str(uuid4())
            with patch.object(motor, "ejecutar_consulta", side_effect=AssertionError("No debe ejecutar SQL")):
                with self.assertRaises(ErrorFactoryResetSQL):
                    motor.eliminar_base_temporal_operacion(
                        self.app.config["DB_DATABASE"],
                        self.app.config["DB_DATABASE"],
                        operacion,
                    )
                with self.assertRaises(ErrorFactoryResetSQL):
                    motor.eliminar_base_temporal_operacion("BASE_AJENA", self.app.config["DB_DATABASE"], operacion)

    def test_drop_temporal_usa_nombre_exactamente_derivado(self):
        with self.app.app_context(), patch(
            "app.servicios.servicio_factory_reset_sql._resolver_sqlcmd", return_value="sqlcmd-test"
        ):
            motor = EjecutorSQLFactoryReset()
            operacion = str(uuid4())
            temporal = derivar_bases_temporales_factory_reset(self.app.config["DB_DATABASE"], operacion)["OLD"]
            with patch.object(motor, "ejecutar_consulta", return_value="FACTORY_DROP_OK|ELIMINADA") as consulta:
                self.assertTrue(
                    motor.eliminar_base_temporal_operacion(
                        temporal,
                        self.app.config["DB_DATABASE"],
                        operacion,
                    )
                )
            sql = consulta.call_args.args[0]
            self.assertIn(f"DROP DATABASE [{temporal}]", sql)
            self.assertNotIn(f"DROP DATABASE [{self.app.config['DB_DATABASE']}]", sql)
            self.assertEqual(consulta.call_args.kwargs["database"], "master")

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
