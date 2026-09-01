"""Casos de uso web del motor unico de ejecuciones."""

from __future__ import annotations

from pathlib import Path

from app_scheduler.compartido.auditoria import crear_evento_auditoria
from app_scheduler.compartido.control_runtime import factory_reset_bloquea
from app_scheduler.compartido.errores import ErrorValidacion
from app_scheduler.compartido.filesystem import AlmacenArchivosProcesos
from app_scheduler.compartido.unidad_trabajo import UnidadTrabajoSQL
from app_scheduler.persistencia.modelos import Paginacion
from app_scheduler.persistencia.repositorio_auditoria import RepositorioAuditoria
from app_scheduler.persistencia.repositorio_ejecuciones import RepositorioEjecuciones
from app_scheduler.persistencia.repositorio_notificaciones import RepositorioNotificaciones


ESTADOS = frozenset({
    "PENDIENTE", "EN_EJECUCION", "EXITOSA", "ERROR", "CANCELADA",
    "DETENIDA_MANUALMENTE",
})
ORIGENES = frozenset({"MANUAL", "AUTOMATICA"})


class ServicioEjecuciones:
    def __init__(self, proveedor, configuracion, *, fabrica_uow=UnidadTrabajoSQL,
                 repositorio=RepositorioEjecuciones,
                 repositorio_notificaciones=RepositorioNotificaciones,
                 repositorio_auditoria=RepositorioAuditoria,
                 control_runtime=factory_reset_bloquea):
        self.proveedor = proveedor
        self.configuracion = configuracion
        self.fabrica_uow = fabrica_uow
        self.tipo_repositorio = repositorio
        self.tipo_notificaciones = repositorio_notificaciones
        self.tipo_auditoria = repositorio_auditoria
        self.control_runtime = control_runtime
        self.almacen = AlmacenArchivosProcesos(
            configuracion.ruta_base_scripts, configuracion.ruta_base_env_scripts,
        )

    def solicitar_manual(self, id_tarea: int, actor, contexto) -> int:
        bloqueado, _estado = self.control_runtime(self.configuracion.ruta_control_runtime)
        if bloqueado:
            raise ErrorValidacion("APP Scheduler se encuentra en mantenimiento critico.")
        with self.fabrica_uow(self.proveedor) as uow:
            repo = self.tipo_repositorio(uow.obtener_conexion())
            if not repo.adquirir_lock_despacho():
                raise ErrorValidacion("No fue posible reservar capacidad de ejecucion.")
            config = repo.obtener_configuracion()
            if config is None:
                raise ErrorValidacion("No existe configuracion operativa del scheduler.")
            if bool(config[1]):
                raise ErrorValidacion("El modo mantenimiento no permite nuevas ejecuciones.")
            if repo.contar_ocupadas() >= int(config[0]):
                raise ErrorValidacion("Se alcanzo el maximo de ejecuciones concurrentes.")
            fila = repo.obtener_contexto_manual(id_tarea)
            self._validar_contexto_manual(fila)
            self._validar_archivos(fila)
            id_ejecucion = repo.reservar_manual(fila, actor.usuario)
            self.tipo_auditoria(uow.obtener_conexion()).registrar(crear_evento_auditoria(
                usuario=actor.usuario, id_usuario=actor.id_usuario,
                accion="EJECUCION_MANUAL_SOLICITADA", entidad="ejecuciones",
                id_entidad=id_ejecucion, nombre_entidad=str(fila[1]),
                descripcion="Ejecucion manual reservada para el worker.",
                valores_despues={"id_tarea": fila[0], "id_script": fila[8],
                                  "id_version": fila[12], "origen": "MANUAL"},
                contexto=contexto, modulo="EJECUCIONES",
            ))
            uow.confirmar()
            return id_ejecucion

    def solicitar_detencion(self, id_ejecucion: int, actor, contexto, motivo=None) -> None:
        texto = str(motivo or "Detencion manual solicitada desde la interfaz.").strip()
        if len(texto) > 500:
            raise ErrorValidacion("El motivo de detencion admite hasta 500 caracteres.")
        with self.fabrica_uow(self.proveedor) as uow:
            repo = self.tipo_repositorio(uow.obtener_conexion())
            actual = repo.obtener_detalle(id_ejecucion)
            if actual is None:
                raise ErrorValidacion("Ejecucion no encontrada.")
            if actual.estado_ejecucion != "EN_EJECUCION":
                raise ErrorValidacion("La ejecucion ya no esta en curso.")
            if not repo.solicitar_detencion(id_ejecucion, actor.usuario, texto):
                raise ErrorValidacion("La detencion ya fue solicitada o la ejecucion finalizo.")
            self.tipo_auditoria(uow.obtener_conexion()).registrar(crear_evento_auditoria(
                usuario=actor.usuario, id_usuario=actor.id_usuario,
                accion="CANCELACION_SOLICITADA", entidad="ejecuciones",
                id_entidad=id_ejecucion, nombre_entidad=actual.nombre_tarea,
                descripcion="Detencion solicitada al worker propietario.",
                valores_despues={"motivo": texto}, contexto=contexto,
                modulo="EJECUCIONES",
            ))
            uow.confirmar()

    def listar(self, *, pagina=1, por_pagina=25, estado=None, origen=None):
        estado = str(estado or "").upper() or None
        origen = str(origen or "").upper() or None
        if estado and estado not in ESTADOS: raise ErrorValidacion("Estado de ejecucion invalido.")
        if origen and origen not in ORIGENES: raise ErrorValidacion("Origen de ejecucion invalido.")
        with self.proveedor.conexion_lectura() as conexion:
            return self.tipo_repositorio(conexion).listar(
                Paginacion(pagina, por_pagina), estado=estado, origen=origen,
            )

    def obtener(self, id_ejecucion: int):
        with self.proveedor.conexion_lectura() as conexion:
            return self.tipo_repositorio(conexion).obtener_detalle(id_ejecucion)

    def obtener_panel(self, id_ejecucion: int):
        with self.proveedor.conexion_lectura() as conexion:
            detalle = self.tipo_repositorio(conexion).obtener_detalle(id_ejecucion)
            repo_notificaciones = self.tipo_notificaciones(conexion)
            envios = (() if detalle is None else
                      repo_notificaciones.listar_envios_ejecucion(id_ejecucion))
            config = (None if detalle is None or detalle.id_tarea is None else
                      repo_notificaciones.obtener_configuracion_tarea(detalle.id_tarea))
        presentadas = tuple(self._presentar_notificacion(item) for item in envios)
        return detalle, self._completar_notificaciones(detalle, config, presentadas)

    def leer_log(self, id_ejecucion: int, max_bytes=120 * 1024):
        detalle, notificaciones = self.obtener_panel(id_ejecucion)
        if detalle is None: raise ErrorValidacion("Ejecucion no encontrada.")
        if not detalle.ruta_fisica_log:
            contenido = "Log aun no disponible."
        else:
            raiz = Path(self.configuracion.ruta_base_logs_tareas).expanduser().resolve()
            ruta = Path(detalle.ruta_fisica_log).expanduser().resolve(strict=False)
            try:
                ruta.relative_to(raiz)
            except ValueError:
                contenido = "Log no disponible en este entorno."
            else:
                if ruta.is_symlink() or not ruta.is_file():
                    contenido = "Log aun no disponible."
                else:
                    with ruta.open("rb") as archivo:
                        archivo.seek(0, 2); tamano = archivo.tell()
                        archivo.seek(max(0, tamano - max_bytes))
                        contenido = archivo.read().decode("utf-8", errors="replace")
        return {
            "id_ejecucion": detalle.id_ejecucion,
            "estado": detalle.estado_ejecucion,
            "es_final": detalle.estado_ejecucion in {
                "EXITOSA", "ERROR", "CANCELADA", "DETENIDA_MANUALMENTE",
            },
            "codigo_salida": detalle.codigo_salida,
            "duracion_segundos": detalle.duracion_segundos,
            "nombre_worker": detalle.nombre_worker or "",
            "pid_proceso": detalle.pid_proceso,
            "estado_evidencia": detalle.estado_evidencia or "NO REQUERIDA",
            "mensaje_error": detalle.mensaje_error or "",
            "notificaciones": notificaciones,
            "log": contenido,
        }

    @staticmethod
    def _presentar_notificacion(item):
        if (item["tipo_envio"] == "EVIDENCIA_CLIENTE"
                and item["estado_envio"] == "OMITIDO"
                and item.get("estado_evidencia") not in {None, "VALIDADA"}):
            return {
                "estado": "NO GENERADA",
                "clase": "advertencia",
                "explicacion": "La ejecucion no genero una Evidencia 1.0 valida. No se envio correo al cliente.",
                "tipo": "Evidencia cliente",
                "evidencia_incluida": False,
                "cantidad_adjuntos": 0,
                "codigo_tipo": item["tipo_envio"],
            }
        estados = {
            "ENVIADO": ("ENVIADA", "activo", "El correo fue aceptado por Microsoft Graph."),
            "OMITIDO": ("OMITIDA", "advertencia", "El correo no fue enviado. Revisa la disponibilidad de Graph y los destinatarios configurados."),
            "FALLIDO": ("ERROR", "error", "El correo no pudo enviarse. La ejecucion conserva su resultado."),
            "PENDIENTE": ("PENDIENTE", "info", "El envio aun no ha finalizado."),
            "NO_REQUERIDO": ("NO REQUERIDO", "inactivo", "Esta notificacion no requirio envio."),
        }
        tipos = {
            "NOTIFICACION_EXITOSA": "Notificacion de exito",
            "ALERTA_INTERNA": "Alerta de error",
            "EVIDENCIA_CLIENTE": "Evidencia cliente",
        }
        codigo, clase, explicacion = estados.get(
            item["estado_envio"], ("ERROR", "error", "El estado del correo no esta disponible."),
        )
        return {
            "estado": codigo,
            "clase": clase,
            "explicacion": explicacion,
            "tipo": tipos.get(item["tipo_envio"], "Notificacion"),
            "evidencia_incluida": bool(item["evidencia_incluida"]),
            "cantidad_adjuntos": int(item["cantidad_adjuntos"]),
            "codigo_tipo": item["tipo_envio"],
        }

    @classmethod
    def _completar_notificaciones(cls, detalle, config, presentadas):
        if detalle is None:
            return ()
        por_tipo = {item["codigo_tipo"]: item for item in presentadas}
        if detalle.estado_ejecucion == "EXITOSA":
            if "NOTIFICACION_EXITOSA" not in por_tipo:
                por_tipo["NOTIFICACION_EXITOSA"] = cls._estado_sintetico(
                    "NOTIFICACION_EXITOSA",
                    "PENDIENTE" if config and config.notificar_exito_activa else "NO_CONFIGURADA",
                )
            if "EVIDENCIA_CLIENTE" not in por_tipo:
                if not config or not config.enviar_evidencia:
                    estado_evidencia = "NO_CONFIGURADA"
                elif detalle.estado_evidencia == "VALIDADA":
                    estado_evidencia = "PENDIENTE"
                else:
                    estado_evidencia = "NO_GENERADA"
                por_tipo["EVIDENCIA_CLIENTE"] = cls._estado_sintetico(
                    "EVIDENCIA_CLIENTE", estado_evidencia,
                )
        orden = ("NOTIFICACION_EXITOSA", "EVIDENCIA_CLIENTE", "ALERTA_INTERNA")
        return tuple(
            {clave: valor for clave, valor in por_tipo[tipo].items() if clave != "codigo_tipo"}
            for tipo in orden if tipo in por_tipo
        )

    @staticmethod
    def _estado_sintetico(tipo, estado):
        nombres = {
            "NOTIFICACION_EXITOSA": "Notificacion de exito",
            "EVIDENCIA_CLIENTE": "Evidencia cliente",
        }
        presentacion = {
            "NO_CONFIGURADA": (
                "inactivo", "Este tipo de comunicacion no estaba configurado para la tarea."
            ),
            "NO_GENERADA": (
                "advertencia", "La ejecucion no genero una Evidencia 1.0 valida. No se envio correo al cliente."
            ),
            "PENDIENTE": ("info", "El envio aun no ha finalizado."),
        }
        clase, explicacion = presentacion[estado]
        return {
            "estado": estado,
            "clase": clase,
            "explicacion": explicacion,
            "tipo": nombres[tipo],
            "evidencia_incluida": False,
            "cantidad_adjuntos": 0,
            "codigo_tipo": tipo,
        }

    @staticmethod
    def _validar_contexto_manual(fila):
        if fila is None: raise ErrorValidacion("Tarea no encontrada.")
        if fila[5] != "ACTIVA" or not bool(fila[6]): raise ErrorValidacion("La tarea no esta activa.")
        if not bool(fila[7]): raise ErrorValidacion("La tarea no permite ejecucion manual.")
        if not fila[8] or not bool(fila[10]): raise ErrorValidacion("La tarea no tiene un script activo.")
        if not fila[11] or not fila[12]: raise ErrorValidacion("La tarea no tiene una version activa.")
        if fila[17] != "ACTIVA" or not bool(fila[18]): raise ErrorValidacion("La version activa no es ejecutable.")
        if bool(fila[22]): raise ErrorValidacion("La tarea ya tiene una ejecucion pendiente o en curso.")

    def _validar_archivos(self, fila):
        ruta = self.almacen.validar_ruta_persistida(Path(fila[15]))
        if ruta.suffix.lower() != ".py" or not ruta.is_file():
            raise ErrorValidacion("El archivo fisico de la version activa no esta disponible.")
        if bool(fila[19]):
            if not fila[20]: raise ErrorValidacion("La version requiere .env y no esta configurado.")
            ruta_env = self.almacen.validar_ruta_persistida(Path(fila[20]))
            if not ruta_env.is_file(): raise ErrorValidacion("El archivo .env requerido no esta disponible.")
