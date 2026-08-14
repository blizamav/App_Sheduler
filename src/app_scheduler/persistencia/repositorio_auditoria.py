"""Persistencia canonica de auditoria para acciones humanas."""

from app_scheduler.persistencia.modelos import EventoAuditoria
from app_scheduler.persistencia.repositorio import RepositorioSQL


SQL_INSERTAR_AUDITORIA = """INSERT INTO dbo.auditoria_cambios
    (usuario, id_usuario, accion, entidad, id_entidad, nombre_entidad,
     descripcion, valores_antes, valores_despues, ip_origen, user_agent,
     resultado, modulo, ruta, metodo_http, activo)
OUTPUT INSERTED.id_auditoria
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)"""


class RepositorioAuditoria(RepositorioSQL):
    def registrar(self, evento: EventoAuditoria) -> int:
        fila = self.ejecutar_uno(
            SQL_INSERTAR_AUDITORIA,
            (
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
            ),
            operacion="registrar_auditoria",
        )
        return int(fila[0])
