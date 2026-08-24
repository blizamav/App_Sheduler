"""Casos de uso de configuracion con allowlist y auditoria."""

from __future__ import annotations

from app_scheduler.compartido.auditoria import crear_evento_auditoria
from app_scheduler.compartido.errores import ErrorValidacion
from app_scheduler.compartido.unidad_trabajo import UnidadTrabajoSQL
from app_scheduler.persistencia.repositorio_auditoria import RepositorioAuditoria
from app_scheduler.persistencia.repositorio_operacion import RepositorioOperacion


class ServicioConfiguracionOperativa:
    CAMPOS_EDITABLES = frozenset({
        "scheduler_activo", "intervalo_revision_segundos",
        "max_ejecuciones_concurrentes", "permitir_ejecucion_automatica",
        "modo_mantenimiento",
    })

    def __init__(self, proveedor, *, fabrica_uow=UnidadTrabajoSQL,
                 repositorio=RepositorioOperacion, repositorio_auditoria=RepositorioAuditoria):
        self.proveedor = proveedor
        self.fabrica_uow = fabrica_uow
        self.tipo_repositorio = repositorio
        self.tipo_auditoria = repositorio_auditoria

    def obtener(self):
        with self.proveedor.conexion_lectura() as conexion:
            repo = self.tipo_repositorio(conexion)
            scheduler = repo.obtener_configuracion_scheduler()
            configuraciones = tuple(self._presentar_config(item)
                                    for item in repo.listar_configuracion_sistema())
        return {"scheduler": scheduler, "configuraciones": configuraciones}

    def guardar_scheduler(self, formulario, actor, contexto):
        datos = self._validar_scheduler(formulario)
        with self.fabrica_uow(self.proveedor) as uow:
            conexion = uow.obtener_conexion()
            repo = self.tipo_repositorio(conexion)
            actual = repo.obtener_configuracion_scheduler()
            if actual is None:
                raise ErrorValidacion("No existe una configuracion activa del scheduler.")
            antes = {campo: getattr(actual, campo) for campo in self.CAMPOS_EDITABLES}
            if antes == datos:
                raise ErrorValidacion("No hay cambios para guardar.")
            if not repo.actualizar_scheduler(actual.id_configuracion, datos, actor.usuario):
                raise ErrorValidacion("La configuracion activa cambio durante la operacion.")
            self.tipo_auditoria(conexion).registrar(crear_evento_auditoria(
                usuario=actor.usuario, id_usuario=actor.id_usuario,
                accion="CONFIGURACION_SCHEDULER_EDITADA", entidad="configuracion_scheduler",
                id_entidad=actual.id_configuracion, nombre_entidad="Scheduler",
                descripcion="Configuracion operativa del scheduler actualizada.",
                valores_antes=antes, valores_despues=datos, contexto=contexto,
                modulo="CONFIGURACION",
            ))
            uow.confirmar()

    @classmethod
    def _validar_scheduler(cls, formulario):
        recibidos = {clave: formulario.get(clave) for clave in cls.CAMPOS_EDITABLES}
        try:
            intervalo = int(str(recibidos["intervalo_revision_segundos"] or ""))
            concurrencia = int(str(recibidos["max_ejecuciones_concurrentes"] or ""))
        except ValueError as error:
            raise ErrorValidacion("Intervalo y concurrencia deben ser numeros enteros.") from error
        if not 10 <= intervalo <= 3600:
            raise ErrorValidacion("El intervalo debe estar entre 10 y 3600 segundos.")
        if not 1 <= concurrencia <= 20:
            raise ErrorValidacion("La concurrencia debe estar entre 1 y 20.")
        return {
            "scheduler_activo": recibidos["scheduler_activo"] == "1",
            "intervalo_revision_segundos": intervalo,
            "max_ejecuciones_concurrentes": concurrencia,
            "permitir_ejecucion_automatica": recibidos["permitir_ejecucion_automatica"] == "1",
            "modo_mantenimiento": recibidos["modo_mantenimiento"] == "1",
        }

    @staticmethod
    def _presentar_config(item):
        return {
            "clave": item.clave,
            "proposito": item.descripcion or "Parametro tecnico registrado por el sistema.",
            "tipo": item.tipo_dato,
            "editable": False,
            "sensible": item.es_sensible,
            "valor": "[PROTEGIDO]" if item.es_sensible else item.valor,
            "validacion": "Gestionada por su consumidor; sin edicion arbitraria desde UI.",
            "consumidor": "Runtime / proceso tecnico",
            "requiere_restart": "No determinado por este registro",
            "activo": item.activo,
        }
