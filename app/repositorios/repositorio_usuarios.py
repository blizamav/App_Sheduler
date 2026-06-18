from app.database.conexion import obtener_conexion


def _fila_a_dict(cursor, fila):
    columnas = [columna[0] for columna in cursor.description]
    return dict(zip(columnas, fila))


def obtener_usuario_por_usuario(usuario):
    consulta = """
        SELECT id_usuario, usuario, nombre_completo, email, password_hash,
               debe_cambiar_password, ultimo_login, intentos_fallidos,
               bloqueado, activo, fecha_creacion, fecha_actualizacion
        FROM dbo.usuarios
        WHERE usuario = ?
          AND ISNULL(eliminado_operativo, 0) = 0
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, usuario)
        fila = cursor.fetchone()
        return _fila_a_dict(cursor, fila) if fila else None


def obtener_usuario_por_id(id_usuario):
    consulta = """
        SELECT u.id_usuario, u.usuario, u.nombre_completo, u.email, u.activo,
               u.fecha_creacion, u.fecha_actualizacion, rol.id_rol, rol.codigo_rol,
               rol.nombre_rol
        FROM dbo.usuarios u
        OUTER APPLY (
            SELECT TOP 1 r.id_rol, r.codigo_rol, r.nombre_rol
            FROM dbo.usuarios_roles ur
            INNER JOIN dbo.roles r ON r.id_rol = ur.id_rol
            WHERE ur.id_usuario = u.id_usuario
              AND ur.activo = 1
              AND r.activo = 1
            ORDER BY ur.fecha_creacion DESC
        ) rol
        WHERE u.id_usuario = ?
          AND ISNULL(u.eliminado_operativo, 0) = 0
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, id_usuario)
        fila = cursor.fetchone()
        return _fila_a_dict(cursor, fila) if fila else None


def listar_usuarios(filtros=None):
    filtros = filtros or {}
    condiciones = []
    parametros = []

    estado = filtros.get("estado")
    if estado == "activo":
        condiciones.append("u.activo = 1")
    elif estado == "inactivo":
        condiciones.append("u.activo = 0")
    condiciones.append("ISNULL(u.eliminado_operativo, 0) = 0")

    rol = filtros.get("rol")
    if rol:
        condiciones.append("rol.codigo_rol = ?")
        parametros.append(rol)

    buscar = filtros.get("buscar")
    if buscar:
        condiciones.append("(u.usuario LIKE ? OR u.nombre_completo LIKE ? OR u.email LIKE ?)")
        patron = f"%{buscar}%"
        parametros.extend([patron, patron, patron])

    where = ""
    if condiciones:
        where = "WHERE " + " AND ".join(condiciones)

    consulta = """
        SELECT u.id_usuario, u.usuario, u.nombre_completo, u.email, u.activo,
               u.fecha_creacion, rol.codigo_rol, rol.nombre_rol
        FROM dbo.usuarios u
        OUTER APPLY (
            SELECT TOP 1 r.codigo_rol, r.nombre_rol
            FROM dbo.usuarios_roles ur
            INNER JOIN dbo.roles r ON r.id_rol = ur.id_rol
            WHERE ur.id_usuario = u.id_usuario
              AND ur.activo = 1
              AND r.activo = 1
            ORDER BY ur.fecha_creacion DESC
        ) rol
        {where}
        ORDER BY u.fecha_creacion DESC, u.usuario
    """.format(where=where)
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, *parametros)
        return [_fila_a_dict(cursor, fila) for fila in cursor.fetchall()]


def existe_usuario(usuario, excluir_id=None):
    consulta = "SELECT COUNT(1) FROM dbo.usuarios WHERE usuario = ? AND ISNULL(eliminado_operativo, 0) = 0"
    parametros = [usuario]
    if excluir_id:
        consulta += " AND id_usuario <> ?"
        parametros.append(excluir_id)

    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, *parametros)
        return cursor.fetchone()[0] > 0


def crear_usuario(datos):
    consulta_usuario = """
        INSERT INTO dbo.usuarios
            (usuario, nombre_completo, email, password_hash, usuario_creacion, activo)
        OUTPUT INSERTED.id_usuario
        VALUES (?, ?, ?, ?, ?, ?)
    """
    consulta_rol = """
        INSERT INTO dbo.usuarios_roles (id_usuario, id_rol, usuario_creacion, activo)
        VALUES (?, ?, ?, 1)
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            consulta_usuario,
            datos["usuario"],
            datos["nombre_completo"],
            datos.get("email"),
            datos["password_hash"],
            datos.get("usuario_accion"),
            datos.get("activo", 1),
        )
        id_usuario = cursor.fetchone()[0]
        cursor.execute(consulta_rol, id_usuario, datos["id_rol"], datos.get("usuario_accion"))
        conexion.commit()
        return id_usuario


def actualizar_usuario(id_usuario, datos):
    campos_password = ""
    parametros = [
        datos["nombre_completo"],
        datos.get("email"),
        datos.get("activo", 1),
        datos.get("usuario_accion"),
    ]

    if datos.get("password_hash"):
        campos_password = ", password_hash = ?"
        parametros.append(datos["password_hash"])

    parametros.append(id_usuario)

    consulta_usuario = f"""
        UPDATE dbo.usuarios
        SET nombre_completo = ?,
            email = ?,
            activo = ?,
            usuario_actualizacion = ?,
            fecha_actualizacion = SYSDATETIME()
            {campos_password}
        WHERE id_usuario = ?
    """

    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta_usuario, *parametros)
        cursor.execute(
            """
            UPDATE dbo.usuarios_roles
            SET activo = 0
            WHERE id_usuario = ? AND activo = 1 AND id_rol <> ?
            """,
            id_usuario,
            datos["id_rol"],
        )
        cursor.execute(
            """
            IF EXISTS (SELECT 1 FROM dbo.usuarios_roles WHERE id_usuario = ? AND id_rol = ?)
                UPDATE dbo.usuarios_roles
                SET activo = 1
                WHERE id_usuario = ? AND id_rol = ?
            ELSE
                INSERT INTO dbo.usuarios_roles (id_usuario, id_rol, usuario_creacion, activo)
                VALUES (?, ?, ?, 1)
            """,
            id_usuario,
            datos["id_rol"],
            id_usuario,
            datos["id_rol"],
            id_usuario,
            datos["id_rol"],
            datos.get("usuario_accion"),
        )
        conexion.commit()


def cambiar_estado_usuario(id_usuario, activo, usuario_accion):
    consulta = """
        UPDATE dbo.usuarios
        SET activo = ?,
            usuario_actualizacion = ?,
            fecha_actualizacion = SYSDATETIME()
        WHERE id_usuario = ?
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, activo, usuario_accion, id_usuario)
        conexion.commit()


def contar_historial_usuario(usuario):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT
                (SELECT COUNT(1) FROM dbo.ejecuciones WHERE usuario_ejecucion = ?) +
                (SELECT COUNT(1) FROM dbo.logs_tareas WHERE usuario_ejecucion = ?) +
                (SELECT COUNT(1) FROM dbo.logs_sistema WHERE usuario = ?)
            """,
            usuario,
            usuario,
            usuario,
        )
        return cursor.fetchone()[0]


def contar_administradores_activos(excluir_id=None):
    consulta = """
        SELECT COUNT(DISTINCT u.id_usuario)
        FROM dbo.usuarios u
        INNER JOIN dbo.usuarios_roles ur ON ur.id_usuario = u.id_usuario AND ur.activo = 1
        INNER JOIN dbo.roles r ON r.id_rol = ur.id_rol AND r.activo = 1
        WHERE u.activo = 1
          AND ISNULL(u.eliminado_operativo, 0) = 0
          AND r.codigo_rol = 'ADMIN'
    """
    parametros = []
    if excluir_id:
        consulta += " AND u.id_usuario <> ?"
        parametros.append(excluir_id)
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, *parametros)
        return cursor.fetchone()[0]


def asegurar_snapshots_usuario(usuario):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            UPDATE dbo.ejecuciones
            SET usuario_ejecucion_snapshot = COALESCE(usuario_ejecucion_snapshot, usuario_ejecucion)
            WHERE usuario_ejecucion = ?
            """,
            usuario,
        )
        conexion.commit()


def marcar_usuario_eliminado_operativo(id_usuario, usuario_accion, motivo=None):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            UPDATE dbo.usuarios_roles
            SET activo = 0
            WHERE id_usuario = ? AND activo = 1
            """,
            id_usuario,
        )
        cursor.execute(
            """
            UPDATE dbo.usuarios
            SET activo = 0,
                bloqueado = 1,
                eliminado_operativo = 1,
                fecha_eliminado_operativo = COALESCE(fecha_eliminado_operativo, SYSDATETIME()),
                usuario_eliminado_operativo = ?,
                motivo_eliminado_operativo = COALESCE(?, motivo_eliminado_operativo),
                usuario_actualizacion = ?,
                fecha_actualizacion = SYSDATETIME()
            WHERE id_usuario = ?
            """,
            usuario_accion,
            motivo,
            usuario_accion,
            id_usuario,
        )
        conexion.commit()


def eliminar_usuario_fisico(id_usuario):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM dbo.usuarios_roles WHERE id_usuario = ?", id_usuario)
        cursor.execute("DELETE FROM dbo.usuarios WHERE id_usuario = ?", id_usuario)
        conexion.commit()


def registrar_login_exitoso(id_usuario):
    consulta = """
        UPDATE dbo.usuarios
        SET ultimo_login = SYSDATETIME(),
            intentos_fallidos = 0,
            fecha_actualizacion = SYSDATETIME()
        WHERE id_usuario = ?
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, id_usuario)
        conexion.commit()


def registrar_login_fallido(usuario):
    consulta = """
        UPDATE dbo.usuarios
        SET intentos_fallidos = intentos_fallidos + 1,
            fecha_actualizacion = SYSDATETIME()
        WHERE usuario = ?
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, usuario)
        conexion.commit()
