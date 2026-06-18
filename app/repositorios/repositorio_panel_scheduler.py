from app.database.conexion import obtener_conexion


def _fila_a_dict(cursor, fila):
    columnas = [columna[0] for columna in cursor.description]
    return dict(zip(columnas, fila))


def _columnas(tabla):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT name
            FROM sys.columns
            WHERE object_id = OBJECT_ID(?)
            """,
            f"dbo.{tabla}",
        )
        return {fila[0] for fila in cursor.fetchall()}


def obtener_resumen_ejecuciones_automaticas():
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT
                COUNT(1) AS total,
                SUM(CASE WHEN estado_ejecucion = 'EN_EJECUCION' THEN 1 ELSE 0 END) AS en_ejecucion,
                SUM(CASE WHEN estado_ejecucion = 'EXITOSA' THEN 1 ELSE 0 END) AS exitosas,
                SUM(CASE WHEN estado_ejecucion = 'ERROR' THEN 1 ELSE 0 END) AS errores,
                SUM(CASE WHEN estado_ejecucion = 'DETENIDA_MANUALMENTE' THEN 1 ELSE 0 END) AS detenidas
            FROM dbo.ejecuciones
            WHERE origen_ejecucion = 'AUTOMATICA'
            """
        )
        fila = cursor.fetchone()
        return _fila_a_dict(cursor, fila) if fila else {}


def listar_ultimas_ejecuciones_automaticas(limite=8):
    columnas = _columnas("ejecuciones")
    fecha_programada = "e.fecha_programada" if "fecha_programada" in columnas else "CAST(NULL AS datetime2(0))"
    clave_programacion = "e.clave_programacion" if "clave_programacion" in columnas else "CAST(NULL AS varchar(200))"
    nombre_worker = "e.nombre_worker" if "nombre_worker" in columnas else "CAST(NULL AS varchar(100))"
    consulta = f"""
        SELECT TOP ({int(limite)})
               e.id_ejecucion, e.estado_ejecucion, e.fecha_hora_inicio, e.fecha_hora_termino,
               e.duracion_segundos, e.codigo_salida, e.mensaje_error,
               {fecha_programada} AS fecha_programada,
               {clave_programacion} AS clave_programacion,
               {nombre_worker} AS nombre_worker,
               COALESCE(e.nombre_tarea_snapshot, t.nombre_tarea, 'Tarea eliminada') AS nombre_tarea
        FROM dbo.ejecuciones e
        LEFT JOIN dbo.tareas t ON t.id_tarea = e.id_tarea
        WHERE e.origen_ejecucion = 'AUTOMATICA'
        ORDER BY e.fecha_hora_inicio DESC, e.id_ejecucion DESC
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta)
        return [_fila_a_dict(cursor, fila) for fila in cursor.fetchall()]


def listar_errores_scheduler_recientes(limite=8):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            f"""
            SELECT TOP ({int(limite)})
                   fecha_hora, accion, descripcion, nivel, usuario
            FROM dbo.logs_sistema
            WHERE modulo = 'SCHEDULER'
              AND (nivel IN ('ERROR','WARNING') OR accion LIKE 'WORKER%ERROR%')
            ORDER BY fecha_hora DESC, id DESC
            """
        )
        return [_fila_a_dict(cursor, fila) for fila in cursor.fetchall()]


def listar_tareas_candidatas(limite=10):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            f"""
            SELECT TOP ({int(limite)})
                   t.id_tarea, t.nombre_tarea, t.estado_tarea,
                   p.tipo_programacion, p.modo_ejecucion_dia, p.hora_ejecucion,
                   p.dias_semana, p.dia_mes, p.fecha_especifica, p.intervalo_minutos,
                   p.hora_inicio, p.hora_termino, p.ejecutar_en_feriados,
                   s.id_script, s.id_version_activa,
                   v.nombre_archivo
            FROM dbo.tareas t
            INNER JOIN dbo.programaciones p ON p.id_tarea = t.id_tarea AND p.activo = 1
            LEFT JOIN dbo.scripts s ON s.id_tarea = t.id_tarea AND s.activo = 1 AND ISNULL(s.eliminado_operativo, 0) = 0
            LEFT JOIN dbo.scripts_versiones v ON v.id_version = s.id_version_activa AND ISNULL(v.eliminado_operativo, 0) = 0
            WHERE t.activo = 1
              AND t.estado_tarea = 'ACTIVA'
              AND ISNULL(t.eliminado_operativo, 0) = 0
              AND p.tipo_programacion <> 'MANUAL'
            ORDER BY t.nombre_tarea
            """
        )
        return [_fila_a_dict(cursor, fila) for fila in cursor.fetchall()]


def obtener_estado_feriados_locales():
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT
                COUNT(1) AS total,
                SUM(CASE WHEN activo = 1 THEN 1 ELSE 0 END) AS activos,
                SUM(CASE WHEN activo = 1 AND origen = 'MANUAL' THEN 1 ELSE 0 END) AS manuales_activos,
                SUM(CASE WHEN activo = 1 AND origen = 'API_NAGER' THEN 1 ELSE 0 END) AS api_nager_activos
            FROM dbo.feriados
            """
        )
        resumen = _fila_a_dict(cursor, cursor.fetchone())
        cursor.execute(
            """
            SELECT TOP 1 fecha, nombre, pais, irrenunciable, origen
            FROM dbo.feriados
            WHERE activo = 1
              AND fecha >= CAST(GETDATE() AS date)
            ORDER BY fecha ASC
            """
        )
        proximo = cursor.fetchone()
        resumen["proximo"] = _fila_a_dict(cursor, proximo) if proximo else None
        return resumen
