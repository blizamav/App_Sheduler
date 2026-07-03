from app.database.conexion import obtener_conexion


def registrar_evidencia_ejecucion(registro):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT id_evidencia
            FROM dbo.evidencias_ejecucion
            WHERE id_ejecucion = ?
            """,
            registro["id_ejecucion"],
        )
        fila = cursor.fetchone()
        if fila:
            id_evidencia = fila[0]
            cursor.execute(
                """
                UPDATE dbo.evidencias_ejecucion
                SET estado_evidencia = ?,
                    version_contrato = ?,
                    tipo_evidencia = ?,
                    titulo = ?,
                    asunto_sugerido = ?,
                    hash_evidencia = ?,
                    cantidad_campos_resumen = ?,
                    cantidad_adjuntos_declarados = ?,
                    cantidad_problemas = ?,
                    bloque_detectado = ?,
                    delimitador_inicio_detectado = ?,
                    delimitador_fin_detectado = ?,
                    error_validacion = ?
                WHERE id_evidencia = ?
                """,
                registro["estado_evidencia"],
                registro.get("version_contrato"),
                registro.get("tipo_evidencia"),
                registro.get("titulo"),
                registro.get("asunto_sugerido"),
                registro.get("hash_evidencia"),
                registro["cantidad_campos_resumen"],
                registro["cantidad_adjuntos_declarados"],
                registro["cantidad_problemas"],
                _bit(registro["bloque_detectado"]),
                _bit(registro["delimitador_inicio_detectado"]),
                _bit(registro["delimitador_fin_detectado"]),
                registro.get("error_validacion"),
                id_evidencia,
            )
        else:
            cursor.execute(
                """
                INSERT INTO dbo.evidencias_ejecucion (
                    id_ejecucion, estado_evidencia, version_contrato,
                    tipo_evidencia, titulo, asunto_sugerido, hash_evidencia,
                    cantidad_campos_resumen, cantidad_adjuntos_declarados,
                    cantidad_problemas, bloque_detectado,
                    delimitador_inicio_detectado, delimitador_fin_detectado,
                    error_validacion
                )
                OUTPUT INSERTED.id_evidencia
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                registro["id_ejecucion"],
                registro["estado_evidencia"],
                registro.get("version_contrato"),
                registro.get("tipo_evidencia"),
                registro.get("titulo"),
                registro.get("asunto_sugerido"),
                registro.get("hash_evidencia"),
                registro["cantidad_campos_resumen"],
                registro["cantidad_adjuntos_declarados"],
                registro["cantidad_problemas"],
                _bit(registro["bloque_detectado"]),
                _bit(registro["delimitador_inicio_detectado"]),
                _bit(registro["delimitador_fin_detectado"]),
                registro.get("error_validacion"),
            )
            id_evidencia = cursor.fetchone()[0]
        conexion.commit()
        return id_evidencia


def _bit(valor):
    return 1 if bool(valor) else 0
