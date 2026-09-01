"""Configuracion humana de notificaciones y proveedor Graph global."""

from __future__ import annotations

import re

from app_scheduler.compartido.auditoria import crear_evento_auditoria
from app_scheduler.compartido.errores import ErrorValidacion
from app_scheduler.compartido.unidad_trabajo import UnidadTrabajoSQL
from app_scheduler.modulos.notificaciones.seguridad import normalizar_email
from app_scheduler.persistencia.modelos import ConfiguracionNotificacionTarea, DestinatarioNotificacion
from app_scheduler.persistencia.repositorio_auditoria import RepositorioAuditoria
from app_scheduler.persistencia.repositorio_notificaciones import RepositorioNotificaciones
from app_scheduler.persistencia.repositorio_tareas import RepositorioTareas


PATRON_IDENTIFICADOR = re.compile(r"^[A-Za-z0-9-]{1,100}$")
SCOPE_GRAPH = "https://graph.microsoft.com/.default"


class ServicioNotificacionesTarea:
    def __init__(self, proveedor, servicio_evidencias, *, fabrica_uow=UnidadTrabajoSQL,
                 repositorio=RepositorioNotificaciones, repositorio_tareas=RepositorioTareas,
                 repositorio_auditoria=RepositorioAuditoria):
        self.proveedor = proveedor
        self.servicio_evidencias = servicio_evidencias
        self.fabrica_uow = fabrica_uow
        self.tipo_repositorio = repositorio
        self.tipo_tareas = repositorio_tareas
        self.tipo_auditoria = repositorio_auditoria

    def obtener(self, id_tarea: int):
        with self.proveedor.conexion_lectura() as conexion:
            config = self.tipo_repositorio(conexion).obtener_configuracion_tarea(id_tarea)
        soporte = self.servicio_evidencias.obtener_para_tarea(id_tarea)["soporte"]
        return {"configuracion": config, "destinatarios": self._para_formulario(config.destinatarios),
                "soporte": soporte}

    def guardar(self, id_tarea: int, formulario, actor, contexto):
        destinatarios = self._destinatarios(formulario)
        asunto = str(formulario.get("asunto_personalizado") or "").strip() or None
        if asunto and len(asunto) > 255:
            raise ErrorValidacion("El asunto personalizado admite hasta 255 caracteres.")
        notificar_exito = formulario.get("notificar_exito_activa") == "1"
        enviar = formulario.get("enviar_evidencia") == "1"
        alerta = formulario.get("alerta_error_activa") == "1"
        usar_global = formulario.get("usar_alerta_global") == "1"
        if notificar_exito and not any(
            d.tipo_destinatario == "EXITO" and d.canal == "TO"
            for d in destinatarios
        ):
            raise ErrorValidacion("Para la notificacion de exito configura al menos un destinatario TO.")
        if enviar and not any(
            d.tipo_destinatario == "EVIDENCIA" and d.canal == "TO"
            for d in destinatarios
        ):
            raise ErrorValidacion("Para enviar Evidencia al cliente configura al menos un destinatario TO.")
        if alerta and not usar_global and not any(
            d.tipo_destinatario == "ALERTA" and d.canal == "TO" for d in destinatarios
        ):
            raise ErrorValidacion("Configura un destinatario TO de alerta o usa los destinatarios globales.")
        soporte = self.servicio_evidencias.obtener_para_tarea(id_tarea)["soporte"]
        if enviar and not soporte["compatible"]:
            raise ErrorValidacion("No se puede activar evidencia: " + " ".join(soporte["errores"]))
        with self.fabrica_uow(self.proveedor) as uow:
            conexion = uow.obtener_conexion()
            tarea = self.tipo_tareas(conexion).obtener_por_id(id_tarea)
            if tarea is None:
                raise ErrorValidacion("Tarea no encontrada.")
            repo = self.tipo_repositorio(conexion)
            actual = repo.obtener_configuracion_tarea(id_tarea)
            nueva = ConfiguracionNotificacionTarea(
                actual.id_config_notificacion, id_tarea, enviar, notificar_exito,
                "STDOUT_V1", asunto,
                formulario.get("usar_asunto_sugerido_script") == "1",
                formulario.get("adjuntar_archivos_declarados") == "1",
                False, alerta, usar_global, destinatarios,
            )
            antes = self._snapshot(actual)
            despues = self._snapshot(nueva)
            if antes == despues:
                raise ErrorValidacion("No hay cambios de notificaciones para guardar.")
            identificador = repo.guardar_configuracion_tarea(nueva)
            repo.reemplazar_destinatarios(identificador, destinatarios)
            self.tipo_auditoria(conexion).registrar(crear_evento_auditoria(
                usuario=actor.usuario, id_usuario=actor.id_usuario,
                accion="NOTIFICACIONES_TAREA_EDITADAS", entidad="notificaciones_config_tarea",
                id_entidad=id_tarea, nombre_entidad=tarea.nombre_tarea,
                descripcion="Configuracion y destinatarios de notificacion actualizados.",
                valores_antes=antes, valores_despues=despues, contexto=contexto,
                modulo="NOTIFICACIONES",
            ))
            uow.confirmar()

    @classmethod
    def _destinatarios(cls, formulario):
        resultado = []
        vistos = set()
        for tipo in ("EXITO", "ALERTA", "EVIDENCIA"):
            for canal in ("TO", "CC", "BCC"):
                valor = str(formulario.get(f"{tipo.lower()}_{canal.lower()}") or "")
                for bruto in re.split(r"[,;\r\n]+", valor):
                    if not bruto.strip():
                        continue
                    try:
                        email = normalizar_email(bruto)
                    except ValueError as error:
                        raise ErrorValidacion(f"Email invalido en {tipo} {canal}.") from error
                    clave_email = (tipo, email)
                    if clave_email in vistos:
                        raise ErrorValidacion(f"El email {email} esta repetido en destinatarios {tipo}.")
                    vistos.add(clave_email)
                    resultado.append(DestinatarioNotificacion(None, tipo, canal, email, None))
        return tuple(resultado)

    @staticmethod
    def _para_formulario(destinatarios):
        resultado = {
            f"{tipo.lower()}_{canal.lower()}": ""
            for tipo in ("EXITO", "ALERTA", "EVIDENCIA")
            for canal in ("TO", "CC", "BCC")
        }
        for item in destinatarios:
            clave = f"{item.tipo_destinatario.lower()}_{item.canal.lower()}"
            resultado[clave] = "\n".join(filter(None, (resultado[clave], item.email)))
        return resultado

    @staticmethod
    def _snapshot(config):
        return {
            "enviar_evidencia": config.enviar_evidencia,
            "notificar_exito_activa": config.notificar_exito_activa,
            "asunto_personalizado": config.asunto_personalizado,
            "usar_asunto_sugerido_script": config.usar_asunto_sugerido_script,
            "adjuntar_archivos_declarados": config.adjuntar_archivos_declarados,
            "adjuntar_log_tecnico": config.adjuntar_log_tecnico,
            "alerta_error_activa": config.alerta_error_activa,
            "usar_alerta_global": config.usar_alerta_global,
            "destinatarios": tuple((d.tipo_destinatario, d.canal, d.email) for d in config.destinatarios),
        }


class ServicioConfiguracionGraph:
    def __init__(self, proveedor, configuracion, *, fabrica_uow=UnidadTrabajoSQL,
                 repositorio=RepositorioNotificaciones,
                 repositorio_auditoria=RepositorioAuditoria):
        self.proveedor = proveedor
        self.configuracion = configuracion
        self.fabrica_uow = fabrica_uow
        self.tipo_repositorio = repositorio
        self.tipo_auditoria = repositorio_auditoria

    def obtener(self):
        with self.proveedor.conexion_lectura() as conexion:
            sql = self.tipo_repositorio(conexion).obtener_configuracion_graph()
        return self._estado(sql)

    def resumen_publico(self):
        """Expone solo el estado operativo necesario fuera del modulo Graph."""
        estado = self.obtener()
        return {
            "disponible_envio": bool(estado["disponible_envio"]),
            "estado": str(estado["estado"]),
        }

    def guardar(self, formulario, actor, contexto):
        if any("secret" in str(clave).lower() for clave in formulario.keys()):
            raise ErrorValidacion("Los secretos Graph solo se configuran por variables de entorno.")
        with self.fabrica_uow(self.proveedor) as uow:
            conexion = uow.obtener_conexion()
            repo = self.tipo_repositorio(conexion)
            actual = repo.obtener_configuracion_graph()
            if actual is None:
                raise ErrorValidacion("No existe la configuracion global MAIL_GRAPH del bootstrap.")
            datos = self._validar(formulario, actual)
            antes = self._snapshot(actual)
            if antes == datos:
                raise ErrorValidacion("No hay cambios de Graph para guardar.")
            if not repo.guardar_configuracion_graph(actual.id_config_mail, datos, actor.usuario):
                raise ErrorValidacion("La configuracion Graph ya no esta disponible.")
            self.tipo_auditoria(conexion).registrar(crear_evento_auditoria(
                usuario=actor.usuario, id_usuario=actor.id_usuario,
                accion="CONFIGURACION_MAIL_GRAPH_EDITADA", entidad="configuracion_mail_graph",
                id_entidad=actual.id_config_mail, nombre_entidad="MAIL_GRAPH",
                descripcion="Configuracion no secreta de Microsoft Graph actualizada.",
                valores_antes=antes, valores_despues=datos, contexto=contexto,
                modulo="MAIL_GRAPH",
            ))
            uow.confirmar()

    def efectiva(self):
        estado = self.obtener()
        if not estado["disponible_envio"]:
            return None
        return {**estado["efectiva"], "client_secret": self.configuracion.graph_client_secret}

    def _estado(self, sql):
        efectiva = {
            "tenant_id": (sql.tenant_id if sql else None) or self.configuracion.graph_tenant_id,
            "client_id": (sql.client_id if sql else None) or self.configuracion.graph_client_id,
            "graph_scope": (sql.graph_scope if sql else None) or self.configuracion.graph_scope,
            "send_mail_user": (sql.send_mail_user if sql else None) or self.configuracion.graph_send_mail_user,
            "save_to_sent_items": sql.save_to_sent_items if sql else self.configuracion.graph_save_to_sent_items,
            "alertas_destinatarios_default": (sql.alertas_destinatarios_default if sql else None) or self.configuracion.graph_alertas_default,
        }
        campos = all(efectiva[clave] for clave in ("tenant_id", "client_id", "graph_scope", "send_mail_user"))
        secret = bool(self.configuracion.graph_client_secret)
        sql_activo = bool(sql and sql.activo)
        disponible = bool(self.configuracion.graph_mail_enabled and sql_activo and campos and secret)
        codigo = "CONFIGURADO" if disponible else (
            "DESHABILITADO" if not self.configuracion.graph_mail_enabled or not sql_activo else "INCOMPLETO"
        )
        return {"sql": sql, "efectiva": efectiva, "estado": codigo,
                "mail_enabled_env": self.configuracion.graph_mail_enabled,
                "secret_configurado": secret, "campos_completos": campos,
                "disponible_envio": disponible}

    def _validar(self, formulario, actual=None):
        tenant = (
            str(formulario.get("tenant_id") or "").strip()
            or (actual.tenant_id if actual else None)
        )
        client = (
            str(formulario.get("client_id") or "").strip()
            or (actual.client_id if actual else None)
        )
        scope = str(
            formulario.get("graph_scope")
            or (actual.graph_scope if actual else None)
            or SCOPE_GRAPH
        ).strip()
        sender = str(formulario.get("send_mail_user") or "").strip().lower() or None
        alertas = str(formulario.get("alertas_destinatarios_default") or "").strip() or None
        activo = formulario.get("activo") == "1"
        if tenant and not PATRON_IDENTIFICADOR.fullmatch(tenant):
            raise ErrorValidacion("Tenant ID contiene caracteres no validos.")
        if client and not PATRON_IDENTIFICADOR.fullmatch(client):
            raise ErrorValidacion("Client ID contiene caracteres no validos.")
        if scope != SCOPE_GRAPH:
            raise ErrorValidacion("El scope de aplicacion debe ser https://graph.microsoft.com/.default.")
        if sender:
            try: sender = normalizar_email(sender)
            except ValueError as error: raise ErrorValidacion("El buzon remitente no es valido.") from error
        emails = []
        for bruto in re.split(r"[,;\r\n]+", alertas or ""):
            if bruto.strip():
                try: email = normalizar_email(bruto)
                except ValueError as error: raise ErrorValidacion("Existe un destinatario global invalido.") from error
                if email not in emails: emails.append(email)
        tenant_efectivo = tenant or self.configuracion.graph_tenant_id
        client_efectivo = client or self.configuracion.graph_client_id
        if activo and not all((tenant_efectivo, client_efectivo, sender)):
            raise ErrorValidacion("Tenant ID, Client ID y buzon remitente son obligatorios para activar Graph.")
        if activo and not self.configuracion.graph_client_secret:
            raise ErrorValidacion("GRAPH_CLIENT_SECRET no esta configurado en el ambiente.")
        return {"activo": activo, "tenant_id": tenant, "client_id": client,
                "graph_scope": scope, "send_mail_user": sender,
                "save_to_sent_items": formulario.get("save_to_sent_items") == "1",
                "alertas_destinatarios_default": ";".join(emails) or None}

    @staticmethod
    def _snapshot(actual):
        return {"activo": actual.activo, "tenant_id": actual.tenant_id,
                "client_id": actual.client_id, "graph_scope": actual.graph_scope,
                "send_mail_user": actual.send_mail_user,
                "save_to_sent_items": actual.save_to_sent_items,
                "alertas_destinatarios_default": actual.alertas_destinatarios_default}
