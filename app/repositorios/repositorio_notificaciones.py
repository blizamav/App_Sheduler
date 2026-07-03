from app.database.conexion import obtener_conexion


def _fila_a_dict(cursor, fila):
    columnas = [columna[0] for columna in cursor.description]
    return dict(zip(columnas, fila))


def obtener_tarea_notificaciones(id_tarea):
    consulta = """
        SELECT id_tarea, nombre_tarea, activo, ISNULL(eliminado_operativo, 0) AS eliminado_operativo
        FROM dbo.tareas
        WHERE id_tarea = ?
          AND ISNULL(eliminado_operativo, 0) = 0
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, id_tarea)
        fila = cursor.fetchone()
        return _fila_a_dict(cursor, fila) if fila else None


def obtener_configuracion_notificacion(id_tarea):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        config = _obtener_configuracion_activa_cursor(cursor, id_tarea)
        if not config:
            return None
        config["destinatarios"] = _listar_destinatarios_cursor(cursor, config["id_config_notificacion"])
        return config


def guardar_configuracion_notificacion(id_tarea, datos_config, destinatarios):
    with obtener_conexion() as conexion:
        try:
            cursor = conexion.cursor()
            config_actual = _obtener_configuracion_activa_cursor(cursor, id_tarea)
            if config_actual:
                id_config = config_actual["id_config_notificacion"]
                cursor.execute(
                    """
                    UPDATE dbo.notificaciones_config_tarea
                    SET enviar_evidencia = ?,
                        plantilla_evidencia = ?,
                        asunto_personalizado = ?,
                        usar_asunto_sugerido_script = ?,
                        adjuntar_archivos_declarados = ?,
                        adjuntar_log_tecnico = ?,
                        alerta_error_activa = ?,
                        usar_alerta_global = ?,
                        actualizado_en = SYSDATETIME()
                    WHERE id_config_notificacion = ?
                      AND activo = 1
                    """,
                    _bit(datos_config["enviar_evidencia"]),
                    datos_config["plantilla_evidencia"],
                    datos_config.get("asunto_personalizado"),
                    _bit(datos_config["usar_asunto_sugerido_script"]),
                    _bit(datos_config["adjuntar_archivos_declarados"]),
                    _bit(datos_config["adjuntar_log_tecnico"]),
                    _bit(datos_config["alerta_error_activa"]),
                    _bit(datos_config["usar_alerta_global"]),
                    id_config,
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO dbo.notificaciones_config_tarea
                        (id_tarea, enviar_evidencia, plantilla_evidencia, asunto_personalizado,
                         usar_asunto_sugerido_script, adjuntar_archivos_declarados,
                         adjuntar_log_tecnico, alerta_error_activa, usar_alerta_global, activo)
                    OUTPUT INSERTED.id_config_notificacion
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                    """,
                    id_tarea,
                    _bit(datos_config["enviar_evidencia"]),
                    datos_config["plantilla_evidencia"],
                    datos_config.get("asunto_personalizado"),
                    _bit(datos_config["usar_asunto_sugerido_script"]),
                    _bit(datos_config["adjuntar_archivos_declarados"]),
                    _bit(datos_config["adjuntar_log_tecnico"]),
                    _bit(datos_config["alerta_error_activa"]),
                    _bit(datos_config["usar_alerta_global"]),
                )
                id_config = cursor.fetchone()[0]

            _asegurar_config_unica_activa_cursor(cursor, id_tarea, id_config)
            _reemplazar_destinatarios_cursor(cursor, id_config, destinatarios)
            conexion.commit()
            return id_config
        except Exception:
            conexion.rollback()
            raise


def desactivar_configuracion_notificacion(id_tarea):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            UPDATE dbo.notificaciones_config_tarea
            SET activo = 0,
                actualizado_en = SYSDATETIME()
            WHERE id_tarea = ?
              AND activo = 1
            """,
            id_tarea,
        )
        conexion.commit()
        return cursor.rowcount


def listar_destinatarios_config(id_config_notificacion):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        return _listar_destinatarios_cursor(cursor, id_config_notificacion)


def reemplazar_destinatarios_config(id_config_notificacion, destinatarios):
    with obtener_conexion() as conexion:
        try:
            cursor = conexion.cursor()
            _reemplazar_destinatarios_cursor(cursor, id_config_notificacion, destinatarios)
            conexion.commit()
        except Exception:
            conexion.rollback()
            raise


def _obtener_configuracion_activa_cursor(cursor, id_tarea):
    cursor.execute(
        """
        SELECT TOP 1 id_config_notificacion, id_tarea, enviar_evidencia, plantilla_evidencia,
               asunto_personalizado, usar_asunto_sugerido_script, adjuntar_archivos_declarados,
               adjuntar_log_tecnico, alerta_error_activa, usar_alerta_global, activo,
               creado_en, actualizado_en
        FROM dbo.notificaciones_config_tarea
        WHERE id_tarea = ?
          AND activo = 1
        ORDER BY id_config_notificacion DESC
        """,
        id_tarea,
    )
    fila = cursor.fetchone()
    return _fila_a_dict(cursor, fila) if fila else None


def _listar_destinatarios_cursor(cursor, id_config_notificacion):
    cursor.execute(
        """
        SELECT id_destinatario, id_config_notificacion, tipo_destinatario, canal,
               email, nombre, activo, creado_en
        FROM dbo.notificaciones_destinatarios
        WHERE id_config_notificacion = ?
          AND activo = 1
        ORDER BY tipo_destinatario, canal, email
        """,
        id_config_notificacion,
    )
    return [_fila_a_dict(cursor, fila) for fila in cursor.fetchall()]


def _asegurar_config_unica_activa_cursor(cursor, id_tarea, id_config_notificacion):
    cursor.execute(
        """
        UPDATE dbo.notificaciones_config_tarea
        SET activo = 0,
            actualizado_en = SYSDATETIME()
        WHERE id_tarea = ?
          AND activo = 1
          AND id_config_notificacion <> ?
        """,
        id_tarea,
        id_config_notificacion,
    )


def _reemplazar_destinatarios_cursor(cursor, id_config_notificacion, destinatarios):
    cursor.execute(
        """
        UPDATE dbo.notificaciones_destinatarios
        SET activo = 0
        WHERE id_config_notificacion = ?
          AND activo = 1
        """,
        id_config_notificacion,
    )
    for destinatario in destinatarios:
        cursor.execute(
            """
            INSERT INTO dbo.notificaciones_destinatarios
                (id_config_notificacion, tipo_destinatario, canal, email, nombre, activo)
            VALUES (?, ?, ?, ?, ?, 1)
            """,
            id_config_notificacion,
            destinatario["tipo_destinatario"],
            destinatario["canal"],
            destinatario["email"],
            destinatario.get("nombre"),
        )


def _bit(valor):
    return 1 if bool(valor) else 0
