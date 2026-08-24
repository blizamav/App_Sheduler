"""Persistencia canonica de auditoria para acciones humanas."""

from app_scheduler.persistencia.modelos import EventoAuditoria
from app_scheduler.persistencia.repositorio import RepositorioSQL


SQL_INSERTAR_AUDITORIA = """INSERT INTO dbo.auditoria_cambios
    (usuario, id_usuario, accion, entidad, id_entidad, nombre_entidad,
     descripcion, valores_antes, valores_despues, ip_origen, user_agent,
     resultado, modulo, ruta, metodo_http, activo)
OUTPUT INSERTED.id_auditoria
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)"""

SQL_INSERTAR_AUDITORIA_LEGACY = """INSERT INTO dbo.auditoria_cambios
    (usuario, id_usuario, accion, entidad, id_entidad, nombre_entidad,
     descripcion, valores_antes, valores_despues, ip_origen, user_agent,
     resultado, modulo, ruta, metodo_http, activo,
     fecha_hora, tabla_afectada, id_registro, valor_anterior, valor_nuevo, ip)
OUTPUT INSERTED.id_auditoria
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1,
        SYSDATETIME(), ?, ?, ?, ?, ?)"""

SQL_TIENE_COLUMNAS_LEGACY = """SELECT CASE WHEN
COL_LENGTH('dbo.auditoria_cambios', 'tabla_afectada') IS NOT NULL AND
COL_LENGTH('dbo.auditoria_cambios', 'id_registro') IS NOT NULL
THEN 1 ELSE 0 END"""


class RepositorioAuditoria(RepositorioSQL):
    def registrar(self, evento: EventoAuditoria) -> int:
        parametros = (
            evento.usuario,
            evento.id_usuario,
            evento.accion,
            evento.entidad,
            evento.id_entidad,
            evento.nombre_entidad,
            evento.descripcion,
            evento.valores_antes,
            evento.valores_despues,
            evento.ip_origen,
            evento.user_agent,
            evento.resultado,
            evento.modulo,
            evento.ruta,
            evento.metodo_http,
        )
        usa_legacy = bool(self.ejecutar_escalar(
            SQL_TIENE_COLUMNAS_LEGACY,
            operacion="detectar_auditoria_legacy",
        ))
        sql = SQL_INSERTAR_AUDITORIA_LEGACY if usa_legacy else SQL_INSERTAR_AUDITORIA
        if usa_legacy:
            parametros += (
                evento.entidad or "GENERAL",
                evento.id_entidad or "-",
                evento.valores_antes,
                evento.valores_despues,
                evento.ip_origen,
            )
        fila = self.ejecutar_uno(
            sql,
            parametros,
            operacion="registrar_auditoria",
        )
        return int(fila[0])
