"""Lecturas operativas y configuracion acotada del Hito 8."""

from __future__ import annotations

from app_scheduler.persistencia.mapeadores import (
    mapear_configuracion_scheduler,
    mapear_configuracion_sistema,
    mapear_heartbeat,
    mapear_log_sistema,
)
from app_scheduler.persistencia.modelos import Pagina, Paginacion
from app_scheduler.persistencia.repositorio import RepositorioSQL


class RepositorioLogsSistema(RepositorioSQL):
    _COLUMNAS = """id, usuario, accion, modulo, descripcion, valor_anterior,
valor_nuevo, ip, user_agent, fecha_hora, nivel"""

    def listar(self, paginacion: Paginacion, *, desde=None, hasta=None, nivel=None,
               modulo=None, evento=None, busqueda=None) -> Pagina:
        filtros = ["1 = 1"]
        parametros: list[object] = []
        if desde is not None:
            filtros.append("fecha_hora >= ?")
            parametros.append(desde)
        if hasta is not None:
            filtros.append("fecha_hora < DATEADD(day, 1, ?)")
            parametros.append(hasta)
        if nivel:
            filtros.append("nivel = ?")
            parametros.append(nivel)
        if modulo:
            filtros.append("modulo = ?")
            parametros.append(modulo)
        if evento:
            filtros.append("accion = ?")
            parametros.append(evento)
        if busqueda:
            patron = f"%{self._escapar_like(busqueda)}%"
            filtros.append("(descripcion LIKE ? ESCAPE '~' OR accion LIKE ? ESCAPE '~' OR usuario LIKE ? ESCAPE '~')")
            parametros.extend((patron, patron, patron))
        donde = " AND ".join(filtros)
        total = int(self.ejecutar_escalar(
            f"SELECT COUNT(1) FROM dbo.logs_sistema WHERE {donde}", tuple(parametros),
            operacion="contar_logs_sistema",
        ) or 0)
        filas = self.ejecutar_lista(
            f"""SELECT {self._COLUMNAS} FROM dbo.logs_sistema
WHERE {donde}
ORDER BY fecha_hora DESC, id DESC
OFFSET ? ROWS FETCH NEXT ? ROWS ONLY""",
            tuple(parametros) + (paginacion.desplazamiento, paginacion.por_pagina),
            operacion="listar_logs_sistema",
        )
        return Pagina(tuple(mapear_log_sistema(fila) for fila in filas), total,
                      paginacion.pagina, paginacion.por_pagina)

    def obtener(self, id_log: int):
        fila = self.ejecutar_uno(
            f"SELECT {self._COLUMNAS} FROM dbo.logs_sistema WHERE id = ?",
            (id_log,), operacion="obtener_log_sistema",
        )
        return None if fila is None else mapear_log_sistema(fila)

    def opciones(self):
        modulos = self.ejecutar_lista(
            "SELECT DISTINCT TOP (100) modulo FROM dbo.logs_sistema WHERE modulo IS NOT NULL ORDER BY modulo",
            operacion="listar_modulos_log",
        )
        eventos = self.ejecutar_lista(
            "SELECT DISTINCT TOP (100) accion FROM dbo.logs_sistema WHERE accion IS NOT NULL ORDER BY accion",
            operacion="listar_eventos_log",
        )
        return tuple(f[0] for f in modulos), tuple(f[0] for f in eventos)

    def registrar(self, *, accion: str, modulo: str, descripcion: str,
                  nivel: str = "INFO", usuario: str | None = None,
                  valor_anterior: str | None = None, valor_nuevo: str | None = None,
                  ip: str | None = None, user_agent: str | None = None) -> int:
        fila = self.ejecutar_uno(
            """INSERT INTO dbo.logs_sistema
(usuario, accion, modulo, descripcion, valor_anterior, valor_nuevo, ip, user_agent, nivel)
OUTPUT INSERTED.id
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (usuario, accion, modulo, descripcion, valor_anterior, valor_nuevo,
             ip, user_agent, nivel), operacion="registrar_log_sistema",
        )
        return int(fila[0])

    @staticmethod
    def _escapar_like(valor: str) -> str:
        return valor.replace("~", "~~").replace("%", "~%").replace("_", "~_")


class RepositorioOperacion(RepositorioSQL):
    _CONFIG_SCHEDULER = """id_configuracion, scheduler_activo,
intervalo_revision_segundos, max_ejecuciones_concurrentes,
permitir_ejecucion_automatica, modo_mantenimiento, nombre_worker_principal,
descripcion, fecha_actualizacion, usuario_actualizacion"""

    def obtener_configuracion_scheduler(self):
        fila = self.ejecutar_uno(
            f"""SELECT TOP 1 {self._CONFIG_SCHEDULER}
FROM dbo.configuracion_scheduler WHERE activo = 1 ORDER BY id_configuracion""",
            operacion="obtener_configuracion_operativa_scheduler",
        )
        return None if fila is None else mapear_configuracion_scheduler(fila)

    def obtener_heartbeat(self, nombre_worker=None):
        parametros = ()
        filtro = ""
        if nombre_worker:
            filtro = "AND nombre_worker = ?"
            parametros = (nombre_worker,)
        fila = self.ejecutar_uno(
            f"""SELECT TOP 1 id_worker, nombre_worker, estado, fecha_inicio,
fecha_ultimo_heartbeat, fecha_ultimo_ciclo, resultado_ultimo_ciclo, ultimo_error,
ciclos_ejecutados, tareas_evaluadas_ultimo_ciclo, tareas_ejecutadas_ultimo_ciclo,
tareas_omitidas_ultimo_ciclo, pid_proceso, host, version_app
FROM dbo.scheduler_worker_heartbeat WHERE activo = 1 {filtro}
ORDER BY fecha_ultimo_heartbeat DESC, id_worker DESC""",
            parametros, operacion="obtener_heartbeat_operativo",
        )
        return None if fila is None else mapear_heartbeat(fila)

    def metricas(self):
        fila = self.ejecutar_uno(
            """SELECT
(SELECT COUNT(1) FROM dbo.ejecuciones WHERE estado_ejecucion IN ('PENDIENTE','EN_EJECUCION')),
(SELECT COUNT(1) FROM dbo.logs_sistema WHERE nivel IN ('ERROR','CRITICAL')
 AND fecha_hora >= DATEADD(hour, -24, SYSDATETIME())),
(SELECT MAX(fecha_hora_inicio) FROM dbo.ejecuciones WHERE origen_ejecucion = 'AUTOMATICA'),
(SELECT COUNT(1) FROM dbo.tareas WHERE eliminado_operativo = 0 AND activo = 1
 AND estado_tarea = 'ACTIVA' AND tipo_tarea = 'PROGRAMADA'
 AND proxima_ejecucion IS NOT NULL AND proxima_ejecucion <= SYSDATETIME())""",
            operacion="obtener_metricas_operativas",
        )
        return {
            "ejecuciones_en_curso": int(fila[0] or 0),
            "errores_24h": int(fila[1] or 0),
            "ultima_ejecucion_automatica": fila[2],
            "tareas_candidatas": int(fila[3] or 0),
        }

    def listar_configuracion_sistema(self):
        filas = self.ejecutar_lista(
            """SELECT id_configuracion, clave, valor, tipo_dato, descripcion,
es_sensible, fecha_actualizacion, usuario_actualizacion, activo
FROM dbo.configuracion_sistema ORDER BY clave""",
            operacion="listar_configuracion_sistema",
        )
        return tuple(mapear_configuracion_sistema(fila) for fila in filas)

    def actualizar_scheduler(self, id_configuracion: int, datos, actor: str) -> bool:
        return self.ejecutar(
            """UPDATE dbo.configuracion_scheduler
SET scheduler_activo = ?, intervalo_revision_segundos = ?,
    max_ejecuciones_concurrentes = ?, permitir_ejecucion_automatica = ?,
    modo_mantenimiento = ?, fecha_actualizacion = SYSDATETIME(),
    usuario_actualizacion = ?
WHERE id_configuracion = ? AND activo = 1""",
            (int(datos["scheduler_activo"]), datos["intervalo_revision_segundos"],
             datos["max_ejecuciones_concurrentes"],
             int(datos["permitir_ejecucion_automatica"]),
             int(datos["modo_mantenimiento"]), actor, id_configuracion),
            operacion="actualizar_configuracion_scheduler",
        ) == 1
