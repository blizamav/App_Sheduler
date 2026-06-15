from app.database.conexion import obtener_conexion


def _fila_a_dict(cursor, fila):
    columnas = [columna[0] for columna in cursor.description]
    return dict(zip(columnas, fila))


def obtener_contexto_tarea_ejecucion(id_tarea):
    consulta = """
        SELECT t.id_tarea, t.nombre_tarea, t.descripcion, t.estado_tarea, t.activo,
               c.nombre_cliente, ca.nombre_categoria, ti.nombre_tipo,
               s.id_script, s.nombre_script, s.activo AS script_activo, s.id_version_activa,
               v.id_version, v.numero_version, v.nombre_archivo, v.ruta_fisica, v.ruta_relativa,
               v.estado_version, v.es_activa, v.requiere_env, v.ruta_env_fisica, v.ruta_env_relativa
        FROM dbo.tareas t
        INNER JOIN dbo.clientes c ON c.id_cliente = t.id_cliente
        INNER JOIN dbo.categorias ca ON ca.id_categoria = t.id_categoria
        INNER JOIN dbo.tipos ti ON ti.id_tipo = t.id_tipo
        LEFT JOIN dbo.scripts s ON s.id_tarea = t.id_tarea
        LEFT JOIN dbo.scripts_versiones v ON v.id_version = s.id_version_activa
        WHERE t.id_tarea = ?
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, id_tarea)
        fila = cursor.fetchone()
        return _fila_a_dict(cursor, fila) if fila else None


def existe_ejecucion_en_curso_tarea(id_tarea):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT COUNT(1)
            FROM dbo.ejecuciones
            WHERE id_tarea = ? AND estado_ejecucion = 'EN_EJECUCION'
            """,
            id_tarea,
        )
        return cursor.fetchone()[0] > 0


def crear_ejecucion_manual(contexto, usuario):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            INSERT INTO dbo.ejecuciones
                (id_tarea, id_script, id_version, origen_ejecucion, estado_ejecucion,
                 fecha_hora_inicio, usuario_ejecucion)
            OUTPUT INSERTED.id_ejecucion
            VALUES (?, ?, ?, 'MANUAL', 'EN_EJECUCION', SYSDATETIME(), ?)
            """,
            contexto["id_tarea"],
            contexto["id_script"],
            contexto["id_version"],
            usuario,
        )
        id_ejecucion = cursor.fetchone()[0]
        conexion.commit()
        return id_ejecucion


def actualizar_pid_ejecucion(id_ejecucion, pid):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute("UPDATE dbo.ejecuciones SET pid_proceso = ? WHERE id_ejecucion = ?", pid, id_ejecucion)
        conexion.commit()


def finalizar_ejecucion(id_ejecucion, estado, codigo_salida=None, mensaje_error=None):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            UPDATE dbo.ejecuciones
            SET estado_ejecucion = ?,
                fecha_hora_termino = SYSDATETIME(),
                duracion_segundos = DATEDIFF(SECOND, fecha_hora_inicio, SYSDATETIME()),
                codigo_salida = ?,
                mensaje_error = ?
            WHERE id_ejecucion = ? AND estado_ejecucion = 'EN_EJECUCION'
            """,
            estado,
            codigo_salida,
            mensaje_error,
            id_ejecucion,
        )
        conexion.commit()


def marcar_ejecucion_detenida(id_ejecucion, usuario, motivo, fue_forzada):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            UPDATE dbo.ejecuciones
            SET estado_ejecucion = 'DETENIDA_MANUALMENTE',
                fecha_hora_termino = SYSDATETIME(),
                duracion_segundos = DATEDIFF(SECOND, fecha_hora_inicio, SYSDATETIME()),
                usuario_detencion = ?,
                fecha_hora_detencion = SYSDATETIME(),
                motivo_detencion = ?,
                fue_detencion_forzada = ?
            WHERE id_ejecucion = ? AND estado_ejecucion = 'EN_EJECUCION'
            """,
            usuario,
            motivo,
            1 if fue_forzada else 0,
            id_ejecucion,
        )
        conexion.commit()


def crear_log_tarea(id_ejecucion, contexto, ruta_fisica_log, ruta_relativa_log, nombre_archivo_log, usuario):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            INSERT INTO dbo.logs_tareas
                (id_tarea, id_ejecucion, nombre_tarea, nombre_script, nombre_archivo_log,
                 ruta_fisica_log, ruta_relativa_log, fecha_hora_inicio, estado_final, usuario_ejecucion)
            VALUES (?, ?, ?, ?, ?, ?, ?, SYSDATETIME(), 'EN_EJECUCION', ?)
            """,
            contexto["id_tarea"],
            id_ejecucion,
            contexto["nombre_tarea"],
            contexto["nombre_archivo"],
            nombre_archivo_log,
            str(ruta_fisica_log),
            ruta_relativa_log,
            usuario,
        )
        conexion.commit()


def actualizar_log_tarea_final(id_ejecucion, estado, codigo_salida=None, mensaje_error=None):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            UPDATE dbo.logs_tareas
            SET estado_final = ?,
                fecha_hora_termino = SYSDATETIME(),
                duracion_segundos = DATEDIFF(SECOND, fecha_hora_inicio, SYSDATETIME()),
                codigo_salida = ?,
                mensaje_error = ?
            WHERE id_ejecucion = ?
            """,
            estado,
            codigo_salida,
            mensaje_error,
            id_ejecucion,
        )
        conexion.commit()


def obtener_ejecucion(id_ejecucion):
    consulta = """
        SELECT e.id_ejecucion, e.id_tarea, e.id_script, e.id_version, e.origen_ejecucion,
               e.estado_ejecucion, e.fecha_hora_inicio, e.fecha_hora_termino, e.duracion_segundos,
               e.codigo_salida, e.mensaje_error, e.usuario_ejecucion, e.pid_proceso,
               e.usuario_detencion, e.fecha_hora_detencion, e.motivo_detencion, e.fue_detencion_forzada,
               t.nombre_tarea, c.nombre_cliente, ca.nombre_categoria, ti.nombre_tipo,
               v.numero_version, v.nombre_archivo, v.ruta_relativa,
               lt.ruta_fisica_log, lt.ruta_relativa_log, lt.nombre_archivo_log
        FROM dbo.ejecuciones e
        INNER JOIN dbo.tareas t ON t.id_tarea = e.id_tarea
        INNER JOIN dbo.clientes c ON c.id_cliente = t.id_cliente
        INNER JOIN dbo.categorias ca ON ca.id_categoria = t.id_categoria
        INNER JOIN dbo.tipos ti ON ti.id_tipo = t.id_tipo
        INNER JOIN dbo.scripts_versiones v ON v.id_version = e.id_version
        LEFT JOIN dbo.logs_tareas lt ON lt.id_ejecucion = e.id_ejecucion
        WHERE e.id_ejecucion = ?
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, id_ejecucion)
        fila = cursor.fetchone()
        return _fila_a_dict(cursor, fila) if fila else None
