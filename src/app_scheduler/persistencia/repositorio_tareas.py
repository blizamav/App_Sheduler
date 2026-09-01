"""Persistencia parametrizada del modulo de tareas."""

from __future__ import annotations

from app_scheduler.persistencia.mapeadores import mapear_tarea
from app_scheduler.persistencia.modelos import Pagina, Paginacion, Tarea
from app_scheduler.persistencia.repositorio import RepositorioSQL


class RepositorioTareas(RepositorioSQL):
    _SELECCION = """t.id_tarea, t.nombre_tarea, t.descripcion, t.observacion_tecnica,
    t.id_cliente, c.nombre_cliente, t.id_categoria, g.nombre_categoria,
    t.id_tipo, p.nombre_tipo, t.tipo_tarea, t.estado_tarea,
    t.permite_ejecucion_manual, t.fecha_creacion, t.fecha_actualizacion, t.activo,
    CASE WHEN EXISTS (
        SELECT 1 FROM dbo.notificaciones_config_tarea n
        WHERE n.id_tarea = t.id_tarea AND n.activo = 1
          AND (n.notificar_exito_activa = 1 OR n.alerta_error_activa = 1
               OR n.enviar_evidencia = 1)
    ) THEN 1 ELSE 0 END"""

    def obtener_por_id(self, id_tarea: int) -> Tarea | None:
        fila = self.ejecutar_uno(
            f"""SELECT {self._SELECCION}
FROM dbo.tareas t
JOIN dbo.clientes c ON c.id_cliente = t.id_cliente
JOIN dbo.categorias g ON g.id_categoria = t.id_categoria
JOIN dbo.tipos p ON p.id_tipo = t.id_tipo
WHERE t.id_tarea = ? AND t.eliminado_operativo = 0""",
            (id_tarea,), operacion="obtener_tarea",
        )
        return None if fila is None else mapear_tarea(fila)

    def listar_paginado(self, paginacion: Paginacion, *, busqueda=None, estado=None, id_cliente=None) -> Pagina[Tarea]:
        filtros = ["t.eliminado_operativo = 0"]
        parametros: list[object] = []
        if busqueda:
            patron = f"%{busqueda.replace('~', '~~').replace('%', '~%').replace('_', '~_')}%"
            filtros.append("(t.nombre_tarea LIKE ? ESCAPE '~' OR t.descripcion LIKE ? ESCAPE '~')")
            parametros.extend((patron, patron))
        if estado:
            filtros.append("t.estado_tarea = ?")
            parametros.append(estado)
        if id_cliente:
            filtros.append("t.id_cliente = ?")
            parametros.append(id_cliente)
        where = " AND ".join(filtros)
        total = int(self.ejecutar_escalar(
            f"SELECT COUNT(1) FROM dbo.tareas t WHERE {where}", parametros,
            operacion="contar_tareas",
        ) or 0)
        filas = self.ejecutar_lista(
            f"""SELECT {self._SELECCION}
FROM dbo.tareas t
JOIN dbo.clientes c ON c.id_cliente = t.id_cliente
JOIN dbo.categorias g ON g.id_categoria = t.id_categoria
JOIN dbo.tipos p ON p.id_tipo = t.id_tipo
WHERE {where}
ORDER BY t.nombre_tarea, t.id_tarea
OFFSET ? ROWS FETCH NEXT ? ROWS ONLY""",
            (*parametros, paginacion.desplazamiento, paginacion.por_pagina),
            operacion="listar_tareas",
        )
        return Pagina(tuple(mapear_tarea(f) for f in filas), total, paginacion.pagina, paginacion.por_pagina)

    def existe_clave(self, nombre: str, id_cliente: int, id_categoria: int, id_tipo: int, excluir_id=None) -> bool:
        sql = """SELECT COUNT(1) FROM dbo.tareas
WHERE UPPER(LTRIM(RTRIM(nombre_tarea))) = UPPER(LTRIM(RTRIM(?)))
  AND id_cliente = ? AND id_categoria = ? AND id_tipo = ?"""
        parametros: list[object] = [nombre, id_cliente, id_categoria, id_tipo]
        if excluir_id is not None:
            sql += " AND id_tarea <> ?"
            parametros.append(excluir_id)
        return bool(self.ejecutar_escalar(sql, parametros, operacion="validar_tarea_unica"))

    def catalogos_activos(self):
        resultado = {}
        for clave, tabla, columna_id, columna_nombre in (
            ("clientes", "clientes", "id_cliente", "nombre_cliente"),
            ("categorias", "categorias", "id_categoria", "nombre_categoria"),
            ("tipos", "tipos", "id_tipo", "nombre_tipo"),
        ):
            resultado[clave] = tuple(self.ejecutar_lista(
                f"""SELECT {columna_id}, {columna_nombre} FROM dbo.{tabla}
WHERE activo = 1 AND eliminado_operativo = 0 ORDER BY {columna_nombre}""",
                operacion=f"listar_{clave}_activos",
            ))
        return resultado

    def catalogos_validos(self, id_cliente: int, id_categoria: int, id_tipo: int) -> bool:
        return bool(self.ejecutar_escalar(
            """SELECT CASE WHEN
EXISTS (SELECT 1 FROM dbo.clientes WHERE id_cliente = ? AND activo = 1 AND eliminado_operativo = 0)
AND EXISTS (SELECT 1 FROM dbo.categorias WHERE id_categoria = ? AND activo = 1 AND eliminado_operativo = 0)
AND EXISTS (SELECT 1 FROM dbo.tipos WHERE id_tipo = ? AND activo = 1 AND eliminado_operativo = 0)
THEN 1 ELSE 0 END""",
            (id_cliente, id_categoria, id_tipo), operacion="validar_catalogos_tarea",
        ))

    def crear(self, datos, actor: str) -> int:
        fila = self.ejecutar_uno(
            """INSERT INTO dbo.tareas
    (nombre_tarea, descripcion, observacion_tecnica, id_cliente, id_categoria,
     id_tipo, tipo_tarea, estado_tarea, permite_ejecucion_manual, usuario_creacion, activo)
OUTPUT INSERTED.id_tarea
VALUES (?, ?, ?, ?, ?, ?, 'MANUAL', ?, 1, ?, ?)""",
            (datos["nombre_tarea"], datos["descripcion"], datos["observacion_tecnica"],
             datos["id_cliente"], datos["id_categoria"], datos["id_tipo"],
             datos["estado_tarea"], actor, int(datos["estado_tarea"] == "ACTIVA")),
            operacion="crear_tarea",
        )
        return int(fila[0])

    def actualizar(self, id_tarea: int, datos, actor: str) -> bool:
        return self.ejecutar(
            """UPDATE dbo.tareas SET nombre_tarea = ?, descripcion = ?, observacion_tecnica = ?,
id_cliente = ?, id_categoria = ?, id_tipo = ?, usuario_actualizacion = ?,
fecha_actualizacion = SYSDATETIME()
WHERE id_tarea = ? AND eliminado_operativo = 0""",
            (datos["nombre_tarea"], datos["descripcion"], datos["observacion_tecnica"],
             datos["id_cliente"], datos["id_categoria"], datos["id_tipo"], actor, id_tarea),
            operacion="actualizar_tarea",
        ) > 0

    def cambiar_estado(self, id_tarea: int, estado: str, actor: str) -> bool:
        return self.ejecutar(
            """UPDATE dbo.tareas SET estado_tarea = ?, activo = ?, usuario_actualizacion = ?,
fecha_actualizacion = SYSDATETIME() WHERE id_tarea = ? AND eliminado_operativo = 0""",
            (estado, int(estado == "ACTIVA"), actor, id_tarea), operacion="cambiar_estado_tarea",
        ) > 0
