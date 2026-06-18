from app.database.conexion import obtener_conexion


def _fila_a_dict(cursor, fila):
    columnas = [columna[0] for columna in cursor.description]
    return dict(zip(columnas, fila))


def _existe_tabla(cursor, tabla):
    cursor.execute("SELECT CASE WHEN OBJECT_ID(?) IS NULL THEN 0 ELSE 1 END", tabla)
    return bool(cursor.fetchone()[0])


def _columnas_tabla(cursor, nombre_tabla):
    cursor.execute(
        """
        SELECT c.name
        FROM sys.columns c
        INNER JOIN sys.objects o ON o.object_id = c.object_id
        INNER JOIN sys.schemas s ON s.schema_id = o.schema_id
        WHERE s.name + '.' + o.name = ?
        """,
        nombre_tabla,
    )
    return {fila[0] for fila in cursor.fetchall()}


def listar_catalogo(tabla, id_columna, nombre_columna):
    consulta = f"""
        SELECT {id_columna} AS id, {nombre_columna} AS nombre
        FROM {tabla}
        WHERE activo = 1
          AND ISNULL(eliminado_operativo, 0) = 0
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

    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        columnas_tareas = _columnas_tabla(cursor, "dbo.tareas")
        columnas_scripts = _columnas_tabla(cursor, "dbo.scripts")
        columnas_versiones = _columnas_tabla(cursor, "dbo.scripts_versiones")

        tarea_eliminada = "ISNULL(t.eliminado_operativo, 0)" if "eliminado_operativo" in columnas_tareas else "CAST(0 AS bit)"
        script_eliminado = "ISNULL(s.eliminado_operativo, 0)" if "eliminado_operativo" in columnas_scripts else "CAST(0 AS bit)"
        version_eliminada = "ISNULL(v.eliminado_operativo, 0)" if "eliminado_operativo" in columnas_versiones else "CAST(0 AS bit)"
        version_es_activa = "ISNULL(v.es_activa, 0)" if "es_activa" in columnas_versiones else "CAST(0 AS bit)"
        estado_version = "v.estado_version" if "estado_version" in columnas_versiones else "NULL"

        condiciones.append(f"{tarea_eliminada} = 0")
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
                   t.activo AS tarea_activo,
                   {tarea_eliminada} AS tarea_eliminada_operativo,
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
                   p.ejecutar_en_feriados,
                   s.id_script,
                   s.activo AS script_activo,
                   {script_eliminado} AS script_eliminado_operativo,
                   s.id_version_activa AS id_version_activa_script,
                   v.id_version AS id_version_activa,
                   {version_es_activa} AS version_es_activa,
                   {estado_version} AS estado_version_activa,
                   {version_eliminada} AS version_eliminada_operativo,
                   v.nombre_archivo AS nombre_archivo_activo,
                   (
                       SELECT COUNT(1)
                       FROM dbo.ejecuciones e
                       WHERE e.id_tarea = t.id_tarea
                         AND e.estado_ejecucion = 'EN_EJECUCION'
                   ) AS ejecuciones_en_curso
            FROM dbo.tareas t
            INNER JOIN dbo.clientes c ON c.id_cliente = t.id_cliente
            INNER JOIN dbo.categorias ca ON ca.id_categoria = t.id_categoria
            INNER JOIN dbo.tipos ti ON ti.id_tipo = t.id_tipo
            LEFT JOIN dbo.programaciones p ON p.id_tarea = t.id_tarea AND p.activo = 1
            LEFT JOIN dbo.scripts s ON s.id_tarea = t.id_tarea
            LEFT JOIN dbo.scripts_versiones v ON v.id_version = s.id_version_activa
            {where}
            ORDER BY t.fecha_creacion DESC, t.nombre_tarea
        """
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
          AND ISNULL(t.eliminado_operativo, 0) = 0
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
          AND ISNULL(eliminado_operativo, 0) = 0
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


def contar_historial_tarea(id_tarea):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT
                (SELECT COUNT(1) FROM dbo.ejecuciones WHERE id_tarea = ?) +
                (SELECT COUNT(1) FROM dbo.logs_tareas WHERE id_tarea = ?)
            """,
            id_tarea,
            id_tarea,
        )
        total = cursor.fetchone()[0]
        if _existe_tabla(cursor, "dbo.scheduler_eventos"):
            cursor.execute("SELECT COUNT(1) FROM dbo.scheduler_eventos WHERE id_tarea = ?", id_tarea)
            total += cursor.fetchone()[0]
        return total


def existe_ejecucion_en_curso_tarea(id_tarea):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT COUNT(1)
            FROM dbo.ejecuciones
            WHERE id_tarea = ? AND estado_ejecucion = 'EN_EJECUCION'
            """,
            id_tarea,
        )
        return cursor.fetchone()[0] > 0


def asegurar_snapshots_tarea(id_tarea):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
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
            WHERE e.id_tarea = ?
            """,
            id_tarea,
        )
        if _existe_tabla(cursor, "dbo.scheduler_eventos"):
            cursor.execute(
                """
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
                WHERE se.id_tarea = ?
                """,
                id_tarea,
            )
        conexion.commit()


def marcar_tarea_eliminada_operativa(id_tarea, usuario_accion, motivo=None):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            UPDATE dbo.programaciones
            SET activo = 0,
                usuario_actualizacion = ?,
                fecha_actualizacion = SYSDATETIME()
            WHERE id_tarea = ? AND activo = 1
            """,
            usuario_accion,
            id_tarea,
        )
        cursor.execute(
            """
            UPDATE dbo.scripts_versiones
            SET eliminado_operativo = 1,
                es_activa = 0,
                estado_version = CASE WHEN estado_version = 'ACTIVA' THEN 'INACTIVA' ELSE estado_version END,
                fecha_eliminado_operativo = COALESCE(fecha_eliminado_operativo, SYSDATETIME()),
                usuario_eliminado_operativo = ?,
                motivo_eliminado_operativo = COALESCE(?, motivo_eliminado_operativo),
                fecha_actualizacion = SYSDATETIME()
            WHERE id_script IN (SELECT id_script FROM dbo.scripts WHERE id_tarea = ?)
            """,
            usuario_accion,
            motivo,
            id_tarea,
        )
        cursor.execute(
            """
            UPDATE dbo.scripts
            SET activo = 0,
                id_version_activa = NULL,
                eliminado_operativo = 1,
                fecha_eliminado_operativo = COALESCE(fecha_eliminado_operativo, SYSDATETIME()),
                usuario_eliminado_operativo = ?,
                motivo_eliminado_operativo = COALESCE(?, motivo_eliminado_operativo),
                usuario_actualizacion = ?,
                fecha_actualizacion = SYSDATETIME()
            WHERE id_tarea = ?
            """,
            usuario_accion,
            motivo,
            usuario_accion,
            id_tarea,
        )
        cursor.execute(
            """
            UPDATE dbo.tareas
            SET activo = 0,
                estado_tarea = 'INACTIVA',
                eliminado_operativo = 1,
                fecha_eliminado_operativo = COALESCE(fecha_eliminado_operativo, SYSDATETIME()),
                usuario_eliminado_operativo = ?,
                motivo_eliminado_operativo = COALESCE(?, motivo_eliminado_operativo),
                usuario_actualizacion = ?,
                fecha_actualizacion = SYSDATETIME()
            WHERE id_tarea = ?
            """,
            usuario_accion,
            motivo,
            usuario_accion,
            id_tarea,
        )
        conexion.commit()


def eliminar_tarea(id_tarea):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM dbo.programaciones WHERE id_tarea = ?", id_tarea)
        cursor.execute("UPDATE dbo.scripts SET id_version_activa = NULL WHERE id_tarea = ?", id_tarea)
        cursor.execute(
            """
            DELETE FROM dbo.scripts_versiones
            WHERE id_script IN (SELECT id_script FROM dbo.scripts WHERE id_tarea = ?)
            """,
            id_tarea,
        )
        cursor.execute("DELETE FROM dbo.scripts WHERE id_tarea = ?", id_tarea)
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
