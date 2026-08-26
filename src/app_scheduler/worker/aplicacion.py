"""Punto de entrada del worker scheduler reconstruido."""

from __future__ import annotations

import argparse
import signal
import socket
from datetime import datetime
from threading import Event

from app_scheduler.compartido.base_datos import ProveedorConexionesSQLServer
from app_scheduler.compartido.logging import configurar_logging
from app_scheduler.configuracion import ConfiguracionAplicacion
from app_scheduler.worker.scheduler import ServicioScheduler
from app_scheduler.worker.servicio import ServicioWorker
from app_scheduler.worker.cola import ProcesadorColaEjecuciones
from app_scheduler.worker.motor import MotorEjecucionSubprocess
from app_scheduler.modulos.notificaciones.casos_uso import ServicioConfiguracionGraph
from app_scheduler.modulos.notificaciones.despacho import ServicioDespachoNotificaciones
from app_scheduler.compartido.unidad_trabajo import UnidadTrabajoSQL
from app_scheduler.persistencia.repositorio_operacion import RepositorioOperacion


ESTADOS_WORKER_SALUDABLES = frozenset({"INICIADO", "ACTIVO", "EN_CICLO", "ESPERANDO"})


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


def construir_worker(configuracion, logger, *, queue_only: bool = False):
    """Construye el Worker oficial con Scheduler opcional y un unico motor."""
    proveedor = ProveedorConexionesSQLServer(configuracion)
    servicio_graph = ServicioConfiguracionGraph(proveedor, configuracion)
    notificador = ServicioDespachoNotificaciones(proveedor, servicio_graph)
    detener = Event()
    scheduler = None if queue_only else ServicioScheduler(proveedor, configuracion)
    worker = ServicioWorker(
        proveedor, scheduler, configuracion, logger, detener=detener,
    )
    motor = MotorEjecucionSubprocess(
        proveedor, configuracion, logger, evento_detencion=detener,
        timeout_segundos=configuracion.ejecucion_timeout_segundos,
        espera_terminacion_segundos=configuracion.ejecucion_gracia_terminacion_segundos,
        notificador=notificador,
    )
    worker.procesador_ejecuciones = ProcesadorColaEjecuciones(
        proveedor, configuracion, motor, worker.nombre_worker,
    )
    return worker, detener


def comprobar_salud_worker(
    configuracion,
    *,
    proveedor=None,
    host=None,
    reloj=datetime.now,
    fabrica_uow=UnidadTrabajoSQL,
    repositorio=RepositorioOperacion,
) -> tuple[bool, str]:
    """Comprueba la senal del Worker de este host sin crear ciclos ni reservas."""
    proveedor = proveedor or ProveedorConexionesSQLServer(configuracion)
    host = host or socket.gethostname()
    with fabrica_uow(proveedor) as uow:
        repo = repositorio(uow.obtener_conexion())
        scheduler = repo.obtener_configuracion_scheduler()
        heartbeat = repo.obtener_heartbeat_del_host(host)
    if heartbeat is None:
        return False, "No existe heartbeat del Worker reconstruido para este contenedor."
    if heartbeat.estado not in ESTADOS_WORKER_SALUDABLES:
        return False, f"El Worker reporta estado {heartbeat.estado}."
    if heartbeat.fecha_ultimo_heartbeat is None:
        return False, "El Worker no informa fecha de heartbeat."
    ahora = reloj()
    fecha = heartbeat.fecha_ultimo_heartbeat
    if getattr(ahora, "tzinfo", None) and not getattr(fecha, "tzinfo", None):
        ahora = ahora.replace(tzinfo=None)
    if getattr(fecha, "tzinfo", None) and not getattr(ahora, "tzinfo", None):
        fecha = fecha.replace(tzinfo=None)
    antiguedad = max(0, int((ahora - fecha).total_seconds()))
    intervalo = max(1, int(scheduler.intervalo_revision_segundos if scheduler else 60))
    if antiguedad > intervalo * 5:
        return False, "El heartbeat del Worker excede la ventana operativa."
    return True, "Heartbeat del Worker operativo."


def main() -> int:
    parser = argparse.ArgumentParser(description="Base tecnica del worker reconstruido.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Valida configuracion e inicializacion sin iniciar scheduler ni ejecuciones.",
    )
    parser.add_argument(
        "--once", action="store_true",
        help="Ejecuta un unico ciclo y espera el cierre de los trabajos reclamados.",
    )
    parser.add_argument(
        "--queue-only", action="store_true",
        help="Consume unicamente la cola y no evalua programaciones del Scheduler.",
    )
    parser.add_argument(
        "--healthcheck", action="store_true",
        help="Valida en SQL el heartbeat de este contenedor sin ejecutar ciclos.",
    )
    argumentos = parser.parse_args()
    configuracion = ConfiguracionAplicacion.desde_entorno()
    if argumentos.healthcheck:
        try:
            configuracion.validar("worker")
            saludable, _mensaje = comprobar_salud_worker(configuracion)
        except Exception:
            return 1
        return 0 if saludable else 1
    logger = preparar_worker(configuracion)
    if argumentos.check:
        logger.info("Worker base validado", extra={"evento": "WORKER_BASE_OK"})
        return 0
    worker, detener = construir_worker(
        configuracion, logger, queue_only=argumentos.queue_only,
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
