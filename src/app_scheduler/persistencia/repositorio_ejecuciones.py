"""Persistencia del motor unico de ejecuciones manuales y automaticas."""

from __future__ import annotations

from app_scheduler.persistencia.modelos import (
    ContextoEjecucion,
    DetalleEjecucion,
    EjecucionResumen,
    Pagina,
    Paginacion,
)
from app_scheduler.persistencia.repositorio import RepositorioSQL


class RepositorioEjecuciones(RepositorioSQL):
    def adquirir_lock_despacho(self) -> bool:
        resultado = self.ejecutar_escalar(
            """DECLARE @resultado int;
EXEC @resultado = sys.sp_getapplock
    @Resource = 'APP_SCHEDULER_SCHEDULER_DESPACHO',
    @LockMode = 'Exclusive', @LockOwner = 'Transaction', @LockTimeout = 0;
SELECT @resultado;""",
            operacion="adquirir_lock_despacho_manual",
        )
        return resultado is not None and int(resultado) >= 0

    def obtener_configuracion(self):
        return self.ejecutar_uno(
            """SELECT TOP 1 max_ejecuciones_concurrentes, modo_mantenimiento,
intervalo_revision_segundos
FROM dbo.configuracion_scheduler
WHERE activo = 1 ORDER BY id_configuracion""",
            operacion="obtener_configuracion_ejecuciones",
        )

    def contar_ocupadas(self) -> int:
        return int(self.ejecutar_escalar(
            """SELECT COUNT(1) FROM dbo.ejecuciones WITH (UPDLOCK, HOLDLOCK)
WHERE estado_ejecucion IN ('PENDIENTE','EN_EJECUCION')""",
            operacion="contar_ejecuciones_ocupadas",
        ) or 0)

    def contar_en_ejecucion(self) -> int:
        return int(self.ejecutar_escalar(
            "SELECT COUNT(1) FROM dbo.ejecuciones WHERE estado_ejecucion = 'EN_EJECUCION'",
            operacion="contar_ejecuciones_activas",
        ) or 0)

    def obtener_contexto_manual(self, id_tarea: int):
        return self.ejecutar_uno(
            """SELECT t.id_tarea, t.nombre_tarea, c.nombre_cliente, g.nombre_categoria,
p.nombre_tipo, t.estado_tarea, t.activo, t.permite_ejecucion_manual,
s.id_script, s.nombre_script, s.activo, s.id_version_activa,
v.id_version, v.numero_version, v.nombre_archivo, v.ruta_fisica,
v.ruta_relativa, v.estado_version, v.es_activa, v.requiere_env,
v.ruta_env_fisica, v.ruta_env_relativa,
CASE WHEN EXISTS (
    SELECT 1 FROM dbo.ejecuciones e
    WHERE e.id_tarea = t.id_tarea
      AND e.estado_ejecucion IN ('PENDIENTE','EN_EJECUCION')
) THEN 1 ELSE 0 END AS tiene_ejecucion
FROM dbo.tareas t WITH (UPDLOCK, HOLDLOCK)
JOIN dbo.clientes c ON c.id_cliente = t.id_cliente
JOIN dbo.categorias g ON g.id_categoria = t.id_categoria
JOIN dbo.tipos p ON p.id_tipo = t.id_tipo
LEFT JOIN dbo.scripts s ON s.id_tarea = t.id_tarea AND s.eliminado_operativo = 0
LEFT JOIN dbo.scripts_versiones v ON v.id_version = s.id_version_activa
    AND v.eliminado_operativo = 0
WHERE t.id_tarea = ? AND t.eliminado_operativo = 0""",
            (id_tarea,), operacion="obtener_contexto_ejecucion_manual",
        )

    def reservar_manual(self, fila, usuario: str) -> int:
        resultado = self.ejecutar_uno(
            """INSERT INTO dbo.ejecuciones
    (id_tarea, id_script, id_version, origen_ejecucion, estado_ejecucion,
     fecha_hora_inicio, usuario_ejecucion, nombre_worker, id_tarea_original,
     nombre_tarea_snapshot, cliente_snapshot, categoria_snapshot, tipo_snapshot,
     nombre_script_snapshot, nombre_archivo_snapshot, version_script_snapshot,
     usuario_ejecucion_snapshot)
OUTPUT INSERTED.id_ejecucion
VALUES (?, ?, ?, 'MANUAL', 'PENDIENTE', SYSDATETIME(), ?, NULL, ?,
        ?, ?, ?, ?, ?, ?, ?, ?)""",
            (fila[0], fila[8], fila[12], usuario, fila[0], fila[1], fila[2],
             fila[3], fila[4], fila[9], fila[14], str(fila[13]), usuario),
            operacion="reservar_ejecucion_manual",
        )
        return int(resultado[0])

    def reclamar_siguiente(self, nombre_worker: str, limite: int) -> int | None:
        fila = self.ejecutar_uno(
            """SET NOCOUNT ON;
DECLARE @lock int;
DECLARE @reclamadas TABLE (id_ejecucion bigint NOT NULL);
EXEC @lock = sys.sp_getapplock
    @Resource = 'APP_SCHEDULER_MOTOR_CLAIM',
    @LockMode = 'Exclusive', @LockOwner = 'Transaction', @LockTimeout = 0;
IF @lock >= 0 AND (
    SELECT COUNT(1) FROM dbo.ejecuciones
    WHERE estado_ejecucion = 'EN_EJECUCION'
) < ?
BEGIN
;WITH siguiente AS (
    SELECT TOP (1) *
    FROM dbo.ejecuciones WITH (UPDLOCK, READPAST, ROWLOCK)
    WHERE estado_ejecucion = 'PENDIENTE'
    ORDER BY fecha_creacion, id_ejecucion
)
UPDATE siguiente
SET estado_ejecucion = 'EN_EJECUCION',
    fecha_hora_inicio = SYSDATETIME(),
    fecha_hora_termino = NULL,
    duracion_segundos = NULL,
    codigo_salida = NULL,
    mensaje_error = NULL,
    nombre_worker = ?
OUTPUT INSERTED.id_ejecucion INTO @reclamadas;
END;
SELECT TOP (1) id_ejecucion FROM @reclamadas;""",
            (limite, nombre_worker[:100]), operacion="reclamar_ejecucion_pendiente",
        )
        return None if fila is None else int(fila[0])

    def obtener_contexto(self, id_ejecucion: int) -> ContextoEjecucion | None:
        fila = self.ejecutar_uno(
            """SELECT e.id_ejecucion, e.id_tarea, e.id_script, e.id_version,
e.origen_ejecucion, e.estado_ejecucion, e.usuario_ejecucion, e.nombre_worker,
COALESCE(e.nombre_tarea_snapshot, t.nombre_tarea, N'Tarea historica'),
COALESCE(e.nombre_script_snapshot, s.nombre_script, N'Script historico'),
COALESCE(e.nombre_archivo_snapshot, v.nombre_archivo, N'Archivo historico'),
v.numero_version, v.ruta_fisica, v.ruta_relativa, v.requiere_env,
v.ruta_env_fisica, v.ruta_env_relativa,
CASE WHEN EXISTS (
    SELECT 1 FROM dbo.notificaciones_config_tarea n
    WHERE n.id_tarea = e.id_tarea AND n.activo = 1 AND n.enviar_evidencia = 1
) THEN 1 ELSE 0 END
FROM dbo.ejecuciones e
LEFT JOIN dbo.tareas t ON t.id_tarea = e.id_tarea
LEFT JOIN dbo.scripts s ON s.id_script = e.id_script
LEFT JOIN dbo.scripts_versiones v ON v.id_version = e.id_version
    AND v.id_script = e.id_script
WHERE e.id_ejecucion = ?""",
            (id_ejecucion,), operacion="obtener_contexto_motor",
        )
        if fila is None:
            return None
        if fila[2] is None or fila[3] is None or fila[11] is None or not fila[12]:
            return None
        return ContextoEjecucion(
            int(fila[0]), fila[1], int(fila[2]), int(fila[3]), str(fila[4]),
            str(fila[5]), fila[6], fila[7], str(fila[8]), str(fila[9]),
            str(fila[10]), int(fila[11]), str(fila[12]), str(fila[13]),
            bool(fila[14]), fila[15], fila[16], bool(fila[17]),
        )

    def registrar_pid(self, id_ejecucion: int, pid: int) -> bool:
        return self.ejecutar(
            """UPDATE dbo.ejecuciones SET pid_proceso = ?
WHERE id_ejecucion = ? AND estado_ejecucion = 'EN_EJECUCION'""",
            (pid, id_ejecucion), operacion="registrar_pid_ejecucion",
        ) == 1

    def crear_log(self, contexto: ContextoEjecucion, *, ruta_fisica: str,
                  ruta_relativa: str, nombre_archivo: str) -> None:
        self.ejecutar(
            """INSERT INTO dbo.logs_tareas
    (id_tarea, id_ejecucion, nombre_tarea, nombre_script, nombre_archivo_log,
     ruta_fisica_log, ruta_relativa_log, fecha_hora_inicio, estado_final,
     usuario_ejecucion)
VALUES (?, ?, ?, ?, ?, ?, ?, SYSDATETIME(), 'EN_EJECUCION', ?)""",
            (contexto.id_tarea, contexto.id_ejecucion, contexto.nombre_tarea,
             contexto.nombre_archivo, nombre_archivo, ruta_fisica, ruta_relativa,
             contexto.usuario_ejecucion), operacion="crear_log_ejecucion",
        )

    def cancelacion_solicitada(self, id_ejecucion: int) -> bool:
        return bool(self.ejecutar_escalar(
            """SELECT CASE WHEN fecha_hora_detencion IS NOT NULL THEN 1 ELSE 0 END
FROM dbo.ejecuciones WHERE id_ejecucion = ? AND estado_ejecucion = 'EN_EJECUCION'""",
            (id_ejecucion,), operacion="consultar_cancelacion_ejecucion",
        ) or 0)

    def solicitar_detencion(self, id_ejecucion: int, usuario: str, motivo: str) -> bool:
        return self.ejecutar(
            """UPDATE dbo.ejecuciones
SET usuario_detencion = ?, fecha_hora_detencion = SYSDATETIME(), motivo_detencion = ?
WHERE id_ejecucion = ? AND estado_ejecucion = 'EN_EJECUCION'
  AND fecha_hora_detencion IS NULL""",
            (usuario, motivo[:500], id_ejecucion),
            operacion="solicitar_detencion_ejecucion",
        ) == 1

    def finalizar(self, id_ejecucion: int, estado: str, codigo_salida: int | None,
                  mensaje_error: str | None, *, forzada: bool = False) -> bool:
        condicion = (
            "fecha_hora_detencion IS NOT NULL" if estado == "DETENIDA_MANUALMENTE"
            else "fecha_hora_detencion IS NULL"
        )
        actualizadas = self.ejecutar(
            f"""DECLARE @fin datetime2(0) = SYSDATETIME();
UPDATE dbo.ejecuciones
SET estado_ejecucion = ?, fecha_hora_termino = @fin,
    duracion_segundos = CASE WHEN DATEDIFF(SECOND, fecha_hora_inicio, @fin) < 0
        THEN 0 ELSE DATEDIFF(SECOND, fecha_hora_inicio, @fin) END,
    codigo_salida = ?, mensaje_error = ?, fue_detencion_forzada = ?
WHERE id_ejecucion = ? AND estado_ejecucion = 'EN_EJECUCION'
  AND {condicion}""",
            (estado, codigo_salida, mensaje_error, int(forzada), id_ejecucion),
            operacion="finalizar_ejecucion",
        )
        if actualizadas:
            self.ejecutar(
                """DECLARE @fin datetime2(0) = SYSDATETIME();
UPDATE dbo.logs_tareas SET estado_final = ?, fecha_hora_termino = @fin,
duracion_segundos = CASE WHEN DATEDIFF(SECOND, fecha_hora_inicio, @fin) < 0
    THEN 0 ELSE DATEDIFF(SECOND, fecha_hora_inicio, @fin) END,
codigo_salida = ?, mensaje_error = ? WHERE id_ejecucion = ?""",
                (estado, codigo_salida, mensaje_error, id_ejecucion),
                operacion="finalizar_log_ejecucion",
            )
        return bool(actualizadas)

    def registrar_evidencia(self, id_ejecucion: int, datos: dict) -> None:
        self.ejecutar(
            """INSERT INTO dbo.evidencias_ejecucion
    (id_ejecucion, estado_evidencia, version_contrato, tipo_evidencia, titulo,
     asunto_sugerido, hash_evidencia, cantidad_campos_resumen,
     cantidad_adjuntos_declarados, cantidad_problemas, bloque_detectado,
     delimitador_inicio_detectado, delimitador_fin_detectado, error_validacion)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (id_ejecucion, datos["estado_evidencia"], datos.get("version_contrato"),
             datos.get("tipo_evidencia"), datos.get("titulo"),
             datos.get("asunto_sugerido"), datos.get("hash_evidencia"),
             datos.get("cantidad_campos_resumen", 0),
             datos.get("cantidad_adjuntos_declarados", 0),
             datos.get("cantidad_problemas", 0), int(datos.get("bloque_detectado", False)),
             int(datos.get("delimitador_inicio_detectado", False)),
             int(datos.get("delimitador_fin_detectado", False)),
             datos.get("error_validacion")), operacion="registrar_evidencia_ejecucion",
        )

    def listar(self, paginacion: Paginacion, *, estado=None, origen=None) -> Pagina[EjecucionResumen]:
        filtros = ["1 = 1"]
        parametros: list[object] = []
        if estado:
            filtros.append("e.estado_ejecucion = ?"); parametros.append(estado)
        if origen:
            filtros.append("e.origen_ejecucion = ?"); parametros.append(origen)
        where = " AND ".join(filtros)
        total = int(self.ejecutar_escalar(
            f"SELECT COUNT(1) FROM dbo.ejecuciones e WHERE {where}", parametros,
            operacion="contar_ejecuciones",
        ) or 0)
        filas = self.ejecutar_lista(
            f"""SELECT e.id_ejecucion, e.id_tarea, e.origen_ejecucion,
e.estado_ejecucion, e.fecha_hora_inicio, e.fecha_hora_termino,
e.duracion_segundos, e.codigo_salida,
COALESCE(e.usuario_ejecucion_snapshot, e.usuario_ejecucion), e.nombre_worker,
COALESCE(e.nombre_tarea_snapshot, t.nombre_tarea, N'Tarea historica'),
COALESCE(e.nombre_script_snapshot, s.nombre_script, N'Script historico'),
COALESCE(e.nombre_archivo_snapshot, v.nombre_archivo, N'Archivo historico'),
COALESCE(e.version_script_snapshot, CONVERT(nvarchar(50), v.numero_version), N'-')
FROM dbo.ejecuciones e
LEFT JOIN dbo.tareas t ON t.id_tarea = e.id_tarea
LEFT JOIN dbo.scripts s ON s.id_script = e.id_script
LEFT JOIN dbo.scripts_versiones v ON v.id_version = e.id_version
WHERE {where}
ORDER BY e.fecha_hora_inicio DESC, e.id_ejecucion DESC
OFFSET ? ROWS FETCH NEXT ? ROWS ONLY""",
            (*parametros, paginacion.desplazamiento, paginacion.por_pagina),
            operacion="listar_ejecuciones",
        )
        elementos = tuple(EjecucionResumen(
            int(f[0]), f[1], str(f[2]), str(f[3]), f[4], f[5], f[6], f[7],
            f[8], f[9], str(f[10]), str(f[11]), str(f[12]), str(f[13]),
        ) for f in filas)
        return Pagina(elementos, total, paginacion.pagina, paginacion.por_pagina)

    def obtener_detalle(self, id_ejecucion: int) -> DetalleEjecucion | None:
        fila = self.ejecutar_uno(
            """SELECT e.id_ejecucion, e.id_tarea, e.origen_ejecucion,
e.estado_ejecucion, e.fecha_hora_inicio, e.fecha_hora_termino,
e.duracion_segundos, e.codigo_salida,
COALESCE(e.usuario_ejecucion_snapshot, e.usuario_ejecucion), e.nombre_worker,
COALESCE(e.nombre_tarea_snapshot, t.nombre_tarea, N'Tarea historica'),
COALESCE(e.nombre_script_snapshot, s.nombre_script, N'Script historico'),
COALESCE(e.nombre_archivo_snapshot, v.nombre_archivo, N'Archivo historico'),
COALESCE(e.version_script_snapshot, CONVERT(nvarchar(50), v.numero_version), N'-'),
e.id_script, e.id_version, e.mensaje_error, e.pid_proceso,
e.fecha_programada, e.clave_programacion, e.usuario_detencion,
e.fecha_hora_detencion, e.motivo_detencion, e.fue_detencion_forzada,
l.ruta_fisica_log, l.ruta_relativa_log, ev.estado_evidencia
FROM dbo.ejecuciones e
LEFT JOIN dbo.tareas t ON t.id_tarea = e.id_tarea
LEFT JOIN dbo.scripts s ON s.id_script = e.id_script
LEFT JOIN dbo.scripts_versiones v ON v.id_version = e.id_version
LEFT JOIN dbo.logs_tareas l ON l.id_ejecucion = e.id_ejecucion
LEFT JOIN dbo.evidencias_ejecucion ev ON ev.id_ejecucion = e.id_ejecucion
WHERE e.id_ejecucion = ?""",
            (id_ejecucion,), operacion="obtener_detalle_ejecucion",
        )
        if fila is None:
            return None
        return DetalleEjecucion(
            int(fila[0]), fila[1], str(fila[2]), str(fila[3]), fila[4], fila[5],
            fila[6], fila[7], fila[8], fila[9], str(fila[10]), str(fila[11]),
            str(fila[12]), str(fila[13]), fila[14], fila[15], fila[16], fila[17],
            fila[18], fila[19], fila[20], fila[21], fila[22], bool(fila[23]),
            fila[24], fila[25], fila[26],
        )
