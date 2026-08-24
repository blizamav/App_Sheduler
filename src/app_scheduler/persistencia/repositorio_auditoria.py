"""Persistencia canonica e inmutable de auditoria para acciones humanas."""

from app_scheduler.persistencia.modelos import (
    EventoAuditoria,
    Pagina,
    Paginacion,
    RegistroAuditoria,
)
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

    def listar(
        self,
        paginacion: Paginacion,
        *,
        fecha_desde=None,
        fecha_hasta=None,
        usuario: str | None = None,
        accion: str | None = None,
        entidad: str | None = None,
        id_entidad: str | None = None,
        busqueda: str | None = None,
    ) -> Pagina[RegistroAuditoria]:
        expresiones = self._expresiones_lectura()
        condiciones, parametros = self._filtros(
            expresiones,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            usuario=usuario,
            accion=accion,
            entidad=entidad,
            id_entidad=id_entidad,
            busqueda=busqueda,
        )
        where = " AND ".join(condiciones)
        total = int(self.ejecutar_escalar(
            f"SELECT COUNT(1) FROM dbo.auditoria_cambios WHERE {where}",
            parametros,
            operacion="contar_auditoria",
        ) or 0)
        campos = self._seleccion(expresiones)
        filas = self.ejecutar_lista(
            f"""SELECT {campos}
FROM dbo.auditoria_cambios
WHERE {where}
ORDER BY {expresiones['fecha_evento']} DESC, id_auditoria DESC
OFFSET ? ROWS FETCH NEXT ? ROWS ONLY""",
            (*parametros, paginacion.desplazamiento, paginacion.por_pagina),
            operacion="listar_auditoria",
        )
        return Pagina(
            tuple(self._mapear(fila) for fila in filas),
            total,
            paginacion.pagina,
            paginacion.por_pagina,
        )

    def obtener(self, id_auditoria: int) -> RegistroAuditoria | None:
        expresiones = self._expresiones_lectura()
        fila = self.ejecutar_uno(
            f"""SELECT {self._seleccion(expresiones)}
FROM dbo.auditoria_cambios
WHERE id_auditoria = ?""",
            (id_auditoria,),
            operacion="obtener_auditoria",
        )
        return None if fila is None else self._mapear(fila)

    def opciones_filtros(self) -> tuple[tuple[str, ...], tuple[str, ...]]:
        acciones = self.ejecutar_lista(
            """SELECT DISTINCT accion FROM dbo.auditoria_cambios
WHERE activo = 1 AND accion IS NOT NULL ORDER BY accion""",
            operacion="listar_acciones_auditoria",
        )
        expresiones = self._expresiones_lectura()
        entidades = self.ejecutar_lista(
            f"""SELECT DISTINCT {expresiones['entidad']} AS entidad
FROM dbo.auditoria_cambios
WHERE activo = 1 AND {expresiones['entidad']} IS NOT NULL
ORDER BY entidad""",
            operacion="listar_entidades_auditoria",
        )
        return (
            tuple(str(fila[0]) for fila in acciones),
            tuple(str(fila[0]) for fila in entidades),
        )

    def _expresiones_lectura(self) -> dict[str, str]:
        usa_legacy = bool(self.ejecutar_escalar(
            SQL_TIENE_COLUMNAS_LEGACY,
            operacion="detectar_auditoria_legacy_lectura",
        ))
        if not usa_legacy:
            return {
                "fecha_evento": "fecha_evento",
                "entidad": "entidad",
                "id_entidad": "id_entidad",
                "valores_antes": "valores_antes",
                "valores_despues": "valores_despues",
                "ip_origen": "ip_origen",
            }
        return {
            "fecha_evento": "COALESCE(fecha_evento, fecha_hora)",
            "entidad": "COALESCE(NULLIF(entidad, ''), tabla_afectada)",
            "id_entidad": "COALESCE(NULLIF(id_entidad, ''), id_registro)",
            "valores_antes": "COALESCE(valores_antes, valor_anterior)",
            "valores_despues": "COALESCE(valores_despues, valor_nuevo)",
            "ip_origen": "COALESCE(ip_origen, ip)",
        }

    @staticmethod
    def _seleccion(expresiones: dict[str, str]) -> str:
        return f"""id_auditoria, {expresiones['fecha_evento']} AS fecha_evento,
usuario, id_usuario, accion, {expresiones['entidad']} AS entidad,
{expresiones['id_entidad']} AS id_entidad, nombre_entidad, descripcion,
{expresiones['valores_antes']} AS valores_antes,
{expresiones['valores_despues']} AS valores_despues,
{expresiones['ip_origen']} AS ip_origen, user_agent, resultado, modulo, ruta,
metodo_http"""

    @staticmethod
    def _filtros(expresiones: dict[str, str], **filtros):
        condiciones = ["activo = 1"]
        parametros: list[object] = []
        if filtros.get("fecha_desde"):
            condiciones.append(f"{expresiones['fecha_evento']} >= ?")
            parametros.append(filtros["fecha_desde"])
        if filtros.get("fecha_hasta"):
            condiciones.append(f"{expresiones['fecha_evento']} < DATEADD(day, 1, CAST(? AS date))")
            parametros.append(filtros["fecha_hasta"])
        for campo in ("usuario", "accion"):
            valor = filtros.get(campo)
            if valor:
                condiciones.append(f"{campo} LIKE ? ESCAPE '~'")
                parametros.append(_patron_like(valor))
        if filtros.get("entidad"):
            condiciones.append(f"{expresiones['entidad']} = ?")
            parametros.append(filtros["entidad"])
        if filtros.get("id_entidad"):
            condiciones.append(f"{expresiones['id_entidad']} = ?")
            parametros.append(filtros["id_entidad"])
        if filtros.get("busqueda"):
            patron = _patron_like(filtros["busqueda"])
            condiciones.append(
                "(descripcion LIKE ? ESCAPE '~' OR nombre_entidad LIKE ? ESCAPE '~' "
                "OR modulo LIKE ? ESCAPE '~')"
            )
            parametros.extend((patron, patron, patron))
        return condiciones, tuple(parametros)

    @staticmethod
    def _mapear(fila) -> RegistroAuditoria:
        return RegistroAuditoria(*fila)


def _patron_like(valor: str) -> str:
    texto = str(valor).strip().replace("~", "~~").replace("%", "~%").replace("_", "~_")
    return f"%{texto}%"
