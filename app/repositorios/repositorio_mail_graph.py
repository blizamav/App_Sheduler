from app.database.conexion import obtener_conexion


def _fila_a_dict(cursor, fila):
    columnas = [columna[0] for columna in cursor.description]
    return dict(zip(columnas, fila))


def obtener_configuracion_mail_graph():
    consulta = """
        SELECT TOP 1 id_config_mail, activo, tenant_id, client_id, graph_scope,
               send_mail_user, save_to_sent_items, alertas_destinatarios_default,
               client_secret_origen, fecha_creacion, fecha_actualizacion,
               usuario_actualizacion
        FROM dbo.configuracion_mail_graph
        ORDER BY id_config_mail DESC
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta)
        fila = cursor.fetchone()
        return _fila_a_dict(cursor, fila) if fila else None


def crear_configuracion_mail_graph_default(usuario):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            INSERT INTO dbo.configuracion_mail_graph (
                activo, graph_scope, save_to_sent_items,
                alertas_destinatarios_default, client_secret_origen,
                usuario_actualizacion
            )
            OUTPUT INSERTED.id_config_mail
            VALUES (0, N'https://graph.microsoft.com/.default', 1, NULL, N'ENV', ?)
            """,
            usuario,
        )
        id_config = cursor.fetchone()[0]
        conexion.commit()
        return id_config


def guardar_configuracion_mail_graph(id_config_mail, datos, usuario):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            UPDATE dbo.configuracion_mail_graph
            SET activo = ?,
                tenant_id = ?,
                client_id = ?,
                graph_scope = ?,
                send_mail_user = ?,
                save_to_sent_items = ?,
                alertas_destinatarios_default = ?,
                client_secret_origen = N'ENV',
                fecha_actualizacion = SYSDATETIME(),
                usuario_actualizacion = ?
            WHERE id_config_mail = ?
            """,
            1 if datos["activo"] else 0,
            datos.get("tenant_id"),
            datos.get("client_id"),
            datos["graph_scope"],
            datos.get("send_mail_user"),
            1 if datos["save_to_sent_items"] else 0,
            datos.get("alertas_destinatarios_default"),
            usuario,
            id_config_mail,
        )
        conexion.commit()
        return id_config_mail
