from app.database.conexion import obtener_conexion


def _fila_a_dict(cursor, fila):
    columnas = [columna[0] for columna in cursor.description]
    return dict(zip(columnas, fila))


def _columnas_eventos():
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT name
            FROM sys.columns
            WHERE object_id = OBJECT_ID('dbo.scheduler_eventos')
            """
        )
        return {fila[0] for fila in cursor.fetchall()}


def insertar_evento_programador(evento):
    columnas = _columnas_eventos()
    if {"id_tarea_original", "nombre_tarea_snapshot", "cliente_snapshot", "categoria_snapshot", "tipo_snapshot"}.issubset(columnas):
        return _insertar_evento_programador_con_snapshots(evento)

    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            INSERT INTO dbo.scheduler_eventos
                (nombre_worker, id_tarea, nombre_tarea, id_programacion,
                 fecha_programada, clave_programacion, tipo_evento, decision,
                 motivo, detalle, estado_scheduler, ejecutar_en_feriados,
                 es_feriado, nombre_feriado, origen, activo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'SCHEDULER', 1)
            """,
            evento.get("nombre_worker"),
            evento.get("id_tarea"),
            evento.get("nombre_tarea"),
            evento.get("id_programacion"),
            evento.get("fecha_programada"),
            evento.get("clave_programacion"),
            evento["tipo_evento"],
            evento["decision"],
            evento.get("motivo"),
            evento.get("detalle"),
            evento.get("estado_scheduler"),
            evento.get("ejecutar_en_feriados"),
            evento.get("es_feriado"),
            evento.get("nombre_feriado"),
        )
        conexion.commit()


def _insertar_evento_programador_con_snapshots(evento):
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            INSERT INTO dbo.scheduler_eventos
                (nombre_worker, id_tarea, nombre_tarea, id_tarea_original,
                 nombre_tarea_snapshot, cliente_snapshot, categoria_snapshot,
                 tipo_snapshot, id_programacion, fecha_programada,
                 clave_programacion, tipo_evento, decision, motivo, detalle,
                 estado_scheduler, ejecutar_en_feriados, es_feriado,
                 nombre_feriado, origen, activo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'SCHEDULER', 1)
            """,
            evento.get("nombre_worker"),
            evento.get("id_tarea"),
            evento.get("nombre_tarea"),
            evento.get("id_tarea"),
            evento.get("nombre_tarea"),
            evento.get("cliente_snapshot"),
            evento.get("categoria_snapshot"),
            evento.get("tipo_snapshot"),
            evento.get("id_programacion"),
            evento.get("fecha_programada"),
            evento.get("clave_programacion"),
            evento["tipo_evento"],
            evento["decision"],
            evento.get("motivo"),
            evento.get("detalle"),
            evento.get("estado_scheduler"),
            evento.get("ejecutar_en_feriados"),
            evento.get("es_feriado"),
            evento.get("nombre_feriado"),
        )
        conexion.commit()


def listar_eventos_programador(filtros=None, limite=10):
    columnas = _columnas_eventos()
    nombre_tarea_select = "COALESCE(nombre_tarea_snapshot, nombre_tarea, 'Tarea eliminada') AS nombre_tarea" if "nombre_tarea_snapshot" in columnas else "COALESCE(nombre_tarea, 'Tarea eliminada') AS nombre_tarea"
    nombre_tarea_filtro = "COALESCE(nombre_tarea_snapshot, nombre_tarea)" if "nombre_tarea_snapshot" in columnas else "nombre_tarea"
    filtros = filtros or {}
    condiciones = ["activo = 1"]
    parametros = []

    if filtros.get("fecha_desde"):
        condiciones.append("fecha_evento >= ?")
        parametros.append(filtros["fecha_desde"])
    if filtros.get("fecha_hasta"):
        condiciones.append("fecha_evento < DATEADD(day, 1, ?)")
        parametros.append(filtros["fecha_hasta"])
    if filtros.get("tarea"):
        condiciones.append(f"({nombre_tarea_filtro} LIKE ? OR CONVERT(varchar(20), id_tarea) = ?)")
        parametros.extend([f"%{filtros['tarea']}%", filtros["tarea"]])
    if filtros.get("decision"):
        condiciones.append("decision = ?")
        parametros.append(filtros["decision"])
    if filtros.get("motivo"):
        condiciones.append("motivo = ?")
        parametros.append(filtros["motivo"])
    if filtros.get("worker"):
        condiciones.append("nombre_worker LIKE ?")
        parametros.append(f"%{filtros['worker']}%")

    consulta = f"""
        SELECT TOP ({int(limite)})
               id_evento, fecha_evento, nombre_worker, id_tarea, {nombre_tarea_select},
               id_programacion, fecha_programada, clave_programacion,
               tipo_evento, decision, motivo, detalle, estado_scheduler,
               ejecutar_en_feriados, es_feriado, nombre_feriado, origen
        FROM dbo.scheduler_eventos
        WHERE {" AND ".join(condiciones)}
        ORDER BY fecha_evento DESC, id_evento DESC
    """

    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(consulta, *parametros)
        return [_fila_a_dict(cursor, fila) for fila in cursor.fetchall()]


def resumir_eventos_recientes(limite=10):
    return listar_eventos_programador(limite=limite)


def obtener_resumen_eventos_hoy():
    columnas = _columnas_eventos()
    nombre_tarea_select = "COALESCE(nombre_tarea_snapshot, nombre_tarea, 'Tarea eliminada') AS nombre_tarea" if "nombre_tarea_snapshot" in columnas else "COALESCE(nombre_tarea, 'Tarea eliminada') AS nombre_tarea"
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT
                COUNT(1) AS eventos_hoy,
                SUM(CASE WHEN decision = 'EJECUTAR' OR tipo_evento = 'TAREA_EJECUTADA' THEN 1 ELSE 0 END) AS tareas_ejecutadas,
                SUM(CASE WHEN decision = 'OMITIR' OR tipo_evento = 'TAREA_OMITIDA' THEN 1 ELSE 0 END) AS tareas_omitidas,
                SUM(CASE WHEN decision = 'ERROR' OR tipo_evento = 'ERROR_SCHEDULER' THEN 1 ELSE 0 END) AS errores_programador
            FROM dbo.scheduler_eventos
            WHERE activo = 1
              AND fecha_evento >= CONVERT(date, GETDATE())
              AND fecha_evento < DATEADD(day, 1, CONVERT(date, GETDATE()))
            """
        )
        fila = cursor.fetchone()
        resumen = _fila_a_dict(cursor, fila) if fila else {}

        cursor.execute(
            f"""
            SELECT TOP (1)
                   id_evento, fecha_evento, nombre_worker, id_tarea, {nombre_tarea_select},
                   id_programacion, fecha_programada, clave_programacion,
                   tipo_evento, decision, motivo, detalle, estado_scheduler,
                   ejecutar_en_feriados, es_feriado, nombre_feriado, origen
            FROM dbo.scheduler_eventos
            WHERE activo = 1
            ORDER BY fecha_evento DESC, id_evento DESC
            """
        )
        ultimo = cursor.fetchone()
        resumen["ultimo_evento"] = _fila_a_dict(cursor, ultimo) if ultimo else None
        return resumen


def obtener_omisiones_por_motivo_hoy():
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT ISNULL(motivo, 'OTROS') AS motivo, COUNT(1) AS total
            FROM dbo.scheduler_eventos
            WHERE activo = 1
              AND (decision = 'OMITIR' OR tipo_evento = 'TAREA_OMITIDA')
              AND fecha_evento >= CONVERT(date, GETDATE())
              AND fecha_evento < DATEADD(day, 1, CONVERT(date, GETDATE()))
            GROUP BY ISNULL(motivo, 'OTROS')
            ORDER BY total DESC, motivo ASC
            """
        )
        return [_fila_a_dict(cursor, fila) for fila in cursor.fetchall()]


def obtener_eventos_relevantes_recientes(limite=10):
    columnas = _columnas_eventos()
    nombre_tarea_select = "COALESCE(nombre_tarea_snapshot, nombre_tarea, 'Tarea eliminada') AS nombre_tarea" if "nombre_tarea_snapshot" in columnas else "COALESCE(nombre_tarea, 'Tarea eliminada') AS nombre_tarea"
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            f"""
            SELECT TOP ({int(limite)})
                   id_evento, fecha_evento, nombre_worker, id_tarea, {nombre_tarea_select},
                   id_programacion, fecha_programada, clave_programacion,
                   tipo_evento, decision, motivo, detalle, estado_scheduler,
                   ejecutar_en_feriados, es_feriado, nombre_feriado, origen
            FROM dbo.scheduler_eventos
            WHERE activo = 1
              AND (
                    tipo_evento = 'ERROR_SCHEDULER'
                 OR decision = 'ERROR'
                 OR tipo_evento = 'TAREA_EJECUTADA'
                 OR (
                        tipo_evento = 'TAREA_OMITIDA'
                    AND motivo IN ('FERIADO','EJECUCION_EN_CURSO','DUPLICADO_SLOT','LIMITE_CONCURRENCIA')
                    )
              )
            ORDER BY fecha_evento DESC, id_evento DESC
            """
        )
        return [_fila_a_dict(cursor, fila) for fila in cursor.fetchall()]


def desactivar_eventos_antiguos(dias_retencion=90):
    dias = max(1, int(dias_retencion or 90))
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            UPDATE dbo.scheduler_eventos
               SET activo = 0
             WHERE activo = 1
               AND fecha_evento < DATEADD(day, ?, GETDATE())
            """,
            -dias,
        )
        afectados = cursor.rowcount if cursor.rowcount is not None else 0
        conexion.commit()
        return afectados


def contar_eventos_limpiables_antiguos(dias_retencion, categorias):
    dias = int(dias_retencion)
    detalle = []
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            """
            SELECT CONVERT(varchar(19), DATEADD(day, ?, SYSDATETIME()), 120)
            """,
            -dias,
        )
        fila_limite = cursor.fetchone()
        fecha_limite = fila_limite[0] if fila_limite else None

        for categoria in categorias:
            cursor.execute(
                f"""
                SELECT COUNT(1) AS total
                FROM dbo.scheduler_eventos
                WHERE fecha_evento < DATEADD(day, ?, SYSDATETIME())
                  AND ({categoria['condicion_sql']})
                """,
                -dias,
            )
            fila = cursor.fetchone()
            detalle.append({
                "clave": categoria["clave"],
                "nombre": categoria["nombre"],
                "total": int(fila[0] or 0) if fila else 0,
            })

    return {
        "total": sum(item["total"] for item in detalle),
        "fecha_limite": fecha_limite,
        "detalle": detalle,
    }


def contar_eventos_informativos_antiguos(dias_retencion):
    return contar_eventos_limpiables_antiguos(
        dias_retencion,
        [
            {"clave": "ciclo_iniciado", "nombre": "Ciclos iniciados", "condicion_sql": "tipo_evento = 'CICLO_INICIADO'"},
            {"clave": "ciclo_finalizado", "nombre": "Ciclos finalizados", "condicion_sql": "tipo_evento = 'CICLO_FINALIZADO'"},
            {"clave": "fuera_ventana", "nombre": "Omitidas por fuera de ventana", "condicion_sql": "tipo_evento = 'TAREA_OMITIDA' AND motivo = 'FUERA_DE_VENTANA'"},
        ],
    )


def eliminar_eventos_limpiables_antiguos(dias_retencion, categorias):
    dias = int(dias_retencion)
    condiciones = [f"({categoria['condicion_sql']})" for categoria in categorias]
    where_categorias = " OR ".join(condiciones)
    previo = contar_eventos_limpiables_antiguos(dias, categorias)
    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            f"""
            DELETE FROM dbo.scheduler_eventos
            WHERE fecha_evento < DATEADD(day, ?, SYSDATETIME())
              AND ({where_categorias})
            """,
            -dias,
        )
        eliminados = cursor.rowcount if cursor.rowcount is not None else 0
        conexion.commit()
        return {
            "ok": True,
            "dias": dias,
            "fecha_limite": previo.get("fecha_limite"),
            "eliminados": int(eliminados or 0),
            "detalle": previo.get("detalle", []),
            "categorias": [categoria["clave"] for categoria in categorias],
        }


def eliminar_eventos_informativos_antiguos(dias_retencion):
    return eliminar_eventos_limpiables_antiguos(
        dias_retencion,
        [
            {"clave": "ciclo_iniciado", "nombre": "Ciclos iniciados", "condicion_sql": "tipo_evento = 'CICLO_INICIADO'"},
            {"clave": "ciclo_finalizado", "nombre": "Ciclos finalizados", "condicion_sql": "tipo_evento = 'CICLO_FINALIZADO'"},
            {"clave": "fuera_ventana", "nombre": "Omitidas por fuera de ventana", "condicion_sql": "tipo_evento = 'TAREA_OMITIDA' AND motivo = 'FUERA_DE_VENTANA'"},
        ],
    )


def listar_eventos_programador_paginado(filtros=None, page=1, per_page=25):
    filtros = filtros or {}
    page = max(1, int(page or 1))
    per_page = int(per_page or 25)
    if per_page not in {10, 25, 50, 100}:
        per_page = 25

    columnas = _columnas_eventos()
    nombre_tarea_select = "COALESCE(nombre_tarea_snapshot, nombre_tarea, 'Tarea eliminada') AS nombre_tarea" if "nombre_tarea_snapshot" in columnas else "COALESCE(nombre_tarea, 'Tarea eliminada') AS nombre_tarea"
    condiciones, parametros = _condiciones_eventos(filtros, columnas)
    where_sql = " AND ".join(condiciones)
    offset = (page - 1) * per_page

    with obtener_conexion() as conexion:
        cursor = conexion.cursor()
        cursor.execute(
            f"""
            SELECT COUNT(1) AS total
            FROM dbo.scheduler_eventos
            WHERE {where_sql}
            """,
            *parametros,
        )
        fila_total = cursor.fetchone()
        total = int(fila_total[0] or 0) if fila_total else 0
        total_paginas = max(1, (total + per_page - 1) // per_page)
        if page > total_paginas:
            page = total_paginas
            offset = (page - 1) * per_page

        cursor.execute(
            f"""
            SELECT id_evento, fecha_evento, nombre_worker, id_tarea, {nombre_tarea_select},
                   id_programacion, fecha_programada, clave_programacion,
                   tipo_evento, decision, motivo, detalle, estado_scheduler,
                   ejecutar_en_feriados, es_feriado, nombre_feriado, origen
            FROM dbo.scheduler_eventos
            WHERE {where_sql}
            ORDER BY fecha_evento DESC, id_evento DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """,
            *parametros,
            offset,
            per_page,
        )
        eventos = [_fila_a_dict(cursor, fila) for fila in cursor.fetchall()]

    return {"eventos": eventos, "total": total, "page": page, "per_page": per_page}


def _condiciones_eventos(filtros, columnas=None):
    columnas = columnas or set()
    nombre_tarea_filtro = "COALESCE(nombre_tarea_snapshot, nombre_tarea)" if "nombre_tarea_snapshot" in columnas else "nombre_tarea"
    condiciones = ["activo = 1"]
    parametros = []

    if filtros.get("fecha_desde"):
        condiciones.append("fecha_evento >= ?")
        parametros.append(filtros["fecha_desde"])
    if filtros.get("fecha_hasta"):
        condiciones.append("fecha_evento < DATEADD(day, 1, ?)")
        parametros.append(filtros["fecha_hasta"])
    if filtros.get("tarea"):
        condiciones.append(f"({nombre_tarea_filtro} LIKE ? OR CONVERT(varchar(20), id_tarea) = ?)")
        parametros.extend([f"%{filtros['tarea']}%", filtros["tarea"]])
    if filtros.get("tipo_evento"):
        condiciones.append("tipo_evento = ?")
        parametros.append(filtros["tipo_evento"])
    if filtros.get("decision"):
        condiciones.append("decision = ?")
        parametros.append(filtros["decision"])
    if filtros.get("motivo"):
        condiciones.append("motivo = ?")
        parametros.append(filtros["motivo"])
    if filtros.get("worker"):
        condiciones.append("nombre_worker LIKE ?")
        parametros.append(f"%{filtros['worker']}%")
    if filtros.get("texto"):
        condiciones.append("(detalle LIKE ? OR clave_programacion LIKE ? OR nombre_feriado LIKE ?)")
        texto = f"%{filtros['texto']}%"
        parametros.extend([texto, texto, texto])

    return condiciones, parametros
