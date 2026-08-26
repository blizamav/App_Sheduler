"""Lecturas acotadas para el preview y precheck de Factory Reset."""

from app_scheduler.persistencia.repositorio import RepositorioSQL


TABLAS_FACTORY_RESET = (
    "cat_estados_tarea", "cat_estados_ejecucion", "cat_tipos_programacion",
    "cat_niveles_log", "cat_tipos_tarea", "cat_estados_version_script",
    "usuarios", "roles", "permisos", "usuarios_roles", "roles_permisos",
    "clientes", "categorias", "tipos", "tareas", "programaciones",
    "scripts", "scripts_versiones", "configuracion_sistema", "ejecuciones",
    "logs_tareas", "logs_sistema", "auditoria_cambios",
    "configuracion_scheduler", "scheduler_worker_heartbeat", "scheduler_eventos",
    "feriados", "reglas_feriados_irrenunciables",
    "notificaciones_config_tarea", "notificaciones_destinatarios",
    "evidencias_ejecucion", "notificaciones_envios", "configuracion_mail_graph",
)


class RepositorioFactoryReset(RepositorioSQL):
    def obtener_conteos(self) -> dict[str, int]:
        expresiones = ",\n".join(
            f"(SELECT COUNT_BIG(1) FROM dbo.[{tabla}]) AS [{tabla}]"
            for tabla in TABLAS_FACTORY_RESET
        )
        fila = self.ejecutar_uno(
            f"SELECT {expresiones}", operacion="inventariar_factory_reset"
        )
        return {
            tabla: int(fila[indice] or 0)
            for indice, tabla in enumerate(TABLAS_FACTORY_RESET)
        }

    def obtener_version_bootstrap(self) -> str | None:
        fila = self.ejecutar_uno(
            """SELECT TOP 1 valor FROM dbo.configuracion_sistema
WHERE clave = 'BOOTSTRAP_SQL' AND activo = 1
ORDER BY id_configuracion DESC""",
            operacion="obtener_version_bootstrap_factory_reset",
        )
        return str(fila[0]).strip() if fila and fila[0] is not None else None

    def listar_ejecuciones_activas(self):
        filas = self.ejecutar_lista(
            """SELECT id_ejecucion, id_tarea, origen_ejecucion,
fecha_hora_inicio, pid_proceso
FROM dbo.ejecuciones WHERE estado_ejecucion = 'EN_EJECUCION'
ORDER BY fecha_hora_inicio, id_ejecucion""",
            operacion="listar_activas_factory_reset",
        )
        return tuple(
            {
                "id_ejecucion": fila[0], "id_tarea": fila[1],
                "origen": fila[2], "fecha_inicio": fila[3],
                "pid_registrado": bool(fila[4]),
            }
            for fila in filas
        )
