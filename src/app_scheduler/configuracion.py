"""Carga y validacion tipada de configuracion por ambiente."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from dotenv import dotenv_values


RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
VALORES_PLANTILLA = {
    "",
    "CAMBIAR_EN_ENV_REAL",
    "SERVIDOR_O_INSTANCIA",
    "USUARIO_SQL",
    "PASSWORD_SQL",
    "PASSWORD_SQL_ESCAPADA_PARA_DOCKER",
}


class ErrorConfiguracion(RuntimeError):
    """Indica configuracion ausente o invalida sin exponer valores."""


def _texto(valores: Mapping[str, str], nombre: str, default: str = "") -> str:
    return str(valores.get(nombre, default) or "").strip()


def _booleano(valores: Mapping[str, str], nombre: str, default: bool = False) -> bool:
    bruto = _texto(valores, nombre, "true" if default else "false").lower()
    if bruto in {"1", "true", "yes", "si"}:
        return True
    if bruto in {"0", "false", "no"}:
        return False
    raise ErrorConfiguracion(f"{nombre} debe ser un valor booleano valido.")


def _entero(
    valores: Mapping[str, str],
    nombre: str,
    default: int,
    minimo: int = 1,
    maximo: int | None = None,
) -> int:
    try:
        valor = int(_texto(valores, nombre, str(default)))
    except ValueError as error:
        raise ErrorConfiguracion(f"{nombre} debe ser un numero entero valido.") from error
    if valor < minimo or (maximo is not None and valor > maximo):
        rango = f"entre {minimo} y {maximo}" if maximo is not None else f"mayor o igual a {minimo}"
        raise ErrorConfiguracion(f"{nombre} debe ser {rango}.")
    return valor


@dataclass(frozen=True, slots=True)
class ConfiguracionAplicacion:
    """Configuracion inmutable compartida por web y worker."""

    app_env: str
    app_secret_key: str
    app_host: str
    app_port: int
    app_debug: bool
    app_version: str
    session_cookie_secure: bool
    session_cookie_samesite: str
    csrf_ttl_segundos: int
    log_level: str
    db_server: str
    db_database: str
    db_user: str
    db_password: str
    db_driver: str
    db_encrypt: str
    db_trust_server_certificate: str
    db_timeout: int
    db_application_name: str
    usuario_admin_defecto: str
    password_admin_defecto: str
    ruta_base_scripts: Path
    ruta_base_env_scripts: Path
    ruta_base_logs_tareas: Path
    ruta_base_logs_sistema: Path
    ruta_base_logs_worker: Path
    ruta_control_runtime: Path
    zona_horaria: str
    max_script_size_mb: int
    max_env_size_kb: int
    ejecucion_timeout_segundos: int
    ejecucion_gracia_terminacion_segundos: int
    factory_reset_lock_timeout_segundos: int
    factory_reset_preview_ttl_segundos: int
    factory_reset_csrf_ttl_segundos: int
    factory_reset_habilitado: bool
    factory_reset_db_target: str
    factory_reset_db_allowed_targets: str
    factory_reset_db_server: str
    factory_reset_db_user: str
    factory_reset_db_password: str
    factory_reset_db_encrypt: str
    factory_reset_db_trust_server_certificate: str
    factory_reset_sqlcmd: str
    factory_reset_sqlcmd_timeout_segundos: int
    factory_reset_app_name_prefix: str
    graph_mail_enabled: bool
    graph_client_secret: str
    graph_secret_config_mode: str
    graph_tenant_id: str
    graph_client_id: str
    graph_scope: str
    graph_send_mail_user: str
    graph_save_to_sent_items: bool
    graph_alertas_default: str

    @classmethod
    def desde_entorno(
        cls,
        valores: Mapping[str, str] | None = None,
        archivo_local: Path | None = None,
    ) -> "ConfiguracionAplicacion":
        """Construye configuracion sin cargar nunca `.env.docker` por cuenta propia."""
        if valores is None:
            combinados = {
                clave: str(valor)
                for clave, valor in dotenv_values(archivo_local or RAIZ_PROYECTO / ".env").items()
                if valor is not None
            }
            combinados.update(os.environ)
            valores = combinados

        entorno = _texto(valores, "APP_ENV", "LOCAL").upper()
        if entorno not in {"LOCAL", "QA", "PRODUCCION"}:
            raise ErrorConfiguracion("APP_ENV debe ser LOCAL, QA o PRODUCCION.")

        samesite = _texto(valores, "SESSION_COOKIE_SAMESITE", "Lax").capitalize()
        if samesite not in {"Lax", "Strict", "None"}:
            raise ErrorConfiguracion("SESSION_COOKIE_SAMESITE debe ser Lax, Strict o None.")

        log_level = _texto(valores, "LOG_LEVEL", "INFO").upper()
        if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ErrorConfiguracion("LOG_LEVEL no es valido.")

        return cls(
            app_env=entorno,
            app_secret_key=_texto(valores, "APP_SECRET_KEY"),
            app_host=_texto(valores, "APP_HOST", "127.0.0.1"),
            app_port=_entero(valores, "APP_PORT", 5000, 1, 65535),
            app_debug=_booleano(valores, "APP_DEBUG", False),
            app_version=_texto(valores, "APP_VERSION", "reconstruccion-local"),
            session_cookie_secure=_booleano(valores, "SESSION_COOKIE_SECURE", False),
            session_cookie_samesite=samesite,
            csrf_ttl_segundos=_entero(valores, "CSRF_TTL_SEGUNDOS", 3600, 60, 86400),
            log_level=log_level,
            db_server=_texto(valores, "DB_SERVER"),
            db_database=_texto(valores, "DB_DATABASE", "APP_SCHEDULER_QA"),
            db_user=_texto(valores, "DB_USER"),
            db_password=_texto(valores, "DB_PASSWORD"),
            db_driver=_texto(valores, "DB_DRIVER", "ODBC Driver 17 for SQL Server"),
            db_encrypt=_texto(valores, "DB_ENCRYPT", "no").lower(),
            db_trust_server_certificate=_texto(
                valores, "DB_TRUST_SERVER_CERTIFICATE", "yes"
            ).lower(),
            db_timeout=_entero(valores, "DB_TIMEOUT", 10, 1, 120),
            db_application_name=_texto(valores, "DB_APPLICATION_NAME", "APP_SCHEDULER"),
            usuario_admin_defecto=_texto(valores, "USUARIO_ADMIN_DEFECTO"),
            password_admin_defecto=_texto(valores, "PASSWORD_ADMIN_DEFECTO"),
            ruta_base_scripts=Path(_texto(valores, "RUTA_BASE_SCRIPTS", "scripts")),
            ruta_base_env_scripts=Path(_texto(valores, "RUTA_BASE_ENV_SCRIPTS", "env_scripts")),
            ruta_base_logs_tareas=Path(_texto(valores, "RUTA_BASE_LOGS_TAREAS", "logs_tareas")),
            ruta_base_logs_sistema=Path(_texto(valores, "RUTA_BASE_LOGS_SISTEMA", "logs_sistema")),
            ruta_base_logs_worker=Path(_texto(valores, "RUTA_BASE_LOGS_WORKER", "logs")),
            ruta_control_runtime=Path(_texto(valores, "RUTA_CONTROL_RUNTIME", "runtime_control")),
            zona_horaria=_texto(valores, "ZONA_HORARIA", "America/Santiago"),
            max_script_size_mb=_entero(valores, "MAX_SCRIPT_SIZE_MB", 5, 1, 100),
            max_env_size_kb=_entero(valores, "MAX_ENV_SIZE_KB", 100, 1, 1024),
            ejecucion_timeout_segundos=_entero(
                valores, "EJECUCION_TIMEOUT_SEGUNDOS", 3600, 10, 86400
            ),
            ejecucion_gracia_terminacion_segundos=_entero(
                valores, "EJECUCION_GRACIA_TERMINACION_SEGUNDOS", 5, 1, 60
            ),
            factory_reset_lock_timeout_segundos=_entero(
                valores, "FACTORY_RESET_LOCK_TIMEOUT_SEGUNDOS", 1800, 60, 86400
            ),
            factory_reset_preview_ttl_segundos=_entero(
                valores, "FACTORY_RESET_PREVIEW_TTL_SEGUNDOS", 300, 60, 3600
            ),
            factory_reset_csrf_ttl_segundos=_entero(
                valores, "FACTORY_RESET_CSRF_TTL_SEGUNDOS", 600, 60, 3600
            ),
            factory_reset_habilitado=_booleano(valores, "FACTORY_RESET_HABILITADO", False),
            factory_reset_db_target=_texto(valores, "FACTORY_RESET_DB_TARGET"),
            factory_reset_db_allowed_targets=_texto(valores, "FACTORY_RESET_DB_ALLOWED_TARGETS"),
            factory_reset_db_server=_texto(valores, "FACTORY_RESET_DB_SERVER"),
            factory_reset_db_user=_texto(valores, "FACTORY_RESET_DB_USER"),
            factory_reset_db_password=_texto(valores, "FACTORY_RESET_DB_PASSWORD"),
            factory_reset_db_encrypt=_texto(valores, "FACTORY_RESET_DB_ENCRYPT", "no").lower(),
            factory_reset_db_trust_server_certificate=_texto(
                valores, "FACTORY_RESET_DB_TRUST_SERVER_CERTIFICATE", "yes"
            ).lower(),
            factory_reset_sqlcmd=_texto(valores, "FACTORY_RESET_SQLCMD", "sqlcmd"),
            factory_reset_sqlcmd_timeout_segundos=_entero(
                valores, "FACTORY_RESET_SQLCMD_TIMEOUT_SEGUNDOS", 900, 30, 7200
            ),
            factory_reset_app_name_prefix=_texto(
                valores, "FACTORY_RESET_APP_NAME_PREFIX", "APP_SCHEDULER"
            ),
            graph_mail_enabled=_booleano(valores, "GRAPH_MAIL_ENABLED", False),
            graph_client_secret=_texto(valores, "GRAPH_CLIENT_SECRET"),
            graph_secret_config_mode=_texto(valores, "GRAPH_SECRET_CONFIG_MODE", "ENV"),
            graph_tenant_id=_texto(valores, "GRAPH_TENANT_ID"),
            graph_client_id=_texto(valores, "GRAPH_CLIENT_ID"),
            graph_scope=_texto(valores, "GRAPH_SCOPE", "https://graph.microsoft.com/.default"),
            graph_send_mail_user=_texto(valores, "GRAPH_SEND_MAIL_USER"),
            graph_save_to_sent_items=_booleano(valores, "GRAPH_SAVE_TO_SENT_ITEMS", True),
            graph_alertas_default=_texto(valores, "GRAPH_ALERTAS_DEFAULT"),
        )

    def validar(self, capacidad: str = "web") -> None:
        """Valida solo las variables que necesita la capacidad solicitada."""
        requeridas = {
            "DB_SERVER": self.db_server,
            "DB_DATABASE": self.db_database,
            "DB_USER": self.db_user,
            "DB_PASSWORD": self.db_password,
            "DB_DRIVER": self.db_driver,
        }
        if capacidad == "web":
            requeridas["APP_SECRET_KEY"] = self.app_secret_key
        if capacidad == "autenticacion":
            requeridas.update(
                {
                    "APP_SECRET_KEY": self.app_secret_key,
                    "USUARIO_ADMIN_DEFECTO": self.usuario_admin_defecto,
                    "PASSWORD_ADMIN_DEFECTO": self.password_admin_defecto,
                }
            )
        if capacidad == "factory_reset" and self.factory_reset_habilitado:
            requeridas.update(
                {
                    "FACTORY_RESET_DB_TARGET": self.factory_reset_db_target,
                    "FACTORY_RESET_DB_ALLOWED_TARGETS": self.factory_reset_db_allowed_targets,
                    "FACTORY_RESET_DB_SERVER": self.factory_reset_db_server,
                    "FACTORY_RESET_DB_USER": self.factory_reset_db_user,
                    "FACTORY_RESET_DB_PASSWORD": self.factory_reset_db_password,
                    "FACTORY_RESET_SQLCMD": self.factory_reset_sqlcmd,
                }
            )
        if capacidad == "graph" and self.graph_mail_enabled:
            requeridas.update(
                {
                    "GRAPH_CLIENT_SECRET": self.graph_client_secret,
                    "GRAPH_TENANT_ID": self.graph_tenant_id,
                    "GRAPH_CLIENT_ID": self.graph_client_id,
                    "GRAPH_SCOPE": self.graph_scope,
                    "GRAPH_SEND_MAIL_USER": self.graph_send_mail_user,
                }
            )

        invalidas = sorted(
            nombre
            for nombre, valor in requeridas.items()
            if str(valor or "").strip() in VALORES_PLANTILLA
        )
        if invalidas:
            raise ErrorConfiguracion(
                "Configuracion incompleta para "
                f"{capacidad}: {', '.join(invalidas)}. Revisa el archivo del ambiente."
            )
        if self.db_database.upper() != "APP_SCHEDULER_QA":
            raise ErrorConfiguracion("DB_DATABASE debe ser APP_SCHEDULER_QA.")
        if self.session_cookie_samesite == "None" and not self.session_cookie_secure:
            raise ErrorConfiguracion(
                "SESSION_COOKIE_SECURE debe estar activo cuando SESSION_COOKIE_SAMESITE=None."
            )

    def como_config_flask(self) -> dict[str, object]:
        return {
            "APP_ENV": self.app_env,
            "APP_HOST": self.app_host,
            "APP_PORT": self.app_port,
            "APP_DEBUG": self.app_debug,
            "APP_VERSION": self.app_version,
            "SECRET_KEY": self.app_secret_key,
            "SESSION_COOKIE_HTTPONLY": True,
            "SESSION_COOKIE_SECURE": self.session_cookie_secure,
            "SESSION_COOKIE_SAMESITE": self.session_cookie_samesite,
            "SESSION_REFRESH_EACH_REQUEST": False,
            "CSRF_TTL_SEGUNDOS": self.csrf_ttl_segundos,
            "DB_SERVER": self.db_server,
            "DB_DATABASE": self.db_database,
            "DB_USER": self.db_user,
            "DB_PASSWORD": self.db_password,
            "DB_DRIVER": self.db_driver,
            "DB_ENCRYPT": self.db_encrypt,
            "DB_TRUST_SERVER_CERTIFICATE": self.db_trust_server_certificate,
            "DB_TIMEOUT": self.db_timeout,
            "DB_APPLICATION_NAME": self.db_application_name,
            "CONFIGURACION_APLICACION": self,
        }

    def secretos_conocidos(self) -> tuple[str, ...]:
        return tuple(
            valor
            for valor in (
                self.app_secret_key,
                self.db_password,
                self.password_admin_defecto,
                self.factory_reset_db_password,
                self.graph_client_secret,
            )
            if valor and valor not in VALORES_PLANTILLA
        )
