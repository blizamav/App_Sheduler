"""Persistencia allowlist para retiro, restauracion y purga operacional."""

from __future__ import annotations

from app_scheduler.compartido.errores import ErrorValidacion
from app_scheduler.persistencia.modelos import ElementoPapelera, Pagina, Paginacion
from app_scheduler.persistencia.repositorio import RepositorioSQL


ENTIDADES = {
    "usuarios": ("dbo.usuarios", "id_usuario", "usuario", "nombre_completo"),
    "clientes": ("dbo.clientes", "id_cliente", "nombre_cliente", "descripcion"),
    "categorias": ("dbo.categorias", "id_categoria", "nombre_categoria", "descripcion"),
    "tipos": ("dbo.tipos", "id_tipo", "nombre_tipo", "descripcion"),
    "tareas": ("dbo.tareas", "id_tarea", "nombre_tarea", "descripcion"),
    "scripts": ("dbo.scripts", "id_script", "nombre_script", "descripcion"),
    "scripts_versiones": ("dbo.scripts_versiones", "id_version", "nombre_archivo", "observacion"),
}

ETIQUETAS_ENTIDAD = {
    "usuarios": "Usuarios",
    "clientes": "Clientes",
    "categorias": "Categorias",
    "tipos": "Tipos",
    "tareas": "Tareas",
    "scripts": "Scripts",
    "scripts_versiones": "Versiones",
}


def _union_papelera() -> str:
    consultas = []
    for entidad, (tabla, identificador, nombre, descripcion) in ENTIDADES.items():
        alias = "x"
        if entidad == "tareas":
            contexto = "CONCAT(c.nombre_cliente, N' / ', ca.nombre_categoria, N' / ', ti.nombre_tipo)"
            joins = """LEFT JOIN dbo.clientes c ON c.id_cliente = x.id_cliente
LEFT JOIN dbo.categorias ca ON ca.id_categoria = x.id_categoria
LEFT JOIN dbo.tipos ti ON ti.id_tipo = x.id_tipo"""
            activo = "x.activo"
        elif entidad == "scripts":
            contexto = "t.nombre_tarea"
            joins = "LEFT JOIN dbo.tareas t ON t.id_tarea = x.id_tarea"
            activo = "x.activo"
        elif entidad == "scripts_versiones":
            contexto = "CONCAT(s.nombre_script, N' / v', x.numero_version)"
            joins = "LEFT JOIN dbo.scripts s ON s.id_script = x.id_script"
            activo = "x.es_activa"
        else:
            contexto = "CAST(NULL AS nvarchar(500))"
            joins = ""
            activo = "x.activo"
        consultas.append(f"""SELECT N'{entidad}' AS entidad,
CAST(x.{identificador} AS bigint) AS id_registro, x.{nombre} AS nombre,
x.{descripcion} AS descripcion, {contexto} AS contexto,
CAST({activo} AS bit) AS activo_anterior, x.fecha_eliminado_operativo AS fecha_retiro,
x.usuario_eliminado_operativo AS usuario_retiro,
x.motivo_eliminado_operativo AS motivo_retiro
FROM {tabla} x
{joins}
WHERE x.eliminado_operativo = 1""")
    return "\nUNION ALL\n".join(consultas)


SQL_UNION_PAPELERA = _union_papelera()


class RepositorioPapelera(RepositorioSQL):
    def listar(self, paginacion: Paginacion, *, entidad=None, busqueda=None,
               usuario=None, fecha_desde=None, fecha_hasta=None) -> Pagina[ElementoPapelera]:
        condiciones = ["1 = 1"]
        parametros: list[object] = []
        if entidad:
            condiciones.append("p.entidad = ?")
            parametros.append(entidad)
        if busqueda:
            patron = _patron_like(busqueda)
            condiciones.append(
                "(p.nombre LIKE ? ESCAPE '~' OR p.descripcion LIKE ? ESCAPE '~' "
                "OR p.contexto LIKE ? ESCAPE '~' OR p.motivo_retiro LIKE ? ESCAPE '~')"
            )
            parametros.extend((patron, patron, patron, patron))
        if usuario:
            condiciones.append("p.usuario_retiro LIKE ? ESCAPE '~'")
            parametros.append(_patron_like(usuario))
        if fecha_desde:
            condiciones.append("p.fecha_retiro >= ?")
            parametros.append(fecha_desde)
        if fecha_hasta:
            condiciones.append("p.fecha_retiro < DATEADD(day, 1, CAST(? AS date))")
            parametros.append(fecha_hasta)
        where = " AND ".join(condiciones)
        total = int(self.ejecutar_escalar(
            f"SELECT COUNT(1) FROM ({SQL_UNION_PAPELERA}) p WHERE {where}",
            parametros,
            operacion="contar_papelera",
        ) or 0)
        filas = self.ejecutar_lista(
            f"""SELECT p.entidad, p.id_registro, p.nombre, p.descripcion, p.contexto,
p.activo_anterior, p.fecha_retiro, p.usuario_retiro, p.motivo_retiro
FROM ({SQL_UNION_PAPELERA}) p
WHERE {where}
ORDER BY p.fecha_retiro DESC, p.entidad, p.id_registro DESC
OFFSET ? ROWS FETCH NEXT ? ROWS ONLY""",
            (*parametros, paginacion.desplazamiento, paginacion.por_pagina),
            operacion="listar_papelera",
        )
        return Pagina(
            tuple(self._mapear(fila) for fila in filas), total,
            paginacion.pagina, paginacion.por_pagina,
        )

    def obtener(self, entidad: str, id_registro: int, *, retirado=True,
                bloquear=False) -> ElementoPapelera | None:
        tabla, identificador, nombre, descripcion = _config(entidad)
        contexto, joins, activo = self._contexto_entidad(entidad)
        bloqueo = " WITH (UPDLOCK, HOLDLOCK)" if bloquear else ""
        operador = "= 1" if retirado else "= 0"
        fila = self.ejecutar_uno(
            f"""SELECT N'{entidad}', CAST(x.{identificador} AS bigint), x.{nombre},
x.{descripcion}, {contexto}, CAST({activo} AS bit), x.fecha_eliminado_operativo,
x.usuario_eliminado_operativo, x.motivo_eliminado_operativo
FROM {tabla} x{bloqueo}
{joins}
WHERE x.{identificador} = ? AND x.eliminado_operativo {operador}""",
            (id_registro,),
            operacion="obtener_elemento_papelera",
        )
        return None if fila is None else self._mapear(fila)

    def retirar(self, entidad: str, id_registro: int, actor: str, motivo: str) -> bool:
        if entidad == "tareas":
            self.ejecutar("""UPDATE v SET eliminado_operativo = 1, es_activa = 0,
estado_version = CASE WHEN estado_version = 'ACTIVA' THEN 'INACTIVA' ELSE estado_version END,
fecha_eliminado_operativo = COALESCE(fecha_eliminado_operativo, SYSDATETIME()),
usuario_eliminado_operativo = ?, motivo_eliminado_operativo = ?, fecha_actualizacion = SYSDATETIME()
FROM dbo.scripts_versiones v INNER JOIN dbo.scripts s ON s.id_script = v.id_script
WHERE s.id_tarea = ?""", (actor, motivo, id_registro), operacion="retirar_versiones_tarea")
            self.ejecutar("""UPDATE dbo.scripts SET activo = 0, id_version_activa = NULL,
eliminado_operativo = 1, fecha_eliminado_operativo = COALESCE(fecha_eliminado_operativo, SYSDATETIME()),
usuario_eliminado_operativo = ?, motivo_eliminado_operativo = ?, usuario_actualizacion = ?,
fecha_actualizacion = SYSDATETIME() WHERE id_tarea = ?""",
                (actor, motivo, actor, id_registro), operacion="retirar_scripts_tarea")
        elif entidad == "scripts":
            self.ejecutar("""UPDATE dbo.scripts_versiones SET eliminado_operativo = 1,
es_activa = 0, estado_version = CASE WHEN estado_version = 'ACTIVA' THEN 'INACTIVA' ELSE estado_version END,
fecha_eliminado_operativo = COALESCE(fecha_eliminado_operativo, SYSDATETIME()),
usuario_eliminado_operativo = ?, motivo_eliminado_operativo = ?, fecha_actualizacion = SYSDATETIME()
WHERE id_script = ?""", (actor, motivo, id_registro), operacion="retirar_versiones_script")
        if entidad == "scripts_versiones":
            afectadas = self.ejecutar("""UPDATE dbo.scripts_versiones SET eliminado_operativo = 1,
es_activa = 0, estado_version = CASE WHEN estado_version = 'ACTIVA' THEN 'INACTIVA' ELSE estado_version END,
fecha_eliminado_operativo = COALESCE(fecha_eliminado_operativo, SYSDATETIME()),
usuario_eliminado_operativo = ?, motivo_eliminado_operativo = ?, fecha_actualizacion = SYSDATETIME()
WHERE id_version = ? AND eliminado_operativo = 0""",
                (actor, motivo, id_registro), operacion="retirar_version")
            self.ejecutar("""UPDATE dbo.scripts SET id_version_activa = NULL, activo = 0,
fecha_actualizacion = SYSDATETIME(), usuario_actualizacion = ?
WHERE id_version_activa = ?""", (actor, id_registro), operacion="desvincular_version_activa")
            return afectadas > 0
        tabla, identificador, _, _ = _config(entidad)
        extras = {
            "usuarios": "activo = 0, bloqueado = 1,",
            "tareas": "activo = 0, estado_tarea = 'INACTIVA',",
            "scripts": "activo = 0, id_version_activa = NULL,",
        }.get(entidad, "activo = 0,")
        afectadas = self.ejecutar(
            f"""UPDATE {tabla} SET {extras} eliminado_operativo = 1,
fecha_eliminado_operativo = COALESCE(fecha_eliminado_operativo, SYSDATETIME()),
usuario_eliminado_operativo = ?, motivo_eliminado_operativo = ?,
usuario_actualizacion = ?, fecha_actualizacion = SYSDATETIME()
WHERE {identificador} = ? AND eliminado_operativo = 0""",
            (actor, motivo, actor, id_registro),
            operacion="enviar_papelera",
        )
        return afectadas > 0

    def restaurar(self, entidad: str, id_registro: int, actor: str) -> bool:
        tabla, identificador, _, _ = _config(entidad)
        if entidad == "scripts_versiones":
            sql = """UPDATE dbo.scripts_versiones SET eliminado_operativo = 0,
estado_version = 'INACTIVA', es_activa = 0, fecha_eliminado_operativo = NULL,
usuario_eliminado_operativo = NULL, motivo_eliminado_operativo = NULL,
fecha_actualizacion = SYSDATETIME() WHERE id_version = ? AND eliminado_operativo = 1"""
            parametros = (id_registro,)
        else:
            extras = {
                "usuarios": "activo = 0, bloqueado = 0,",
                "tareas": "activo = 0, estado_tarea = 'INACTIVA',",
                "scripts": "activo = 0, id_version_activa = NULL,",
            }.get(entidad, "activo = 0,")
            sql = f"""UPDATE {tabla} SET {extras} eliminado_operativo = 0,
fecha_eliminado_operativo = NULL, usuario_eliminado_operativo = NULL,
motivo_eliminado_operativo = NULL, usuario_actualizacion = ?,
fecha_actualizacion = SYSDATETIME()
WHERE {identificador} = ? AND eliminado_operativo = 1"""
            parametros = (actor, id_registro)
        return self.ejecutar(sql, parametros, operacion="restaurar_papelera") > 0

    def dependencias(self, entidad: str, id_registro: int) -> dict[str, int]:
        if entidad in {"clientes", "categorias", "tipos"}:
            campo = {"clientes": "id_cliente", "categorias": "id_categoria", "tipos": "id_tipo"}[entidad]
            tabla, identificador, _, _ = _config(entidad)
            return {
                "tareas": self._contar(f"SELECT COUNT(1) FROM dbo.tareas WHERE {campo} = ?", id_registro),
                "conflicto_clave": self._contar(f"""SELECT COUNT(1) FROM {tabla} actual
JOIN {tabla} otro ON otro.nombre_normalizado=actual.nombre_normalizado AND otro.{identificador}<>actual.{identificador}
WHERE actual.{identificador}=? AND otro.eliminado_operativo=0""", id_registro),
            }
        if entidad == "usuarios":
            usuario = self.ejecutar_escalar("SELECT usuario FROM dbo.usuarios WHERE id_usuario = ?", (id_registro,), operacion="usuario_papelera") or ""
            historial = self._contar("""SELECT
(SELECT COUNT(1) FROM dbo.ejecuciones WHERE usuario_ejecucion = ?) +
(SELECT COUNT(1) FROM dbo.logs_tareas WHERE usuario_ejecucion = ?) +
(SELECT COUNT(1) FROM dbo.logs_sistema WHERE usuario = ?)""", usuario, usuario, usuario)
            administradores = self._contar("""SELECT COUNT(DISTINCT u.id_usuario)
FROM dbo.usuarios u JOIN dbo.usuarios_roles ur ON ur.id_usuario = u.id_usuario AND ur.activo = 1
JOIN dbo.roles r ON r.id_rol = ur.id_rol AND r.activo = 1
WHERE u.id_usuario <> ? AND u.activo = 1 AND u.eliminado_operativo = 0
AND r.codigo_rol IN ('SUPER_ADMIN','ADMIN')""", id_registro)
            es_admin = self._contar("""SELECT COUNT(1) FROM dbo.usuarios_roles ur
JOIN dbo.roles r ON r.id_rol = ur.id_rol WHERE ur.id_usuario = ? AND ur.activo = 1
AND r.codigo_rol IN ('SUPER_ADMIN','ADMIN')""", id_registro)
            conflicto = self._contar("""SELECT COUNT(1) FROM dbo.usuarios actual
JOIN dbo.usuarios otro ON otro.usuario=actual.usuario AND otro.id_usuario<>actual.id_usuario
WHERE actual.id_usuario=? AND otro.eliminado_operativo=0""", id_registro)
            return {"historial": historial, "administradores_restantes": administradores,
                    "es_admin": es_admin, "conflicto_clave": conflicto}
        if entidad == "tareas":
            return {
                "ejecuciones_en_curso": self._contar("SELECT COUNT(1) FROM dbo.ejecuciones WHERE id_tarea = ? AND estado_ejecucion = 'EN_EJECUCION'", id_registro),
                "ejecuciones_historicas": self._contar("""SELECT COUNT(1) FROM dbo.ejecuciones e
WHERE e.id_tarea=? OR e.id_script IN (SELECT id_script FROM dbo.scripts WHERE id_tarea=?)
OR e.id_version IN (SELECT v.id_version FROM dbo.scripts_versiones v
JOIN dbo.scripts s ON s.id_script=v.id_script WHERE s.id_tarea=?)""",
                    id_registro, id_registro, id_registro),
                "maestros_eliminados": self._contar("""SELECT COUNT(1) FROM dbo.tareas t
JOIN dbo.clientes c ON c.id_cliente=t.id_cliente JOIN dbo.categorias ca ON ca.id_categoria=t.id_categoria
JOIN dbo.tipos ti ON ti.id_tipo=t.id_tipo WHERE t.id_tarea=? AND
(c.eliminado_operativo=1 OR ca.eliminado_operativo=1 OR ti.eliminado_operativo=1)""", id_registro),
                "scripts": self._contar("SELECT COUNT(1) FROM dbo.scripts WHERE id_tarea = ?", id_registro),
                "programaciones": self._contar("SELECT COUNT(1) FROM dbo.programaciones WHERE id_tarea = ?", id_registro),
                "snapshots_incompletos": self._contar("""SELECT COUNT(1) FROM dbo.ejecuciones
WHERE id_tarea = ? AND (nombre_tarea_snapshot IS NULL OR cliente_snapshot IS NULL
OR categoria_snapshot IS NULL OR tipo_snapshot IS NULL)""", id_registro),
                "conflicto_clave": self._contar("""SELECT COUNT(1) FROM dbo.tareas actual
JOIN dbo.tareas otra ON otra.nombre_tarea=actual.nombre_tarea AND otra.id_cliente=actual.id_cliente
AND otra.id_categoria=actual.id_categoria AND otra.id_tipo=actual.id_tipo AND otra.id_tarea<>actual.id_tarea
WHERE actual.id_tarea=? AND otra.eliminado_operativo=0""", id_registro),
            }
        if entidad == "scripts":
            return {
                "tarea_operativa": self._contar("""SELECT COUNT(1) FROM dbo.scripts s JOIN dbo.tareas t ON t.id_tarea=s.id_tarea
WHERE s.id_script=? AND t.eliminado_operativo=0""", id_registro),
                "versiones_operativas": self._contar("SELECT COUNT(1) FROM dbo.scripts_versiones WHERE id_script=? AND eliminado_operativo=0", id_registro),
                "padre_eliminado": self._contar("""SELECT COUNT(1) FROM dbo.scripts s JOIN dbo.tareas t ON t.id_tarea=s.id_tarea
WHERE s.id_script=? AND t.eliminado_operativo=1""", id_registro),
                "snapshots_incompletos": self._contar("""SELECT COUNT(1) FROM dbo.ejecuciones
WHERE id_script=? AND nombre_script_snapshot IS NULL""", id_registro),
                "ejecuciones_en_curso": self._contar("SELECT COUNT(1) FROM dbo.ejecuciones WHERE id_script=? AND estado_ejecucion='EN_EJECUCION'", id_registro),
                "ejecuciones_historicas": self._contar("""SELECT COUNT(1) FROM dbo.ejecuciones e
WHERE e.id_script=? OR e.id_version IN
(SELECT id_version FROM dbo.scripts_versiones WHERE id_script=?)""", id_registro, id_registro),
                "conflicto_clave": self._contar("""SELECT COUNT(1) FROM dbo.scripts actual
JOIN dbo.scripts otro ON otro.id_tarea=actual.id_tarea AND otro.id_script<>actual.id_script
WHERE actual.id_script=? AND otro.eliminado_operativo=0""", id_registro),
            }
        if entidad == "scripts_versiones":
            return {
                "version_activa": self._contar("SELECT COUNT(1) FROM dbo.scripts WHERE id_version_activa=? AND eliminado_operativo=0", id_registro),
                "padre_operativo": self._contar("""SELECT COUNT(1) FROM dbo.scripts_versiones v JOIN dbo.scripts s ON s.id_script=v.id_script
WHERE v.id_version=? AND s.eliminado_operativo=0""", id_registro),
                "padre_eliminado": self._contar("""SELECT COUNT(1) FROM dbo.scripts_versiones v JOIN dbo.scripts s ON s.id_script=v.id_script
WHERE v.id_version=? AND s.eliminado_operativo=1""", id_registro),
                "snapshots_incompletos": self._contar("""SELECT COUNT(1) FROM dbo.ejecuciones
WHERE id_version=? AND (nombre_archivo_snapshot IS NULL OR version_script_snapshot IS NULL)""", id_registro),
                "ejecuciones_en_curso": self._contar("SELECT COUNT(1) FROM dbo.ejecuciones WHERE id_version=? AND estado_ejecucion='EN_EJECUCION'", id_registro),
                "ejecuciones_historicas": self._contar(
                    "SELECT COUNT(1) FROM dbo.ejecuciones WHERE id_version=?", id_registro
                ),
                "conflicto_clave": self._contar("""SELECT COUNT(1) FROM dbo.scripts_versiones actual
JOIN dbo.scripts_versiones otra ON otra.id_script=actual.id_script AND otra.numero_version=actual.numero_version
AND otra.id_version<>actual.id_version WHERE actual.id_version=? AND otra.eliminado_operativo=0""", id_registro),
            }
        return {}

    def rutas_operativas(self, entidad: str, id_registro: int) -> tuple[tuple[str | None, str | None], ...]:
        if entidad == "tareas":
            sql = """SELECT v.ruta_fisica, v.ruta_env_fisica FROM dbo.scripts_versiones v
JOIN dbo.scripts s ON s.id_script=v.id_script WHERE s.id_tarea=?"""
        elif entidad == "scripts":
            sql = "SELECT ruta_fisica, ruta_env_fisica FROM dbo.scripts_versiones WHERE id_script=?"
        elif entidad == "scripts_versiones":
            sql = "SELECT ruta_fisica, ruta_env_fisica FROM dbo.scripts_versiones WHERE id_version=?"
        else:
            return ()
        return tuple((fila[0], fila[1]) for fila in self.ejecutar_lista(sql, (id_registro,), operacion="rutas_papelera"))

    def eliminar_permanente(self, entidad: str, id_registro: int) -> bool:
        if entidad == "usuarios":
            self.ejecutar("DELETE FROM dbo.usuarios_roles WHERE id_usuario=?", (id_registro,), operacion="eliminar_roles_usuario")
        elif entidad == "tareas":
            self._validar_sin_historia_tarea(id_registro)
            self.ejecutar("""DELETE d FROM dbo.notificaciones_destinatarios d
JOIN dbo.notificaciones_config_tarea c ON c.id_config_notificacion=d.id_config_notificacion
WHERE c.id_tarea=?""", (id_registro,), operacion="eliminar_destinatarios_tarea")
            self.ejecutar("DELETE FROM dbo.notificaciones_config_tarea WHERE id_tarea=?", (id_registro,), operacion="eliminar_config_notificacion")
            self.ejecutar("DELETE FROM dbo.programaciones WHERE id_tarea=?", (id_registro,), operacion="eliminar_programaciones_tarea")
            self.ejecutar("UPDATE dbo.scripts SET id_version_activa=NULL WHERE id_tarea=?", (id_registro,), operacion="desvincular_version_tarea")
            self.ejecutar("""DELETE v FROM dbo.scripts_versiones v JOIN dbo.scripts s ON s.id_script=v.id_script
WHERE s.id_tarea=?""", (id_registro,), operacion="eliminar_versiones_tarea")
            self.ejecutar("DELETE FROM dbo.scripts WHERE id_tarea=?", (id_registro,), operacion="eliminar_scripts_tarea")
        elif entidad == "scripts":
            self._validar_sin_historia_script(id_registro)
            self.ejecutar("UPDATE dbo.scripts SET id_version_activa=NULL WHERE id_script=?", (id_registro,), operacion="desvincular_version_script")
            self.ejecutar("DELETE FROM dbo.scripts_versiones WHERE id_script=?", (id_registro,), operacion="eliminar_versiones_script")
        elif entidad == "scripts_versiones":
            self._validar_sin_historia_version(id_registro)
            self.ejecutar("UPDATE dbo.scripts SET id_version_activa=NULL WHERE id_version_activa=?", (id_registro,), operacion="desvincular_version")
        tabla, identificador, _, _ = _config(entidad)
        return self.ejecutar(
            f"DELETE FROM {tabla} WHERE {identificador}=? AND eliminado_operativo=1",
            (id_registro,), operacion="eliminar_permanente_papelera",
        ) > 0

    def _validar_sin_historia_tarea(self, id_tarea):
        total = self._contar("""SELECT COUNT(1) FROM dbo.ejecuciones e
WHERE e.id_tarea=? OR e.id_script IN (SELECT id_script FROM dbo.scripts WHERE id_tarea=?)
OR e.id_version IN (SELECT v.id_version FROM dbo.scripts_versiones v
JOIN dbo.scripts s ON s.id_script=v.id_script WHERE s.id_tarea=?)""",
            id_tarea, id_tarea, id_tarea)
        if total:
            raise ErrorValidacion("No se puede eliminar la tarea porque conserva ejecuciones historicas.")

    def _validar_sin_historia_script(self, id_script):
        total = self._contar("""SELECT COUNT(1) FROM dbo.ejecuciones e
WHERE e.id_script=? OR e.id_version IN
(SELECT id_version FROM dbo.scripts_versiones WHERE id_script=?)""", id_script, id_script)
        if total:
            raise ErrorValidacion("No se puede eliminar el script porque conserva ejecuciones historicas.")

    def _validar_sin_historia_version(self, id_version):
        if self._contar("SELECT COUNT(1) FROM dbo.ejecuciones WHERE id_version=?", id_version):
            raise ErrorValidacion("No se puede eliminar la version porque conserva ejecuciones historicas.")

    def _contar(self, sql, *parametros):
        return int(self.ejecutar_escalar(sql, parametros, operacion="contar_dependencias_papelera") or 0)

    @staticmethod
    def _contexto_entidad(entidad):
        if entidad == "tareas":
            return ("CONCAT(c.nombre_cliente, N' / ', ca.nombre_categoria, N' / ', ti.nombre_tipo)",
                    "LEFT JOIN dbo.clientes c ON c.id_cliente=x.id_cliente LEFT JOIN dbo.categorias ca ON ca.id_categoria=x.id_categoria LEFT JOIN dbo.tipos ti ON ti.id_tipo=x.id_tipo", "x.activo")
        if entidad == "scripts":
            return "t.nombre_tarea", "LEFT JOIN dbo.tareas t ON t.id_tarea=x.id_tarea", "x.activo"
        if entidad == "scripts_versiones":
            return "CONCAT(s.nombre_script, N' / v', x.numero_version)", "LEFT JOIN dbo.scripts s ON s.id_script=x.id_script", "x.es_activa"
        return "CAST(NULL AS nvarchar(500))", "", "x.activo"

    @staticmethod
    def _mapear(fila):
        return ElementoPapelera(
            entidad=str(fila[0]), id_registro=int(fila[1]), nombre=str(fila[2]),
            descripcion=fila[3], contexto=fila[4], activo_anterior=bool(fila[5]),
            fecha_retiro=fila[6], usuario_retiro=fila[7], motivo_retiro=fila[8],
        )


def _config(entidad):
    try:
        return ENTIDADES[entidad]
    except KeyError as error:
        raise ValueError("Entidad de Papelera no permitida.") from error


def _patron_like(valor):
    texto = str(valor).strip().replace("~", "~~").replace("%", "~%").replace("_", "~_")
    return f"%{texto}%"
