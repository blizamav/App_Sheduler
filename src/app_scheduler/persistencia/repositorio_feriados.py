"""Persistencia acotada para calendario local y sincronizacion externa."""

from __future__ import annotations

from app_scheduler.persistencia.modelos import Feriado, Pagina, Paginacion
from app_scheduler.persistencia.repositorio import RepositorioSQL


class RepositorioFeriados(RepositorioSQL):
    _COLUMNAS = """id_feriado, fecha, nombre, tipo, pais, irrenunciable,
activo, origen, observacion, fecha_creacion, fecha_actualizacion,
usuario_creacion, usuario_actualizacion"""

    @staticmethod
    def _mapear(fila) -> Feriado:
        return Feriado(
            int(fila[0]), fila[1], str(fila[2]), fila[3], str(fila[4]),
            bool(fila[5]), bool(fila[6]), str(fila[7]), fila[8], fila[9],
            fila[10], fila[11], fila[12],
        )

    def listar(self, paginacion: Paginacion, *, anio=None, pais=None, origen=None,
               activo=None, busqueda=None) -> Pagina[Feriado]:
        filtros = ["1 = 1"]
        parametros: list[object] = []
        if anio:
            filtros.append("YEAR(fecha) = ?")
            parametros.append(anio)
        if pais:
            filtros.append("pais = ?")
            parametros.append(pais)
        if origen:
            filtros.append("origen = ?")
            parametros.append(origen)
        if activo is not None:
            filtros.append("activo = ?")
            parametros.append(int(activo))
        if busqueda:
            texto = str(busqueda).replace("~", "~~").replace("%", "~%").replace("_", "~_")
            filtros.append("(nombre LIKE ? ESCAPE '~' OR observacion LIKE ? ESCAPE '~')")
            parametros.extend((f"%{texto}%", f"%{texto}%"))
        donde = " AND ".join(filtros)
        total = int(self.ejecutar_escalar(
            f"SELECT COUNT(1) FROM dbo.feriados WHERE {donde}", parametros,
            operacion="contar_feriados",
        ) or 0)
        filas = self.ejecutar_lista(
            f"""SELECT {self._COLUMNAS} FROM dbo.feriados
WHERE {donde}
ORDER BY fecha DESC, id_feriado DESC
OFFSET ? ROWS FETCH NEXT ? ROWS ONLY""",
            (*parametros, paginacion.desplazamiento, paginacion.por_pagina),
            operacion="listar_feriados",
        )
        return Pagina(tuple(self._mapear(fila) for fila in filas), total,
                      paginacion.pagina, paginacion.por_pagina)

    def obtener(self, id_feriado: int) -> Feriado | None:
        fila = self.ejecutar_uno(
            f"SELECT {self._COLUMNAS} FROM dbo.feriados WHERE id_feriado = ?",
            (id_feriado,), operacion="obtener_feriado",
        )
        return None if fila is None else self._mapear(fila)

    def obtener_por_fecha_pais(self, fecha, pais: str) -> Feriado | None:
        fila = self.ejecutar_uno(
            f"""SELECT TOP 1 {self._COLUMNAS} FROM dbo.feriados
WHERE fecha = ? AND pais = ? ORDER BY activo DESC, id_feriado DESC""",
            (fecha, pais), operacion="obtener_feriado_fecha_pais",
        )
        return None if fila is None else self._mapear(fila)

    def crear_manual(self, datos, actor: str) -> int:
        fila = self.ejecutar_uno(
            """INSERT INTO dbo.feriados
(fecha, nombre, tipo, pais, irrenunciable, activo, origen, observacion,
 usuario_creacion, usuario_actualizacion)
OUTPUT INSERTED.id_feriado
VALUES (?, ?, ?, ?, ?, 1, 'MANUAL', ?, ?, ?)""",
            (datos["fecha"], datos["nombre"], datos["tipo"], datos["pais"],
             int(datos["irrenunciable"]), datos["observacion"], actor, actor),
            operacion="crear_feriado_manual",
        )
        return int(fila[0])

    def actualizar_manual(self, id_feriado: int, datos, actor: str) -> bool:
        return self.ejecutar(
            """UPDATE dbo.feriados
SET fecha = ?, nombre = ?, tipo = ?, pais = ?, irrenunciable = ?,
    observacion = ?, fecha_actualizacion = SYSDATETIME(), usuario_actualizacion = ?
WHERE id_feriado = ? AND origen = 'MANUAL'""",
            (datos["fecha"], datos["nombre"], datos["tipo"], datos["pais"],
             int(datos["irrenunciable"]), datos["observacion"], actor, id_feriado),
            operacion="actualizar_feriado_manual",
        ) == 1

    def cambiar_estado(self, id_feriado: int, activo: bool, actor: str) -> bool:
        return self.ejecutar(
            """UPDATE dbo.feriados SET activo = ?, fecha_actualizacion = SYSDATETIME(),
usuario_actualizacion = ? WHERE id_feriado = ?""",
            (int(activo), actor, id_feriado), operacion="cambiar_estado_feriado",
        ) == 1

    def eliminar_manual(self, id_feriado: int) -> bool:
        return self.ejecutar(
            "DELETE FROM dbo.feriados WHERE id_feriado = ? AND origen = 'MANUAL'",
            (id_feriado,), operacion="eliminar_feriado_manual",
        ) == 1

    def obtener_regla_irrenunciable(self, pais: str, mes: int, dia: int) -> bool:
        return bool(self.ejecutar_escalar(
            """SELECT TOP 1 irrenunciable FROM dbo.reglas_feriados_irrenunciables
WHERE pais = ? AND mes = ? AND dia = ? AND activo = 1 ORDER BY id_regla""",
            (pais, mes, dia), operacion="obtener_regla_irrenunciable",
        ))

    def crear_api_nager(self, datos, actor: str) -> int:
        fila = self.ejecutar_uno(
            """INSERT INTO dbo.feriados
(fecha, nombre, tipo, pais, irrenunciable, activo, origen, observacion,
 usuario_creacion, usuario_actualizacion)
OUTPUT INSERTED.id_feriado
VALUES (?, ?, ?, ?, ?, 1, 'API_NAGER', ?, ?, ?)""",
            (datos["fecha"], datos["nombre"], datos["tipo"], datos["pais"],
             int(datos["irrenunciable"]), datos["observacion"], actor, actor),
            operacion="crear_feriado_nager",
        )
        return int(fila[0])

    def actualizar_api_nager(self, id_feriado: int, datos, actor: str) -> bool:
        return self.ejecutar(
            """UPDATE dbo.feriados
SET nombre = ?, tipo = ?, irrenunciable = ?, observacion = ?,
    fecha_actualizacion = SYSDATETIME(), usuario_actualizacion = ?
WHERE id_feriado = ? AND origen = 'API_NAGER' AND activo = 1""",
            (datos["nombre"], datos["tipo"], int(datos["irrenunciable"]),
             datos["observacion"], actor, id_feriado),
            operacion="actualizar_feriado_nager",
        ) == 1
