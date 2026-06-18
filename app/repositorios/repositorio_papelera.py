from app.database.conexion import obtener_conexion


MENSAJE_BLOQUEO_PERMANENTE = (
    "No fue posible eliminar permanentemente este registro porque aún existen dependencias "
    "operativas no históricas. El registro seguirá en papelera y oculto de la operación normal."
)
MENSAJE_MIGRACION_DESACOPLE = (
    "Falta ejecutar la migracion 017 de desacople historico antes de eliminar permanentemente "
    "este registro sin perder trazabilidad."
)
MENSAJE_SNAPSHOTS_INSUFICIENTES = (
    "Faltan snapshots historicos para eliminar permanentemente este registro sin perder trazabilidad."
)


ENTIDADES = {
    "usuarios": {
        "label": "Usuarios",
        "tabla": "dbo.usuarios",
        "id": "id_usuario",
        "nombre": "usuario",
        "descripcion": "nombre_completo",
        "modulo": "USUARIOS",
    },
    "clientes": {
        "label": "Clientes",
        "tabla": "dbo.clientes",
        "id": "id_cliente",
        "nombre": "nombre_cliente",
        "descripcion": "descripcion",
        "campo_tarea": "id_cliente",
        "modulo": "CLIENTES",
    },
    "categorias": {
        "label": "Categorias",
        "tabla": "dbo.categorias",
        "id": "id_categoria",
        "nombre": "nombre_categoria",
        "descripcion": "descripcion",
        "campo_tarea": "id_categoria",
        "modulo": "CATEGORIAS",
    },
    "tipos": {
        "label": "Tipos",
        "tabla": "dbo.tipos",
        "id": "id_tipo",
        "nombre": "nombre_tipo",
        "descripcion": "descripcion",
        "campo_tarea": "id_tipo",
        "modulo": "TIPOS",
    },
    "tareas": {
        "label": "Tareas",
        "tabla": "dbo.tareas",
        "id": "id_tarea",
        "nombre": "nombre_tarea",
        "descripcion": "descripcion",
        "modulo": "TAREAS",
    },
    "scripts": {
        "label": "Scripts",
        "tabla": "dbo.scripts",
        "id": "id_script",
        "nombre": "nombre_script",
        "descripcion": "descripcion",
        "modulo": "SCRIPTS",
    },
    "scripts_versiones": {
        "label": "Versiones de scripts",
        "tabla": "dbo.scripts_versiones",
        "id": "id_version",
        "nombre": "nombre_archivo",
        "descripcion": "observacion",
        "activo_expr": "CASE WHEN es_activa = 1 OR estado_version <> 'INACTIVA' THEN 1 ELSE 0 END",
        "activo_expr_alias": "CASE WHEN m.es_activa = 1 OR m.estado_version <> 'INACTIVA' THEN 1 ELSE 0 END",
        "modulo": "SCRIPTS",
    },
}


def _fila_a_dict(cursor, fila):
    columnas = [columna[0] for columna in cursor.description]
    return dict(zip(columnas, fila))


def _existe_tabla(cursor, tabla):
    cursor.execute("SELECT CASE WHEN OBJECT_ID(?) IS NULL THEN 0 ELSE 1 END", tabla)
    return bool(cursor.fetchone()[0])


def _existe_columna(cursor, tabla, columna):
    cursor.execute("SELECT CASE WHEN COL_LENGTH(?, ?) IS NULL THEN 0 ELSE 1 END", tabla, columna)
    return bool(cursor.fetchone()[0])


def _columna_nullable(cursor, tabla, columna):
    cursor.execute(
        """
        SELECT c.is_nullable
        FROM sys.columns c
        WHERE c.object_id = OBJECT_ID(?)
          AND c.name = ?
        """,
        tabla,
        columna,
    )
    fila = cursor.fetchone()
    return bool(fila and fila[0])


def _existe_fk(cursor, tabla, nombre_fk):
    cursor.execute(
        """
        SELECT COUNT(1)
        FROM sys.foreign_keys
        WHERE parent_object_id = OBJECT_ID(?)
          AND name = ?
        """,
        tabla,
        nombre_fk,
    )
    return int(cursor.fetchone()[0] or 0) > 0


def listar_eliminados():
    resultados = []
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        for entidad, cfg in ENTIDADES.items():
            consulta = _consulta_entidad(entidad, cfg)
            cursor.execute(consulta)
            resultados.extend(_normalizar_fila(entidad, cfg, _fila_a_dict(cursor, fila)) for fila in cursor.fetchall())
    return resultados


def obtener_eliminado(entidad, id_registro):
    cfg = ENTIDADES[entidad]
    consulta = f"""
        SELECT {cfg['id']} AS id_registro,
               {cfg['nombre']} AS nombre,
               {cfg['descripcion']} AS descripcion,
               {cfg.get('activo_expr', 'activo')} AS activo,
               fecha_eliminado_operativo,
               usuario_eliminado_operativo,
               motivo_eliminado_operativo
        FROM {cfg['tabla']}
        WHERE {cfg['id']} = ?
          AND ISNULL(eliminado_operativo, 0) = 1
    """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, id_registro)
        fila = cursor.fetchone()
        return _normalizar_fila(entidad, cfg, _fila_a_dict(cursor, fila)) if fila else None


def restaurar(entidad, id_registro, usuario):
    cfg = ENTIDADES[entidad]
    if entidad == "tareas":
        consulta = """
            UPDATE dbo.tareas
            SET eliminado_operativo = 0,
                activo = 0,
                estado_tarea = 'INACTIVA',
                fecha_eliminado_operativo = NULL,
                usuario_eliminado_operativo = NULL,
                motivo_eliminado_operativo = NULL,
                usuario_actualizacion = ?,
                fecha_actualizacion = SYSDATETIME()
            WHERE id_tarea = ?
        """
    elif entidad == "scripts":
        consulta = """
            UPDATE dbo.scripts
            SET eliminado_operativo = 0,
                activo = 0,
                fecha_eliminado_operativo = NULL,
                usuario_eliminado_operativo = NULL,
                motivo_eliminado_operativo = NULL,
                usuario_actualizacion = ?,
                fecha_actualizacion = SYSDATETIME()
            WHERE id_script = ?
        """
    elif entidad == "scripts_versiones":
        consulta = """
            UPDATE dbo.scripts_versiones
            SET eliminado_operativo = 0,
                estado_version = 'INACTIVA',
                es_activa = 0,
                fecha_eliminado_operativo = NULL,
                usuario_eliminado_operativo = NULL,
                motivo_eliminado_operativo = NULL,
                fecha_actualizacion = SYSDATETIME()
            WHERE id_version = ?
        """
    elif entidad == "usuarios":
        consulta = """
            UPDATE dbo.usuarios
            SET eliminado_operativo = 0,
                activo = 0,
                bloqueado = 0,
                fecha_eliminado_operativo = NULL,
                usuario_eliminado_operativo = NULL,
                motivo_eliminado_operativo = NULL,
                usuario_actualizacion = ?,
                fecha_actualizacion = SYSDATETIME()
            WHERE id_usuario = ?
        """
    else:
        consulta = f"""
            UPDATE {cfg['tabla']}
            SET eliminado_operativo = 0,
                activo = 0,
                fecha_eliminado_operativo = NULL,
                usuario_eliminado_operativo = NULL,
                motivo_eliminado_operativo = NULL,
                usuario_actualizacion = ?,
                fecha_actualizacion = SYSDATETIME()
            WHERE {cfg['id']} = ?
        """
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        if entidad == "scripts_versiones":
            cursor.execute(consulta, id_registro)
        else:
            cursor.execute(consulta, usuario, id_registro)
        conexion.commit()


def eliminar_permanente(entidad, id_registro):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        if entidad == "usuarios":
            cursor.execute("DELETE FROM dbo.usuarios_roles WHERE id_usuario = ?", id_registro)
            cursor.execute("DELETE FROM dbo.usuarios WHERE id_usuario = ?", id_registro)
        elif entidad in ("clientes", "categorias", "tipos"):
            cfg = ENTIDADES[entidad]
            cursor.execute(f"DELETE FROM {cfg['tabla']} WHERE {cfg['id']} = ?", id_registro)
        elif entidad == "tareas":
            _validar_desacople_historico(cursor, entidad, id_registro)
            ids_scripts = _ids_scripts_tarea(cursor, id_registro)
            ids_versiones = _ids_versiones_scripts(cursor, ids_scripts)
            _asegurar_snapshots_tarea(cursor, id_registro)
            _validar_snapshots_tarea(cursor, id_registro)
            cursor.execute("UPDATE dbo.ejecuciones SET id_tarea = NULL WHERE id_tarea = ?", id_registro)
            cursor.execute("UPDATE dbo.logs_tareas SET id_tarea = NULL WHERE id_tarea = ?", id_registro)
            for id_script in ids_scripts:
                cursor.execute("UPDATE dbo.ejecuciones SET id_script = NULL WHERE id_script = ?", id_script)
            for id_version in ids_versiones:
                cursor.execute("UPDATE dbo.ejecuciones SET id_version = NULL WHERE id_version = ?", id_version)
            if _existe_tabla(cursor, "dbo.scheduler_eventos") and _existe_columna(cursor, "dbo.scheduler_eventos", "id_tarea"):
                cursor.execute("UPDATE dbo.scheduler_eventos SET id_tarea = NULL WHERE id_tarea = ?", id_registro)
            cursor.execute("DELETE FROM dbo.programaciones WHERE id_tarea = ?", id_registro)
            cursor.execute("UPDATE dbo.scripts SET id_version_activa = NULL WHERE id_tarea = ?", id_registro)
            cursor.execute(
                """
                DELETE FROM dbo.scripts_versiones
                WHERE id_script IN (
                    SELECT id_script FROM dbo.scripts WHERE id_tarea = ?
                )
                  AND ISNULL(eliminado_operativo, 0) = 1
                """,
                id_registro,
            )
            cursor.execute("DELETE FROM dbo.scripts WHERE id_tarea = ? AND ISNULL(eliminado_operativo, 0) = 1", id_registro)
            cursor.execute("DELETE FROM dbo.tareas WHERE id_tarea = ?", id_registro)
        elif entidad == "scripts":
            _validar_desacople_historico(cursor, entidad, id_registro)
            ids_versiones = _ids_versiones_scripts(cursor, [id_registro])
            _asegurar_snapshots_script(cursor, id_registro)
            _validar_snapshots_script(cursor, id_registro)
            cursor.execute("UPDATE dbo.ejecuciones SET id_script = NULL WHERE id_script = ?", id_registro)
            for id_version in ids_versiones:
                cursor.execute("UPDATE dbo.ejecuciones SET id_version = NULL WHERE id_version = ?", id_version)
            cursor.execute("UPDATE dbo.scripts SET id_version_activa = NULL WHERE id_script = ?", id_registro)
            cursor.execute(
                "DELETE FROM dbo.scripts_versiones WHERE id_script = ? AND ISNULL(eliminado_operativo, 0) = 1",
                id_registro,
            )
            cursor.execute("DELETE FROM dbo.scripts WHERE id_script = ?", id_registro)
        elif entidad == "scripts_versiones":
            _validar_desacople_historico(cursor, entidad, id_registro)
            _asegurar_snapshots_version(cursor, id_registro)
            _validar_snapshots_version(cursor, id_registro)
            cursor.execute("UPDATE dbo.ejecuciones SET id_version = NULL WHERE id_version = ?", id_registro)
            cursor.execute("UPDATE dbo.scripts SET id_version_activa = NULL WHERE id_version_activa = ?", id_registro)
            cursor.execute("DELETE FROM dbo.scripts_versiones WHERE id_version = ?", id_registro)
        conexion.commit()


def _ids_scripts_tarea(cursor, id_tarea):
    cursor.execute("SELECT id_script FROM dbo.scripts WHERE id_tarea = ?", id_tarea)
    return [int(fila[0]) for fila in cursor.fetchall()]


def _ids_versiones_scripts(cursor, ids_scripts):
    ids_versiones = []
    for id_script in ids_scripts:
        cursor.execute("SELECT id_version FROM dbo.scripts_versiones WHERE id_script = ?", id_script)
        ids_versiones.extend(int(fila[0]) for fila in cursor.fetchall())
    return ids_versiones


def _validar_desacople_historico(cursor, entidad, id_registro):
    deps = _dependencias_desacople_historico(cursor, entidad, id_registro)
    if deps.get("migracion_desacople_pendiente", 0) > 0:
        raise RuntimeError(MENSAJE_MIGRACION_DESACOPLE)


def _dependencias_desacople_historico(cursor, entidad, id_registro):
    if entidad == "tareas":
        migracion_pendiente = not (
            _columna_nullable(cursor, "dbo.ejecuciones", "id_tarea")
            and _columna_nullable(cursor, "dbo.ejecuciones", "id_script")
            and _columna_nullable(cursor, "dbo.ejecuciones", "id_version")
            and _columna_nullable(cursor, "dbo.logs_tareas", "id_tarea")
            and not _existe_fk(cursor, "dbo.ejecuciones", "FK_ejecuciones_tareas")
            and not _existe_fk(cursor, "dbo.ejecuciones", "FK_ejecuciones_scripts")
            and not _existe_fk(cursor, "dbo.ejecuciones", "FK_ejecuciones_scripts_versiones")
            and not _existe_fk(cursor, "dbo.logs_tareas", "FK_logs_tareas_tareas")
        )
        return {
            "migracion_desacople_pendiente": int(migracion_pendiente),
            "snapshots_incompletos": _contar_snapshots_tarea_incompletos(cursor, id_registro),
        }
    if entidad == "scripts":
        migracion_pendiente = not (
            _columna_nullable(cursor, "dbo.ejecuciones", "id_script")
            and _columna_nullable(cursor, "dbo.ejecuciones", "id_version")
            and not _existe_fk(cursor, "dbo.ejecuciones", "FK_ejecuciones_scripts")
            and not _existe_fk(cursor, "dbo.ejecuciones", "FK_ejecuciones_scripts_versiones")
        )
        return {
            "migracion_desacople_pendiente": int(migracion_pendiente),
            "snapshots_incompletos": _contar_snapshots_script_incompletos(cursor, id_registro),
        }
    if entidad == "scripts_versiones":
        migracion_pendiente = not (
            _columna_nullable(cursor, "dbo.ejecuciones", "id_version")
            and not _existe_fk(cursor, "dbo.ejecuciones", "FK_ejecuciones_scripts_versiones")
        )
        return {
            "migracion_desacople_pendiente": int(migracion_pendiente),
            "snapshots_incompletos": _contar_snapshots_version_incompletos(cursor, id_registro),
        }
    return {"migracion_desacople_pendiente": 0, "snapshots_incompletos": 0}


def _asegurar_snapshots_tarea(cursor, id_tarea):
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
            version_script_snapshot = COALESCE(e.version_script_snapshot, CONVERT(nvarchar(20), v.numero_version)),
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
    if _existe_tabla(cursor, "dbo.scheduler_eventos") and _existe_columna(cursor, "dbo.scheduler_eventos", "id_tarea_original"):
        cursor.execute(
            """
            UPDATE se
            SET id_tarea_original = COALESCE(se.id_tarea_original, se.id_tarea),
                nombre_tarea_snapshot = COALESCE(se.nombre_tarea_snapshot, t.nombre_tarea),
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


def _asegurar_snapshots_script(cursor, id_script):
    cursor.execute(
        """
        UPDATE e
        SET nombre_script_snapshot = COALESCE(e.nombre_script_snapshot, s.nombre_script),
            nombre_archivo_snapshot = COALESCE(e.nombre_archivo_snapshot, v.nombre_archivo),
            version_script_snapshot = COALESCE(e.version_script_snapshot, CONVERT(nvarchar(20), v.numero_version))
        FROM dbo.ejecuciones e
        LEFT JOIN dbo.scripts s ON s.id_script = e.id_script
        LEFT JOIN dbo.scripts_versiones v ON v.id_version = e.id_version
        WHERE e.id_script = ?
        """,
        id_script,
    )


def _asegurar_snapshots_version(cursor, id_version):
    cursor.execute(
        """
        UPDATE e
        SET nombre_script_snapshot = COALESCE(e.nombre_script_snapshot, s.nombre_script),
            nombre_archivo_snapshot = COALESCE(e.nombre_archivo_snapshot, v.nombre_archivo),
            version_script_snapshot = COALESCE(e.version_script_snapshot, CONVERT(nvarchar(20), v.numero_version))
        FROM dbo.ejecuciones e
        LEFT JOIN dbo.scripts_versiones v ON v.id_version = e.id_version
        LEFT JOIN dbo.scripts s ON s.id_script = v.id_script
        WHERE e.id_version = ?
        """,
        id_version,
    )


def _validar_snapshots_tarea(cursor, id_tarea):
    incompletos = _contar_snapshots_tarea_incompletos(cursor, id_tarea)
    if incompletos > 0:
        raise RuntimeError(MENSAJE_SNAPSHOTS_INSUFICIENTES)


def _validar_snapshots_script(cursor, id_script):
    incompletos = _contar_snapshots_script_incompletos(cursor, id_script)
    if incompletos > 0:
        raise RuntimeError(MENSAJE_SNAPSHOTS_INSUFICIENTES)


def _validar_snapshots_version(cursor, id_version):
    incompletos = _contar_snapshots_version_incompletos(cursor, id_version)
    if incompletos > 0:
        raise RuntimeError(MENSAJE_SNAPSHOTS_INSUFICIENTES)


def _contar_snapshots_tarea_incompletos(cursor, id_tarea):
    cursor.execute(
        """
        SELECT COUNT(1)
        FROM dbo.ejecuciones
        WHERE id_tarea = ?
          AND (
              id_tarea_original IS NULL
              OR nombre_tarea_snapshot IS NULL
              OR cliente_snapshot IS NULL
              OR categoria_snapshot IS NULL
              OR tipo_snapshot IS NULL
              OR nombre_script_snapshot IS NULL
              OR nombre_archivo_snapshot IS NULL
              OR version_script_snapshot IS NULL
          )
        """,
        id_tarea,
    )
    return int(cursor.fetchone()[0] or 0)


def _contar_snapshots_script_incompletos(cursor, id_script):
    cursor.execute(
        """
        SELECT COUNT(1)
        FROM dbo.ejecuciones
        WHERE id_script = ?
          AND (
              nombre_script_snapshot IS NULL
              OR nombre_archivo_snapshot IS NULL
              OR version_script_snapshot IS NULL
          )
        """,
        id_script,
    )
    return int(cursor.fetchone()[0] or 0)


def _contar_snapshots_version_incompletos(cursor, id_version):
    cursor.execute(
        """
        SELECT COUNT(1)
        FROM dbo.ejecuciones
        WHERE id_version = ?
          AND (
              nombre_script_snapshot IS NULL
              OR nombre_archivo_snapshot IS NULL
              OR version_script_snapshot IS NULL
          )
        """,
        id_version,
    )
    return int(cursor.fetchone()[0] or 0)


def dependencias(entidad, id_registro):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        if entidad == "usuarios":
            return _dependencias_usuario(cursor, id_registro)
        if entidad in ("clientes", "categorias", "tipos"):
            return _dependencias_mantenedor(cursor, entidad, id_registro)
        if entidad == "tareas":
            return _dependencias_tarea(cursor, id_registro)
        if entidad == "scripts":
            return _dependencias_script(cursor, id_registro)
        if entidad == "scripts_versiones":
            return _dependencias_version(cursor, id_registro)
    return {}


def _consulta_entidad(entidad, cfg):
    extras = {
        "usuarios": "NULL AS contexto, rol.codigo_rol AS codigo_rol",
        "clientes": "NULL AS contexto, NULL AS codigo_rol",
        "categorias": "NULL AS contexto, NULL AS codigo_rol",
        "tipos": "NULL AS contexto, NULL AS codigo_rol",
        "tareas": "CONCAT(c.nombre_cliente, ' / ', ca.nombre_categoria, ' / ', ti.nombre_tipo) AS contexto, NULL AS codigo_rol",
        "scripts": "t.nombre_tarea AS contexto, NULL AS codigo_rol",
        "scripts_versiones": "CONCAT(s.nombre_script, ' / v', m.numero_version) AS contexto, NULL AS codigo_rol",
    }[entidad]
    joins = {
        "usuarios": """
            OUTER APPLY (
                SELECT TOP 1 r.codigo_rol
                FROM dbo.usuarios_roles ur
                INNER JOIN dbo.roles r ON r.id_rol = ur.id_rol
                WHERE ur.id_usuario = u.id_usuario
                ORDER BY ur.fecha_creacion DESC
            ) rol
        """,
        "clientes": "",
        "categorias": "",
        "tipos": "",
        "tareas": """
            LEFT JOIN dbo.clientes c ON c.id_cliente = m.id_cliente
            LEFT JOIN dbo.categorias ca ON ca.id_categoria = m.id_categoria
            LEFT JOIN dbo.tipos ti ON ti.id_tipo = m.id_tipo
        """,
        "scripts": "LEFT JOIN dbo.tareas t ON t.id_tarea = m.id_tarea",
        "scripts_versiones": "LEFT JOIN dbo.scripts s ON s.id_script = m.id_script",
    }[entidad]
    alias = "u" if entidad == "usuarios" else "m"
    tabla = f"{cfg['tabla']} {alias}"
    return f"""
        SELECT {alias}.{cfg['id']} AS id_registro,
               {alias}.{cfg['nombre']} AS nombre,
               {alias}.{cfg['descripcion']} AS descripcion,
               {cfg.get('activo_expr_alias', f'{alias}.activo')} AS activo,
               {alias}.fecha_eliminado_operativo,
               {alias}.usuario_eliminado_operativo,
               {alias}.motivo_eliminado_operativo,
               {extras}
        FROM {tabla}
        {joins}
        WHERE ISNULL({alias}.eliminado_operativo, 0) = 1
    """


def _normalizar_fila(entidad, cfg, fila):
    fila.update(
        {
            "entidad": entidad,
            "entidad_label": cfg["label"],
            "descripcion": fila.get("descripcion") or fila.get("contexto") or "",
        }
    )
    return fila


def _dependencias_mantenedor(cursor, entidad, id_registro):
    campo = ENTIDADES[entidad]["campo_tarea"]
    cursor.execute(
        f"""
        SELECT
            SUM(CASE WHEN ISNULL(eliminado_operativo, 0) = 0 AND activo = 1 THEN 1 ELSE 0 END) AS tareas_activas,
            COUNT(1) AS tareas_total
        FROM dbo.tareas
        WHERE {campo} = ?
        """,
        id_registro,
    )
    fila = cursor.fetchone()
    return {"tareas_activas": int(fila[0] or 0), "tareas_total": int(fila[1] or 0)}


def _dependencias_usuario(cursor, id_usuario):
    cursor.execute(
        """
        SELECT u.usuario,
               ISNULL(rol.codigo_rol, '') AS codigo_rol
        FROM dbo.usuarios u
        OUTER APPLY (
            SELECT TOP 1 r.codigo_rol
            FROM dbo.usuarios_roles ur
            INNER JOIN dbo.roles r ON r.id_rol = ur.id_rol
            WHERE ur.id_usuario = u.id_usuario
            ORDER BY ur.fecha_creacion DESC
        ) rol
        WHERE u.id_usuario = ?
        """,
        id_usuario,
    )
    fila = cursor.fetchone()
    usuario = fila[0] if fila else ""
    codigo_rol = fila[1] if fila else ""
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
    historial = int(cursor.fetchone()[0] or 0)
    return {"usuario": usuario, "codigo_rol": codigo_rol, "historial": historial}


def _dependencias_tarea(cursor, id_tarea):
    cursor.execute(
        """
        SELECT COUNT(1)
        FROM dbo.ejecuciones
        WHERE id_tarea = ? AND estado_ejecucion = 'EN_EJECUCION'
        """,
        id_tarea,
    )
    en_curso = int(cursor.fetchone()[0] or 0)
    cursor.execute("SELECT COUNT(1) FROM dbo.scripts WHERE id_tarea = ? AND ISNULL(eliminado_operativo, 0) = 0", id_tarea)
    scripts_operativos = int(cursor.fetchone()[0] or 0)
    cursor.execute(
        """
        SELECT
            CAST(ISNULL(c.eliminado_operativo, 0) AS INT) +
            CAST(ISNULL(ca.eliminado_operativo, 0) AS INT) +
            CAST(ISNULL(ti.eliminado_operativo, 0) AS INT)
        FROM dbo.tareas t
        LEFT JOIN dbo.clientes c ON c.id_cliente = t.id_cliente
        LEFT JOIN dbo.categorias ca ON ca.id_categoria = t.id_categoria
        LEFT JOIN dbo.tipos ti ON ti.id_tipo = t.id_tipo
        WHERE t.id_tarea = ?
        """,
        id_tarea,
    )
    maestros_eliminados = int(cursor.fetchone()[0] or 0)
    resultado = {
        "ejecuciones_en_curso": en_curso,
        "scripts_operativos": scripts_operativos,
        "maestros_eliminados": maestros_eliminados,
    }
    resultado.update(_dependencias_desacople_historico(cursor, "tareas", id_tarea))
    return resultado


def _dependencias_script(cursor, id_script):
    cursor.execute(
        """
        SELECT COUNT(1)
        FROM dbo.tareas t
        INNER JOIN dbo.scripts s ON s.id_tarea = t.id_tarea
        WHERE s.id_script = ?
          AND ISNULL(t.eliminado_operativo, 0) = 0
          AND t.activo = 1
        """,
        id_script,
    )
    tareas_vigentes = int(cursor.fetchone()[0] or 0)
    cursor.execute(
        "SELECT COUNT(1) FROM dbo.scripts_versiones WHERE id_script = ? AND ISNULL(eliminado_operativo, 0) = 0",
        id_script,
    )
    versiones_operativas = int(cursor.fetchone()[0] or 0)
    cursor.execute(
        """
        SELECT COUNT(1)
        FROM dbo.scripts s
        INNER JOIN dbo.tareas t ON t.id_tarea = s.id_tarea
        WHERE s.id_script = ?
          AND ISNULL(t.eliminado_operativo, 0) = 1
        """,
        id_script,
    )
    tarea_eliminada = int(cursor.fetchone()[0] or 0)
    resultado = {
        "tareas_vigentes": tareas_vigentes,
        "versiones_operativas": versiones_operativas,
        "tarea_eliminada": tarea_eliminada,
    }
    resultado.update(_dependencias_desacople_historico(cursor, "scripts", id_script))
    return resultado


def _dependencias_version(cursor, id_version):
    cursor.execute("SELECT COUNT(1) FROM dbo.scripts WHERE id_version_activa = ? AND ISNULL(eliminado_operativo, 0) = 0", id_version)
    activa = int(cursor.fetchone()[0] or 0)
    cursor.execute(
        """
        SELECT COUNT(1)
        FROM dbo.scripts_versiones v
        INNER JOIN dbo.scripts s ON s.id_script = v.id_script
        WHERE v.id_version = ?
          AND ISNULL(s.eliminado_operativo, 0) = 1
        """,
        id_version,
    )
    script_eliminado = int(cursor.fetchone()[0] or 0)
    resultado = {"version_activa": activa, "script_eliminado": script_eliminado}
    resultado.update(_dependencias_desacople_historico(cursor, "scripts_versiones", id_version))
    return resultado
