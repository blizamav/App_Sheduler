from app.database.conexion import obtener_conexion


def _fila_a_dict(cursor, fila):
    columnas = [columna[0] for columna in cursor.description]
    return dict(zip(columnas, fila))


def listar_roles_activos():
    consulta = """
        SELECT id_rol, codigo_rol, nombre_rol, descripcion
        FROM dbo.roles
        WHERE activo = 1
        ORDER BY
            CASE codigo_rol
                WHEN 'SUPER_ADMIN' THEN 1
                WHEN 'ADMIN' THEN 2
                WHEN 'TI' THEN 3
                WHEN 'TERCERO' THEN 4
                ELSE 9
            END,
            nombre_rol
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta)
        return [_fila_a_dict(cursor, fila) for fila in cursor.fetchall()]


def obtener_rol_por_id(id_rol):
    consulta = """
        SELECT id_rol, codigo_rol, nombre_rol
        FROM dbo.roles
        WHERE id_rol = ? AND activo = 1
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, id_rol)
        fila = cursor.fetchone()
        return _fila_a_dict(cursor, fila) if fila else None
