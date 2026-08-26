"""Contrato del modo oficial Worker queue-only."""

from datetime import datetime, timedelta
from threading import Event
from types import SimpleNamespace

import pytest

from app_scheduler.worker import aplicacion as aplicacion_worker
from app_scheduler.worker.scheduler import ResultadoCiclo
from app_scheduler.worker.servicio import ResultadoCicloCola, ServicioWorker


class LoggerFake:
    def __init__(self):
        self.infos = []
        self.errores = []

    def info(self, mensaje, *argumentos, **_kwargs):
        self.infos.append(mensaje % argumentos if argumentos else mensaje)

    def exception(self, mensaje, *_args, **_kwargs):
        self.errores.append(mensaje)


class EstadoHeartbeat:
    def __init__(self):
        self.eventos = []
        self.commits = 0


class UowHeartbeat:
    def __init__(self, estado):
        self.estado = estado

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def obtener_conexion(self):
        return self.estado

    def confirmar(self):
        self.estado.commits += 1


class RepoHeartbeatFake:
    def __init__(self, estado):
        self._estado = estado

    def iniciar(self, *datos):
        self._estado.eventos.append(("iniciar", datos))

    def estado(self, *datos):
        self._estado.eventos.append(("estado", datos))

    def fin_ciclo(self, *datos):
        self._estado.eventos.append(("fin", datos))

    def error(self, *datos):
        self._estado.eventos.append(("error", datos))


class ProcesadorFake:
    def __init__(self, reclamadas=0, *, intervalo=30, detener=None, error=None):
        self.reclamadas = reclamadas
        self.intervalo_revision_segundos = intervalo
        self.detener = detener
        self.error = error
        self.llamadas = 0
        self.cerrado = False

    def procesar_disponibles(self):
        self.llamadas += 1
        if self.detener is not None:
            self.detener.set()
        if self.error is not None:
            raise self.error
        return self.reclamadas

    def cerrar(self, *, esperar=True):
        self.cerrado = esperar


def worker_fake(estado, *, scheduler=None, procesador=None, detener=None):
    worker = ServicioWorker(
        estado, scheduler, type("Config", (), {"app_version": "test"})(),
        LoggerFake(), detener=detener or Event(), fabrica_uow=UowHeartbeat,
        repositorio=RepoHeartbeatFake,
    )
    worker.procesador_ejecuciones = procesador
    return worker


def test_construccion_queue_only_no_instancia_servicio_scheduler(
    configuracion, monkeypatch,
):
    instancias = []

    class SchedulerProhibido:
        def __init__(self, *_args, **_kwargs):
            instancias.append(1)

    monkeypatch.setattr(aplicacion_worker, "ServicioScheduler", SchedulerProhibido)
    worker, _detener = aplicacion_worker.construir_worker(
        configuracion, LoggerFake(), queue_only=True,
    )
    try:
        assert worker.scheduler is None
        assert instancias == []
    finally:
        worker.procesador_ejecuciones.cerrar(esperar=True)


def test_construccion_default_conserva_scheduler_y_cola(configuracion, monkeypatch):
    scheduler = object()
    monkeypatch.setattr(
        aplicacion_worker, "ServicioScheduler", lambda *_args, **_kwargs: scheduler,
    )
    worker, _detener = aplicacion_worker.construir_worker(
        configuracion, LoggerFake(), queue_only=False,
    )
    try:
        assert worker.scheduler is scheduler
        assert worker.procesador_ejecuciones is not None
    finally:
        worker.procesador_ejecuciones.cerrar(esperar=True)


@pytest.mark.parametrize("reclamadas", [0, 1])
def test_queue_only_once_cicla_heartbeat_y_sale_limpio(reclamadas):
    estado = EstadoHeartbeat()
    procesador = ProcesadorFake(reclamadas, intervalo=17)
    worker = worker_fake(estado, procesador=procesador)

    resultado = worker.ejecutar_solo_un_ciclo()

    assert resultado == ResultadoCicloCola(
        despachadas=reclamadas, intervalo_segundos=17,
    )
    assert procesador.llamadas == 1 and procesador.cerrado
    assert [evento[0] for evento in estado.eventos] == [
        "iniciar", "estado", "fin", "estado",
    ]
    assert estado.eventos[-1][1][1] == "DETENIDO"


def test_queue_only_continuo_mantiene_loop_heartbeat_sin_scheduler():
    estado = EstadoHeartbeat()
    detener = Event()
    procesador = ProcesadorFake(1, intervalo=10, detener=detener)
    worker = worker_fake(estado, procesador=procesador, detener=detener)

    worker.ejecutar()

    resultado = estado.eventos[2][1][1]
    assert resultado.resultado == "QUEUE_ONLY" and resultado.despachadas == 1
    assert procesador.llamadas == 1 and procesador.cerrado
    assert [evento[0] for evento in estado.eventos] == [
        "iniciar", "estado", "fin", "estado",
    ]


def test_default_y_once_siguen_invocando_scheduler():
    estado = EstadoHeartbeat()

    class Scheduler:
        llamadas = 0

        def ejecutar_ciclo(self, *_args):
            self.llamadas += 1
            return ResultadoCiclo("OK", intervalo_segundos=60)

    scheduler = Scheduler()
    procesador = ProcesadorFake(0)
    resultado = worker_fake(
        estado, scheduler=scheduler, procesador=procesador,
    ).ejecutar_solo_un_ciclo()

    assert resultado.resultado == "OK"
    assert scheduler.llamadas == 1 and procesador.llamadas == 1


def test_queue_only_conserva_error_controlado_del_consumidor():
    estado = EstadoHeartbeat()
    procesador = ProcesadorFake(error=RuntimeError("fallo controlado"))
    worker = worker_fake(estado, procesador=procesador)

    assert worker.ejecutar_una_vez() is None
    assert [evento[0] for evento in estado.eventos] == ["estado", "error"]


class RepoSaludFake:
    def __init__(self, estado):
        self.estado = estado

    def obtener_configuracion_scheduler(self):
        return SimpleNamespace(intervalo_revision_segundos=self.estado["intervalo"])

    def obtener_heartbeat_del_host(self, host):
        assert host == "worker-qa"
        return self.estado["heartbeat"]


def test_healthcheck_worker_usa_heartbeat_del_contenedor(configuracion):
    ahora = datetime(2026, 8, 26, 12, 0, 0)
    estado = {
        "intervalo": 60,
        "heartbeat": SimpleNamespace(
            estado="ESPERANDO", fecha_ultimo_heartbeat=ahora - timedelta(seconds=45),
        ),
    }

    saludable, mensaje = aplicacion_worker.comprobar_salud_worker(
        configuracion, proveedor=estado, host="worker-qa", reloj=lambda: ahora,
        fabrica_uow=UowHeartbeat, repositorio=RepoSaludFake,
    )

    assert saludable is True
    assert mensaje == "Heartbeat del Worker operativo."


@pytest.mark.parametrize(
    ("heartbeat", "esperado"),
    [
        (None, "No existe heartbeat"),
        (SimpleNamespace(estado="DETENIDO", fecha_ultimo_heartbeat=datetime(2026, 8, 26, 12)), "estado DETENIDO"),
        (SimpleNamespace(estado="ESPERANDO", fecha_ultimo_heartbeat=datetime(2026, 8, 26, 11, 54)), "excede la ventana"),
    ],
)
def test_healthcheck_worker_falla_sin_senal_operativa(configuracion, heartbeat, esperado):
    ahora = datetime(2026, 8, 26, 12, 0, 0)
    estado = {"intervalo": 60, "heartbeat": heartbeat}

    saludable, mensaje = aplicacion_worker.comprobar_salud_worker(
        configuracion, proveedor=estado, host="worker-qa", reloj=lambda: ahora,
        fabrica_uow=UowHeartbeat, repositorio=RepoSaludFake,
    )

    assert saludable is False
    assert esperado in mensaje
