from __future__ import annotations

import logging

import pytest

from app_scheduler.compartido.logging import FiltroSecretos, sanitizar_texto
from app_scheduler.worker.aplicacion import preparar_worker
from app_scheduler.worker.contratos import MotorNoImplementado, OrigenEjecucion, SolicitudEjecucion


def test_sanitizacion_oculta_claves_y_valores_conocidos():
    texto = sanitizar_texto(
        "password=secreto token:abc conexion clave-real",
        secretos=("clave-real",),
    )

    assert "secreto" not in texto
    assert "abc" not in texto
    assert "clave-real" not in texto
    assert texto.count("***") == 3


def test_filtro_agrega_evento_y_elimina_argumentos():
    registro = logging.LogRecord("test", logging.INFO, __file__, 1, "pwd=%s", ("valor",), None)

    assert FiltroSecretos().filter(registro) is True
    assert registro.evento == "GENERAL"
    assert registro.args == ()
    assert "valor" not in registro.msg


def test_worker_base_prepara_logging_sin_scheduler(configuracion):
    logger = preparar_worker(configuracion)

    assert logger.name == "app_scheduler.worker"
    assert logger.handlers


def test_motor_de_ejecucion_permanece_bloqueado_hasta_hito_7():
    solicitud = SolicitudEjecucion(1, 2, 3, OrigenEjecucion.MANUAL, "usuario-test")

    with pytest.raises(NotImplementedError, match="Hito 7"):
        MotorNoImplementado().solicitar(solicitud)
