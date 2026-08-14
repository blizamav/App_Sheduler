"""Consultas de roles y permisos sin cargar catalogos por memoria."""

from __future__ import annotations

from collections.abc import Sequence

from app_scheduler.persistencia.mapeadores import mapear_permiso, mapear_rol
from app_scheduler.persistencia.modelos import Permiso, Rol
from app_scheduler.persistencia.repositorio import RepositorioSQL


_SELECCION_ROL = """r.id_rol,
    r.codigo_rol,
    r.nombre_rol,
    r.descripcion,
    r.es_sistema,
    r.activo"""
_SELECCION_PERMISO = """p.id_permiso,
    p.codigo_permiso,
    p.modulo,
    p.accion,
    p.descripcion,
    p.activo"""

SQL_ROLES_USUARIO = f"""SELECT {_SELECCION_ROL}
FROM dbo.usuarios_roles ur
INNER JOIN dbo.roles r ON r.id_rol = ur.id_rol
WHERE ur.id_usuario = ?
  AND ur.activo = 1
  AND r.activo = 1
ORDER BY r.codigo_rol, r.id_rol"""

SQL_PERMISOS_EFECTIVOS = f"""SELECT DISTINCT {_SELECCION_PERMISO}
FROM dbo.usuarios_roles ur
INNER JOIN dbo.roles r ON r.id_rol = ur.id_rol
INNER JOIN dbo.roles_permisos rp ON rp.id_rol = r.id_rol
INNER JOIN dbo.permisos p ON p.id_permiso = rp.id_permiso
WHERE ur.id_usuario = ?
  AND ur.activo = 1
  AND r.activo = 1
  AND rp.activo = 1
  AND rp.permitido = 1
  AND p.activo = 1
ORDER BY p.codigo_permiso, p.id_permiso"""


class RepositorioSeguridad(RepositorioSQL):
    def listar_roles(self, *, solo_activos: bool = True) -> tuple[Rol, ...]:
        filtro = "WHERE r.activo = 1" if solo_activos else ""
        sql = f"""SELECT {_SELECCION_ROL}
FROM dbo.roles r
{filtro}
ORDER BY r.codigo_rol, r.id_rol"""
        filas = self.ejecutar_lista(sql, operacion="listar_roles")
        return tuple(mapear_rol(fila) for fila in filas)

    def listar_permisos(self, *, solo_activos: bool = True) -> tuple[Permiso, ...]:
        filtro = "WHERE p.activo = 1" if solo_activos else ""
        sql = f"""SELECT {_SELECCION_PERMISO}
FROM dbo.permisos p
{filtro}
ORDER BY p.codigo_permiso, p.id_permiso"""
        filas = self.ejecutar_lista(sql, operacion="listar_permisos")
        return tuple(mapear_permiso(fila) for fila in filas)

    def obtener_roles_usuario(self, id_usuario: int) -> tuple[Rol, ...]:
        filas = self.ejecutar_lista(
            SQL_ROLES_USUARIO,
            (id_usuario,),
            operacion="obtener_roles_usuario",
        )
        return tuple(mapear_rol(fila) for fila in filas)

    def obtener_permisos_efectivos(self, id_usuario: int) -> tuple[Permiso, ...]:
        filas = self.ejecutar_lista(
            SQL_PERMISOS_EFECTIVOS,
            (id_usuario,),
            operacion="obtener_permisos_efectivos",
        )
        return tuple(mapear_permiso(fila) for fila in filas)

    def obtener_rol_por_id(self, id_rol: int) -> Rol | None:
        fila = self.ejecutar_uno(
            f"""SELECT {_SELECCION_ROL}
FROM dbo.roles r
WHERE r.id_rol = ? AND r.activo = 1""",
            (id_rol,),
            operacion="obtener_rol_por_id",
        )
        return None if fila is None else mapear_rol(fila)

    def asignar_rol_usuario(self, id_usuario: int, id_rol: int, actor: str) -> None:
        self.ejecutar(
            """UPDATE dbo.usuarios_roles
SET activo = CASE WHEN id_rol = ? THEN 1 ELSE 0 END
WHERE id_usuario = ?""",
            (id_rol, id_usuario),
            operacion="desactivar_roles_usuario",
        )
        self.ejecutar(
            """IF EXISTS (
    SELECT 1 FROM dbo.usuarios_roles WHERE id_usuario = ? AND id_rol = ?
)
    UPDATE dbo.usuarios_roles SET activo = 1 WHERE id_usuario = ? AND id_rol = ?
ELSE
    INSERT INTO dbo.usuarios_roles (id_usuario, id_rol, usuario_creacion, activo)
    VALUES (?, ?, ?, 1)""",
            (id_usuario, id_rol, id_usuario, id_rol, id_usuario, id_rol, actor),
            operacion="asignar_rol_usuario",
        )

    def obtener_roles_por_usuarios(
        self, ids_usuarios: Sequence[int]
    ) -> dict[int, tuple[Rol, ...]]:
        ids = tuple(dict.fromkeys(int(valor) for valor in ids_usuarios))
        if not ids:
            return {}
        marcadores = ", ".join("?" for _ in ids)
        filas = self.ejecutar_lista(
            f"""SELECT ur.id_usuario, {_SELECCION_ROL}
FROM dbo.usuarios_roles ur
INNER JOIN dbo.roles r ON r.id_rol = ur.id_rol
WHERE ur.id_usuario IN ({marcadores})
  AND ur.activo = 1
  AND r.activo = 1
ORDER BY ur.id_usuario, r.codigo_rol""",
            ids,
            operacion="obtener_roles_usuarios",
        )
        resultado: dict[int, list[Rol]] = {id_usuario: [] for id_usuario in ids}
        for fila in filas:
            resultado.setdefault(int(fila[0]), []).append(mapear_rol(fila[1:]))
        return {clave: tuple(roles) for clave, roles in resultado.items()}

    def contar_super_admin_activos(self, *, excluir_id: int | None = None) -> int:
        sql = """SELECT COUNT(DISTINCT u.id_usuario)
FROM dbo.usuarios u
INNER JOIN dbo.usuarios_roles ur ON ur.id_usuario = u.id_usuario AND ur.activo = 1
INNER JOIN dbo.roles r ON r.id_rol = ur.id_rol AND r.activo = 1
WHERE u.activo = 1
  AND u.eliminado_operativo = 0
  AND r.codigo_rol = 'SUPER_ADMIN'"""
        parametros: tuple[object, ...] = ()
        if excluir_id is not None:
            sql += " AND u.id_usuario <> ?"
            parametros = (excluir_id,)
        return int(
            self.ejecutar_escalar(
                sql,
                parametros,
                operacion="contar_super_admin_activos",
            )
            or 0
        )

    def obtener_matriz_roles_permisos(self) -> dict[str, frozenset[str]]:
        filas = self.ejecutar_lista(
            """SELECT r.codigo_rol, p.codigo_permiso
FROM dbo.roles r
LEFT JOIN dbo.roles_permisos rp
    ON rp.id_rol = r.id_rol AND rp.activo = 1 AND rp.permitido = 1
LEFT JOIN dbo.permisos p ON p.id_permiso = rp.id_permiso AND p.activo = 1
WHERE r.activo = 1
ORDER BY r.codigo_rol, p.codigo_permiso""",
            operacion="obtener_matriz_roles_permisos",
        )
        matriz: dict[str, set[str]] = {}
        for codigo_rol, codigo_permiso in filas:
            matriz.setdefault(str(codigo_rol), set())
            if codigo_permiso:
                matriz[str(codigo_rol)].add(str(codigo_permiso))
        return {rol: frozenset(permisos) for rol, permisos in matriz.items()}
