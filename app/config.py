import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env", override=False)


VALORES_PLANTILLA = {
    "",
    "CAMBIAR_EN_ENV_REAL",
    "SERVIDOR_O_INSTANCIA",
    "USUARIO_SQL",
    "PASSWORD_SQL",
}


VARIABLES_CRITICAS = [
    "APP_SECRET_KEY",
    "DB_SERVER",
    "DB_DATABASE",
    "DB_USER",
    "DB_PASSWORD",
    "DB_DRIVER",
    "USUARIO_ADMIN_DEFECTO",
    "PASSWORD_ADMIN_DEFECTO",
]


def validar_configuracion_critica():
    """Retorna variables criticas faltantes o con valores de plantilla."""
    advertencias = []

    for nombre in VARIABLES_CRITICAS:
        valor = os.getenv(nombre, "")
        if str(valor or "").strip() in VALORES_PLANTILLA:
            advertencias.append(nombre)

    return advertencias


class Configuracion:
    """Configuracion central de la aplicacion cargada desde variables de entorno."""

    APP_ENV = os.getenv("APP_ENV", "LOCAL")
    SECRET_KEY = os.getenv("APP_SECRET_KEY", "CAMBIAR_EN_ENV_REAL")
    APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
    APP_PORT = int(os.getenv("APP_PORT", "5000"))
    APP_DEBUG = os.getenv("APP_DEBUG", "False").lower() in {"1", "true", "yes", "si"}

    DB_SERVER = os.getenv("DB_SERVER", "")
    DB_DATABASE = os.getenv("DB_DATABASE", "APP_SCHEDULER_QA")
    DB_USER = os.getenv("DB_USER", "")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
    DB_ENCRYPT = os.getenv("DB_ENCRYPT", "no")
    DB_TRUST_SERVER_CERTIFICATE = os.getenv("DB_TRUST_SERVER_CERTIFICATE", "yes")
    DB_TIMEOUT = int(os.getenv("DB_TIMEOUT", "10"))
    DB_APPLICATION_NAME = os.getenv("DB_APPLICATION_NAME", "APP_SCHEDULER")

    USUARIO_ADMIN_DEFECTO = os.getenv("USUARIO_ADMIN_DEFECTO", "blizama")
    PASSWORD_ADMIN_DEFECTO = os.getenv("PASSWORD_ADMIN_DEFECTO", "")

    RUTA_BASE_SCRIPTS = os.getenv("RUTA_BASE_SCRIPTS", "scripts")
    RUTA_BASE_ENV_SCRIPTS = os.getenv("RUTA_BASE_ENV_SCRIPTS", "env_scripts")
    RUTA_BASE_LOGS_TAREAS = os.getenv("RUTA_BASE_LOGS_TAREAS", "logs_tareas")
    RUTA_BASE_LOGS_SISTEMA = os.getenv("RUTA_BASE_LOGS_SISTEMA", "logs_sistema")
    RUTA_BASE_LOGS_WORKER = os.getenv("RUTA_BASE_LOGS_WORKER", "logs")
    RUTA_CONTROL_RUNTIME = os.getenv("RUTA_CONTROL_RUNTIME", "runtime_control")
    FACTORY_RESET_LOCK_TIMEOUT_SEGUNDOS = int(os.getenv("FACTORY_RESET_LOCK_TIMEOUT_SEGUNDOS", "1800"))
    FACTORY_RESET_PREVIEW_TTL_SEGUNDOS = int(os.getenv("FACTORY_RESET_PREVIEW_TTL_SEGUNDOS", "300"))
    FACTORY_RESET_CSRF_TTL_SEGUNDOS = int(os.getenv("FACTORY_RESET_CSRF_TTL_SEGUNDOS", "600"))
    FACTORY_RESET_HABILITADO = os.getenv("FACTORY_RESET_HABILITADO", "false").lower() in {"1", "true", "yes", "si"}
    FACTORY_RESET_DB_TARGET = os.getenv("FACTORY_RESET_DB_TARGET", "")
    FACTORY_RESET_DB_SERVER = os.getenv("FACTORY_RESET_DB_SERVER", "")
    FACTORY_RESET_DB_USER = os.getenv("FACTORY_RESET_DB_USER", "")
    FACTORY_RESET_DB_PASSWORD = os.getenv("FACTORY_RESET_DB_PASSWORD", "")
    FACTORY_RESET_DB_ENCRYPT = os.getenv("FACTORY_RESET_DB_ENCRYPT", "no")
    FACTORY_RESET_DB_TRUST_SERVER_CERTIFICATE = os.getenv("FACTORY_RESET_DB_TRUST_SERVER_CERTIFICATE", "yes")
    FACTORY_RESET_SQLCMD = os.getenv("FACTORY_RESET_SQLCMD", "sqlcmd")
    FACTORY_RESET_SQLCMD_TIMEOUT_SEGUNDOS = int(os.getenv("FACTORY_RESET_SQLCMD_TIMEOUT_SEGUNDOS", "900"))
    FACTORY_RESET_APP_NAME_PREFIX = os.getenv("FACTORY_RESET_APP_NAME_PREFIX", "APP_SCHEDULER")
    MAX_SCRIPT_SIZE_MB = int(os.getenv("MAX_SCRIPT_SIZE_MB", "5"))
    MAX_ENV_SIZE_KB = int(os.getenv("MAX_ENV_SIZE_KB", "100"))
    ZONA_HORARIA = os.getenv("ZONA_HORARIA", "America/Santiago")
    APP_VERSION = os.getenv("APP_VERSION", "local")

    GRAPH_CLIENT_SECRET = os.getenv("GRAPH_CLIENT_SECRET", "")
    GRAPH_SECRET_CONFIG_MODE = os.getenv("GRAPH_SECRET_CONFIG_MODE", "ENV")
    GRAPH_TENANT_ID = os.getenv("GRAPH_TENANT_ID", "")
    GRAPH_CLIENT_ID = os.getenv("GRAPH_CLIENT_ID", "")
    GRAPH_SCOPE = os.getenv("GRAPH_SCOPE", "https://graph.microsoft.com/.default")
    GRAPH_SEND_MAIL_USER = os.getenv("GRAPH_SEND_MAIL_USER", "")
    GRAPH_MAIL_ENABLED = os.getenv("GRAPH_MAIL_ENABLED", "false").lower() in {"1", "true", "yes", "si"}
    GRAPH_SAVE_TO_SENT_ITEMS = os.getenv("GRAPH_SAVE_TO_SENT_ITEMS", "true").lower() in {"1", "true", "yes", "si"}
    GRAPH_ALERTAS_DEFAULT = os.getenv("GRAPH_ALERTAS_DEFAULT", "")
