from app.database.conexion import obtener_conexion


def _fila_a_dict(cursor, fila):
    columnas = [columna[0] for columna in cursor.description]
    return dict(zip(columnas, fila))


def listar_tareas_programadas_activas():
    consulta = """
        SELECT t.id_tarea,
               t.nombre_tarea,
               t.estado_tarea,
               t.activo,
               p.id_programacion,
               p.tipo_programacion,
               p.modo_ejecucion_dia,
               p.hora_ejecucion,
               p.dias_semana,
               p.dia_mes,
               p.fecha_especifica,
               p.intervalo_minutos,
               p.hora_inicio AS hora_inicio_intervalo,
               p.hora_termino AS hora_fin_intervalo,
               p.ejecutar_en_feriados,
               s.id_script,
               s.activo AS script_activo,
               s.id_version_activa,
               v.id_version,
               v.nombre_archivo
        FROM dbo.tareas t
        INNER JOIN dbo.programaciones p ON p.id_tarea = t.id_tarea AND p.activo = 1
        LEFT JOIN dbo.scripts s ON s.id_tarea = t.id_tarea
        LEFT JOIN dbo.scripts_versiones v ON v.id_version = s.id_version_activa
        WHERE t.activo = 1
          AND t.estado_tarea = 'ACTIVA'
          AND p.tipo_programacion <> 'MANUAL'
        ORDER BY t.id_tarea
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta)
        return [_fila_a_dict(cursor, fila) for fila in cursor.fetchall()]


def contar_ejecuciones_automaticas_en_curso():
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT COUNT(1)
            FROM dbo.ejecuciones
            WHERE origen_ejecucion = 'AUTOMATICA'
              AND estado_ejecucion = 'EN_EJECUCION'
            """
        )
        return cursor.fetchone()[0]


def existe_clave_programacion(clave_programacion):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT COUNT(1)
            FROM dbo.ejecuciones
            WHERE origen_ejecucion = 'AUTOMATICA'
              AND clave_programacion = ?
            """,
            clave_programacion,
        )
        return cursor.fetchone()[0] > 0
