from app.database.conexion import obtener_conexion


def obtener_roles_usuario(id_usuario):
    consulta = """
        SELECT r.codigo_rol
        FROM dbo.usuarios_roles ur
        INNER JOIN dbo.roles r ON r.id_rol = ur.id_rol
        WHERE ur.id_usuario = ?
          AND ur.activo = 1
          AND r.activo = 1
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, id_usuario)
        return [fila[0] for fila in cursor.fetchall()]


def obtener_permisos_usuario(id_usuario):
    consulta = """
        SELECT DISTINCT p.codigo_permiso
        FROM dbo.usuarios_roles ur
        INNER JOIN dbo.roles r ON r.id_rol = ur.id_rol
        INNER JOIN dbo.roles_permisos rp ON rp.id_rol = r.id_rol
        INNER JOIN dbo.permisos p ON p.id_permiso = rp.id_permiso
        WHERE ur.id_usuario = ?
          AND ur.activo = 1
          AND r.activo = 1
          AND rp.activo = 1
          AND rp.permitido = 1
          AND p.activo = 1
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, id_usuario)
        return [fila[0] for fila in cursor.fetchall()]
