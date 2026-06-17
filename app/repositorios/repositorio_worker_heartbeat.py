from app.database.conexion import obtener_conexion


def _fila_a_dict(cursor, fila):
    columnas = [columna[0] for columna in cursor.description]
    return dict(zip(columnas, fila))


def upsert_inicio_worker(datos):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            UPDATE dbo.scheduler_worker_heartbeat
            SET estado = 'INICIADO',
                fecha_inicio = SYSDATETIME(),
                fecha_ultimo_heartbeat = SYSDATETIME(),
                pid_proceso = ?,
                host = ?,
                version_app = ?,
                ultimo_error = NULL,
                activo = 1,
                fecha_actualizacion = SYSDATETIME()
            WHERE nombre_worker = ?
              AND activo = 1
            """,
            datos.get("pid_proceso"),
            datos.get("host"),
            datos.get("version_app"),
            datos["nombre_worker"],
        )
        if cursor.rowcount == 0:
            cursor.execute(
                """
                INSERT INTO dbo.scheduler_worker_heartbeat
                    (nombre_worker, estado, fecha_inicio, fecha_ultimo_heartbeat,
                     pid_proceso, host, version_app, activo)
                VALUES (?, 'INICIADO', SYSDATETIME(), SYSDATETIME(), ?, ?, ?, 1)
                """,
                datos["nombre_worker"],
                datos.get("pid_proceso"),
                datos.get("host"),
                datos.get("version_app"),
            )
        conexion.commit()


def actualizar_estado_worker(nombre_worker, estado):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            UPDATE dbo.scheduler_worker_heartbeat
            SET estado = ?,
                fecha_ultimo_heartbeat = SYSDATETIME(),
                fecha_actualizacion = SYSDATETIME()
            WHERE nombre_worker = ?
              AND activo = 1
            """,
            estado,
            nombre_worker,
        )
        conexion.commit()


def registrar_fin_ciclo_worker(nombre_worker, resultado, evaluadas, ejecutadas, omitidas, estado_final):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            UPDATE dbo.scheduler_worker_heartbeat
            SET estado = ?,
                fecha_ultimo_heartbeat = SYSDATETIME(),
                fecha_ultimo_ciclo = SYSDATETIME(),
                resultado_ultimo_ciclo = ?,
                ultimo_error = NULL,
                ciclos_ejecutados = ciclos_ejecutados + 1,
                tareas_evaluadas_ultimo_ciclo = ?,
                tareas_ejecutadas_ultimo_ciclo = ?,
                tareas_omitidas_ultimo_ciclo = ?,
                fecha_actualizacion = SYSDATETIME()
            WHERE nombre_worker = ?
              AND activo = 1
            """,
            estado_final,
            resultado,
            int(evaluadas or 0),
            int(ejecutadas or 0),
            int(omitidas or 0),
            nombre_worker,
        )
        conexion.commit()


def registrar_error_worker_bd(nombre_worker, mensaje_error, incrementar_ciclo=False):
    incremento = "ciclos_ejecutados + 1" if incrementar_ciclo else "ciclos_ejecutados"
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            f"""
            UPDATE dbo.scheduler_worker_heartbeat
            SET estado = 'ERROR',
                fecha_ultimo_heartbeat = SYSDATETIME(),
                fecha_ultimo_ciclo = SYSDATETIME(),
                resultado_ultimo_ciclo = 'ERROR',
                ultimo_error = ?,
                ciclos_ejecutados = {incremento},
                fecha_actualizacion = SYSDATETIME()
            WHERE nombre_worker = ?
              AND activo = 1
            """,
            str(mensaje_error or "")[:2000],
            nombre_worker,
        )
        conexion.commit()


def registrar_detencion_worker_bd(nombre_worker):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            UPDATE dbo.scheduler_worker_heartbeat
            SET estado = 'DETENIDO',
                fecha_ultimo_heartbeat = SYSDATETIME(),
                fecha_actualizacion = SYSDATETIME()
            WHERE nombre_worker = ?
              AND activo = 1
            """,
            nombre_worker,
        )
        conexion.commit()


def obtener_heartbeat_worker(nombre_worker=None):
    consulta = """
        SELECT TOP 1 id_worker, nombre_worker, estado, fecha_inicio,
               fecha_ultimo_heartbeat, fecha_ultimo_ciclo, resultado_ultimo_ciclo,
               ultimo_error, ciclos_ejecutados, tareas_evaluadas_ultimo_ciclo,
               tareas_ejecutadas_ultimo_ciclo, tareas_omitidas_ultimo_ciclo,
               pid_proceso, host, version_app, activo, fecha_creacion, fecha_actualizacion
        FROM dbo.scheduler_worker_heartbeat
        WHERE activo = 1
    """
    parametros = []
    if nombre_worker:
        consulta += " AND nombre_worker = ?"
        parametros.append(nombre_worker)
    consulta += " ORDER BY fecha_ultimo_heartbeat DESC, id_worker DESC"

    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        if parametros:
            cursor.execute(consulta, *parametros)
        else:
            cursor.execute(consulta)
        fila = cursor.fetchone()
        return _fila_a_dict(cursor, fila) if fila else None
