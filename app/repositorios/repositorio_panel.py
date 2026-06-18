from app.database.conexion import obtener_conexion


def _fila_a_dict(cursor, fila):
    columnas = [columna[0] for columna in cursor.description]
    return dict(zip(columnas, fila))


def obtener_metricas_panel():
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT
                (SELECT COUNT(1) FROM dbo.tareas WHERE ISNULL(eliminado_operativo, 0) = 0) AS total_tareas,
                (SELECT COUNT(1) FROM dbo.tareas WHERE activo = 1 AND estado_tarea = 'ACTIVA' AND ISNULL(eliminado_operativo, 0) = 0) AS tareas_activas,
                (SELECT COUNT(1) FROM dbo.scripts WHERE activo = 1 AND ISNULL(eliminado_operativo, 0) = 0) AS scripts_activos,
                (SELECT COUNT(DISTINCT id_tarea) FROM dbo.scripts WHERE activo = 1 AND ISNULL(eliminado_operativo, 0) = 0) AS tareas_con_script,
                (SELECT COUNT(1) FROM dbo.ejecuciones WHERE fecha_hora_inicio >= CAST(GETDATE() AS date)) AS ejecuciones_hoy,
                (SELECT COUNT(1) FROM dbo.ejecuciones WHERE fecha_hora_inicio >= CAST(GETDATE() AS date) AND estado_ejecucion = 'EXITOSA') AS exitosas_hoy,
                (SELECT COUNT(1) FROM dbo.ejecuciones WHERE fecha_hora_inicio >= CAST(GETDATE() AS date) AND estado_ejecucion = 'ERROR') AS errores_hoy,
                (SELECT COUNT(1) FROM dbo.ejecuciones WHERE estado_ejecucion = 'EN_EJECUCION') AS en_curso,
                (SELECT COUNT(1) FROM dbo.feriados WHERE YEAR(fecha) = YEAR(GETDATE()) AND activo = 1) AS feriados_anio_actual
            """
        )
        fila = cursor.fetchone()
        return _fila_a_dict(cursor, fila) if fila else {}


def obtener_configuracion_scheduler_panel():
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT TOP 1
                   scheduler_activo,
                   permitir_ejecucion_automatica,
                   modo_mantenimiento,
                   intervalo_revision_segundos,
                   max_ejecuciones_concurrentes
            FROM dbo.configuracion_scheduler
            WHERE activo = 1
            ORDER BY id_configuracion DESC
            """
        )
        fila = cursor.fetchone()
        return _fila_a_dict(cursor, fila) if fila else None


def obtener_ultima_ejecucion():
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT TOP 1
                   e.id_ejecucion,
                   e.estado_ejecucion,
                   e.origen_ejecucion,
                   e.fecha_hora_inicio,
                   COALESCE(e.nombre_tarea_snapshot, t.nombre_tarea, 'Tarea eliminada') AS nombre_tarea
            FROM dbo.ejecuciones e
            LEFT JOIN dbo.tareas t ON t.id_tarea = e.id_tarea
            ORDER BY e.fecha_hora_inicio DESC, e.id_ejecucion DESC
            """
        )
        fila = cursor.fetchone()
        return _fila_a_dict(cursor, fila) if fila else None


def listar_ultimas_ejecuciones(limite=6):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            f"""
            SELECT TOP ({int(limite)})
                   e.id_ejecucion,
                   e.estado_ejecucion,
                   e.origen_ejecucion,
                   e.fecha_hora_inicio,
                   COALESCE(e.nombre_tarea_snapshot, t.nombre_tarea, 'Tarea eliminada') AS nombre_tarea
            FROM dbo.ejecuciones e
            LEFT JOIN dbo.tareas t ON t.id_tarea = e.id_tarea
            ORDER BY e.fecha_hora_inicio DESC, e.id_ejecucion DESC
            """
        )
        return [_fila_a_dict(cursor, fila) for fila in cursor.fetchall()]
