from app.database.conexion import obtener_conexion


def _fila_a_dict(cursor, fila):
    columnas = [columna[0] for columna in cursor.description]
    return dict(zip(columnas, fila))


def _columnas_ejecuciones():
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT name
            FROM sys.columns
            WHERE object_id = OBJECT_ID('dbo.ejecuciones')
            """
        )
        return {fila[0] for fila in cursor.fetchall()}


def _columnas_tabla(nombre_tabla):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT name
            FROM sys.columns
            WHERE object_id = OBJECT_ID(?)
            """,
            f"dbo.{nombre_tabla}",
        )
        return {fila[0] for fila in cursor.fetchall()}


def obtener_contexto_tarea_ejecucion(id_tarea):
    columnas_tareas = _columnas_tabla("tareas")
    columnas_scripts = _columnas_tabla("scripts")
    columnas_versiones = _columnas_tabla("scripts_versiones")
    tarea_eliminada = "ISNULL(t.eliminado_operativo, 0)" if "eliminado_operativo" in columnas_tareas else "CAST(0 AS bit)"
    script_eliminado = "ISNULL(s.eliminado_operativo, 0)" if "eliminado_operativo" in columnas_scripts else "CAST(0 AS bit)"
    version_eliminada = "ISNULL(v.eliminado_operativo, 0)" if "eliminado_operativo" in columnas_versiones else "CAST(0 AS bit)"
    consulta = f"""
        SELECT t.id_tarea, t.nombre_tarea, t.descripcion, t.estado_tarea,
               t.activo AS tarea_activo,
               {tarea_eliminada} AS tarea_eliminada_operativo,
               c.nombre_cliente, ca.nombre_categoria, ti.nombre_tipo,
               s.id_script, s.nombre_script, s.activo AS script_activo,
               {script_eliminado} AS script_eliminado_operativo,
               s.id_version_activa,
               v.id_version, v.numero_version, v.nombre_archivo, v.ruta_fisica, v.ruta_relativa,
               v.estado_version, v.es_activa,
               {version_eliminada} AS version_eliminada_operativo,
               v.requiere_env, v.ruta_env_fisica, v.ruta_env_relativa
        FROM dbo.tareas t
        INNER JOIN dbo.clientes c ON c.id_cliente = t.id_cliente
        INNER JOIN dbo.categorias ca ON ca.id_categoria = t.id_categoria
        INNER JOIN dbo.tipos ti ON ti.id_tipo = t.id_tipo
        LEFT JOIN dbo.scripts s ON s.id_tarea = t.id_tarea
        LEFT JOIN dbo.scripts_versiones v ON v.id_version = s.id_version_activa
        WHERE t.id_tarea = ?
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, id_tarea)
        fila = cursor.fetchone()
        return _fila_a_dict(cursor, fila) if fila else None


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


def crear_ejecucion_manual(contexto, usuario):
    columnas = _columnas_ejecuciones()
    if _tiene_snapshots(columnas):
        return _crear_ejecucion_con_snapshots(contexto, usuario, "MANUAL")

    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            INSERT INTO dbo.ejecuciones
                (id_tarea, id_script, id_version, origen_ejecucion, estado_ejecucion,
                 fecha_hora_inicio, usuario_ejecucion)
            OUTPUT INSERTED.id_ejecucion
            VALUES (?, ?, ?, 'MANUAL', 'EN_EJECUCION', SYSDATETIME(), ?)
            """,
            contexto["id_tarea"],
            contexto["id_script"],
            contexto["id_version"],
            usuario,
        )
        id_ejecucion = cursor.fetchone()[0]
        conexion.commit()
        return id_ejecucion


def crear_ejecucion_automatica(contexto, nombre_worker, fecha_programada, clave_programacion):
    columnas = _columnas_ejecuciones()
    if not {"fecha_programada", "clave_programacion", "nombre_worker"}.issubset(columnas):
        raise RuntimeError("La migracion 011 debe ejecutarse antes de iniciar ejecuciones automaticas.")
    if _tiene_snapshots(columnas):
        return _crear_ejecucion_con_snapshots(
            contexto,
            None,
            "AUTOMATICA",
            fecha_programada=fecha_programada,
            clave_programacion=clave_programacion,
            nombre_worker=nombre_worker,
        )

    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            INSERT INTO dbo.ejecuciones
                (id_tarea, id_script, id_version, origen_ejecucion, estado_ejecucion,
                 fecha_hora_inicio, usuario_ejecucion, fecha_programada, clave_programacion, nombre_worker)
            OUTPUT INSERTED.id_ejecucion
            VALUES (?, ?, ?, 'AUTOMATICA', 'EN_EJECUCION', SYSDATETIME(), NULL, ?, ?, ?)
            """,
            contexto["id_tarea"],
            contexto["id_script"],
            contexto["id_version"],
            fecha_programada,
            clave_programacion,
            nombre_worker,
        )
        id_ejecucion = cursor.fetchone()[0]
        conexion.commit()
        return id_ejecucion


def _tiene_snapshots(columnas):
    return {
        "id_tarea_original",
        "nombre_tarea_snapshot",
        "cliente_snapshot",
        "categoria_snapshot",
        "tipo_snapshot",
        "nombre_script_snapshot",
        "nombre_archivo_snapshot",
        "version_script_snapshot",
        "usuario_ejecucion_snapshot",
    }.issubset(columnas)


def _crear_ejecucion_con_snapshots(
    contexto,
    usuario,
    origen,
    fecha_programada=None,
    clave_programacion=None,
    nombre_worker=None,
):
    es_automatica = origen == "AUTOMATICA"
    columnas_extra = ", fecha_programada, clave_programacion, nombre_worker" if es_automatica else ""
    valores_extra = ", ?, ?, ?" if es_automatica else ""
    parametros_extra = [fecha_programada, clave_programacion, nombre_worker] if es_automatica else []
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            f"""
            INSERT INTO dbo.ejecuciones
                (id_tarea, id_script, id_version, origen_ejecucion, estado_ejecucion,
                 fecha_hora_inicio, usuario_ejecucion, id_tarea_original,
                 nombre_tarea_snapshot, cliente_snapshot, categoria_snapshot, tipo_snapshot,
                 nombre_script_snapshot, nombre_archivo_snapshot, version_script_snapshot,
                 usuario_ejecucion_snapshot{columnas_extra})
            OUTPUT INSERTED.id_ejecucion
            VALUES (?, ?, ?, ?, 'EN_EJECUCION', SYSDATETIME(), ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?{valores_extra})
            """,
            contexto["id_tarea"],
            contexto["id_script"],
            contexto["id_version"],
            origen,
            usuario,
            contexto["id_tarea"],
            contexto.get("nombre_tarea"),
            contexto.get("nombre_cliente"),
            contexto.get("nombre_categoria"),
            contexto.get("nombre_tipo"),
            contexto.get("nombre_script"),
            contexto.get("nombre_archivo"),
            str(contexto.get("numero_version")) if contexto.get("numero_version") else None,
            usuario,
            *parametros_extra,
        )
        id_ejecucion = cursor.fetchone()[0]
        conexion.commit()
        return id_ejecucion


def actualizar_pid_ejecucion(id_ejecucion, pid):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute("UPDATE dbo.ejecuciones SET pid_proceso = ? WHERE id_ejecucion = ?", pid, id_ejecucion)
        conexion.commit()


def finalizar_ejecucion(id_ejecucion, estado, codigo_salida=None, mensaje_error=None):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            DECLARE @fecha_termino datetime2(0) = SYSDATETIME();

            UPDATE dbo.ejecuciones
            SET estado_ejecucion = ?,
                fecha_hora_termino = @fecha_termino,
                duracion_segundos =
                    CASE
                        WHEN DATEDIFF(SECOND, fecha_hora_inicio, @fecha_termino) < 0 THEN 0
                        ELSE DATEDIFF(SECOND, fecha_hora_inicio, @fecha_termino)
                    END,
                codigo_salida = ?,
                mensaje_error = ?
            WHERE id_ejecucion = ? AND estado_ejecucion = 'EN_EJECUCION'
            """,
            estado,
            codigo_salida,
            mensaje_error,
            id_ejecucion,
        )
        conexion.commit()


def marcar_ejecucion_detenida(id_ejecucion, usuario, motivo, fue_forzada):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            DECLARE @fecha_termino datetime2(0) = SYSDATETIME();

            UPDATE dbo.ejecuciones
            SET estado_ejecucion = 'DETENIDA_MANUALMENTE',
                fecha_hora_termino = @fecha_termino,
                duracion_segundos =
                    CASE
                        WHEN DATEDIFF(SECOND, fecha_hora_inicio, @fecha_termino) < 0 THEN 0
                        ELSE DATEDIFF(SECOND, fecha_hora_inicio, @fecha_termino)
                    END,
                usuario_detencion = ?,
                fecha_hora_detencion = @fecha_termino,
                motivo_detencion = ?,
                fue_detencion_forzada = ?
            WHERE id_ejecucion = ? AND estado_ejecucion = 'EN_EJECUCION'
            """,
            usuario,
            motivo,
            1 if fue_forzada else 0,
            id_ejecucion,
        )
        conexion.commit()


def crear_log_tarea(id_ejecucion, contexto, ruta_fisica_log, ruta_relativa_log, nombre_archivo_log, usuario):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            INSERT INTO dbo.logs_tareas
                (id_tarea, id_ejecucion, nombre_tarea, nombre_script, nombre_archivo_log,
                 ruta_fisica_log, ruta_relativa_log, fecha_hora_inicio, estado_final, usuario_ejecucion)
            VALUES (?, ?, ?, ?, ?, ?, ?, SYSDATETIME(), 'EN_EJECUCION', ?)
            """,
            contexto["id_tarea"],
            id_ejecucion,
            contexto["nombre_tarea"],
            contexto["nombre_archivo"],
            nombre_archivo_log,
            str(ruta_fisica_log),
            ruta_relativa_log,
            usuario,
        )
        conexion.commit()


def actualizar_log_tarea_final(id_ejecucion, estado, codigo_salida=None, mensaje_error=None):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            DECLARE @fecha_termino datetime2(0) = SYSDATETIME();

            UPDATE dbo.logs_tareas
            SET estado_final = ?,
                fecha_hora_termino = @fecha_termino,
                duracion_segundos =
                    CASE
                        WHEN DATEDIFF(SECOND, fecha_hora_inicio, @fecha_termino) < 0 THEN 0
                        ELSE DATEDIFF(SECOND, fecha_hora_inicio, @fecha_termino)
                    END,
                codigo_salida = ?,
                mensaje_error = ?
            WHERE id_ejecucion = ?
            """,
            estado,
            codigo_salida,
            mensaje_error,
            id_ejecucion,
        )
        conexion.commit()


def listar_ejecuciones_en_curso():
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT id_ejecucion, id_tarea, estado_ejecucion, fecha_hora_inicio,
                   fecha_hora_termino, pid_proceso, usuario_ejecucion
            FROM dbo.ejecuciones
            WHERE estado_ejecucion = 'EN_EJECUCION'
            ORDER BY fecha_hora_inicio ASC, id_ejecucion ASC
            """
        )
        return [_fila_a_dict(cursor, fila) for fila in cursor.fetchall()]


def obtener_ejecucion(id_ejecucion):
    columnas = _columnas_ejecuciones()
    fecha_programada = "e.fecha_programada" if "fecha_programada" in columnas else "CAST(NULL AS datetime2(0))"
    clave_programacion = "e.clave_programacion" if "clave_programacion" in columnas else "CAST(NULL AS varchar(200))"
    nombre_worker = "e.nombre_worker" if "nombre_worker" in columnas else "CAST(NULL AS varchar(100))"
    nombre_tarea = "COALESCE(e.nombre_tarea_snapshot, t.nombre_tarea, 'Tarea eliminada')" if "nombre_tarea_snapshot" in columnas else "COALESCE(t.nombre_tarea, 'Tarea eliminada')"
    nombre_cliente = "COALESCE(e.cliente_snapshot, c.nombre_cliente, 'Cliente historico')" if "cliente_snapshot" in columnas else "COALESCE(c.nombre_cliente, 'Cliente historico')"
    nombre_categoria = "COALESCE(e.categoria_snapshot, ca.nombre_categoria, 'Categoria historica')" if "categoria_snapshot" in columnas else "COALESCE(ca.nombre_categoria, 'Categoria historica')"
    nombre_tipo = "COALESCE(e.tipo_snapshot, ti.nombre_tipo, 'Tipo historico')" if "tipo_snapshot" in columnas else "COALESCE(ti.nombre_tipo, 'Tipo historico')"
    nombre_script = "COALESCE(e.nombre_script_snapshot, s.nombre_script, 'Script eliminado')" if "nombre_script_snapshot" in columnas else "COALESCE(s.nombre_script, 'Script eliminado')"
    numero_version = "COALESCE(e.version_script_snapshot, CONVERT(varchar(10), v.numero_version), 'historica')" if "version_script_snapshot" in columnas else "COALESCE(CONVERT(varchar(10), v.numero_version), 'historica')"
    nombre_archivo = "COALESCE(e.nombre_archivo_snapshot, v.nombre_archivo, 'Archivo historico')" if "nombre_archivo_snapshot" in columnas else "COALESCE(v.nombre_archivo, 'Archivo historico')"
    usuario_ejecucion = "COALESCE(e.usuario_ejecucion_snapshot, e.usuario_ejecucion, 'Usuario historico')" if "usuario_ejecucion_snapshot" in columnas else "COALESCE(e.usuario_ejecucion, 'Usuario historico')"
    consulta = f"""
        SELECT e.id_ejecucion, e.id_tarea, e.id_script, e.id_version, e.origen_ejecucion,
               e.estado_ejecucion, e.fecha_hora_inicio, e.fecha_hora_termino, e.duracion_segundos,
               e.codigo_salida, e.mensaje_error, {usuario_ejecucion} AS usuario_ejecucion, e.pid_proceso,
               e.usuario_detencion, e.fecha_hora_detencion, e.motivo_detencion, e.fue_detencion_forzada,
               {fecha_programada} AS fecha_programada,
               {clave_programacion} AS clave_programacion,
               {nombre_worker} AS nombre_worker,
               {nombre_tarea} AS nombre_tarea,
               {nombre_cliente} AS nombre_cliente,
               {nombre_categoria} AS nombre_categoria,
               {nombre_tipo} AS nombre_tipo,
               {nombre_script} AS nombre_script,
               {numero_version} AS numero_version,
               {nombre_archivo} AS nombre_archivo,
               CASE WHEN e.id_tarea IS NULL OR t.id_tarea IS NULL THEN 1 ELSE 0 END AS maestro_tarea_eliminado,
               CASE WHEN e.id_script IS NULL OR s.id_script IS NULL THEN 1 ELSE 0 END AS maestro_script_eliminado,
               CASE WHEN e.id_version IS NULL OR v.id_version IS NULL THEN 1 ELSE 0 END AS maestro_version_eliminado,
               v.ruta_relativa,
               lt.ruta_fisica_log, lt.ruta_relativa_log, lt.nombre_archivo_log
        FROM dbo.ejecuciones e
        LEFT JOIN dbo.tareas t ON t.id_tarea = e.id_tarea
        LEFT JOIN dbo.clientes c ON c.id_cliente = t.id_cliente
        LEFT JOIN dbo.categorias ca ON ca.id_categoria = t.id_categoria
        LEFT JOIN dbo.tipos ti ON ti.id_tipo = t.id_tipo
        LEFT JOIN dbo.scripts s ON s.id_script = e.id_script
        LEFT JOIN dbo.scripts_versiones v ON v.id_version = e.id_version
        LEFT JOIN dbo.logs_tareas lt ON lt.id_ejecucion = e.id_ejecucion
        WHERE e.id_ejecucion = ?
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, id_ejecucion)
        fila = cursor.fetchone()
        return _fila_a_dict(cursor, fila) if fila else None


def _expresiones_campos_ejecucion(columnas):
    return {
        "fecha_programada": "e.fecha_programada" if "fecha_programada" in columnas else "CAST(NULL AS datetime2(0))",
        "clave_programacion": "e.clave_programacion" if "clave_programacion" in columnas else "CAST(NULL AS varchar(200))",
        "nombre_worker": "e.nombre_worker" if "nombre_worker" in columnas else "CAST(NULL AS varchar(100))",
    }


def _where_ejecuciones(filtros, columnas):
    filtros = filtros or {}
    condiciones = []
    parametros = []

    if filtros.get("id_ejecucion"):
        condiciones.append("e.id_ejecucion = ?")
        parametros.append(filtros["id_ejecucion"])
        return "WHERE " + " AND ".join(condiciones), parametros

    if filtros.get("tarea"):
        campo_tarea = "COALESCE(e.nombre_tarea_snapshot, t.nombre_tarea)" if "nombre_tarea_snapshot" in columnas else "t.nombre_tarea"
        condiciones.append(f"{campo_tarea} LIKE ?")
        parametros.append(f"%{filtros['tarea']}%")
    if filtros.get("origen"):
        condiciones.append("e.origen_ejecucion = ?")
        parametros.append(filtros["origen"])
    if filtros.get("estado"):
        condiciones.append("e.estado_ejecucion = ?")
        parametros.append(filtros["estado"])
    if filtros.get("anio"):
        condiciones.append("YEAR(e.fecha_hora_inicio) = ?")
        parametros.append(filtros["anio"])
    if filtros.get("mes"):
        condiciones.append("MONTH(e.fecha_hora_inicio) = ?")
        parametros.append(filtros["mes"])
    if filtros.get("dia"):
        condiciones.append("DAY(e.fecha_hora_inicio) = ?")
        parametros.append(filtros["dia"])
    if filtros.get("fecha_desde"):
        condiciones.append("e.fecha_hora_inicio >= ?")
        parametros.append(filtros["fecha_desde"])
    if filtros.get("fecha_hasta"):
        condiciones.append("e.fecha_hora_inicio < DATEADD(DAY, 1, CAST(? AS date))")
        parametros.append(filtros["fecha_hasta"])
    if filtros.get("usuario"):
        campo_usuario = "COALESCE(e.usuario_ejecucion_snapshot, e.usuario_ejecucion)" if "usuario_ejecucion_snapshot" in columnas else "e.usuario_ejecucion"
        condiciones.append(f"{campo_usuario} LIKE ?")
        parametros.append(f"%{filtros['usuario']}%")
    if filtros.get("worker") and "nombre_worker" in columnas:
        condiciones.append("e.nombre_worker LIKE ?")
        parametros.append(f"%{filtros['worker']}%")

    where = "WHERE " + " AND ".join(condiciones) if condiciones else ""
    return where, parametros


def _from_ejecuciones():
    return """
        FROM dbo.ejecuciones e
        LEFT JOIN dbo.tareas t ON t.id_tarea = e.id_tarea
        LEFT JOIN dbo.clientes c ON c.id_cliente = t.id_cliente
        LEFT JOIN dbo.categorias ca ON ca.id_categoria = t.id_categoria
        LEFT JOIN dbo.tipos ti ON ti.id_tipo = t.id_tipo
        LEFT JOIN dbo.scripts s ON s.id_script = e.id_script
        LEFT JOIN dbo.scripts_versiones v ON v.id_version = e.id_version
    """


def listar_ejecuciones_paginadas(filtros, page=1, per_page=25):
    columnas = _columnas_ejecuciones()
    expresiones = _expresiones_campos_ejecucion(columnas)
    nombre_tarea = "COALESCE(e.nombre_tarea_snapshot, t.nombre_tarea, 'Tarea eliminada')" if "nombre_tarea_snapshot" in columnas else "COALESCE(t.nombre_tarea, 'Tarea eliminada')"
    nombre_cliente = "COALESCE(e.cliente_snapshot, c.nombre_cliente, 'Cliente historico')" if "cliente_snapshot" in columnas else "COALESCE(c.nombre_cliente, 'Cliente historico')"
    nombre_categoria = "COALESCE(e.categoria_snapshot, ca.nombre_categoria, 'Categoria historica')" if "categoria_snapshot" in columnas else "COALESCE(ca.nombre_categoria, 'Categoria historica')"
    nombre_tipo = "COALESCE(e.tipo_snapshot, ti.nombre_tipo, 'Tipo historico')" if "tipo_snapshot" in columnas else "COALESCE(ti.nombre_tipo, 'Tipo historico')"
    nombre_script = "COALESCE(e.nombre_script_snapshot, s.nombre_script, 'Script eliminado')" if "nombre_script_snapshot" in columnas else "COALESCE(s.nombre_script, 'Script eliminado')"
    numero_version = "COALESCE(e.version_script_snapshot, CONVERT(varchar(10), v.numero_version), 'historica')" if "version_script_snapshot" in columnas else "COALESCE(CONVERT(varchar(10), v.numero_version), 'historica')"
    nombre_archivo = "COALESCE(e.nombre_archivo_snapshot, v.nombre_archivo, 'Archivo historico')" if "nombre_archivo_snapshot" in columnas else "COALESCE(v.nombre_archivo, 'Archivo historico')"
    usuario_ejecucion = "COALESCE(e.usuario_ejecucion_snapshot, e.usuario_ejecucion, 'Usuario historico')" if "usuario_ejecucion_snapshot" in columnas else "COALESCE(e.usuario_ejecucion, 'Usuario historico')"
    where, parametros = _where_ejecuciones(filtros, columnas)
    offset = (page - 1) * per_page
    consulta = f"""
        SELECT
               e.id_ejecucion,
               e.id_tarea,
               e.origen_ejecucion,
               e.estado_ejecucion,
               e.fecha_hora_inicio,
               e.fecha_hora_termino,
               {usuario_ejecucion} AS usuario_ejecucion,
               e.pid_proceso,
               {expresiones['fecha_programada']} AS fecha_programada,
               {expresiones['clave_programacion']} AS clave_programacion,
               {expresiones['nombre_worker']} AS nombre_worker,
               {nombre_tarea} AS nombre_tarea,
               {nombre_cliente} AS nombre_cliente,
               {nombre_categoria} AS nombre_categoria,
               {nombre_tipo} AS nombre_tipo,
               {nombre_script} AS nombre_script,
               {numero_version} AS numero_version,
               {nombre_archivo} AS nombre_archivo,
               CASE WHEN e.id_tarea IS NULL OR t.id_tarea IS NULL THEN 1 ELSE 0 END AS maestro_tarea_eliminado,
               CASE WHEN e.id_script IS NULL OR s.id_script IS NULL THEN 1 ELSE 0 END AS maestro_script_eliminado,
               CASE WHEN e.id_version IS NULL OR v.id_version IS NULL THEN 1 ELSE 0 END AS maestro_version_eliminado
        {_from_ejecuciones()}
        {where}
        ORDER BY e.fecha_hora_inicio DESC, e.id_ejecucion DESC
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, *(parametros + [offset, per_page]))
        return [_fila_a_dict(cursor, fila) for fila in cursor.fetchall()]


def contar_ejecuciones_filtradas(filtros):
    columnas = _columnas_ejecuciones()
    where, parametros = _where_ejecuciones(filtros, columnas)
    consulta = f"""
        SELECT COUNT(1)
        {_from_ejecuciones()}
        {where}
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, *parametros)
        return cursor.fetchone()[0]


def resumir_ejecuciones_filtradas(filtros):
    columnas = _columnas_ejecuciones()
    where, parametros = _where_ejecuciones(filtros, columnas)
    consulta = f"""
        SELECT e.estado_ejecucion, COUNT(1) AS total
        {_from_ejecuciones()}
        {where}
        GROUP BY e.estado_ejecucion
    """
    resumen = {
        "total": 0,
        "EXITOSA": 0,
        "ERROR": 0,
        "EN_EJECUCION": 0,
        "DETENIDA_MANUALMENTE": 0,
        "CANCELADA": 0,
    }
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, *parametros)
        for fila in cursor.fetchall():
            estado = fila[0]
            total = fila[1]
            resumen[estado] = total
            resumen["total"] += total
    return resumen
