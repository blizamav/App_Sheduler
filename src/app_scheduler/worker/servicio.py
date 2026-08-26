"""Loop controlado del worker scheduler reconstruido."""

from __future__ import annotations

import os
import socket
import time
from dataclasses import dataclass
from datetime import datetime
from threading import Event

from app_scheduler.compartido.unidad_trabajo import UnidadTrabajoSQL
from app_scheduler.persistencia.repositorio_scheduler import RepositorioHeartbeat


@dataclass(frozen=True, slots=True)
class ResultadoCicloCola:
    """Resultado compatible con heartbeat para un ciclo sin Scheduler."""

    resultado: str = "QUEUE_ONLY"
    evaluadas: int = 0
    despachadas: int = 0
    omitidas: int = 0
    duplicadas: int = 0
    intervalo_segundos: int = 60


class ServicioWorker:
    def __init__(self, proveedor, scheduler, configuracion, logger, *,
                 nombre_worker=None, detener=None,
                 fabrica_uow=UnidadTrabajoSQL, repositorio=RepositorioHeartbeat,
                 reloj=datetime.now, procesador_ejecuciones=None):
        self.proveedor = proveedor
        self.scheduler = scheduler
        self.configuracion = configuracion
        self.logger = logger
        self.nombre_worker = nombre_worker or (
            f"scheduler_worker_reconstruido:{socket.gethostname()}:{os.getpid()}"
        )[:100]
        self.detener = detener or Event()
        self.fabrica_uow = fabrica_uow
        self.tipo_repositorio = repositorio
        self.reloj = reloj
        self.procesador_ejecuciones = procesador_ejecuciones

    def ejecutar_una_vez(self):
        self._heartbeat("estado", "EN_CICLO")
        try:
            resultado = (
                self.scheduler.ejecutar_ciclo(self.reloj(), self.nombre_worker)
                if self.scheduler is not None else None
            )
            reclamadas = 0
            if self.procesador_ejecuciones is not None:
                reclamadas = self.procesador_ejecuciones.procesar_disponibles()
            if resultado is None:
                intervalo = (
                    self.procesador_ejecuciones.intervalo_revision_segundos
                    if self.procesador_ejecuciones is not None else 60
                )
                resultado = ResultadoCicloCola(
                    despachadas=reclamadas,
                    intervalo_segundos=intervalo,
                )
        except Exception as error:
            self._heartbeat("error", f"{error.__class__.__name__}: ciclo no completado")
            evento = "WORKER_CICLO_ERROR" if self.scheduler is None else "SCHEDULER_ERROR"
            self.logger.exception(
                "Error recuperable en ciclo del Worker"
                if self.scheduler is None else "Error recuperable en ciclo scheduler",
                extra={"evento": evento},
            )
            return None
        self._heartbeat("fin_ciclo", resultado)
        return resultado

    def ejecutar(self) -> None:
        self._heartbeat(
            "iniciar", os.getpid(), socket.gethostname(), self.configuracion.app_version,
        )
        mensaje_inicio = (
            "Worker iniciado en modo QUEUE_ONLY"
            if self.scheduler is None else "Worker scheduler iniciado"
        )
        self.logger.info(mensaje_inicio, extra={"evento": "WORKER_INICIADO"})
        intervalo = 60
        while not self.detener.is_set():
            resultado = self.ejecutar_una_vez()
            if resultado is not None:
                intervalo = resultado.intervalo_segundos
            limite_espera = time.monotonic() + max(1, intervalo)
            while not self.detener.is_set() and time.monotonic() < limite_espera:
                if self.detener.wait(min(1.0, max(0.05, limite_espera - time.monotonic()))):
                    break
                if self.procesador_ejecuciones is not None:
                    self.procesador_ejecuciones.procesar_disponibles()
        self._heartbeat("estado", "DETENIDO")
        if self.procesador_ejecuciones is not None:
            self.procesador_ejecuciones.cerrar(esperar=True)
        mensaje_fin = (
            "Worker QUEUE_ONLY detenido"
            if self.scheduler is None else "Worker scheduler detenido"
        )
        self.logger.info(mensaje_fin, extra={"evento": "WORKER_DETENIDO"})

    def ejecutar_solo_un_ciclo(self):
        self._heartbeat(
            "iniciar", os.getpid(), socket.gethostname(), self.configuracion.app_version,
        )
        mensaje_inicio = (
            "Worker iniciado en modo QUEUE_ONLY"
            if self.scheduler is None else "Worker scheduler iniciado"
        )
        self.logger.info(mensaje_inicio, extra={"evento": "WORKER_INICIADO"})
        try:
            return self.ejecutar_una_vez()
        finally:
            if self.procesador_ejecuciones is not None:
                self.procesador_ejecuciones.cerrar(esperar=True)
            self._heartbeat("estado", "DETENIDO")
            mensaje_fin = (
                "Worker QUEUE_ONLY detenido"
                if self.scheduler is None else "Worker scheduler detenido"
            )
            self.logger.info(mensaje_fin, extra={"evento": "WORKER_DETENIDO"})

    def _heartbeat(self, metodo, *argumentos) -> None:
        with self.fabrica_uow(self.proveedor) as uow:
            getattr(self.tipo_repositorio(uow.obtener_conexion()), metodo)(
                self.nombre_worker, *argumentos
            )
            uow.confirmar()
