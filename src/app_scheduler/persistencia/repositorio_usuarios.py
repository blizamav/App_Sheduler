"""Persistencia de usuarios preparada para autenticacion y administracion futura."""

from __future__ import annotations

from datetime import datetime

from app_scheduler.persistencia.mapeadores import (
    mapear_credencial_usuario,
    mapear_usuario,
)
from app_scheduler.persistencia.modelos import CredencialUsuario, Pagina, Paginacion, Usuario
from app_scheduler.persistencia.repositorio import RepositorioSQL


_SELECCION_USUARIO = """u.id_usuario,
    u.usuario,
    u.nombre_completo,
    u.email,
    u.debe_cambiar_password,
    u.ultimo_login,
    u.intentos_fallidos,
    u.bloqueado,
    u.eliminado_operativo,
    u.fecha_eliminado_operativo,
    u.fecha_creacion,
    u.fecha_actualizacion,
    u.activo"""

SQL_USUARIO_POR_ID = f"""SELECT {_SELECCION_USUARIO}
FROM dbo.usuarios u
WHERE u.id_usuario = ?
  AND u.eliminado_operativo = 0"""

SQL_CREDENCIAL_POR_IDENTIFICADOR = f"""SELECT {_SELECCION_USUARIO},
    u.password_hash
FROM dbo.usuarios u
WHERE u.usuario = ?"""

SQL_ACTUALIZAR_ULTIMO_LOGIN = """UPDATE dbo.usuarios
SET ultimo_login = ?,
    fecha_actualizacion = SYSDATETIME(),
    usuario_actualizacion = ?
WHERE id_usuario = ?
  AND eliminado_operativo = 0"""


def _patron_like_literal(valor: str) -> str:
    escapado = valor.replace("~", "~~").replace("%", "~%").replace("_", "~_")
    return f"%{escapado}%"


class RepositorioUsuarios(RepositorioSQL):
    def obtener_por_id(self, id_usuario: int) -> Usuario | None:
        fila = self.ejecutar_uno(
            SQL_USUARIO_POR_ID,
            (id_usuario,),
            operacion="obtener_usuario_por_id",
        )
        return None if fila is None else mapear_usuario(fila)

    def obtener_credencial_por_identificador(
        self, identificador: str
    ) -> CredencialUsuario | None:
        fila = self.ejecutar_uno(
            SQL_CREDENCIAL_POR_IDENTIFICADOR,
            (identificador,),
            operacion="obtener_credencial_usuario",
        )
        return None if fila is None else mapear_credencial_usuario(fila)

    def listar(
        self,
        paginacion: Paginacion,
        *,
        activo: bool | None = None,
        busqueda: str | None = None,
    ) -> Pagina[Usuario]:
        filtros = ["u.eliminado_operativo = 0"]
        parametros: list[object] = []

        if activo is not None:
            filtros.append("u.activo = ?")
            parametros.append(int(activo))
        if busqueda and busqueda.strip():
            filtros.append(
                "(u.usuario LIKE ? ESCAPE '~' "
                "OR u.nombre_completo LIKE ? ESCAPE '~' "
                "OR u.email LIKE ? ESCAPE '~')"
            )
            patron = _patron_like_literal(busqueda.strip())
            parametros.extend((patron, patron, patron))

        clausula_where = " AND ".join(filtros)
        sql_total = f"""SELECT COUNT(1)
FROM dbo.usuarios u
WHERE {clausula_where}"""
        sql_listado = f"""SELECT {_SELECCION_USUARIO}
FROM dbo.usuarios u
WHERE {clausula_where}
ORDER BY u.usuario, u.id_usuario
OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"""

        total = int(
            self.ejecutar_escalar(
                sql_total,
                parametros,
                operacion="contar_usuarios",
            )
            or 0
        )
        filas = self.ejecutar_lista(
            sql_listado,
            (*parametros, paginacion.desplazamiento, paginacion.por_pagina),
            operacion="listar_usuarios",
        )
        return Pagina(
            elementos=tuple(mapear_usuario(fila) for fila in filas),
            total=total,
            pagina=paginacion.pagina,
            por_pagina=paginacion.por_pagina,
        )

    def actualizar_ultimo_login(
        self,
        id_usuario: int,
        fecha: datetime,
        actor: str,
    ) -> bool:
        afectadas = self.ejecutar(
            SQL_ACTUALIZAR_ULTIMO_LOGIN,
            (fecha, actor, id_usuario),
            operacion="actualizar_ultimo_login",
        )
        return afectadas > 0
