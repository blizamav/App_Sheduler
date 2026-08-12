from app.database.conexion import obtener_conexion


TABLAS_FACTORY_RESET = (
    "cat_estados_tarea",
    "cat_estados_ejecucion",
    "cat_tipos_programacion",
    "cat_niveles_log",
    "cat_tipos_tarea",
    "cat_estados_version_script",
    "usuarios",
    "roles",
    "permisos",
    "usuarios_roles",
    "roles_permisos",
    "clientes",
    "categorias",
    "tipos",
    "tareas",
    "programaciones",
    "scripts",
    "scripts_versiones",
    "configuracion_sistema",
    "ejecuciones",
    "logs_tareas",
    "logs_sistema",
    "auditoria_cambios",
    "configuracion_scheduler",
    "scheduler_worker_heartbeat",
    "scheduler_eventos",
    "feriados",
    "reglas_feriados_irrenunciables",
    "notificaciones_config_tarea",
    "notificaciones_destinatarios",
    "evidencias_ejecucion",
    "notificaciones_envios",
    "configuracion_mail_graph",
)


def obtener_conteos_factory_reset():
    conteos = {}
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        for tabla in TABLAS_FACTORY_RESET:
            cursor.execute(f"SELECT COUNT_BIG(1) FROM dbo.[{tabla}]")
            conteos[tabla] = int(cursor.fetchone()[0] or 0)
    return conteos


def obtener_version_bootstrap_sql():
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT TOP 1 valor
            FROM dbo.configuracion_sistema
            WHERE clave = 'BOOTSTRAP_SQL' AND activo = 1
            ORDER BY id_configuracion DESC
            """
        )
        fila = cursor.fetchone()
        return str(fila[0]).strip() if fila and fila[0] is not None else None


def listar_ejecuciones_activas_factory_reset():
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT id_ejecucion, id_tarea, origen_ejecucion, fecha_hora_inicio, pid_proceso
            FROM dbo.ejecuciones
            WHERE estado_ejecucion = 'EN_EJECUCION'
            ORDER BY fecha_hora_inicio, id_ejecucion
            """
        )
        columnas = [columna[0] for columna in cursor.description]
        return [dict(zip(columnas, fila)) for fila in cursor.fetchall()]
