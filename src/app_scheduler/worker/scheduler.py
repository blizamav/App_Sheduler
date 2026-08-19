"""Evaluacion deterministica y despacho persistente del scheduler."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from app_scheduler.compartido.control_runtime import factory_reset_bloquea
from app_scheduler.compartido.unidad_trabajo import UnidadTrabajoSQL
from app_scheduler.modulos.programaciones.calculo import (
    calcular_ocurrencia_vencida,
    calcular_proxima_ejecucion,
)
from app_scheduler.persistencia.repositorio_scheduler import RepositorioScheduler
from app_scheduler.worker.contratos import OrigenEjecucion, SolicitudEjecucion


@dataclass(frozen=True, slots=True)
class ResultadoCiclo:
    resultado: str
    evaluadas: int = 0
    despachadas: int = 0
    omitidas: int = 0
    duplicadas: int = 0
    intervalo_segundos: int = 60


@dataclass(frozen=True, slots=True)
class ResultadoDespacho:
    estado: str
    id_ejecucion: int | None = None


class DespachadorPersistente:
    """Reserva trabajo para Hito 7 sin ejecutar el script de usuario."""

    def __init__(self, proveedor, *, fabrica_uow=UnidadTrabajoSQL,
                 repositorio=RepositorioScheduler):
        self.proveedor = proveedor
        self.fabrica_uow = fabrica_uow
        self.tipo_repositorio = repositorio

    def despachar(self, candidato, solicitud: SolicitudEjecucion,
                  *, limite_concurrencia: int | None = None) -> ResultadoDespacho:
        with self.fabrica_uow(self.proveedor) as uow:
            repositorio = self.tipo_repositorio(uow.obtener_conexion())
            if limite_concurrencia is not None:
                hay_capacidad = (
                    repositorio.adquirir_lock_despacho()
                    and repositorio.contar_ejecuciones_en_curso() < limite_concurrencia
                )
                if not hay_capacidad:
                    uow.confirmar()
                    return ResultadoDespacho("LIMITE_CONCURRENCIA")
            id_ejecucion = repositorio.reservar(solicitud)
            repositorio.actualizar_proxima(solicitud.id_tarea, solicitud.proxima_ejecucion)
            if id_ejecucion is not None:
                repositorio.registrar_evento(
                    candidato, worker=solicitud.nombre_worker, tipo="TAREA_EJECUTADA",
                    decision="EJECUTAR", motivo="PROGRAMACION_VENCIDA",
                    detalle="Solicitud automatica reservada para el motor de ejecucion.",
                    fecha_programada=solicitud.fecha_programada,
                    clave=solicitud.clave_programacion,
                )
            uow.confirmar()
        return ResultadoDespacho("DESPACHADA", id_ejecucion) if id_ejecucion is not None else ResultadoDespacho("DUPLICADA")

    def omitir(self, candidato, *, worker: str, motivo: str, detalle: str,
               fecha_programada: datetime | None, proxima_ejecucion: datetime | None) -> None:
        with self.fabrica_uow(self.proveedor) as uow:
            repositorio = self.tipo_repositorio(uow.obtener_conexion())
            repositorio.actualizar_proxima(candidato.programacion.id_tarea, proxima_ejecucion)
            repositorio.registrar_evento(
                candidato, worker=worker, tipo="TAREA_OMITIDA", decision="OMITIR",
                motivo=motivo, detalle=detalle, fecha_programada=fecha_programada,
            )
            uow.confirmar()


class ServicioScheduler:
    def __init__(self, proveedor, configuracion, *, despachador=None,
                 repositorio=RepositorioScheduler, control_runtime=factory_reset_bloquea):
        self.proveedor = proveedor
        self.configuracion = configuracion
        self.despachador = despachador or DespachadorPersistente(proveedor)
        self.tipo_repositorio = repositorio
        self.control_runtime = control_runtime

    def ejecutar_ciclo(self, ahora: datetime, nombre_worker: str) -> ResultadoCiclo:
        bloqueado, _estado = self.control_runtime(self.configuracion.ruta_control_runtime)
        if bloqueado:
            return ResultadoCiclo("BLOQUEADO_FACTORY_RESET")

        with self.proveedor.conexion_lectura() as conexion:
            repositorio = self.tipo_repositorio(conexion)
            configuracion = repositorio.obtener_configuracion()
            if configuracion is None:
                return ResultadoCiclo("SIN_CONFIGURACION")
            intervalo = configuracion.intervalo_revision_segundos
            if not configuracion.scheduler_activo:
                return ResultadoCiclo("SCHEDULER_INACTIVO", intervalo_segundos=intervalo)
            if configuracion.modo_mantenimiento:
                return ResultadoCiclo("MANTENIMIENTO", intervalo_segundos=intervalo)
            if not configuracion.permitir_ejecucion_automatica:
                return ResultadoCiclo("AUTOMATICAS_DESHABILITADAS", intervalo_segundos=intervalo)
            disponibles = max(
                0,
                configuracion.max_ejecuciones_concurrentes
                - repositorio.contar_ejecuciones_en_curso(),
            )
            candidatos = repositorio.listar_candidatos(ahora)

        if disponibles == 0:
            return ResultadoCiclo(
                "LIMITE_CONCURRENCIA", evaluadas=len(candidatos),
                omitidas=len(candidatos), intervalo_segundos=intervalo,
            )

        despachadas = omitidas = duplicadas = 0
        for candidato in candidatos:
            if despachadas >= disponibles:
                omitidas += 1
                continue
            resultado = self._evaluar(
                candidato, ahora, nombre_worker, intervalo,
                configuracion.max_ejecuciones_concurrentes,
            )
            if resultado == "DESPACHADA":
                despachadas += 1
            elif resultado == "DUPLICADA":
                duplicadas += 1
            elif resultado in {"OMITIDA", "LIMITE_CONCURRENCIA"}:
                omitidas += 1
        return ResultadoCiclo(
            "OK", len(candidatos), despachadas, omitidas, duplicadas, intervalo,
        )

    def _evaluar(self, candidato, ahora, nombre_worker, intervalo,
                 limite_concurrencia) -> str:
        programacion = candidato.programacion
        fecha_programada = candidato.proxima_ejecucion
        limite = ahora - timedelta(seconds=max(1, intervalo))
        if fecha_programada is None:
            fecha_programada = calcular_ocurrencia_vencida(programacion, ahora, intervalo)
            if fecha_programada is None:
                return "NO_VENCIDA"
        if fecha_programada < limite:
            self.despachador.omitir(
                candidato, worker=nombre_worker, motivo="FUERA_DE_VENTANA",
                detalle="La ocurrencia vencida queda fuera de la ventana de polling.",
                fecha_programada=fecha_programada,
                proxima_ejecucion=calcular_proxima_ejecucion(programacion, ahora),
            )
            return "OMITIDA"

        proxima = calcular_proxima_ejecucion(programacion, fecha_programada)
        if not self._version_valida(candidato):
            self.despachador.omitir(
                candidato, worker=nombre_worker, motivo="SCRIPT_SIN_VERSION_ACTIVA",
                detalle="La tarea no posee un script y una version activa validos.",
                fecha_programada=fecha_programada, proxima_ejecucion=proxima,
            )
            return "OMITIDA"

        if not programacion.ejecutar_en_feriados:
            with self.proveedor.conexion_lectura() as conexion:
                es_feriado = self.tipo_repositorio(conexion).es_feriado(fecha_programada.date())
            if es_feriado:
                self.despachador.omitir(
                    candidato, worker=nombre_worker, motivo="FERIADO",
                    detalle="La programacion no permite ejecucion en feriados locales.",
                    fecha_programada=fecha_programada, proxima_ejecucion=proxima,
                )
                return "OMITIDA"

        clave = f"PROGRAMACION_{programacion.id_programacion}_{fecha_programada:%Y%m%dT%H%M%S}"
        solicitud = SolicitudEjecucion(
            id_tarea=programacion.id_tarea,
            id_script=candidato.id_script,
            id_version=candidato.id_version,
            origen=OrigenEjecucion.AUTOMATICA,
            actor=nombre_worker,
            id_programacion=programacion.id_programacion,
            fecha_programada=fecha_programada,
            clave_programacion=clave,
            usuario_ejecucion=None,
            nombre_worker=nombre_worker,
            proxima_ejecucion=proxima,
        )
        return self.despachador.despachar(
            candidato, solicitud, limite_concurrencia=limite_concurrencia,
        ).estado

    @staticmethod
    def _version_valida(candidato) -> bool:
        return bool(
            candidato.id_script
            and candidato.id_version
            and candidato.script_activo
            and candidato.version_activa
            and candidato.estado_version == "ACTIVA"
        )
