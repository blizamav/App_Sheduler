"""Consultas de roles y permisos sin cargar catalogos por memoria."""

from __future__ import annotations

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
