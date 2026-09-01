"""Persistencia para configuracion, destinatarios y trazabilidad de correos."""

from __future__ import annotations

from app_scheduler.persistencia.modelos import (
    ConfiguracionMailGraph,
    ConfiguracionNotificacionTarea,
    DestinatarioNotificacion,
)
from app_scheduler.persistencia.repositorio import RepositorioSQL


class RepositorioNotificaciones(RepositorioSQL):
    def obtener_configuracion_tarea(self, id_tarea: int) -> ConfiguracionNotificacionTarea:
        fila = self.ejecutar_uno(
            """SELECT TOP 1 id_config_notificacion, id_tarea, enviar_evidencia,
notificar_exito_activa,
plantilla_evidencia, asunto_personalizado, usar_asunto_sugerido_script,
adjuntar_archivos_declarados, adjuntar_log_tecnico, alerta_error_activa,
usar_alerta_global
FROM dbo.notificaciones_config_tarea
WHERE id_tarea = ? AND activo = 1 ORDER BY id_config_notificacion""",
            (id_tarea,), operacion="obtener_configuracion_notificaciones_tarea",
        )
        if fila is None:
            return ConfiguracionNotificacionTarea(
                id_config_notificacion=None, id_tarea=id_tarea,
                enviar_evidencia=False, notificar_exito_activa=False,
                plantilla_evidencia="STDOUT_V1", asunto_personalizado=None,
                usar_asunto_sugerido_script=True, adjuntar_archivos_declarados=True,
                adjuntar_log_tecnico=False, alerta_error_activa=True,
                usar_alerta_global=True, destinatarios=(),
            )
        destinatarios = self.listar_destinatarios(int(fila[0]))
        return ConfiguracionNotificacionTarea(
            int(fila[0]), int(fila[1]), bool(fila[2]), bool(fila[3]),
            str(fila[4] or "STDOUT_V1"), fila[5], bool(fila[6]), bool(fila[7]),
            bool(fila[8]), bool(fila[9]), bool(fila[10]), destinatarios,
        )

    def listar_destinatarios(self, id_configuracion: int):
        filas = self.ejecutar_lista(
            """SELECT id_destinatario, tipo_destinatario, canal, email, nombre
FROM dbo.notificaciones_destinatarios
WHERE id_config_notificacion = ? AND activo = 1
ORDER BY tipo_destinatario, canal, email""",
            (id_configuracion,), operacion="listar_destinatarios_notificacion",
        )
        return tuple(DestinatarioNotificacion(
            int(f[0]), str(f[1]), str(f[2]), str(f[3]), f[4]
        ) for f in filas)

    def guardar_configuracion_tarea(self, config: ConfiguracionNotificacionTarea) -> int:
        parametros = (
            int(config.enviar_evidencia), int(config.notificar_exito_activa),
            config.asunto_personalizado,
            int(config.usar_asunto_sugerido_script),
            int(config.adjuntar_archivos_declarados), int(config.adjuntar_log_tecnico),
            int(config.alerta_error_activa), int(config.usar_alerta_global),
        )
        if config.id_config_notificacion is None:
            fila = self.ejecutar_uno(
                """INSERT INTO dbo.notificaciones_config_tarea
(id_tarea, enviar_evidencia, notificar_exito_activa, plantilla_evidencia, asunto_personalizado,
 usar_asunto_sugerido_script, adjuntar_archivos_declarados, adjuntar_log_tecnico,
 alerta_error_activa, usar_alerta_global, activo)
OUTPUT INSERTED.id_config_notificacion
VALUES (?, ?, ?, 'STDOUT_V1', ?, ?, ?, ?, ?, ?, 1)""",
                (config.id_tarea, *parametros), operacion="crear_configuracion_notificacion",
            )
            return int(fila[0])
        if self.ejecutar(
            """UPDATE dbo.notificaciones_config_tarea
SET enviar_evidencia = ?, notificar_exito_activa = ?, plantilla_evidencia = 'STDOUT_V1',
    asunto_personalizado = ?, usar_asunto_sugerido_script = ?,
    adjuntar_archivos_declarados = ?, adjuntar_log_tecnico = ?,
    alerta_error_activa = ?, usar_alerta_global = ?, actualizado_en = SYSDATETIME()
WHERE id_config_notificacion = ? AND id_tarea = ? AND activo = 1""",
            (*parametros, config.id_config_notificacion, config.id_tarea),
            operacion="actualizar_configuracion_notificacion",
        ) != 1:
            raise ValueError("Configuracion de notificacion no disponible.")
        return config.id_config_notificacion

    def reemplazar_destinatarios(self, id_configuracion: int, destinatarios) -> None:
        self.ejecutar(
            """UPDATE dbo.notificaciones_destinatarios SET activo = 0
WHERE id_config_notificacion = ? AND activo = 1""",
            (id_configuracion,), operacion="desactivar_destinatarios_notificacion",
        )
        for item in destinatarios:
            actualizado = self.ejecutar(
                """UPDATE TOP (1) dbo.notificaciones_destinatarios
SET activo = 1, nombre = ?
WHERE id_config_notificacion = ? AND tipo_destinatario = ? AND canal = ?
  AND email = ? AND activo = 0""",
                (item.nombre, id_configuracion, item.tipo_destinatario,
                 item.canal, item.email), operacion="reactivar_destinatario_notificacion",
            )
            if not actualizado:
                self.ejecutar(
                    """INSERT INTO dbo.notificaciones_destinatarios
(id_config_notificacion, tipo_destinatario, canal, email, nombre, activo)
VALUES (?, ?, ?, ?, ?, 1)""",
                    (id_configuracion, item.tipo_destinatario, item.canal,
                     item.email, item.nombre), operacion="crear_destinatario_notificacion",
                )

    def obtener_configuracion_graph(self) -> ConfiguracionMailGraph | None:
        fila = self.ejecutar_uno(
            """SELECT TOP 1 id_config_mail, activo, tenant_id, client_id, graph_scope,
send_mail_user, save_to_sent_items, alertas_destinatarios_default,
client_secret_origen, fecha_actualizacion, usuario_actualizacion
FROM dbo.configuracion_mail_graph
WHERE clave_configuracion = N'MAIL_GRAPH' ORDER BY id_config_mail""",
            operacion="obtener_configuracion_mail_graph",
        )
        if fila is None:
            return None
        return ConfiguracionMailGraph(
            int(fila[0]), bool(fila[1]), fila[2], fila[3], str(fila[4]), fila[5],
            bool(fila[6]), fila[7], str(fila[8]), fila[9], fila[10],
        )

    def guardar_configuracion_graph(self, id_config_mail: int, datos, actor: str) -> bool:
        return self.ejecutar(
            """UPDATE dbo.configuracion_mail_graph
SET activo = ?, tenant_id = ?, client_id = ?, graph_scope = ?,
    send_mail_user = ?, save_to_sent_items = ?,
    alertas_destinatarios_default = ?, client_secret_origen = N'ENV',
    fecha_actualizacion = SYSDATETIME(), usuario_actualizacion = ?
WHERE id_config_mail = ? AND clave_configuracion = N'MAIL_GRAPH'""",
            (int(datos["activo"]), datos["tenant_id"], datos["client_id"],
             datos["graph_scope"], datos["send_mail_user"],
             int(datos["save_to_sent_items"]), datos["alertas_destinatarios_default"],
             actor, id_config_mail), operacion="actualizar_configuracion_mail_graph",
        ) == 1

    def obtener_contexto_envio(self, id_ejecucion: int):
        fila = self.ejecutar_uno(
            """SELECT e.id_ejecucion, e.id_tarea, e.estado_ejecucion, e.codigo_salida,
e.fecha_hora_inicio, e.fecha_hora_termino, e.duracion_segundos,
COALESCE(e.nombre_tarea_snapshot, t.nombre_tarea, N'Tarea historica'),
e.mensaje_error, v.ruta_fisica, e.origen_ejecucion,
COALESCE(e.nombre_script_snapshot, s.nombre_script, N'Script historico'),
COALESCE(e.nombre_archivo_snapshot, v.nombre_archivo, N'Archivo historico'),
COALESCE(e.version_script_snapshot, CONCAT(N'v', v.numero_version), N'Sin version'),
ev.id_evidencia, ev.estado_evidencia, ev.titulo, ev.asunto_sugerido,
ev.tipo_evidencia, ev.error_validacion
FROM dbo.ejecuciones e
LEFT JOIN dbo.tareas t ON t.id_tarea = e.id_tarea
LEFT JOIN dbo.scripts s ON s.id_script = e.id_script
LEFT JOIN dbo.scripts_versiones v ON v.id_version = e.id_version
LEFT JOIN dbo.evidencias_ejecucion ev ON ev.id_ejecucion = e.id_ejecucion
WHERE e.id_ejecucion = ?""",
            (id_ejecucion,), operacion="obtener_contexto_envio_notificacion",
        )
        if fila is None:
            return None
        claves = ("id_ejecucion", "id_tarea", "estado_ejecucion", "codigo_salida",
                  "fecha_inicio", "fecha_termino", "duracion_segundos", "nombre_tarea",
                  "mensaje_error", "ruta_script_fisica", "origen_ejecucion",
                  "nombre_script", "nombre_archivo", "version_script", "id_evidencia",
                  "estado_evidencia", "titulo_evidencia", "asunto_sugerido",
                  "tipo_evidencia", "error_evidencia")
        return dict(zip(claves, fila))

    def reservar_envio(self, id_ejecucion: int, id_evidencia: int | None,
                       tipo_envio: str, asunto: str, destinatarios) -> int | None:
        fila = self.ejecutar_uno(
            """SET NOCOUNT ON;
DECLARE @resultado int;
DECLARE @reservado TABLE (id_envio bigint NOT NULL);
EXEC @resultado = sys.sp_getapplock
 @Resource = ?, @LockMode = 'Exclusive', @LockOwner = 'Transaction', @LockTimeout = 0;
IF @resultado >= 0 AND NOT EXISTS (
 SELECT 1 FROM dbo.notificaciones_envios WITH (UPDLOCK, HOLDLOCK)
 WHERE id_ejecucion = ? AND tipo_envio = ?
)
BEGIN
 INSERT INTO dbo.notificaciones_envios
 (id_ejecucion, id_evidencia, tipo_envio, estado_envio, asunto,
  destinatarios_to, destinatarios_cc, destinatarios_bcc, intento, es_reintento)
 OUTPUT INSERTED.id_envio INTO @reservado
 VALUES (?, ?, ?, N'PENDIENTE', ?, ?, ?, ?, 1, 0);
END;
SELECT TOP 1 id_envio FROM @reservado;""",
            (f"APP_SCHEDULER_MAIL_{id_ejecucion}_{tipo_envio}", id_ejecucion,
             tipo_envio, id_ejecucion, id_evidencia, tipo_envio, asunto,
             destinatarios.get("TO"), destinatarios.get("CC"),
             destinatarios.get("BCC")), operacion="reservar_envio_notificacion",
        )
        return None if fila is None else int(fila[0])

    def finalizar_envio(self, id_envio: int, estado: str, *, status_code=None,
                        request_id=None, error=None) -> bool:
        return self.ejecutar(
            """UPDATE dbo.notificaciones_envios
SET estado_envio = ?, graph_status_code = ?, graph_request_id = ?,
    error_controlado = ?, fecha_envio = CASE WHEN ? = N'ENVIADO' THEN SYSDATETIME() ELSE NULL END
WHERE id_envio = ? AND estado_envio = N'PENDIENTE'""",
            (estado, status_code, request_id, error, estado, id_envio),
            operacion="finalizar_envio_notificacion",
        ) == 1

    def listar_envios_ejecucion(self, id_ejecucion: int):
        """Entrega trazabilidad segura sin destinatarios ni metadatos Graph."""
        filas = self.ejecutar_lista(
            """SELECT n.tipo_envio, n.estado_envio,
CASE WHEN n.tipo_envio = N'EVIDENCIA_CLIENTE' AND ev.estado_evidencia = N'VALIDADA'
     THEN 1 ELSE 0 END,
CASE WHEN n.tipo_envio = N'EVIDENCIA_CLIENTE' AND ev.estado_evidencia = N'VALIDADA'
     THEN COALESCE(ev.cantidad_adjuntos_declarados, 0) ELSE 0 END,
ev.estado_evidencia
FROM dbo.notificaciones_envios n
LEFT JOIN dbo.evidencias_ejecucion ev ON ev.id_evidencia = n.id_evidencia
WHERE n.id_ejecucion = ?
ORDER BY n.fecha_intento, n.id_envio""",
            (id_ejecucion,), operacion="listar_envios_ejecucion_seguro",
        )
        return tuple({
            "tipo_envio": str(fila[0]),
            "estado_envio": str(fila[1]),
            "evidencia_incluida": bool(fila[2]),
            "cantidad_adjuntos": max(0, int(fila[3] or 0)),
            "estado_evidencia": fila[4],
        } for fila in filas)

    def estado_integraciones(self):
        fila = self.ejecutar_uno(
            """SELECT
(SELECT COUNT(1) FROM dbo.feriados WHERE activo = 1),
(SELECT MAX(COALESCE(fecha_actualizacion, fecha_creacion)) FROM dbo.feriados WHERE origen = 'API_NAGER'),
(SELECT TOP 1 activo FROM dbo.configuracion_mail_graph WHERE clave_configuracion=N'MAIL_GRAPH'),
(SELECT TOP 1 estado_envio FROM dbo.notificaciones_envios ORDER BY fecha_intento DESC, id_envio DESC),
(SELECT TOP 1 fecha_intento FROM dbo.notificaciones_envios ORDER BY fecha_intento DESC, id_envio DESC)""",
            operacion="obtener_estado_integraciones",
        )
        return {"feriados_activos": int(fila[0] or 0), "ultima_sync": fila[1],
                "graph_sql_activo": bool(fila[2]), "ultimo_envio_estado": fila[3],
                "ultimo_envio_fecha": fila[4]}
