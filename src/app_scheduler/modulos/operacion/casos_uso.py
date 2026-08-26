"""Consultas seguras de logs, worker y scheduler."""

from __future__ import annotations

import re
from dataclasses import replace
from datetime import date, datetime

from app_scheduler.compartido.errores import ErrorValidacion
from app_scheduler.persistencia.modelos import Paginacion
from app_scheduler.persistencia.repositorio_operacion import (
    RepositorioLogsSistema,
    RepositorioOperacion,
)
from app_scheduler.persistencia.repositorio_notificaciones import RepositorioNotificaciones


NIVELES_LOG = frozenset({"INFO", "WARNING", "ERROR", "CRITICAL"})
INTERVALO_WORKER_DEFECTO_SEGUNDOS = 60
FACTOR_WORKER_ATENCION = 2
FACTOR_WORKER_DETENIDO = 5
ESTADOS_WORKER_VIVOS = frozenset({"INICIADO", "ACTIVO", "EN_CICLO", "ESPERANDO"})
_PATRON_SECRETO = re.compile(
    r"(?i)(password|contrasena|client_secret|secret|token|db_password|pwd)"
    r"([\"']?\s*[:=]\s*)([^\s;,}\]]+|\"[^\"]*\")"
)


class ServicioLogsSistema:
    def __init__(self, proveedor, *, repositorio=RepositorioLogsSistema):
        self.proveedor = proveedor
        self.tipo_repositorio = repositorio

    def listar(self, *, pagina=1, desde=None, hasta=None, nivel=None, modulo=None,
               evento=None, busqueda=None):
        filtros = self._validar_filtros(desde, hasta, nivel, modulo, evento, busqueda)
        with self.proveedor.conexion_lectura() as conexion:
            repo = self.tipo_repositorio(conexion)
            resultado = repo.listar(Paginacion(pagina, 25), **filtros)
            modulos, eventos = repo.opciones()
        return {
            "pagina": replace(resultado, elementos=tuple(_sanitizar_log(item) for item in resultado.elementos)),
            "modulos": modulos,
            "eventos": eventos,
            "filtros": {clave: valor or "" for clave, valor in {
                "desde": desde, "hasta": hasta, "nivel": nivel,
                "modulo": modulo, "evento": evento, "buscar": busqueda,
            }.items()},
            "niveles": tuple(sorted(NIVELES_LOG)),
        }

    def obtener(self, id_log: int):
        with self.proveedor.conexion_lectura() as conexion:
            log = self.tipo_repositorio(conexion).obtener(id_log)
        return None if log is None else _sanitizar_log(log)

    @staticmethod
    def _validar_filtros(desde, hasta, nivel, modulo, evento, busqueda):
        fecha_desde = _fecha(desde, "La fecha desde no es valida.")
        fecha_hasta = _fecha(hasta, "La fecha hasta no es valida.")
        if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
            raise ErrorValidacion("La fecha desde no puede ser posterior a la fecha hasta.")
        nivel = str(nivel or "").strip().upper() or None
        if nivel not in NIVELES_LOG | {None}:
            raise ErrorValidacion("El nivel de log no es valido.")
        textos = {}
        for clave, valor, limite in (
            ("modulo", modulo, 100), ("evento", evento, 100), ("busqueda", busqueda, 100),
        ):
            texto = str(valor or "").strip() or None
            if texto and len(texto) > limite:
                raise ErrorValidacion(f"El filtro {clave} admite hasta {limite} caracteres.")
            textos[clave] = texto
        return {"desde": fecha_desde, "hasta": fecha_hasta, "nivel": nivel, **textos}


class ServicioObservabilidad:
    def __init__(self, proveedor, configuracion=None, *, repositorio=RepositorioOperacion,
                 repositorio_integraciones=None, reloj=datetime.now):
        self.proveedor = proveedor
        self.tipo_repositorio = repositorio
        self.reloj = reloj
        self.configuracion_app = configuracion
        self.tipo_integraciones = repositorio_integraciones

    def obtener_estado(self):
        resumen = self.obtener_resumen_worker_seguro()
        integraciones = {
            "feriados_activos": 0, "ultima_sync": None,
            "graph_sql_activo": False, "ultimo_envio_estado": None,
            "ultimo_envio_fecha": None,
        }
        if self.tipo_integraciones is not None:
            try:
                with self.proveedor.conexion_lectura() as conexion:
                    integraciones = self.tipo_integraciones(conexion).estado_integraciones()
            except Exception:
                pass
        integraciones["graph_env_habilitado"] = bool(
            self.configuracion_app and self.configuracion_app.graph_mail_enabled
        )
        return {**resumen, "integraciones": integraciones}

    def obtener_resumen_worker(self):
        with self.proveedor.conexion_lectura() as conexion:
            repo = self.tipo_repositorio(conexion)
            configuracion = repo.obtener_configuracion_scheduler()
            heartbeat = repo.obtener_heartbeat()
            metricas = repo.metricas()
        estado = self._clasificar_worker(heartbeat, configuracion)
        pendientes = int(metricas.get("ejecuciones_pendientes", 0))
        estado["pendientes"] = pendientes
        estado["aria_label"] = self._aria_worker(estado)
        return {
            "configuracion": configuracion,
            "heartbeat": heartbeat,
            "estado_worker": estado,
            "metricas": metricas,
        }

    def obtener_resumen_worker_seguro(self):
        try:
            return self.obtener_resumen_worker()
        except Exception:
            return self.estado_desconocido()

    @staticmethod
    def estado_desconocido():
        estado = {
            "codigo": "DESCONOCIDO",
            "texto": "Estado Worker desconocido",
            "badge": "info",
            "segundos": None,
            "antiguedad": "Sin informacion suficiente",
            "detalle": "No fue posible determinar la disponibilidad del Worker.",
            "ultimo_heartbeat": None,
            "intervalo_segundos": INTERVALO_WORKER_DEFECTO_SEGUNDOS,
            "umbral_atencion_segundos": INTERVALO_WORKER_DEFECTO_SEGUNDOS * FACTOR_WORKER_ATENCION,
            "umbral_detenido_segundos": INTERVALO_WORKER_DEFECTO_SEGUNDOS * FACTOR_WORKER_DETENIDO,
            "polling_segundos": INTERVALO_WORKER_DEFECTO_SEGUNDOS // 2,
            "pendientes": 0,
        }
        estado["aria_label"] = ServicioObservabilidad._aria_worker(estado)
        return {
            "configuracion": None,
            "heartbeat": None,
            "estado_worker": estado,
            "metricas": {
                "ejecuciones_en_curso": 0,
                "ejecuciones_pendientes": 0,
                "errores_24h": 0,
                "ultima_ejecucion_automatica": None,
                "tareas_candidatas": 0,
            },
        }

    def _clasificar_worker(self, heartbeat, configuracion):
        intervalo = (
            INTERVALO_WORKER_DEFECTO_SEGUNDOS
            if configuracion is None
            else max(1, int(configuracion.intervalo_revision_segundos))
        )
        umbral_atencion = intervalo * FACTOR_WORKER_ATENCION
        umbral_detenido = intervalo * FACTOR_WORKER_DETENIDO
        if heartbeat is None:
            return self._estado_worker(
                "DESCONOCIDO", "Estado Worker desconocido", "info", None,
                "Sin heartbeat registrado",
                "No existe una senal de vida suficiente para determinar disponibilidad.",
                None, intervalo, umbral_atencion, umbral_detenido,
            )
        segundos = _segundos(self.reloj(), heartbeat.fecha_ultimo_heartbeat)
        antiguedad = _texto_antiguedad(segundos)
        comunes = (
            heartbeat.fecha_ultimo_heartbeat.isoformat()
            if heartbeat.fecha_ultimo_heartbeat else None,
            intervalo, umbral_atencion, umbral_detenido,
        )
        if segundos is None:
            return self._estado_worker(
                "DESCONOCIDO", "Estado Worker desconocido", "info", segundos,
                antiguedad, "El heartbeat no contiene una fecha valida.", *comunes,
            )
        if heartbeat.estado == "DETENIDO" or segundos > umbral_detenido:
            detalle = (
                "El Worker informo su detencion."
                if heartbeat.estado == "DETENIDO"
                else "El heartbeat expiro y no existe un consumidor disponible confirmado."
            )
            return self._estado_worker(
                "DETENIDO", "Worker detenido", "error", segundos,
                antiguedad, detalle, *comunes,
            )
        if heartbeat.estado == "ERROR" or segundos > umbral_atencion:
            detalle = (
                "El Worker reporto un error reciente."
                if heartbeat.estado == "ERROR"
                else "El heartbeat esta retrasado y requiere atencion."
            )
            return self._estado_worker(
                "ATENCION", "Worker con retraso", "advertencia", segundos,
                antiguedad, detalle, *comunes,
            )
        if heartbeat.estado not in ESTADOS_WORKER_VIVOS:
            return self._estado_worker(
                "DESCONOCIDO", "Estado Worker desconocido", "info", segundos,
                antiguedad, "El Worker reporto un estado no reconocido.", *comunes,
            )
        return self._estado_worker(
            "OPERATIVO", "Worker operativo", "activo", segundos,
            antiguedad, "El heartbeat se encuentra dentro de la ventana saludable.",
            *comunes,
        )

    @staticmethod
    def _estado_worker(codigo, texto, badge, segundos, antiguedad, detalle,
                       ultimo_heartbeat, intervalo, umbral_atencion, umbral_detenido):
        return {
            "codigo": codigo,
            "texto": texto,
            "badge": badge,
            "segundos": segundos,
            "antiguedad": antiguedad,
            "detalle": detalle,
            "ultimo_heartbeat": ultimo_heartbeat,
            "intervalo_segundos": intervalo,
            "umbral_atencion_segundos": umbral_atencion,
            "umbral_detenido_segundos": umbral_detenido,
            "polling_segundos": max(10, min(60, intervalo // 2)),
        }

    @staticmethod
    def _aria_worker(estado):
        pendientes = int(estado.get("pendientes", 0))
        cola = ""
        if pendientes:
            cola = (
                " 1 ejecucion pendiente."
                if pendientes == 1
                else f" {pendientes} ejecuciones pendientes."
            )
        return f"{estado['texto']}. {estado['antiguedad']}.{cola}".strip()


def _fecha(valor, mensaje):
    if not str(valor or "").strip():
        return None
    try:
        return date.fromisoformat(str(valor))
    except ValueError as error:
        raise ErrorValidacion(mensaje) from error


def _segundos(ahora, fecha):
    if fecha is None:
        return None
    if getattr(ahora, "tzinfo", None) and not getattr(fecha, "tzinfo", None):
        ahora = ahora.replace(tzinfo=None)
    if getattr(fecha, "tzinfo", None) and not getattr(ahora, "tzinfo", None):
        fecha = fecha.replace(tzinfo=None)
    return max(0, int((ahora - fecha).total_seconds()))


def _texto_antiguedad(segundos):
    if segundos is None:
        return "Sin informacion suficiente"
    if segundos < 60:
        return f"Hace {segundos} s"
    if segundos < 3600:
        minutos, resto = divmod(segundos, 60)
        return f"Hace {minutos} min {resto} s" if resto else f"Hace {minutos} min"
    horas, resto = divmod(segundos, 3600)
    minutos = resto // 60
    return f"Hace {horas} h {minutos} min" if minutos else f"Hace {horas} h"


def _sanitizar_log(log):
    def limpiar(valor):
        if valor is None:
            return None
        return _PATRON_SECRETO.sub(lambda m: f"{m.group(1)}{m.group(2)}[PROTEGIDO]", str(valor))
    return replace(log, descripcion=limpiar(log.descripcion) or "",
                   valor_anterior=limpiar(log.valor_anterior),
                   valor_nuevo=limpiar(log.valor_nuevo),
                   user_agent=limpiar(log.user_agent))
