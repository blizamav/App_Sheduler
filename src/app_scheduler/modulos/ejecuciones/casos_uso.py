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


ESTADOS = frozenset({
    "PENDIENTE", "EN_EJECUCION", "EXITOSA", "ERROR", "CANCELADA",
    "DETENIDA_MANUALMENTE",
})
ORIGENES = frozenset({"MANUAL", "AUTOMATICA"})


class ServicioEjecuciones:
    def __init__(self, proveedor, configuracion, *, fabrica_uow=UnidadTrabajoSQL,
                 repositorio=RepositorioEjecuciones,
                 repositorio_auditoria=RepositorioAuditoria,
                 control_runtime=factory_reset_bloquea):
        self.proveedor = proveedor
        self.configuracion = configuracion
        self.fabrica_uow = fabrica_uow
        self.tipo_repositorio = repositorio
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

    def leer_log(self, id_ejecucion: int, max_bytes=120 * 1024):
        detalle = self.obtener(id_ejecucion)
        if detalle is None: raise ErrorValidacion("Ejecucion no encontrada.")
        if not detalle.ruta_fisica_log:
            contenido = "Log aun no disponible."
        else:
            raiz = Path(self.configuracion.ruta_base_logs_tareas).expanduser().resolve()
            ruta = Path(detalle.ruta_fisica_log).expanduser().resolve(strict=False)
            try: ruta.relative_to(raiz)
            except ValueError as error: raise ErrorValidacion("La ruta del log no es valida.") from error
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
            "mensaje_error": detalle.mensaje_error or "",
            "log": contenido,
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
