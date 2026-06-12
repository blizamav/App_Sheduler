import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


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

    USUARIO_ADMIN_DEFECTO = os.getenv("USUARIO_ADMIN_DEFECTO", "blizama")
    PASSWORD_ADMIN_DEFECTO = os.getenv("PASSWORD_ADMIN_DEFECTO", "")

    RUTA_BASE_SCRIPTS = os.getenv("RUTA_BASE_SCRIPTS", "scripts")
    RUTA_BASE_LOGS_TAREAS = os.getenv("RUTA_BASE_LOGS_TAREAS", "logs_tareas")
    RUTA_BASE_LOGS_SISTEMA = os.getenv("RUTA_BASE_LOGS_SISTEMA", "logs_sistema")
    ZONA_HORARIA = os.getenv("ZONA_HORARIA", "America/Santiago")
