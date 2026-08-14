from __future__ import annotations

import pytest

from app_scheduler.configuracion import ConfiguracionAplicacion


@pytest.fixture
def valores_configuracion():
    return {
        "APP_ENV": "LOCAL",
        "APP_SECRET_KEY": "secret-test-no-real",
        "APP_HOST": "127.0.0.1",
        "APP_PORT": "5000",
        "APP_DEBUG": "false",
        "APP_VERSION": "hito1-test",
        "SESSION_COOKIE_SECURE": "false",
        "SESSION_COOKIE_SAMESITE": "Lax",
        "CSRF_TTL_SEGUNDOS": "3600",
        "LOG_LEVEL": "INFO",
        "DB_SERVER": "servidor-test",
        "DB_DATABASE": "APP_SCHEDULER_QA",
        "DB_USER": "usuario-test",
        "DB_PASSWORD": "password-test-no-real",
        "DB_DRIVER": "ODBC Driver Test",
        "DB_ENCRYPT": "no",
        "DB_TRUST_SERVER_CERTIFICATE": "yes",
        "DB_TIMEOUT": "5",
        "DB_APPLICATION_NAME": "APP_SCHEDULER_TESTS",
        "USUARIO_ADMIN_DEFECTO": "admin-test",
        "PASSWORD_ADMIN_DEFECTO": "admin-password-test-no-real",
        "FACTORY_RESET_HABILITADO": "false",
        "GRAPH_MAIL_ENABLED": "false",
    }


@pytest.fixture
def configuracion(valores_configuracion):
    return ConfiguracionAplicacion.desde_entorno(valores_configuracion)
