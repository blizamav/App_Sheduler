"""Persistencia de scripts logicos y sus tres slots de version."""

from __future__ import annotations

from app_scheduler.persistencia.mapeadores import (
    mapear_resumen_script,
    mapear_script,
    mapear_version_script,
)
from app_scheduler.persistencia.modelos import Pagina, Paginacion
from app_scheduler.persistencia.repositorio import RepositorioSQL


class RepositorioScripts(RepositorioSQL):
    _SCRIPT = """id_script, id_tarea, nombre_script, descripcion, id_version_activa,
fecha_creacion, fecha_actualizacion, activo"""
    _VERSION = """id_version, id_script, numero_version, nombre_archivo, ruta_fisica,
ruta_relativa, hash_archivo, estado_version, es_activa, requiere_env, ruta_env_fisica,
ruta_env_relativa, usuario_carga, fecha_carga, observacion, fecha_creacion, fecha_actualizacion"""

    def listar_paginado(
        self,
        paginacion: Paginacion,
        *,
        busqueda: str | None = None,
        activo: bool | None = None,
        version_activa: int | None = None,
    ) -> Pagina:
        filtros = ["s.eliminado_operativo = 0", "t.eliminado_operativo = 0"]
        parametros: list[object] = []
        if busqueda:
            patron = f"%{self._escapar_like(busqueda)}%"
            filtros.append(
                "(s.nombre_script LIKE ? ESCAPE '~' OR "
                "t.nombre_tarea LIKE ? ESCAPE '~' OR "
                "c.nombre_cliente LIKE ? ESCAPE '~')"
            )
            parametros.extend((patron, patron, patron))
        if activo is not None:
            filtros.append("s.activo = ?")
            parametros.append(int(activo))
        if version_activa is not None:
            filtros.append("va.numero_version = ?")
            parametros.append(version_activa)

        origen = """FROM dbo.scripts AS s
INNER JOIN dbo.tareas AS t ON t.id_tarea = s.id_tarea
INNER JOIN dbo.clientes AS c ON c.id_cliente = t.id_cliente
LEFT JOIN dbo.scripts_versiones AS va
    ON va.id_version = s.id_version_activa AND va.eliminado_operativo = 0
LEFT JOIN (
    SELECT id_script,
           COUNT(1) AS slots_ocupados,
           SUM(CASE WHEN ruta_env_relativa IS NOT NULL THEN 1 ELSE 0 END) AS env_configurados,
           MAX(COALESCE(fecha_actualizacion, fecha_carga, fecha_creacion)) AS ultima_modificacion
    FROM dbo.scripts_versiones
    WHERE eliminado_operativo = 0
    GROUP BY id_script
) AS vm ON vm.id_script = s.id_script"""
        donde = " AND ".join(filtros)
        total = int(self.ejecutar_escalar(
            f"SELECT COUNT(1) {origen} WHERE {donde}",
            tuple(parametros), operacion="contar_scripts_global",
        ) or 0)
        filas = self.ejecutar_lista(
            f"""SELECT s.id_script, s.id_tarea, s.nombre_script, t.nombre_tarea,
c.nombre_cliente, s.activo, va.numero_version, va.nombre_archivo,
COALESCE(vm.slots_ocupados, 0), COALESCE(vm.env_configurados, 0),
COALESCE(vm.ultima_modificacion, s.fecha_actualizacion, s.fecha_creacion)
{origen}
WHERE {donde}
ORDER BY s.nombre_script, t.nombre_tarea, s.id_script
OFFSET ? ROWS FETCH NEXT ? ROWS ONLY""",
            tuple(parametros) + (paginacion.desplazamiento, paginacion.por_pagina),
            operacion="listar_scripts_global",
        )
        return Pagina(
            elementos=tuple(mapear_resumen_script(fila) for fila in filas),
            total=total,
            pagina=paginacion.pagina,
            por_pagina=paginacion.por_pagina,
        )

    def obtener_por_tarea(self, id_tarea: int):
        fila = self.ejecutar_uno(
            f"SELECT {self._SCRIPT} FROM dbo.scripts WHERE id_tarea = ? AND eliminado_operativo = 0",
            (id_tarea,), operacion="obtener_script_tarea",
        )
        return None if fila is None else mapear_script(fila)

    def obtener(self, id_script: int):
        fila = self.ejecutar_uno(
            f"SELECT {self._SCRIPT} FROM dbo.scripts WHERE id_script = ? AND eliminado_operativo = 0",
            (id_script,), operacion="obtener_script",
        )
        return None if fila is None else mapear_script(fila)

    def obtener_version(self, id_version: int):
        fila = self.ejecutar_uno(
            f"SELECT {self._VERSION} FROM dbo.scripts_versiones WHERE id_version = ? AND eliminado_operativo = 0",
            (id_version,), operacion="obtener_version_script",
        )
        return None if fila is None else mapear_version_script(fila)

    def listar_versiones(self, id_script: int):
        filas = self.ejecutar_lista(
            f"""SELECT {self._VERSION} FROM dbo.scripts_versiones
WHERE id_script = ? AND eliminado_operativo = 0 ORDER BY numero_version""",
            (id_script,), operacion="listar_versiones_script",
        )
        return tuple(mapear_version_script(f) for f in filas)

    def contar_referencias_version(self, id_version: int) -> int:
        return int(self.ejecutar_escalar(
            "SELECT COUNT(1) FROM dbo.ejecuciones WHERE id_version = ?",
            (id_version,), operacion="contar_referencias_version",
        ) or 0)

    def contar_referencias_version_para_reemplazo(self, id_version: int) -> int:
        return int(self.ejecutar_escalar(
            """SELECT COUNT(1) FROM dbo.ejecuciones WITH (UPDLOCK, HOLDLOCK)
WHERE id_version = ?""",
            (id_version,), operacion="bloquear_referencias_version",
        ) or 0)

    def crear_script(self, id_tarea: int, nombre: str, descripcion, actor: str) -> int:
        fila = self.ejecutar_uno(
            """INSERT INTO dbo.scripts (id_tarea, nombre_script, descripcion, usuario_creacion, activo)
OUTPUT INSERTED.id_script VALUES (?, ?, ?, ?, 1)""",
            (id_tarea, nombre, descripcion, actor), operacion="crear_script",
        )
        return int(fila[0])

    def crear_version(self, id_script: int, numero: int, nombre: str, ruta_fisica: str,
                      ruta_relativa: str, hash_archivo: str, activa: bool, observacion, actor: str) -> int:
        fila = self.ejecutar_uno(
            """INSERT INTO dbo.scripts_versiones
(id_script, numero_version, nombre_archivo, ruta_fisica, ruta_relativa, hash_archivo,
 estado_version, es_activa, requiere_env, usuario_carga, observacion)
OUTPUT INSERTED.id_version VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)""",
            (id_script, numero, nombre, ruta_fisica, ruta_relativa, hash_archivo,
             "ACTIVA" if activa else "DISPONIBLE", int(activa), actor, observacion),
            operacion="crear_version_script",
        )
        return int(fila[0])

    def establecer_version_activa(self, id_script: int, id_version: int, actor: str) -> None:
        self.ejecutar(
            """UPDATE dbo.scripts_versiones SET es_activa = 0,
estado_version = CASE WHEN estado_version = 'ACTIVA' THEN 'DISPONIBLE' ELSE estado_version END,
fecha_actualizacion = SYSDATETIME() WHERE id_script = ? AND es_activa = 1""",
            (id_script,), operacion="desactivar_version_anterior",
        )
        if self.ejecutar(
            """UPDATE dbo.scripts_versiones SET es_activa = 1, estado_version = 'ACTIVA',
fecha_actualizacion = SYSDATETIME() WHERE id_version = ? AND id_script = ?
AND eliminado_operativo = 0 AND estado_version IN ('DISPONIBLE','INACTIVA','ACTIVA')""",
            (id_version, id_script), operacion="activar_version",
        ) != 1:
            raise ValueError("Version no activable.")
        self.ejecutar(
            """UPDATE dbo.scripts SET id_version_activa = ?, activo = 1,
usuario_actualizacion = ?, fecha_actualizacion = SYSDATETIME() WHERE id_script = ?""",
            (id_version, actor, id_script), operacion="actualizar_version_activa_script",
        )

    def reemplazar_version(self, id_version: int, nombre: str, ruta_fisica: str,
                           ruta_relativa: str, hash_archivo: str, observacion, actor: str) -> bool:
        return self.ejecutar(
            """UPDATE dbo.scripts_versiones SET nombre_archivo = ?, ruta_fisica = ?,
ruta_relativa = ?, hash_archivo = ?, estado_version = 'DISPONIBLE', es_activa = 0,
requiere_env = 0, ruta_env_fisica = NULL, ruta_env_relativa = NULL,
usuario_carga = ?, fecha_carga = SYSDATETIME(), observacion = ?,
fecha_actualizacion = SYSDATETIME()
WHERE id_version = ? AND es_activa = 0 AND eliminado_operativo = 0""",
            (nombre, ruta_fisica, ruta_relativa, hash_archivo, actor, observacion, id_version),
            operacion="reemplazar_version",
        ) == 1

    def desactivar_version(self, id_version: int) -> bool:
        return self.ejecutar(
            """UPDATE dbo.scripts_versiones SET estado_version = 'INACTIVA',
fecha_actualizacion = SYSDATETIME() WHERE id_version = ? AND es_activa = 0
AND eliminado_operativo = 0 AND estado_version = 'DISPONIBLE'""",
            (id_version,), operacion="desactivar_version",
        ) == 1

    def actualizar_env(self, id_version: int, requiere: bool, ruta_fisica, ruta_relativa) -> bool:
        return self.ejecutar(
            """UPDATE dbo.scripts_versiones SET requiere_env = ?, ruta_env_fisica = ?,
ruta_env_relativa = ?, fecha_actualizacion = SYSDATETIME()
WHERE id_version = ? AND eliminado_operativo = 0""",
            (int(requiere), ruta_fisica, ruta_relativa, id_version), operacion="actualizar_env_version",
        ) == 1

    @staticmethod
    def _escapar_like(valor: str) -> str:
        return valor.replace("~", "~~").replace("%", "~%").replace("_", "~_").replace("[", "~[")
