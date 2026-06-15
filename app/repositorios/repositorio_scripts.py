from app.database.conexion import obtener_conexion


def _fila_a_dict(cursor, fila):
    columnas = [columna[0] for columna in cursor.description]
    return dict(zip(columnas, fila))


def obtener_tarea_contexto(id_tarea):
    consulta = """
        SELECT t.id_tarea, t.nombre_tarea, t.descripcion, t.id_cliente, c.nombre_cliente,
               t.id_categoria, ca.nombre_categoria, t.id_tipo, ti.nombre_tipo,
               p.tipo_programacion, p.modo_ejecucion_dia, p.hora_ejecucion, p.dias_semana,
               p.dia_mes, p.fecha_especifica, p.intervalo_minutos,
               p.hora_inicio AS hora_inicio_intervalo, p.hora_termino AS hora_fin_intervalo,
               p.ejecutar_en_feriados
        FROM dbo.tareas t
        INNER JOIN dbo.clientes c ON c.id_cliente = t.id_cliente
        INNER JOIN dbo.categorias ca ON ca.id_categoria = t.id_categoria
        INNER JOIN dbo.tipos ti ON ti.id_tipo = t.id_tipo
        LEFT JOIN dbo.programaciones p ON p.id_tarea = t.id_tarea AND p.activo = 1
        WHERE t.id_tarea = ?
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, id_tarea)
        fila = cursor.fetchone()
        return _fila_a_dict(cursor, fila) if fila else None


def obtener_script_por_tarea(id_tarea):
    consulta = """
        SELECT s.id_script, s.id_tarea, s.nombre_script, s.descripcion, s.id_version_activa,
               s.activo, s.fecha_creacion, s.fecha_actualizacion
        FROM dbo.scripts s
        WHERE s.id_tarea = ?
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, id_tarea)
        fila = cursor.fetchone()
        return _fila_a_dict(cursor, fila) if fila else None


def obtener_script(id_script):
    consulta = """
        SELECT id_script, id_tarea, nombre_script, descripcion, id_version_activa, activo
        FROM dbo.scripts
        WHERE id_script = ?
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, id_script)
        fila = cursor.fetchone()
        return _fila_a_dict(cursor, fila) if fila else None


def listar_versiones(id_script):
    consulta = """
        SELECT id_version, id_script, numero_version, nombre_archivo, ruta_fisica, ruta_relativa,
               hash_archivo, estado_version, es_activa, usuario_carga, fecha_carga, observacion,
               requiere_env, ruta_env_fisica, ruta_env_relativa, fecha_creacion, fecha_actualizacion
        FROM dbo.scripts_versiones
        WHERE id_script = ?
        ORDER BY numero_version
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, id_script)
        return [_fila_a_dict(cursor, fila) for fila in cursor.fetchall()]


def obtener_version(id_version):
    consulta = """
        SELECT v.id_version, v.id_script, v.numero_version, v.nombre_archivo, v.ruta_fisica,
               v.ruta_relativa, v.hash_archivo, v.estado_version, v.es_activa, v.usuario_carga,
               v.fecha_carga, v.observacion, v.requiere_env, v.ruta_env_fisica, v.ruta_env_relativa,
               s.id_tarea, s.nombre_script, s.id_version_activa
        FROM dbo.scripts_versiones v
        INNER JOIN dbo.scripts s ON s.id_script = v.id_script
        WHERE v.id_version = ?
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, id_version)
        fila = cursor.fetchone()
        return _fila_a_dict(cursor, fila) if fila else None


def crear_script_con_version(id_tarea, nombre_script, descripcion, version, usuario):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            INSERT INTO dbo.scripts (id_tarea, nombre_script, descripcion, usuario_creacion, activo)
            OUTPUT INSERTED.id_script
            VALUES (?, ?, ?, ?, 1)
            """,
            id_tarea,
            nombre_script,
            descripcion,
            usuario,
        )
        id_script = cursor.fetchone()[0]
        id_version = _insertar_version(cursor, id_script, version, usuario)
        cursor.execute("UPDATE dbo.scripts SET id_version_activa = ? WHERE id_script = ?", id_version, id_script)
        conexion.commit()
        return id_script, id_version


def crear_version(id_script, version, usuario):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        id_version = _insertar_version(cursor, id_script, version, usuario)
        if version["es_activa"]:
            cursor.execute("UPDATE dbo.scripts SET id_version_activa = ? WHERE id_script = ?", id_version, id_script)
        conexion.commit()
        return id_version


def reemplazar_version(id_version, version, usuario):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            UPDATE dbo.scripts_versiones
            SET nombre_archivo = ?, ruta_fisica = ?, ruta_relativa = ?, hash_archivo = ?,
                estado_version = ?, usuario_carga = ?, fecha_carga = SYSDATETIME(),
                observacion = ?, fecha_actualizacion = SYSDATETIME()
            WHERE id_version = ?
            """,
            version["nombre_archivo"],
            version["ruta_fisica"],
            version["ruta_relativa"],
            version["hash_archivo"],
            version["estado_version"],
            usuario,
            version.get("observacion"),
            id_version,
        )
        conexion.commit()


def activar_version(id_version, id_script, usuario):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            UPDATE dbo.scripts_versiones
            SET es_activa = 0,
                estado_version = CASE WHEN estado_version = 'ACTIVA' THEN 'DISPONIBLE' ELSE estado_version END,
                fecha_actualizacion = SYSDATETIME()
            WHERE id_script = ?
            """,
            id_script,
        )
        cursor.execute(
            """
            UPDATE dbo.scripts_versiones
            SET es_activa = 1, estado_version = 'ACTIVA', fecha_actualizacion = SYSDATETIME()
            WHERE id_version = ?
            """,
            id_version,
        )
        cursor.execute(
            """
            UPDATE dbo.scripts
            SET id_version_activa = ?, usuario_actualizacion = ?, fecha_actualizacion = SYSDATETIME()
            WHERE id_script = ?
            """,
            id_version,
            usuario,
            id_script,
        )
        conexion.commit()


def desactivar_version(id_version):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            UPDATE dbo.scripts_versiones
            SET estado_version = 'INACTIVA', es_activa = 0, fecha_actualizacion = SYSDATETIME()
            WHERE id_version = ?
            """,
            id_version,
        )
        conexion.commit()


def eliminar_version(id_version):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM dbo.scripts_versiones WHERE id_version = ?", id_version)
        conexion.commit()


def desactivar_script(id_script, usuario):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            UPDATE dbo.scripts
            SET activo = 0, usuario_actualizacion = ?, fecha_actualizacion = SYSDATETIME()
            WHERE id_script = ?
            """,
            usuario,
            id_script,
        )
        conexion.commit()


def eliminar_script(id_script):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute("UPDATE dbo.scripts SET id_version_activa = NULL WHERE id_script = ?", id_script)
        cursor.execute("DELETE FROM dbo.scripts_versiones WHERE id_script = ?", id_script)
        cursor.execute("DELETE FROM dbo.scripts WHERE id_script = ?", id_script)
        conexion.commit()


def actualizar_env_version(id_version, requiere_env, ruta_env_fisica=None, ruta_env_relativa=None):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            UPDATE dbo.scripts_versiones
            SET requiere_env = ?, ruta_env_fisica = ?, ruta_env_relativa = ?,
                fecha_actualizacion = SYSDATETIME()
            WHERE id_version = ?
            """,
            1 if requiere_env else 0,
            ruta_env_fisica,
            ruta_env_relativa,
            id_version,
        )
        conexion.commit()


def contar_uso_version(id_version):
    consulta = """
        SELECT
            (SELECT COUNT(1) FROM dbo.ejecuciones WHERE id_version = ?) +
            (SELECT COUNT(1) FROM dbo.logs_tareas lt
             INNER JOIN dbo.ejecuciones e ON e.id_ejecucion = lt.id_ejecucion
             WHERE e.id_version = ?)
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, id_version, id_version)
        return cursor.fetchone()[0]


def contar_uso_script(id_script):
    consulta = """
        SELECT
            (SELECT COUNT(1) FROM dbo.ejecuciones WHERE id_script = ?) +
            (SELECT COUNT(1) FROM dbo.logs_tareas lt
             INNER JOIN dbo.ejecuciones e ON e.id_ejecucion = lt.id_ejecucion
             WHERE e.id_script = ?)
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, id_script, id_script)
        return cursor.fetchone()[0]


def _insertar_version(cursor, id_script, version, usuario):
    cursor.execute(
        """
        INSERT INTO dbo.scripts_versiones
            (id_script, numero_version, nombre_archivo, ruta_fisica, ruta_relativa, hash_archivo,
             estado_version, es_activa, usuario_carga, observacion, requiere_env, ruta_env_fisica, ruta_env_relativa)
        OUTPUT INSERTED.id_version
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        id_script,
        version["numero_version"],
        version["nombre_archivo"],
        version["ruta_fisica"],
        version["ruta_relativa"],
        version["hash_archivo"],
        version["estado_version"],
        1 if version["es_activa"] else 0,
        usuario,
        version.get("observacion"),
        1 if version.get("requiere_env") else 0,
        version.get("ruta_env_fisica"),
        version.get("ruta_env_relativa"),
    )
    return cursor.fetchone()[0]
