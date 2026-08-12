import unittest
from unittest.mock import patch

from app import crear_app
from app.servicios.servicio_factory_reset_sql import (
    parsear_targets_permitidos_factory_reset,
    validar_configuracion_factory_reset_sql,
)


class FactoryResetAllowlistTest(unittest.TestCase):
    def setUp(self):
        self.app = crear_app()
        self.app.config.update(
            TESTING=True,
            FACTORY_RESET_HABILITADO=True,
            DB_DATABASE="APP_SCHEDULER_QA",
            FACTORY_RESET_DB_TARGET="APP_SCHEDULER_QA",
            FACTORY_RESET_DB_ALLOWED_TARGETS="APP_SCHEDULER_QA",
            FACTORY_RESET_DB_SERVER="sql-test",
            FACTORY_RESET_DB_USER="admin-test",
            FACTORY_RESET_DB_PASSWORD="secret-test",
        )

    def _validar(self):
        with self.app.app_context(), patch(
            "app.servicios.servicio_factory_reset_sql._resolver_sqlcmd",
            return_value="sqlcmd-test",
        ):
            return validar_configuracion_factory_reset_sql()

    def test_allowlist_vacia_bloquea(self):
        self.app.config["FACTORY_RESET_DB_ALLOWED_TARGETS"] = ""
        resultado = self._validar()
        self.assertFalse(resultado["disponible"])
        self.assertFalse(resultado["allowlist_configurada"])

    def test_target_fuera_de_allowlist_bloquea(self):
        self.app.config["FACTORY_RESET_DB_ALLOWED_TARGETS"] = "APP_SCHEDULER_DEV"
        resultado = self._validar()
        self.assertFalse(resultado["disponible"])
        self.assertFalse(resultado["target_en_allowlist"])

    def test_target_en_allowlist_permite(self):
        resultado = self._validar()
        self.assertTrue(resultado["disponible"])
        self.assertTrue(resultado["target_en_allowlist"])

    def test_target_distinto_de_database_bloquea(self):
        self.app.config["DB_DATABASE"] = "APP_SCHEDULER_DEV"
        resultado = self._validar()
        self.assertFalse(resultado["disponible"])
        self.assertFalse(resultado["target_coincide"])

    def test_allowlist_con_espacios_se_parsea(self):
        permitidos = parsear_targets_permitidos_factory_reset("  APP_SCHEDULER_QA , , APP_SCHEDULER_DEV  ")
        self.assertEqual(permitidos, ["APP_SCHEDULER_QA", "APP_SCHEDULER_DEV"])

    def test_allowlist_multiple_exige_coincidencia_completa(self):
        self.app.config["FACTORY_RESET_DB_ALLOWED_TARGETS"] = "APP_SCHEDULER_DEV,APP_SCHEDULER_QA"
        resultado = self._validar()
        self.assertTrue(resultado["disponible"])
        self.assertEqual(len(resultado["targets_permitidos"]), 2)

    def test_wildcard_es_invalido_y_no_autoriza_qa(self):
        self.app.config["FACTORY_RESET_DB_ALLOWED_TARGETS"] = "APP_SCHEDULER_*"
        resultado = self._validar()
        self.assertFalse(resultado["disponible"])
        self.assertFalse(resultado["allowlist_configurada"])
        self.assertFalse(resultado["target_en_allowlist"])

    def test_produccion_no_es_autorizada_por_allowlist_qa(self):
        self.app.config.update(DB_DATABASE="APP_SCHEDULER", FACTORY_RESET_DB_TARGET="APP_SCHEDULER")
        resultado = self._validar()
        self.assertFalse(resultado["disponible"])
        self.assertFalse(resultado["target_en_allowlist"])

    def test_kill_switch_apagado_bloquea_target_permitido(self):
        self.app.config["FACTORY_RESET_HABILITADO"] = False
        resultado = self._validar()
        self.assertFalse(resultado["disponible"])
        self.assertTrue(resultado["target_en_allowlist"])

    def test_comparacion_de_identificadores_es_case_insensitive(self):
        self.app.config.update(
            DB_DATABASE="app_scheduler_qa",
            FACTORY_RESET_DB_TARGET="App_Scheduler_Qa",
            FACTORY_RESET_DB_ALLOWED_TARGETS="APP_SCHEDULER_QA",
        )
        resultado = self._validar()
        self.assertTrue(resultado["disponible"])
        self.assertTrue(resultado["target_coincide"])
        self.assertTrue(resultado["target_en_allowlist"])


if __name__ == "__main__":
    unittest.main()
