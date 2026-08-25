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
        with self.proveedor.conexion_lectura() as conexion:
            repo = self.tipo_repositorio(conexion)
            configuracion = repo.obtener_configuracion_scheduler()
            heartbeat = repo.obtener_heartbeat()
            metricas = repo.metricas()
            integraciones = (
                self.tipo_integraciones(conexion).estado_integraciones()
                if self.tipo_integraciones is not None
                else {"feriados_activos": 0, "ultima_sync": None,
                      "graph_sql_activo": False, "ultimo_envio_estado": None,
                      "ultimo_envio_fecha": None}
            )
        integraciones["graph_env_habilitado"] = bool(
            self.configuracion_app and self.configuracion_app.graph_mail_enabled
        )
        return {
            "configuracion": configuracion,
            "heartbeat": heartbeat,
            "estado_worker": self._clasificar_worker(heartbeat, configuracion),
            "metricas": metricas,
            "integraciones": integraciones,
        }

    def _clasificar_worker(self, heartbeat, configuracion):
        if heartbeat is None:
            return {"codigo": "NO_REGISTRADO", "texto": "Sin heartbeat", "badge": "info",
                    "segundos": None}
        if heartbeat.estado == "ERROR":
            return {"codigo": "ERROR", "texto": "Error reportado", "badge": "error",
                    "segundos": _segundos(self.reloj(), heartbeat.fecha_ultimo_heartbeat)}
        if heartbeat.estado == "DETENIDO":
            return {"codigo": "DETENIDO", "texto": "Detenido", "badge": "inactivo",
                    "segundos": _segundos(self.reloj(), heartbeat.fecha_ultimo_heartbeat)}
        segundos = _segundos(self.reloj(), heartbeat.fecha_ultimo_heartbeat)
        intervalo = 60 if configuracion is None else configuracion.intervalo_revision_segundos
        if segundos is None or segundos > intervalo * 5:
            return {"codigo": "STALE", "texto": "Sin senal reciente", "badge": "error",
                    "segundos": segundos}
        if segundos > intervalo * 2:
            return {"codigo": "STALE", "texto": "Heartbeat atrasado", "badge": "advertencia",
                    "segundos": segundos}
        return {"codigo": "ACTIVO", "texto": "Activo", "badge": "activo", "segundos": segundos}


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


def _sanitizar_log(log):
    def limpiar(valor):
        if valor is None:
            return None
        return _PATRON_SECRETO.sub(lambda m: f"{m.group(1)}{m.group(2)}[PROTEGIDO]", str(valor))
    return replace(log, descripcion=limpiar(log.descripcion) or "",
                   valor_anterior=limpiar(log.valor_anterior),
                   valor_nuevo=limpiar(log.valor_nuevo),
                   user_agent=limpiar(log.user_agent))
