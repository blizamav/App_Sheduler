"""Consumo concurrente y acotado de ejecuciones PENDIENTES."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Lock

from app_scheduler.compartido.control_runtime import factory_reset_bloquea
from app_scheduler.compartido.unidad_trabajo import UnidadTrabajoSQL
from app_scheduler.persistencia.repositorio_ejecuciones import RepositorioEjecuciones


class ProcesadorColaEjecuciones:
    def __init__(self, proveedor, configuracion, motor, nombre_worker, *,
                 fabrica_uow=UnidadTrabajoSQL, repositorio=RepositorioEjecuciones,
                 control_runtime=factory_reset_bloquea):
        self.proveedor = proveedor
        self.configuracion = configuracion
        self.motor = motor
        self.nombre_worker = nombre_worker
        self.fabrica_uow = fabrica_uow
        self.tipo_repositorio = repositorio
        self.control_runtime = control_runtime
        self._executor = ThreadPoolExecutor(max_workers=20, thread_name_prefix="ejecucion")
        self._futuros = set()
        self._lock = Lock()
        self.intervalo_revision_segundos = 60

    def procesar_disponibles(self) -> int:
        self._depurar()
        bloqueado, _ = self.control_runtime(self.configuracion.ruta_control_runtime)
        if bloqueado:
            return 0
        with self.proveedor.conexion_lectura() as conexion:
            repo = self.tipo_repositorio(conexion)
            config = repo.obtener_configuracion()
            if config is None:
                return 0
            if len(config) > 2:
                self.intervalo_revision_segundos = max(1, int(config[2]))
            if bool(config[1]):
                return 0
            limite = int(config[0])
            en_ejecucion = repo.contar_en_ejecucion()
        disponibles = max(0, limite - en_ejecucion)
        reclamadas = 0
        for _ in range(disponibles):
            id_ejecucion = self._reclamar(limite)
            if id_ejecucion is None:
                break
            futuro = self._executor.submit(self.motor.ejecutar, id_ejecucion)
            with self._lock: self._futuros.add(futuro)
            reclamadas += 1
        return reclamadas

    def cerrar(self, *, esperar=True) -> None:
        self._executor.shutdown(wait=esperar, cancel_futures=False)

    def _reclamar(self, limite):
        with self.fabrica_uow(self.proveedor) as uow:
            identificador = self.tipo_repositorio(
                uow.obtener_conexion()
            ).reclamar_siguiente(self.nombre_worker, limite)
            uow.confirmar()
            return identificador

    def _depurar(self):
        with self._lock:
            self._futuros = {f for f in self._futuros if not f.done()}

    def _activas(self):
        with self._lock: return len(self._futuros)
