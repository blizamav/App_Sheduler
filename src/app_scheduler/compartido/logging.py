"""Logging estructurado y sanitizado para procesos APP Scheduler."""

from __future__ import annotations

import logging
import re
from collections.abc import Iterable


PATRON_SECRETO = re.compile(
    r"(?i)\b(password|passwd|pwd|secret|token|authorization|client_secret|db_password)\b"
    r"(\s*[=:]\s*)([^\s,;]+)"
)


def sanitizar_texto(valor: object, secretos: Iterable[str] = ()) -> str:
    texto = str(valor)
    texto = PATRON_SECRETO.sub(lambda m: f"{m.group(1)}{m.group(2)}***", texto)
    for secreto in secretos:
        if secreto:
            texto = texto.replace(str(secreto), "***")
    return texto


class FiltroSecretos(logging.Filter):
    def __init__(self, secretos: Iterable[str] = ()):
        super().__init__()
        self.secretos = tuple(secretos)

    def filter(self, registro: logging.LogRecord) -> bool:
        try:
            mensaje = registro.getMessage()
        except Exception:
            mensaje = str(registro.msg)
        registro.msg = sanitizar_texto(mensaje, self.secretos)
        registro.args = ()
        if not hasattr(registro, "evento"):
            registro.evento = "GENERAL"
        return True


def configurar_logging(nombre: str, nivel: str, secretos: Iterable[str] = ()) -> logging.Logger:
    logger = logging.getLogger(nombre)
    logger.setLevel(getattr(logging, nivel, logging.INFO))
    logger.propagate = False

    for manejador in list(logger.handlers):
        if getattr(manejador, "_app_scheduler_base", False):
            logger.removeHandler(manejador)

    manejador = logging.StreamHandler()
    manejador._app_scheduler_base = True
    manejador.addFilter(FiltroSecretos(secretos))
    manejador.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(evento)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(manejador)
    return logger
