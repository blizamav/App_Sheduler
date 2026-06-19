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


def _existe_tabla(cursor, tabla):
    cursor.execute("SELECT CASE WHEN OBJECT_ID(?) IS NULL THEN 0 ELSE 1 END", tabla)
    return bool(cursor.fetchone()[0])


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
    condiciones.append("ISNULL(m.eliminado_operativo, 0) = 0")

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
          AND ISNULL(eliminado_operativo, 0) = 0
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, id_registro)
        fila = cursor.fetchone()
        return _fila_a_dict(cursor, fila) if fila else None


def existe_nombre_normalizado(entidad, nombre_normalizado, excluir_id=None):
    cfg = _config(entidad)
    consulta = f"SELECT COUNT(1) FROM {cfg['tabla']} WHERE nombre_normalizado = ? AND ISNULL(eliminado_operativo, 0) = 0"
    parametros = [nombre_normalizado]
    if excluir_id:
        consulta += f" AND {cfg['id']} <> ?"
        parametros.append(excluir_id)

    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, *parametros)
        return cursor.fetchone()[0] > 0


def buscar_duplicado_nombre_normalizado(entidad, nombre_normalizado, excluir_id=None):
    cfg = _config(entidad)
    consulta = f"""
        SELECT TOP 1 {cfg['id']} AS id,
               {cfg['nombre']} AS nombre,
               nombre_normalizado,
               activo,
               ISNULL(eliminado_operativo, 0) AS eliminado_operativo
        FROM {cfg['tabla']}
        WHERE nombre_normalizado = ?
    """
    parametros = [nombre_normalizado]
    if excluir_id:
        consulta += f" AND {cfg['id']} <> ?"
        parametros.append(excluir_id)
    consulta += f"""
        ORDER BY CASE
            WHEN ISNULL(eliminado_operativo, 0) = 0 AND activo = 1 THEN 0
            WHEN ISNULL(eliminado_operativo, 0) = 0 THEN 1
            ELSE 2
        END,
        {cfg['id']} DESC
    """

    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, *parametros)
        fila = cursor.fetchone()
        return _fila_a_dict(cursor, fila) if fila else None


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


def contar_tareas_activas(entidad, id_registro):
    cfg = _config(entidad)
    consulta = f"""
        SELECT COUNT(1)
        FROM dbo.tareas
        WHERE {cfg['campo_tarea']} = ?
          AND activo = 1
          AND ISNULL(eliminado_operativo, 0) = 0
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, id_registro)
        return cursor.fetchone()[0]


def asegurar_snapshots_mantenedor(entidad, id_registro):
    cfg = _config(entidad)
    filtro = f"t.{cfg['campo_tarea']} = ?"
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            f"""
            UPDATE e
            SET id_tarea_original = COALESCE(e.id_tarea_original, e.id_tarea),
                nombre_tarea_snapshot = COALESCE(e.nombre_tarea_snapshot, t.nombre_tarea),
                cliente_snapshot = COALESCE(e.cliente_snapshot, c.nombre_cliente),
                categoria_snapshot = COALESCE(e.categoria_snapshot, ca.nombre_categoria),
                tipo_snapshot = COALESCE(e.tipo_snapshot, ti.nombre_tipo),
                nombre_script_snapshot = COALESCE(e.nombre_script_snapshot, s.nombre_script),
                nombre_archivo_snapshot = COALESCE(e.nombre_archivo_snapshot, v.nombre_archivo),
                version_script_snapshot = COALESCE(e.version_script_snapshot, CONVERT(varchar(10), v.numero_version)),
                usuario_ejecucion_snapshot = COALESCE(e.usuario_ejecucion_snapshot, e.usuario_ejecucion)
            FROM dbo.ejecuciones e
            LEFT JOIN dbo.tareas t ON t.id_tarea = e.id_tarea
            LEFT JOIN dbo.clientes c ON c.id_cliente = t.id_cliente
            LEFT JOIN dbo.categorias ca ON ca.id_categoria = t.id_categoria
            LEFT JOIN dbo.tipos ti ON ti.id_tipo = t.id_tipo
            LEFT JOIN dbo.scripts s ON s.id_script = e.id_script
            LEFT JOIN dbo.scripts_versiones v ON v.id_version = e.id_version
            WHERE {filtro}
            """,
            id_registro,
        )
        if _existe_tabla(cursor, "dbo.scheduler_eventos"):
            cursor.execute(
                f"""
                UPDATE se
                SET id_tarea_original = COALESCE(se.id_tarea_original, se.id_tarea),
                    nombre_tarea_snapshot = COALESCE(se.nombre_tarea_snapshot, se.nombre_tarea, t.nombre_tarea),
                    cliente_snapshot = COALESCE(se.cliente_snapshot, c.nombre_cliente),
                    categoria_snapshot = COALESCE(se.categoria_snapshot, ca.nombre_categoria),
                    tipo_snapshot = COALESCE(se.tipo_snapshot, ti.nombre_tipo)
                FROM dbo.scheduler_eventos se
                LEFT JOIN dbo.tareas t ON t.id_tarea = se.id_tarea
                LEFT JOIN dbo.clientes c ON c.id_cliente = t.id_cliente
                LEFT JOIN dbo.categorias ca ON ca.id_categoria = t.id_categoria
                LEFT JOIN dbo.tipos ti ON ti.id_tipo = t.id_tipo
                WHERE {filtro}
                """,
                id_registro,
            )
        conexion.commit()


def marcar_eliminado_operativo(entidad, id_registro, usuario_accion, motivo=None):
    cfg = _config(entidad)
    consulta = f"""
        UPDATE {cfg['tabla']}
        SET activo = 0,
            eliminado_operativo = 1,
            fecha_eliminado_operativo = COALESCE(fecha_eliminado_operativo, SYSDATETIME()),
            usuario_eliminado_operativo = ?,
            motivo_eliminado_operativo = COALESCE(?, motivo_eliminado_operativo),
            usuario_actualizacion = ?,
            fecha_actualizacion = SYSDATETIME()
        WHERE {cfg['id']} = ?
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, usuario_accion, motivo, usuario_accion, id_registro)
        conexion.commit()


def eliminar(entidad, id_registro):
    cfg = _config(entidad)
    consulta = f"DELETE FROM {cfg['tabla']} WHERE {cfg['id']} = ?"
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, id_registro)
        conexion.commit()
