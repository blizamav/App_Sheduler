"""Persistencia del scheduler, calendario, heartbeat y cola de ejecuciones."""

from __future__ import annotations

from app_scheduler.compartido.errores import ErrorPersistencia
from app_scheduler.persistencia.mapeadores import mapear_programacion
from app_scheduler.persistencia.modelos import CandidatoProgramacion, ConfiguracionScheduler
from app_scheduler.persistencia.repositorio import RepositorioSQL


class RepositorioScheduler(RepositorioSQL):
    _PROGRAMA = """p.id_programacion, p.id_tarea, t.nombre_tarea, t.estado_tarea,
    p.tipo_programacion, p.modo_ejecucion_dia, p.hora_inicio, p.hora_termino,
    p.hora_ejecucion, p.intervalo_minutos, p.dias_semana, p.dia_mes,
    p.fecha_especifica, p.fechas_especificas, p.ejecutar_en_feriados,
    p.zona_horaria, p.fecha_inicio_vigencia, p.fecha_fin_vigencia,
    p.fecha_creacion, p.fecha_actualizacion, p.activo"""

    def obtener_configuracion(self) -> ConfiguracionScheduler | None:
        fila = self.ejecutar_uno(
            """SELECT TOP 1 scheduler_activo, intervalo_revision_segundos,
max_ejecuciones_concurrentes, permitir_ejecucion_automatica, modo_mantenimiento,
nombre_worker_principal FROM dbo.configuracion_scheduler WHERE activo = 1
ORDER BY id_configuracion""", operacion="obtener_configuracion_scheduler",
        )
        return None if fila is None else ConfiguracionScheduler(
            bool(fila[0]), int(fila[1]), int(fila[2]), bool(fila[3]), bool(fila[4]), fila[5]
        )

    def listar_candidatos(self, ahora) -> tuple[CandidatoProgramacion, ...]:
        filas = self.ejecutar_lista(
            f"""SELECT {self._PROGRAMA}, s.id_script, v.id_version, v.estado_version,
ISNULL(s.activo, 0), ISNULL(v.es_activa, 0), t.proxima_ejecucion
FROM dbo.programaciones p
JOIN dbo.tareas t ON t.id_tarea = p.id_tarea
LEFT JOIN dbo.scripts s ON s.id_tarea = t.id_tarea AND s.eliminado_operativo = 0
LEFT JOIN dbo.scripts_versiones v ON v.id_version = s.id_version_activa AND v.eliminado_operativo = 0
WHERE p.activo = 1 AND p.tipo_programacion <> 'MANUAL'
  AND t.activo = 1 AND t.estado_tarea = 'ACTIVA' AND t.tipo_tarea = 'PROGRAMADA'
  AND t.eliminado_operativo = 0
  AND (t.proxima_ejecucion IS NULL OR t.proxima_ejecucion <= ?)
ORDER BY t.proxima_ejecucion, p.id_programacion""",
            (ahora,), operacion="listar_candidatos_scheduler",
        )
        resultado = []
        for fila in filas:
            programa = mapear_programacion(fila[:21])
            resultado.append(CandidatoProgramacion(programa, fila[21], fila[22], fila[23],
                                                   bool(fila[24]), bool(fila[25]), fila[26]))
        return tuple(resultado)

    def contar_ejecuciones_en_curso(self) -> int:
        return int(self.ejecutar_escalar(
            """SELECT COUNT(1) FROM dbo.ejecuciones
WHERE estado_ejecucion IN ('PENDIENTE', 'EN_EJECUCION')""",
            operacion="contar_ejecuciones_en_curso",
        ) or 0)

    def adquirir_lock_despacho(self) -> bool:
        resultado = self.ejecutar_escalar(
            """DECLARE @resultado int;
EXEC @resultado = sys.sp_getapplock
    @Resource = 'APP_SCHEDULER_SCHEDULER_DESPACHO',
    @LockMode = 'Exclusive', @LockOwner = 'Transaction', @LockTimeout = 0;
SELECT @resultado;""",
            operacion="adquirir_lock_despacho_scheduler",
        )
        return resultado is not None and int(resultado) >= 0

    def reservar(self, solicitud) -> int | None:
        cursor = None
        try:
            cursor = self.conexion.cursor()
            cursor.execute(
                """INSERT INTO dbo.ejecuciones
    (id_tarea, id_script, id_version, origen_ejecucion, estado_ejecucion,
     fecha_hora_inicio, usuario_ejecucion, fecha_programada, clave_programacion, nombre_worker)
OUTPUT INSERTED.id_ejecucion
VALUES (?, ?, ?, 'AUTOMATICA', 'PENDIENTE', SYSDATETIME(), NULL, ?, ?, ?)""",
                (solicitud.id_tarea, solicitud.id_script, solicitud.id_version,
                 solicitud.fecha_programada, solicitud.clave_programacion,
                 solicitud.nombre_worker),
            )
            fila = cursor.fetchone()
            return int(fila[0])
        except Exception as error:
            if _es_duplicado(error):
                return None
            raise ErrorPersistencia(
                detalle_tecnico=f"Fallo de persistencia en reservar_ejecucion: {error.__class__.__name__}."
            ) from error
        finally:
            if cursor is not None: cursor.close()

    def actualizar_proxima(self, id_tarea: int, proxima) -> None:
        self.ejecutar(
            """UPDATE dbo.tareas SET proxima_ejecucion = ?, fecha_actualizacion = SYSDATETIME()
WHERE id_tarea = ? AND eliminado_operativo = 0""",
            (proxima, id_tarea), operacion="avanzar_proxima_ejecucion",
        )

    def es_feriado(self, fecha, pais="CL") -> bool:
        return bool(self.ejecutar_escalar(
            "SELECT COUNT(1) FROM dbo.feriados WHERE fecha = ? AND pais = ? AND activo = 1",
            (fecha, pais), operacion="consultar_feriado_local",
        ))

    def registrar_evento(self, candidato, *, worker, tipo, decision, motivo, detalle,
                         fecha_programada=None, clave=None) -> None:
        self.ejecutar(
            """INSERT INTO dbo.scheduler_eventos
    (nombre_worker, id_tarea, nombre_tarea, id_programacion, fecha_programada,
     clave_programacion, tipo_evento, decision, motivo, detalle, origen, activo)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'SCHEDULER', 1)""",
            (worker, candidato.programacion.id_tarea, candidato.programacion.nombre_tarea,
             candidato.programacion.id_programacion, fecha_programada, clave,
             tipo, decision, motivo, detalle), operacion="registrar_evento_scheduler",
        )


class RepositorioHeartbeat(RepositorioSQL):
    def iniciar(self, nombre, pid, host, version):
        actualizadas = self.ejecutar(
            """UPDATE dbo.scheduler_worker_heartbeat SET estado='INICIADO',
fecha_inicio=SYSDATETIME(), fecha_ultimo_heartbeat=SYSDATETIME(), pid_proceso=?, host=?,
version_app=?, ultimo_error=NULL, fecha_actualizacion=SYSDATETIME()
WHERE nombre_worker=? AND activo=1""", (pid, host, version, nombre), operacion="iniciar_heartbeat")
        if not actualizadas:
            self.ejecutar(
                """INSERT INTO dbo.scheduler_worker_heartbeat
(nombre_worker, estado, fecha_inicio, fecha_ultimo_heartbeat, pid_proceso, host, version_app, activo)
VALUES (?, 'INICIADO', SYSDATETIME(), SYSDATETIME(), ?, ?, ?, 1)""",
                (nombre, pid, host, version), operacion="crear_heartbeat")

    def estado(self, nombre, estado):
        self.ejecutar("""UPDATE dbo.scheduler_worker_heartbeat SET estado=?,
fecha_ultimo_heartbeat=SYSDATETIME(), fecha_actualizacion=SYSDATETIME()
WHERE nombre_worker=? AND activo=1""", (estado, nombre), operacion="actualizar_heartbeat")

    def fin_ciclo(self, nombre, resultado):
        self.ejecutar("""UPDATE dbo.scheduler_worker_heartbeat SET estado='ESPERANDO',
fecha_ultimo_heartbeat=SYSDATETIME(), fecha_ultimo_ciclo=SYSDATETIME(),
resultado_ultimo_ciclo=?, ultimo_error=NULL, ciclos_ejecutados=ciclos_ejecutados+1,
tareas_evaluadas_ultimo_ciclo=?, tareas_ejecutadas_ultimo_ciclo=?,
tareas_omitidas_ultimo_ciclo=?, fecha_actualizacion=SYSDATETIME()
WHERE nombre_worker=? AND activo=1""",
            (resultado.resultado, resultado.evaluadas, resultado.despachadas,
             resultado.omitidas, nombre), operacion="cerrar_ciclo_heartbeat")

    def error(self, nombre, mensaje):
        self.ejecutar("""UPDATE dbo.scheduler_worker_heartbeat SET estado='ERROR',
fecha_ultimo_heartbeat=SYSDATETIME(), fecha_ultimo_ciclo=SYSDATETIME(),
resultado_ultimo_ciclo='ERROR', ultimo_error=?, fecha_actualizacion=SYSDATETIME()
WHERE nombre_worker=? AND activo=1""", (str(mensaje)[:2000], nombre), operacion="error_heartbeat")


def _es_duplicado(error) -> bool:
    texto = " ".join(str(item) for item in getattr(error, "args", ())).upper()
    return any(codigo in texto for codigo in ("23000", "2601", "2627"))
