"""Punto de entrada del worker scheduler reconstruido."""

from __future__ import annotations

import argparse
import signal
from threading import Event

from app_scheduler.compartido.base_datos import ProveedorConexionesSQLServer
from app_scheduler.compartido.logging import configurar_logging
from app_scheduler.configuracion import ConfiguracionAplicacion
from app_scheduler.worker.scheduler import ServicioScheduler
from app_scheduler.worker.servicio import ServicioWorker


def preparar_worker(
    configuracion: ConfiguracionAplicacion | None = None,
):
    configuracion = configuracion or ConfiguracionAplicacion.desde_entorno()
    configuracion.validar("worker")
    return configurar_logging(
        "app_scheduler.worker",
        configuracion.log_level,
        configuracion.secretos_conocidos(),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Base tecnica del worker reconstruido.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Valida configuracion e inicializacion sin iniciar scheduler ni ejecuciones.",
    )
    parser.add_argument(
        "--once", action="store_true",
        help="Ejecuta un unico ciclo scheduler sin iniciar procesos de usuario.",
    )
    argumentos = parser.parse_args()
    configuracion = ConfiguracionAplicacion.desde_entorno()
    logger = preparar_worker(configuracion)
    if argumentos.check:
        logger.info("Worker base validado", extra={"evento": "WORKER_BASE_OK"})
        return 0
    proveedor = ProveedorConexionesSQLServer(configuracion)
    detener = Event()
    worker = ServicioWorker(
        proveedor, ServicioScheduler(proveedor, configuracion), configuracion,
        logger, detener=detener,
    )
    if argumentos.once:
        return 0 if worker.ejecutar_solo_un_ciclo() is not None else 1

    def solicitar_detencion(_senal, _marco):
        detener.set()

    signal.signal(signal.SIGINT, solicitar_detencion)
    signal.signal(signal.SIGTERM, solicitar_detencion)
    worker.ejecutar()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
