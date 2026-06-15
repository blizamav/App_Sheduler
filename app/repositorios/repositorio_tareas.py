from app.database.conexion import obtener_conexion


def _fila_a_dict(cursor, fila):
    columnas = [columna[0] for columna in cursor.description]
    return dict(zip(columnas, fila))


def listar_catalogo(tabla, id_columna, nombre_columna):
    consulta = f"""
        SELECT {id_columna} AS id, {nombre_columna} AS nombre
        FROM {tabla}
        WHERE activo = 1
        ORDER BY {nombre_columna}
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta)
        return [_fila_a_dict(cursor, fila) for fila in cursor.fetchall()]


def listar_tareas(filtros=None):
    filtros = filtros or {}
    condiciones = []
    parametros = []

    if filtros.get("estado") == "activo":
        condiciones.append("t.activo = 1")
    elif filtros.get("estado") == "inactivo":
        condiciones.append("t.activo = 0")

    for clave, columna in (
        ("id_cliente", "t.id_cliente"),
        ("id_categoria", "t.id_categoria"),
        ("id_tipo", "t.id_tipo"),
    ):
        if filtros.get(clave):
            condiciones.append(f"{columna} = ?")
            parametros.append(filtros[clave])

    if filtros.get("tipo_programacion"):
        condiciones.append("p.tipo_programacion = ?")
        parametros.append(filtros["tipo_programacion"])

    if filtros.get("buscar"):
        condiciones.append("(t.nombre_tarea LIKE ? OR t.descripcion LIKE ?)")
        patron = f"%{filtros['buscar']}%"
        parametros.extend([patron, patron])

    where = "WHERE " + " AND ".join(condiciones) if condiciones else ""

    consulta = f"""
        SELECT t.id_tarea,
               t.nombre_tarea,
               t.descripcion,
               t.observacion_tecnica,
               t.id_cliente,
               c.nombre_cliente,
               t.id_categoria,
               ca.nombre_categoria,
               t.id_tipo,
               ti.nombre_tipo,
               t.estado_tarea,
               t.activo,
               t.fecha_creacion,
               t.fecha_actualizacion,
               p.id_programacion,
               p.tipo_programacion,
               p.modo_ejecucion_dia,
               p.hora_ejecucion,
               p.dias_semana,
               p.dia_mes,
               p.fecha_especifica,
               p.intervalo_minutos,
               p.hora_inicio AS hora_inicio_intervalo,
               p.hora_termino AS hora_fin_intervalo,
               p.ejecutar_en_feriados
        FROM dbo.tareas t
        INNER JOIN dbo.clientes c ON c.id_cliente = t.id_cliente
        INNER JOIN dbo.categorias ca ON ca.id_categoria = t.id_categoria
        INNER JOIN dbo.tipos ti ON ti.id_tipo = t.id_tipo
        LEFT JOIN dbo.programaciones p ON p.id_tarea = t.id_tarea AND p.activo = 1
        {where}
        ORDER BY t.fecha_creacion DESC, t.nombre_tarea
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, *parametros)
        return [_fila_a_dict(cursor, fila) for fila in cursor.fetchall()]


def obtener_tarea(id_tarea):
    consulta = """
        SELECT t.id_tarea,
               t.nombre_tarea,
               t.descripcion,
               t.observacion_tecnica,
               t.id_cliente,
               t.id_categoria,
               t.id_tipo,
               t.estado_tarea,
               t.activo,
               p.id_programacion,
               p.tipo_programacion,
               p.modo_ejecucion_dia,
               p.hora_ejecucion,
               p.dias_semana,
               p.dia_mes,
               p.fecha_especifica,
               p.intervalo_minutos,
               p.hora_inicio AS hora_inicio_intervalo,
               p.hora_termino AS hora_fin_intervalo,
               p.ejecutar_en_feriados
        FROM dbo.tareas t
        LEFT JOIN dbo.programaciones p ON p.id_tarea = t.id_tarea AND p.activo = 1
        WHERE t.id_tarea = ?
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, id_tarea)
        fila = cursor.fetchone()
        return _fila_a_dict(cursor, fila) if fila else None


def existe_tarea_duplicada(nombre_tarea, id_cliente, id_categoria, id_tipo, excluir_id=None):
    consulta = """
        SELECT COUNT(1)
        FROM dbo.tareas
        WHERE UPPER(LTRIM(RTRIM(nombre_tarea))) = UPPER(LTRIM(RTRIM(?)))
          AND id_cliente = ?
          AND id_categoria = ?
          AND id_tipo = ?
    """
    parametros = [nombre_tarea, id_cliente, id_categoria, id_tipo]
    if excluir_id:
        consulta += " AND id_tarea <> ?"
        parametros.append(excluir_id)

    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, *parametros)
        return cursor.fetchone()[0] > 0


def crear_tarea(datos_tarea, datos_programacion):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            INSERT INTO dbo.tareas
                (nombre_tarea, descripcion, observacion_tecnica, id_cliente, id_categoria, id_tipo,
                 tipo_tarea, estado_tarea, permite_ejecucion_manual, usuario_creacion, activo)
            OUTPUT INSERTED.id_tarea
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            datos_tarea["nombre_tarea"],
            datos_tarea.get("descripcion"),
            datos_tarea.get("observacion_tecnica"),
            datos_tarea["id_cliente"],
            datos_tarea["id_categoria"],
            datos_tarea["id_tipo"],
            datos_tarea["tipo_tarea"],
            datos_tarea["estado_tarea"],
            datos_tarea["permite_ejecucion_manual"],
            datos_tarea.get("usuario_accion"),
            datos_tarea["activo"],
        )
        id_tarea = cursor.fetchone()[0]
        _insertar_programacion(cursor, id_tarea, datos_programacion, datos_tarea.get("usuario_accion"))
        conexion.commit()
        return id_tarea


def actualizar_tarea(id_tarea, datos_tarea, datos_programacion):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            UPDATE dbo.tareas
            SET nombre_tarea = ?,
                descripcion = ?,
                observacion_tecnica = ?,
                id_cliente = ?,
                id_categoria = ?,
                id_tipo = ?,
                tipo_tarea = ?,
                estado_tarea = ?,
                permite_ejecucion_manual = ?,
                usuario_actualizacion = ?,
                fecha_actualizacion = SYSDATETIME(),
                activo = ?
            WHERE id_tarea = ?
            """,
            datos_tarea["nombre_tarea"],
            datos_tarea.get("descripcion"),
            datos_tarea.get("observacion_tecnica"),
            datos_tarea["id_cliente"],
            datos_tarea["id_categoria"],
            datos_tarea["id_tipo"],
            datos_tarea["tipo_tarea"],
            datos_tarea["estado_tarea"],
            datos_tarea["permite_ejecucion_manual"],
            datos_tarea.get("usuario_accion"),
            datos_tarea["activo"],
            id_tarea,
        )
        cursor.execute(
            """
            UPDATE dbo.programaciones
            SET activo = 0,
                usuario_actualizacion = ?,
                fecha_actualizacion = SYSDATETIME()
            WHERE id_tarea = ? AND activo = 1
            """,
            datos_tarea.get("usuario_accion"),
            id_tarea,
        )
        _insertar_programacion(cursor, id_tarea, datos_programacion, datos_tarea.get("usuario_accion"))
        conexion.commit()


def cambiar_estado_tarea(id_tarea, activo, usuario_accion):
    estado = "ACTIVA" if activo else "INACTIVA"
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            UPDATE dbo.tareas
            SET activo = ?,
                estado_tarea = ?,
                usuario_actualizacion = ?,
                fecha_actualizacion = SYSDATETIME()
            WHERE id_tarea = ?
            """,
            1 if activo else 0,
            estado,
            usuario_accion,
            id_tarea,
        )
        conexion.commit()


def contar_dependencias_tarea(id_tarea):
    consulta = """
        SELECT
            (SELECT COUNT(1) FROM dbo.scripts WHERE id_tarea = ?) +
            (SELECT COUNT(1) FROM dbo.ejecuciones WHERE id_tarea = ?) +
            (SELECT COUNT(1) FROM dbo.logs_tareas WHERE id_tarea = ?)
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, id_tarea, id_tarea, id_tarea)
        return cursor.fetchone()[0]


def eliminar_tarea(id_tarea):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM dbo.programaciones WHERE id_tarea = ?", id_tarea)
        cursor.execute("DELETE FROM dbo.tareas WHERE id_tarea = ?", id_tarea)
        conexion.commit()


def _insertar_programacion(cursor, id_tarea, datos, usuario_accion):
    cursor.execute(
        """
        INSERT INTO dbo.programaciones
            (id_tarea, tipo_programacion, modo_ejecucion_dia, hora_inicio, hora_termino,
             hora_ejecucion, intervalo_minutos, dias_semana, dia_mes, fecha_especifica,
             configuracion_json, ejecutar_en_feriados, usuario_creacion, activo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """,
        id_tarea,
        datos["tipo_programacion"],
        datos.get("modo_ejecucion_dia"),
        datos.get("hora_inicio_intervalo"),
        datos.get("hora_fin_intervalo"),
        datos.get("hora_ejecucion"),
        datos.get("intervalo_minutos"),
        datos.get("dias_semana"),
        datos.get("dia_mes"),
        datos.get("fecha_especifica"),
        datos.get("configuracion_json"),
        datos.get("ejecutar_en_feriados", 0),
        usuario_accion,
    )
