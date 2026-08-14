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
    intentos_fallidos = 0,
    fecha_actualizacion = SYSDATETIME(),
    usuario_actualizacion = ?
WHERE id_usuario = ?
  AND eliminado_operativo = 0"""

SQL_INCREMENTAR_INTENTOS = """UPDATE dbo.usuarios
SET intentos_fallidos = intentos_fallidos + 1,
    fecha_actualizacion = SYSDATETIME()
WHERE id_usuario = ?
  AND eliminado_operativo = 0"""

SQL_CREAR_USUARIO = """INSERT INTO dbo.usuarios
    (usuario, nombre_completo, email, password_hash, activo, usuario_creacion)
OUTPUT INSERTED.id_usuario
VALUES (?, ?, ?, ?, ?, ?)"""

SQL_ACTUALIZAR_USUARIO = """UPDATE dbo.usuarios
SET nombre_completo = ?,
    email = ?,
    usuario_actualizacion = ?,
    fecha_actualizacion = SYSDATETIME()
    {actualizacion_password}
WHERE id_usuario = ?
  AND eliminado_operativo = 0"""

SQL_CAMBIAR_ESTADO_USUARIO = """UPDATE dbo.usuarios
SET activo = ?,
    usuario_actualizacion = ?,
    fecha_actualizacion = SYSDATETIME()
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
        id_rol: int | None = None,
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
        if id_rol is not None:
            filtros.append(
                "EXISTS (SELECT 1 FROM dbo.usuarios_roles ur "
                "WHERE ur.id_usuario = u.id_usuario AND ur.id_rol = ? AND ur.activo = 1)"
            )
            parametros.append(id_rol)

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

    def incrementar_intentos_fallidos(self, id_usuario: int) -> bool:
        return self.ejecutar(
            SQL_INCREMENTAR_INTENTOS,
            (id_usuario,),
            operacion="incrementar_intentos_login",
        ) > 0

    def crear(
        self,
        usuario: str,
        nombre_completo: str,
        email: str | None,
        password_hash: str,
        activo: bool,
        actor: str,
    ) -> int:
        fila = self.ejecutar_uno(
            SQL_CREAR_USUARIO,
            (usuario, nombre_completo, email, password_hash, int(activo), actor),
            operacion="crear_usuario",
        )
        return int(fila[0])

    def actualizar(
        self,
        id_usuario: int,
        nombre_completo: str,
        email: str | None,
        actor: str,
        password_hash: str | None = None,
    ) -> bool:
        if password_hash is None:
            sql = SQL_ACTUALIZAR_USUARIO.format(actualizacion_password="")
            parametros = (nombre_completo, email, actor, id_usuario)
        else:
            sql = SQL_ACTUALIZAR_USUARIO.format(
                actualizacion_password=", password_hash = ?, debe_cambiar_password = 0"
            )
            parametros = (nombre_completo, email, actor, password_hash, id_usuario)
        return self.ejecutar(
            sql,
            parametros,
            operacion="actualizar_usuario",
        ) > 0

    def cambiar_estado(self, id_usuario: int, activo: bool, actor: str) -> bool:
        return self.ejecutar(
            SQL_CAMBIAR_ESTADO_USUARIO,
            (int(activo), actor, id_usuario),
            operacion="cambiar_estado_usuario",
        ) > 0

    def existe_usuario(self, usuario: str) -> bool:
        return bool(
            self.ejecutar_escalar(
                "SELECT COUNT(1) FROM dbo.usuarios WHERE usuario = ?",
                (usuario,),
                operacion="validar_usuario_unico",
            )
        )

    def existe_email(self, email: str, *, excluir_id: int | None = None) -> bool:
        sql = "SELECT COUNT(1) FROM dbo.usuarios WHERE LOWER(email) = LOWER(?)"
        parametros: tuple[object, ...] = (email,)
        if excluir_id is not None:
            sql += " AND id_usuario <> ?"
            parametros = (email, excluir_id)
        return bool(
            self.ejecutar_escalar(
                sql,
                parametros,
                operacion="validar_email_usuario_unico",
            )
        )
