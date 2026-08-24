from __future__ import annotations

import pytest

from app_scheduler.configuracion import ConfiguracionAplicacion, ErrorConfiguracion


def test_configuracion_local_tipifica_valores(valores_configuracion):
    configuracion = ConfiguracionAplicacion.desde_entorno(valores_configuracion)

    assert configuracion.app_env == "LOCAL"
    assert configuracion.app_port == 5000
    assert configuracion.app_debug is False
    assert configuracion.db_timeout == 5
    assert configuracion.ejecucion_timeout_segundos == 3600
    assert configuracion.ejecucion_gracia_terminacion_segundos == 5
    assert configuracion.session_cookie_secure is False
    configuracion.validar("web")


def test_configuracion_rechaza_base_distinta(valores_configuracion):
    valores_configuracion["DB_DATABASE"] = "OTRA_BASE"
    configuracion = ConfiguracionAplicacion.desde_entorno(valores_configuracion)

    with pytest.raises(ErrorConfiguracion, match="APP_SCHEDULER_QA"):
        configuracion.validar("web")


def test_configuracion_reporta_nombre_sin_revelar_password(valores_configuracion):
    valores_configuracion["DB_PASSWORD"] = ""
    configuracion = ConfiguracionAplicacion.desde_entorno(valores_configuracion)

    with pytest.raises(ErrorConfiguracion) as captura:
        configuracion.validar("worker")

    assert "DB_PASSWORD" in str(captura.value)
    assert "password-test-no-real" not in str(captura.value)


def test_factory_reset_no_exige_cuenta_mantenimiento_si_esta_apagado(configuracion):
    configuracion.validar("factory_reset")


def test_factory_reset_exige_cuenta_separada_solo_al_habilitar(valores_configuracion):
    valores_configuracion["FACTORY_RESET_HABILITADO"] = "true"
    configuracion = ConfiguracionAplicacion.desde_entorno(valores_configuracion)

    with pytest.raises(ErrorConfiguracion) as captura:
        configuracion.validar("factory_reset")

    assert "FACTORY_RESET_DB_USER" in str(captura.value)
    assert "DB_USER" not in str(captura.value).replace("FACTORY_RESET_DB_USER", "")


def test_graph_no_exige_secret_si_esta_apagado(configuracion):
    configuracion.validar("graph")


def test_samesite_none_exige_cookie_segura(valores_configuracion):
    valores_configuracion["SESSION_COOKIE_SAMESITE"] = "None"
    configuracion = ConfiguracionAplicacion.desde_entorno(valores_configuracion)

    with pytest.raises(ErrorConfiguracion, match="SESSION_COOKIE_SECURE"):
        configuracion.validar("web")
