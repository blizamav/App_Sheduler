from app.database.conexion import obtener_conexion


def _fila_a_dict(cursor, fila):
    columnas = [columna[0] for columna in cursor.description]
    return dict(zip(columnas, fila))


def obtener_configuracion_activa():
    consulta = """
        SELECT TOP 1 id_configuracion, scheduler_activo, intervalo_revision_segundos,
               max_ejecuciones_concurrentes, permitir_ejecucion_automatica,
               modo_mantenimiento, nombre_worker_principal, descripcion,
               fecha_creacion, fecha_actualizacion, usuario_actualizacion, activo
        FROM dbo.configuracion_scheduler
        WHERE activo = 1
        ORDER BY id_configuracion DESC
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta)
        fila = cursor.fetchone()
        return _fila_a_dict(cursor, fila) if fila else None


def crear_configuracion_default(usuario):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute("UPDATE dbo.configuracion_scheduler SET activo = 0 WHERE activo = 1")
        cursor.execute(
            """
            INSERT INTO dbo.configuracion_scheduler
                (scheduler_activo, intervalo_revision_segundos, max_ejecuciones_concurrentes,
                 permitir_ejecucion_automatica, modo_mantenimiento, nombre_worker_principal,
                 descripcion, usuario_actualizacion, activo)
            OUTPUT INSERTED.id_configuracion
            VALUES (0, 60, 3, 0, 0, 'worker_default',
                    'Configuracion inicial segura. Scheduler apagado por defecto.', ?, 1)
            """,
            usuario,
        )
        id_configuracion = cursor.fetchone()[0]
        conexion.commit()
        return id_configuracion


def actualizar_configuracion(id_configuracion, datos, usuario):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            UPDATE dbo.configuracion_scheduler
            SET scheduler_activo = ?,
                intervalo_revision_segundos = ?,
                max_ejecuciones_concurrentes = ?,
                permitir_ejecucion_automatica = ?,
                modo_mantenimiento = ?,
                nombre_worker_principal = ?,
                descripcion = ?,
                usuario_actualizacion = ?,
                fecha_actualizacion = SYSDATETIME()
            WHERE id_configuracion = ? AND activo = 1
            """,
            1 if datos["scheduler_activo"] else 0,
            datos["intervalo_revision_segundos"],
            datos["max_ejecuciones_concurrentes"],
            1 if datos["permitir_ejecucion_automatica"] else 0,
            1 if datos["modo_mantenimiento"] else 0,
            datos.get("nombre_worker_principal"),
            datos.get("descripcion"),
            usuario,
            id_configuracion,
        )
        conexion.commit()
