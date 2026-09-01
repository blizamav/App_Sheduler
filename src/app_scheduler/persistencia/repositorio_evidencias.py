"""Configuracion de captura de evidencia por tarea."""

from app_scheduler.persistencia.mapeadores import mapear_configuracion_evidencia
from app_scheduler.persistencia.modelos import ConfiguracionEvidenciaTarea
from app_scheduler.persistencia.repositorio import RepositorioSQL


class RepositorioEvidencias(RepositorioSQL):
    def obtener_configuracion(self, id_tarea: int) -> ConfiguracionEvidenciaTarea:
        fila = self.ejecutar_uno(
            """SELECT TOP 1 id_config_notificacion, id_tarea, enviar_evidencia,
plantilla_evidencia, adjuntar_archivos_declarados, adjuntar_log_tecnico
FROM dbo.notificaciones_config_tarea
WHERE id_tarea = ? AND activo = 1 ORDER BY id_config_notificacion""",
            (id_tarea,), operacion="obtener_configuracion_evidencia",
        )
        if fila is None:
            return ConfiguracionEvidenciaTarea(None, id_tarea, False, "STDOUT_V1", True, False)
        return mapear_configuracion_evidencia(fila)

    def obtener_script_activo(self, id_tarea: int):
        return self.ejecutar_uno(
            """SELECT v.ruta_fisica, v.nombre_archivo
FROM dbo.scripts s
JOIN dbo.scripts_versiones v ON v.id_version = s.id_version_activa
WHERE s.id_tarea = ? AND s.activo = 1 AND s.eliminado_operativo = 0
  AND v.es_activa = 1 AND v.estado_version = 'ACTIVA' AND v.eliminado_operativo = 0""",
            (id_tarea,), operacion="obtener_script_evidencia",
        )

    def guardar(self, configuracion: ConfiguracionEvidenciaTarea) -> None:
        if configuracion.id_config_notificacion is None:
            self.ejecutar(
                """INSERT INTO dbo.notificaciones_config_tarea
 (id_tarea, enviar_evidencia, notificar_exito_activa, plantilla_evidencia, adjuntar_archivos_declarados,
  adjuntar_log_tecnico, alerta_error_activa, usar_alerta_global, activo)
VALUES (?, ?, ?, 'STDOUT_V1', ?, ?, 1, 1, 1)""",
                (configuracion.id_tarea, int(configuracion.enviar_evidencia),
                 0,
                 int(configuracion.adjuntar_archivos_declarados),
                 int(configuracion.adjuntar_log_tecnico)),
                operacion="crear_configuracion_evidencia",
            )
            return
        if self.ejecutar(
            """UPDATE dbo.notificaciones_config_tarea
SET enviar_evidencia = ?,
    plantilla_evidencia = 'STDOUT_V1',
    adjuntar_archivos_declarados = ?, adjuntar_log_tecnico = ?,
    actualizado_en = SYSDATETIME()
WHERE id_config_notificacion = ? AND id_tarea = ? AND activo = 1""",
            (int(configuracion.enviar_evidencia), int(configuracion.adjuntar_archivos_declarados),
             int(configuracion.adjuntar_log_tecnico),
             configuracion.id_config_notificacion, configuracion.id_tarea),
            operacion="actualizar_configuracion_evidencia",
        ) != 1:
            raise ValueError("Configuracion de evidencia no disponible.")
