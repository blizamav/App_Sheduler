"""Persistencia parametrizada de programaciones."""

from __future__ import annotations

from app_scheduler.persistencia.mapeadores import mapear_programacion
from app_scheduler.persistencia.modelos import Pagina, Paginacion, Programacion
from app_scheduler.persistencia.repositorio import RepositorioSQL


class RepositorioProgramaciones(RepositorioSQL):
    _SELECCION = """p.id_programacion, p.id_tarea, t.nombre_tarea, t.estado_tarea,
    p.tipo_programacion, p.modo_ejecucion_dia, p.hora_inicio, p.hora_termino,
    p.hora_ejecucion, p.intervalo_minutos, p.dias_semana, p.dia_mes,
    p.fecha_especifica, p.fechas_especificas, p.ejecutar_en_feriados,
    p.zona_horaria, p.fecha_inicio_vigencia, p.fecha_fin_vigencia,
    p.fecha_creacion, p.fecha_actualizacion, p.activo, t.proxima_ejecucion"""

    def listar_paginado(self, paginacion: Paginacion, *, id_tarea=None, tipo=None, activo=None):
        filtros = ["t.eliminado_operativo = 0"]
        parametros = []
        if id_tarea:
            filtros.append("p.id_tarea = ?"); parametros.append(id_tarea)
        if tipo:
            filtros.append("p.tipo_programacion = ?"); parametros.append(tipo)
        if activo is not None:
            filtros.append("p.activo = ?"); parametros.append(int(activo))
        where = " AND ".join(filtros)
        total = int(self.ejecutar_escalar(
            f"""SELECT COUNT(1) FROM dbo.programaciones p
JOIN dbo.tareas t ON t.id_tarea = p.id_tarea WHERE {where}""",
            parametros, operacion="contar_programaciones",
        ) or 0)
        filas = self.ejecutar_lista(
            f"""SELECT {self._SELECCION}
FROM dbo.programaciones p JOIN dbo.tareas t ON t.id_tarea = p.id_tarea
WHERE {where}
ORDER BY t.nombre_tarea, p.id_programacion DESC
OFFSET ? ROWS FETCH NEXT ? ROWS ONLY""",
            (*parametros, paginacion.desplazamiento, paginacion.por_pagina),
            operacion="listar_programaciones",
        )
        return Pagina(tuple(mapear_programacion(fila) for fila in filas), total,
                      paginacion.pagina, paginacion.por_pagina)

    def obtener(self, id_programacion: int) -> Programacion | None:
        fila = self.ejecutar_uno(
            f"""SELECT {self._SELECCION}
FROM dbo.programaciones p JOIN dbo.tareas t ON t.id_tarea = p.id_tarea
WHERE p.id_programacion = ? AND t.eliminado_operativo = 0""",
            (id_programacion,), operacion="obtener_programacion",
        )
        return None if fila is None else mapear_programacion(fila)

    def listar_activas_tarea(self, id_tarea: int) -> tuple[Programacion, ...]:
        filas = self.ejecutar_lista(
            f"""SELECT {self._SELECCION}
FROM dbo.programaciones p JOIN dbo.tareas t ON t.id_tarea = p.id_tarea
WHERE p.id_tarea = ? AND p.activo = 1 AND t.eliminado_operativo = 0
ORDER BY p.id_programacion""",
            (id_tarea,), operacion="listar_programaciones_activas_tarea",
        )
        return tuple(mapear_programacion(fila) for fila in filas)

    def bloquear_tarea(self, id_tarea: int) -> bool:
        return self.ejecutar_uno(
            "SELECT id_tarea FROM dbo.tareas WITH (UPDLOCK, HOLDLOCK) WHERE id_tarea = ? AND eliminado_operativo = 0",
            (id_tarea,), operacion="bloquear_tarea_programacion",
        ) is not None

    def existe_otra_activa(self, id_tarea: int, excluir_id=None) -> bool:
        sql = """SELECT COUNT(1) FROM dbo.programaciones WITH (UPDLOCK, HOLDLOCK)
WHERE id_tarea = ? AND activo = 1"""
        parametros = [id_tarea]
        if excluir_id is not None:
            sql += " AND id_programacion <> ?"; parametros.append(excluir_id)
        return bool(self.ejecutar_escalar(sql, parametros, operacion="validar_programacion_activa_unica"))

    def crear(self, id_tarea: int, datos, actor: str) -> int:
        fila = self.ejecutar_uno(
            """INSERT INTO dbo.programaciones
    (id_tarea, tipo_programacion, modo_ejecucion_dia, hora_inicio, hora_termino,
     hora_ejecucion, intervalo_minutos, dias_semana, dia_mes, fecha_especifica,
     fechas_especificas, configuracion_json, ejecutar_en_feriados, zona_horaria,
     fecha_inicio_vigencia, fecha_fin_vigencia, usuario_creacion, activo)
OUTPUT INSERTED.id_programacion
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?, ?, ?)""",
            self._parametros(id_tarea, datos, actor, incluir_id=True), operacion="crear_programacion",
        )
        return int(fila[0])

    def actualizar(self, id_programacion: int, datos, actor: str) -> bool:
        return self.ejecutar(
            """UPDATE dbo.programaciones SET tipo_programacion = ?, modo_ejecucion_dia = ?,
hora_inicio = ?, hora_termino = ?, hora_ejecucion = ?, intervalo_minutos = ?,
dias_semana = ?, dia_mes = ?, fecha_especifica = ?, fechas_especificas = ?,
configuracion_json = NULL, ejecutar_en_feriados = ?, zona_horaria = ?,
fecha_inicio_vigencia = ?, fecha_fin_vigencia = ?, usuario_actualizacion = ?,
fecha_actualizacion = SYSDATETIME(), activo = ? WHERE id_programacion = ?""",
            (*self._parametros(None, datos, actor, incluir_id=False), id_programacion),
            operacion="actualizar_programacion",
        ) > 0

    def cambiar_estado(self, id_programacion: int, activo: bool, actor: str) -> bool:
        return self.ejecutar(
            """UPDATE dbo.programaciones SET activo = ?, usuario_actualizacion = ?,
fecha_actualizacion = SYSDATETIME() WHERE id_programacion = ?""",
            (int(activo), actor, id_programacion), operacion="cambiar_estado_programacion",
        ) > 0

    def actualizar_resumen_tarea(self, id_tarea: int, programada: bool,
                                 proxima_ejecucion, actor: str) -> None:
        self.ejecutar(
            """UPDATE dbo.tareas SET tipo_tarea = ?, proxima_ejecucion = ?,
usuario_actualizacion = ?, fecha_actualizacion = SYSDATETIME()
WHERE id_tarea = ? AND eliminado_operativo = 0""",
            ("PROGRAMADA" if programada else "MANUAL", proxima_ejecucion, actor, id_tarea),
            operacion="actualizar_resumen_programacion_tarea",
        )

    @staticmethod
    def _parametros(id_tarea, datos, actor, *, incluir_id):
        valores = [datos["tipo_programacion"], datos["modo_ejecucion_dia"],
                   datos["hora_inicio"], datos["hora_termino"], datos["hora_ejecucion"],
                   datos["intervalo_minutos"], datos["dias_semana"], datos["dia_mes"],
                   datos["fecha_especifica"], datos["fechas_especificas"],
                   int(datos["ejecutar_en_feriados"]), datos["zona_horaria"],
                   datos["fecha_inicio_vigencia"], datos["fecha_fin_vigencia"], actor,
                   int(datos["activo"])]
        return tuple(([id_tarea] if incluir_id else []) + valores)
