from app.database.conexion import obtener_conexion


CONFIG_MANTENEDORES = {
    "clientes": {
        "tabla": "dbo.clientes",
        "id": "id_cliente",
        "nombre": "nombre_cliente",
        "campo_tarea": "id_cliente",
    },
    "categorias": {
        "tabla": "dbo.categorias",
        "id": "id_categoria",
        "nombre": "nombre_categoria",
        "campo_tarea": "id_categoria",
    },
    "tipos": {
        "tabla": "dbo.tipos",
        "id": "id_tipo",
        "nombre": "nombre_tipo",
        "campo_tarea": "id_tipo",
    },
}


def _config(entidad):
    return CONFIG_MANTENEDORES[entidad]


def _fila_a_dict(cursor, fila):
    columnas = [columna[0] for columna in cursor.description]
    return dict(zip(columnas, fila))


def listar(entidad, filtros=None):
    cfg = _config(entidad)
    filtros = filtros or {}
    condiciones = []
    parametros = []

    estado = filtros.get("estado")
    if estado == "activo":
        condiciones.append("m.activo = 1")
    elif estado == "inactivo":
        condiciones.append("m.activo = 0")

    buscar = filtros.get("buscar")
    if buscar:
        condiciones.append(f"(m.{cfg['nombre']} LIKE ? OR m.descripcion LIKE ?)")
        patron = f"%{buscar}%"
        parametros.extend([patron, patron])

    where = ""
    if condiciones:
        where = "WHERE " + " AND ".join(condiciones)

    consulta = f"""
        SELECT m.{cfg['id']} AS id,
               m.{cfg['nombre']} AS nombre,
               m.nombre_normalizado,
               m.descripcion,
               m.activo,
               m.fecha_creacion,
               m.fecha_actualizacion,
               (
                   SELECT COUNT(1)
                   FROM dbo.tareas t
                   WHERE t.{cfg['campo_tarea']} = m.{cfg['id']}
               ) AS dependencias_tareas
        FROM {cfg['tabla']} m
        {where}
        ORDER BY m.fecha_creacion DESC, m.{cfg['nombre']}
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, *parametros)
        return [_fila_a_dict(cursor, fila) for fila in cursor.fetchall()]


def obtener_por_id(entidad, id_registro):
    cfg = _config(entidad)
    consulta = f"""
        SELECT {cfg['id']} AS id,
               {cfg['nombre']} AS nombre,
               nombre_normalizado,
               descripcion,
               activo,
               fecha_creacion,
               fecha_actualizacion
        FROM {cfg['tabla']}
        WHERE {cfg['id']} = ?
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, id_registro)
        fila = cursor.fetchone()
        return _fila_a_dict(cursor, fila) if fila else None


def existe_nombre_normalizado(entidad, nombre_normalizado, excluir_id=None):
    cfg = _config(entidad)
    consulta = f"SELECT COUNT(1) FROM {cfg['tabla']} WHERE nombre_normalizado = ?"
    parametros = [nombre_normalizado]
    if excluir_id:
        consulta += f" AND {cfg['id']} <> ?"
        parametros.append(excluir_id)

    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, *parametros)
        return cursor.fetchone()[0] > 0


def crear(entidad, datos):
    cfg = _config(entidad)
    consulta = f"""
        INSERT INTO {cfg['tabla']}
            ({cfg['nombre']}, nombre_normalizado, descripcion, usuario_creacion, activo)
        OUTPUT INSERTED.{cfg['id']}
        VALUES (?, ?, ?, ?, 1)
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            consulta,
            datos["nombre"],
            datos["nombre_normalizado"],
            datos.get("descripcion"),
            datos.get("usuario_accion"),
        )
        id_registro = cursor.fetchone()[0]
        conexion.commit()
        return id_registro


def actualizar(entidad, id_registro, datos):
    cfg = _config(entidad)
    consulta = f"""
        UPDATE {cfg['tabla']}
        SET {cfg['nombre']} = ?,
            nombre_normalizado = ?,
            descripcion = ?,
            usuario_actualizacion = ?,
            fecha_actualizacion = SYSDATETIME()
        WHERE {cfg['id']} = ?
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            consulta,
            datos["nombre"],
            datos["nombre_normalizado"],
            datos.get("descripcion"),
            datos.get("usuario_accion"),
            id_registro,
        )
        conexion.commit()


def cambiar_estado(entidad, id_registro, activo, usuario_accion):
    cfg = _config(entidad)
    consulta = f"""
        UPDATE {cfg['tabla']}
        SET activo = ?,
            usuario_actualizacion = ?,
            fecha_actualizacion = SYSDATETIME()
        WHERE {cfg['id']} = ?
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, 1 if activo else 0, usuario_accion, id_registro)
        conexion.commit()


def contar_dependencias(entidad, id_registro):
    cfg = _config(entidad)
    consulta = f"SELECT COUNT(1) FROM dbo.tareas WHERE {cfg['campo_tarea']} = ?"
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, id_registro)
        return cursor.fetchone()[0]


def eliminar(entidad, id_registro):
    cfg = _config(entidad)
    consulta = f"DELETE FROM {cfg['tabla']} WHERE {cfg['id']} = ?"
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, id_registro)
        conexion.commit()
