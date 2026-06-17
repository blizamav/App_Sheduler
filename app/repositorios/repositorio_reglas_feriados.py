from app.database.conexion import obtener_conexion


def _fila_a_dict(cursor, fila):
    columnas = [columna[0] for columna in cursor.description]
    return dict(zip(columnas, fila))


def obtener_regla_irrenunciable(pais, mes, dia):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT TOP 1 id_regla, pais, mes, dia, nombre_referencia,
                   irrenunciable, activo, observacion
            FROM dbo.reglas_feriados_irrenunciables
            WHERE pais = ?
              AND mes = ?
              AND dia = ?
              AND activo = 1
            ORDER BY id_regla DESC
            """,
            pais,
            mes,
            dia,
        )
        fila = cursor.fetchone()
        return _fila_a_dict(cursor, fila) if fila else None


def listar_reglas_irrenunciables(pais=None):
    consulta = """
        SELECT id_regla, pais, mes, dia, nombre_referencia,
               irrenunciable, activo, observacion
        FROM dbo.reglas_feriados_irrenunciables
    """
    parametros = []
    if pais:
        consulta += " WHERE pais = ?"
        parametros.append(pais)
    consulta += " ORDER BY pais, mes, dia"

    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, *parametros)
        return [_fila_a_dict(cursor, fila) for fila in cursor.fetchall()]
