from app.database.conexion import obtener_conexion


def insertar_log_sistema(datos):
    """Inserta un evento en logs_sistema."""
    consulta = """
        INSERT INTO dbo.logs_sistema
            (usuario, accion, modulo, descripcion, valor_anterior, valor_nuevo, ip, user_agent, nivel)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            consulta,
            datos.get("usuario"),
            datos["accion"],
            datos["modulo"],
            datos["descripcion"],
            datos.get("valor_anterior"),
            datos.get("valor_nuevo"),
            datos.get("ip"),
            datos.get("user_agent"),
            datos.get("nivel", "INFO"),
        )
        conexion.commit()
