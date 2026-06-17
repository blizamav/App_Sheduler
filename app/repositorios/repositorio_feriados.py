from app.database.conexion import obtener_conexion


def _fila_a_dict(cursor, fila):
    columnas = [columna[0] for columna in cursor.description]
    return dict(zip(columnas, fila))


def listar_feriados(filtros=None):
    filtros = filtros or {}
    condiciones = []
    parametros = []

    if filtros.get("anio"):
        condiciones.append("YEAR(fecha) = ?")
        parametros.append(filtros["anio"])
    if filtros.get("mes"):
        condiciones.append("MONTH(fecha) = ?")
        parametros.append(filtros["mes"])
    if filtros.get("pais"):
        condiciones.append("pais = ?")
        parametros.append(filtros["pais"])
    if filtros.get("activo") == "activo":
        condiciones.append("activo = 1")
    elif filtros.get("activo") == "inactivo":
        condiciones.append("activo = 0")

    where = "WHERE " + " AND ".join(condiciones) if condiciones else ""
    consulta = f"""
        SELECT id_feriado, fecha, nombre, tipo, pais, irrenunciable, activo,
               origen, observacion, fecha_creacion, fecha_actualizacion,
               usuario_creacion, usuario_actualizacion
        FROM dbo.feriados
        {where}
        ORDER BY fecha DESC, pais, nombre
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, *parametros)
        return [_fila_a_dict(cursor, fila) for fila in cursor.fetchall()]


def obtener_feriado_por_id(id_feriado):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT id_feriado, fecha, nombre, tipo, pais, irrenunciable, activo,
                   origen, observacion, fecha_creacion, fecha_actualizacion,
                   usuario_creacion, usuario_actualizacion
            FROM dbo.feriados
            WHERE id_feriado = ?
            """,
            id_feriado,
        )
        fila = cursor.fetchone()
        return _fila_a_dict(cursor, fila) if fila else None


def obtener_feriado_por_fecha(fecha, pais="CL"):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT TOP 1 id_feriado, fecha, nombre, tipo, pais, irrenunciable, activo,
                   origen, observacion, fecha_creacion, fecha_actualizacion,
                   usuario_creacion, usuario_actualizacion
            FROM dbo.feriados
            WHERE fecha = ?
              AND pais = ?
              AND activo = 1
            ORDER BY id_feriado DESC
            """,
            fecha,
            pais,
        )
        fila = cursor.fetchone()
        return _fila_a_dict(cursor, fila) if fila else None


def existe_feriado_activo(fecha, pais, excluir_id=None):
    consulta = """
        SELECT COUNT(1)
        FROM dbo.feriados
        WHERE fecha = ?
          AND pais = ?
          AND activo = 1
    """
    parametros = [fecha, pais]
    if excluir_id:
        consulta += " AND id_feriado <> ?"
        parametros.append(excluir_id)
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, *parametros)
        return cursor.fetchone()[0] > 0


def crear_feriado(datos):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            INSERT INTO dbo.feriados
                (fecha, nombre, tipo, pais, irrenunciable, activo, origen,
                 observacion, usuario_creacion)
            OUTPUT INSERTED.id_feriado
            VALUES (?, ?, ?, ?, ?, ?, 'MANUAL', ?, ?)
            """,
            datos["fecha"],
            datos["nombre"],
            datos.get("tipo"),
            datos["pais"],
            1 if datos.get("irrenunciable") else 0,
            1 if datos.get("activo") else 0,
            datos.get("observacion"),
            datos.get("usuario"),
        )
        id_feriado = cursor.fetchone()[0]
        conexion.commit()
        return id_feriado


def actualizar_feriado(id_feriado, datos):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            UPDATE dbo.feriados
            SET fecha = ?,
                nombre = ?,
                tipo = ?,
                pais = ?,
                irrenunciable = ?,
                activo = ?,
                observacion = ?,
                fecha_actualizacion = SYSDATETIME(),
                usuario_actualizacion = ?
            WHERE id_feriado = ?
            """,
            datos["fecha"],
            datos["nombre"],
            datos.get("tipo"),
            datos["pais"],
            1 if datos.get("irrenunciable") else 0,
            1 if datos.get("activo") else 0,
            datos.get("observacion"),
            datos.get("usuario"),
            id_feriado,
        )
        conexion.commit()


def cambiar_estado_feriado(id_feriado, activo, usuario):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            UPDATE dbo.feriados
            SET activo = ?,
                fecha_actualizacion = SYSDATETIME(),
                usuario_actualizacion = ?
            WHERE id_feriado = ?
            """,
            1 if activo else 0,
            usuario,
            id_feriado,
        )
        conexion.commit()


def eliminar_feriado(id_feriado):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM dbo.feriados WHERE id_feriado = ?", id_feriado)
        conexion.commit()
