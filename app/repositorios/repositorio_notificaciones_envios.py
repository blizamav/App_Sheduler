from app.database.conexion import obtener_conexion


TIPO_EVIDENCIA_CLIENTE = "EVIDENCIA_CLIENTE"
TIPO_ALERTA_INTERNA = "ALERTA_INTERNA"


def existe_envio_exitoso_evidencia(id_ejecucion):
    return existe_envio_exitoso(id_ejecucion, TIPO_EVIDENCIA_CLIENTE)


def existe_envio_exitoso_alerta(id_ejecucion):
    return existe_envio_exitoso(id_ejecucion, TIPO_ALERTA_INTERNA)


def existe_envio_exitoso(id_ejecucion, tipo_envio):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT TOP 1 id_envio
            FROM dbo.notificaciones_envios
            WHERE id_ejecucion = ?
              AND tipo_envio = ?
              AND estado_envio = N'ENVIADO'
            """,
            id_ejecucion,
            tipo_envio,
        )
        return cursor.fetchone() is not None


def registrar_envio_evidencia(registro):
    return registrar_envio(registro, TIPO_EVIDENCIA_CLIENTE)


def registrar_envio_alerta(registro):
    return registrar_envio(registro, TIPO_ALERTA_INTERNA)


def registrar_envio(registro, tipo_envio):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            INSERT INTO dbo.notificaciones_envios (
                id_ejecucion,
                id_evidencia,
                tipo_envio,
                estado_envio,
                asunto,
                destinatarios_to,
                destinatarios_cc,
                destinatarios_bcc,
                graph_status_code,
                graph_request_id,
                error_controlado,
                fecha_envio
            )
            OUTPUT INSERTED.id_envio
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CASE WHEN ? = N'ENVIADO' THEN SYSDATETIME() ELSE NULL END)
            """,
            registro["id_ejecucion"],
            registro.get("id_evidencia"),
            tipo_envio,
            registro["estado_envio"],
            registro.get("asunto"),
            registro.get("destinatarios_to"),
            registro.get("destinatarios_cc"),
            registro.get("destinatarios_bcc"),
            registro.get("graph_status_code"),
            registro.get("graph_request_id"),
            registro.get("error_controlado"),
            registro["estado_envio"],
        )
        id_envio = cursor.fetchone()[0]
        conexion.commit()
        return id_envio
