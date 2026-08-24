"""Casos de uso transaccionales de Papelera."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from app_scheduler.compartido.auditoria import crear_evento_auditoria
from app_scheduler.compartido.errores import ErrorValidacion
from app_scheduler.compartido.filesystem import AlmacenArchivosProcesos
from app_scheduler.compartido.unidad_trabajo import UnidadTrabajoSQL
from app_scheduler.persistencia.modelos import Pagina, Paginacion
from app_scheduler.persistencia.repositorio_auditoria import RepositorioAuditoria
from app_scheduler.persistencia.repositorio_papelera import (
    ENTIDADES,
    ETIQUETAS_ENTIDAD,
    RepositorioPapelera,
)


PERMISOS_RETIRO = {
    "usuarios": "USUARIOS_ADMIN",
    "clientes": "CLIENTES_ESTADO",
    "categorias": "CATEGORIAS_ESTADO",
    "tipos": "TIPOS_ESTADO",
    "tareas": "TAREAS_ELIMINAR",
    "scripts": "SCRIPTS_ELIMINAR",
    "scripts_versiones": "SCRIPTS_ELIMINAR",
}


class ServicioPapelera:
    def __init__(self, proveedor, configuracion, *, fabrica_uow=UnidadTrabajoSQL,
                 repositorio=RepositorioPapelera,
                 repositorio_auditoria=RepositorioAuditoria, almacen=None):
        self.proveedor = proveedor
        self.fabrica_uow = fabrica_uow
        self.tipo_repositorio = repositorio
        self.tipo_auditoria = repositorio_auditoria
        self.almacen = almacen or AlmacenArchivosProcesos(
            configuracion.ruta_base_scripts, configuracion.ruta_base_env_scripts
        )

    def listar(self, parametros, actor=None):
        entidad = _texto(parametros.get("entidad"), 40)
        if entidad and entidad not in ENTIDADES:
            raise ErrorValidacion("El tipo de entidad no es valido.")
        filtros = {
            "entidad": entidad,
            "busqueda": _texto(parametros.get("buscar"), 200),
            "usuario": _texto(parametros.get("usuario"), 100),
            "fecha_desde": _fecha(parametros.get("fecha_desde"), "Fecha desde"),
            "fecha_hasta": _fecha(parametros.get("fecha_hasta"), "Fecha hasta"),
        }
        if filtros["fecha_desde"] and filtros["fecha_hasta"]:
            if filtros["fecha_desde"] > filtros["fecha_hasta"]:
                raise ErrorValidacion("La fecha desde no puede ser posterior a la fecha hasta.")
        pagina = _entero(parametros.get("pagina"), 1, 1, 100000)
        with self.proveedor.conexion_lectura() as conexion:
            repo = self.tipo_repositorio(conexion)
            resultado = repo.listar(Paginacion(pagina, 25), **filtros)
            enriquecidos = tuple(self._presentar(repo, item, actor) for item in resultado.elementos)
        return {
            "resultado": Pagina(enriquecidos, resultado.total, resultado.pagina, resultado.por_pagina),
            "filtros": {clave: _presentar_filtro(valor) for clave, valor in filtros.items()},
            "entidades": tuple(ETIQUETAS_ENTIDAD.items()),
        }

    def enviar(self, entidad, id_registro, motivo, actor, contexto):
        self._validar_entidad(entidad)
        motivo = _texto(motivo, 500) or "Retiro operacional solicitado desde APP Scheduler."
        with self.fabrica_uow(self.proveedor) as uow:
            repo = self.tipo_repositorio(uow.obtener_conexion())
            item = repo.obtener(entidad, id_registro, retirado=False, bloquear=True)
            if item is None:
                raise ErrorValidacion("El registro no existe o ya fue enviado a Papelera.")
            dependencias = repo.dependencias(entidad, id_registro)
            motivo_bloqueo = self._bloqueo_retiro(entidad, id_registro, actor, dependencias)
            if motivo_bloqueo:
                self._auditar(uow, actor, contexto, "ENVIO_PAPELERA_BLOQUEADO", item,
                              resultado="BLOQUEADO", descripcion=motivo_bloqueo)
                uow.confirmar()
                raise ErrorValidacion(motivo_bloqueo)
            if not repo.retirar(entidad, id_registro, actor.usuario, motivo):
                raise ErrorValidacion("El registro cambio mientras se procesaba la solicitud.")
            self._auditar(uow, actor, contexto, "ENVIADO_A_PAPELERA", item,
                          valores_despues={"eliminado_operativo": True, "activo": False})
            uow.confirmar()

    def restaurar(self, entidad, id_registro, actor, contexto):
        self._validar_entidad(entidad)
        with self.fabrica_uow(self.proveedor) as uow:
            repo = self.tipo_repositorio(uow.obtener_conexion())
            item = repo.obtener(entidad, id_registro, bloquear=True)
            if item is None:
                raise ErrorValidacion("El registro no se encuentra en Papelera.")
            dependencias = repo.dependencias(entidad, id_registro)
            motivo = self._bloqueo_restauracion(entidad, dependencias)
            if not motivo:
                motivo = self._validar_filesystem_restauracion(repo, entidad, id_registro)
            if motivo:
                self._auditar(uow, actor, contexto, "RESTAURACION_BLOQUEADA", item,
                              resultado="BLOQUEADO", descripcion=motivo)
                uow.confirmar()
                raise ErrorValidacion(motivo)
            if not repo.restaurar(entidad, id_registro, actor.usuario):
                raise ErrorValidacion("El registro cambio mientras se procesaba la restauracion.")
            self._auditar(uow, actor, contexto, "RESTAURADO", item,
                          valores_despues={"eliminado_operativo": False, "activo": False})
            uow.confirmar()

    def eliminar_permanente(self, entidad, id_registro, actor, contexto):
        self._validar_entidad(entidad)
        retiros = []
        confirmado = False
        try:
            with self.fabrica_uow(self.proveedor) as uow:
                repo = self.tipo_repositorio(uow.obtener_conexion())
                item = repo.obtener(entidad, id_registro, bloquear=True)
                if item is None:
                    raise ErrorValidacion("El registro no se encuentra en Papelera.")
                dependencias = repo.dependencias(entidad, id_registro)
                motivo = self._bloqueo_eliminacion(entidad, id_registro, actor, dependencias)
                if motivo:
                    self._auditar(uow, actor, contexto, "ELIMINACION_PERMANENTE_BLOQUEADA",
                                  item, resultado="BLOQUEADO", descripcion=motivo)
                    uow.confirmar()
                    raise ErrorValidacion(motivo)
                retiros = self._preparar_retiros(repo.rutas_operativas(entidad, id_registro))
                for retiro in retiros:
                    retiro.aplicar()
                if not repo.eliminar_permanente(entidad, id_registro):
                    raise ErrorValidacion("El registro cambio mientras se procesaba la eliminacion.")
                self._auditar(uow, actor, contexto, "ELIMINADO_PERMANENTEMENTE", item,
                              valores_despues={"registro_operativo_eliminado": True,
                                               "archivos_retirados": len(retiros)})
                uow.confirmar()
                confirmado = True
            for retiro in retiros:
                retiro.confirmar()
            self._podar_directorios(retiros)
        finally:
            if not confirmado:
                for retiro in reversed(retiros):
                    retiro.revertir()

    def _presentar(self, repo, item, actor):
        dependencias = repo.dependencias(item.entidad, item.id_registro)
        restauracion = self._bloqueo_restauracion(item.entidad, dependencias)
        if not restauracion:
            restauracion = self._validar_filesystem_restauracion(
                repo, item.entidad, item.id_registro
            )
        eliminacion = self._bloqueo_eliminacion(
            item.entidad, item.id_registro, actor, dependencias
        )
        return {
            "item": item,
            "etiqueta": ETIQUETAS_ENTIDAD[item.entidad],
            "dependencias": dependencias,
            "restaurable": not restauracion,
            "motivo_restauracion": restauracion,
            "eliminable": not eliminacion,
            "motivo_eliminacion": eliminacion,
            "resumen_dependencias": _resumen_dependencias(item.entidad, dependencias),
        }

    @staticmethod
    def _bloqueo_retiro(entidad, id_registro, actor, deps):
        if entidad == "usuarios" and actor and actor.id_usuario == id_registro:
            return "No puedes enviar a Papelera el usuario con el que iniciaste sesion."
        if entidad == "usuarios" and deps.get("es_admin") and not deps.get("administradores_restantes"):
            return "No puedes retirar el ultimo administrador operativo."
        if entidad in {"tareas", "scripts", "scripts_versiones"} and deps.get("ejecuciones_en_curso"):
            return "No puedes retirar un recurso con una ejecucion en curso."
        return ""

    @staticmethod
    def _bloqueo_restauracion(entidad, deps):
        if deps.get("conflicto_clave"):
            return "No se puede restaurar porque existe otro registro operativo con la misma clave."
        if entidad == "tareas" and deps.get("maestros_eliminados"):
            return "Restaura primero el cliente, la categoria y el tipo asociados."
        if entidad == "scripts" and not deps.get("tarea_operativa"):
            return "Restaura primero la tarea propietaria del script."
        if entidad == "scripts_versiones" and not deps.get("padre_operativo"):
            return "Restaura primero el script propietario de la version."
        return ""

    @staticmethod
    def _bloqueo_eliminacion(entidad, id_registro, actor, deps):
        if entidad == "usuarios":
            if actor and actor.id_usuario == id_registro:
                return "No puedes eliminar permanentemente tu propio usuario."
            if deps.get("es_admin") and not deps.get("administradores_restantes"):
                return "No puedes eliminar permanentemente el ultimo administrador."
        if entidad in {"clientes", "categorias", "tipos"} and deps.get("tareas"):
            return f"No puede eliminarse porque existen {deps['tareas']} tareas asociadas."
        if entidad == "tareas" and deps.get("ejecuciones_en_curso"):
            return "No puede eliminarse porque existe una ejecucion en curso."
        if entidad == "tareas" and deps.get("ejecuciones_historicas"):
            return "No puede eliminarse porque existen ejecuciones historicas asociadas."
        if entidad == "scripts":
            if deps.get("ejecuciones_en_curso"):
                return "No puede eliminarse porque existe una ejecucion en curso."
            if deps.get("ejecuciones_historicas"):
                return "No puede eliminarse porque existen ejecuciones historicas asociadas."
            if deps.get("tarea_operativa"):
                return "No puede eliminarse mientras su tarea siga operativa."
            if deps.get("versiones_operativas"):
                return "No puede eliminarse mientras tenga versiones operativas."
        if entidad == "scripts_versiones":
            if deps.get("ejecuciones_en_curso"):
                return "No puede eliminarse porque existe una ejecucion en curso."
            if deps.get("ejecuciones_historicas"):
                return "No puede eliminarse porque existen ejecuciones historicas asociadas."
            if deps.get("version_activa"):
                return "No puede eliminarse mientras sea la version activa."
        return ""

    def _validar_filesystem_restauracion(self, repo, entidad, id_registro):
        if entidad != "scripts_versiones":
            return ""
        rutas = repo.rutas_operativas(entidad, id_registro)
        if not rutas or not any(ruta_script for ruta_script, _ in rutas):
            return "No se puede restaurar porque falta la metadata del archivo Python."
        for ruta_script, ruta_env in rutas:
            for ruta in (ruta_script, ruta_env):
                if not ruta:
                    continue
                try:
                    archivo = self.almacen.validar_ruta_persistida(Path(ruta))
                except ErrorValidacion:
                    return "La version conserva una ruta fuera del almacenamiento autorizado."
                if not archivo.is_file():
                    return "No se puede restaurar porque falta un archivo operativo requerido."
        return ""

    def _preparar_retiros(self, rutas):
        retiros = []
        vistos = set()
        for ruta_script, ruta_env in rutas:
            for ruta in (ruta_script, ruta_env):
                if not ruta:
                    continue
                archivo = self.almacen.validar_ruta_persistida(Path(ruta))
                clave = str(archivo).casefold()
                if clave not in vistos:
                    retiros.append(self.almacen.preparar_retiro(archivo))
                    vistos.add(clave)
        return retiros

    def _podar_directorios(self, retiros):
        roots = {self.almacen.raiz_scripts, self.almacen.raiz_env}
        for retiro in retiros:
            carpeta = retiro.origen.parent
            while carpeta not in roots and any(root in carpeta.parents for root in roots):
                try:
                    carpeta.rmdir()
                except OSError:
                    break
                carpeta = carpeta.parent

    def _auditar(self, uow, actor, contexto, accion, item, *, resultado="OK",
                  descripcion=None, valores_despues=None):
        self.tipo_auditoria(uow.obtener_conexion()).registrar(crear_evento_auditoria(
            usuario=actor.usuario,
            id_usuario=actor.id_usuario,
            accion=accion,
            entidad=item.entidad,
            id_entidad=item.id_registro,
            nombre_entidad=item.nombre,
            descripcion=descripcion or f"Accion de Papelera aplicada sobre {item.nombre}.",
            valores_antes={"eliminado_operativo": item.fecha_retiro is not None,
                            "activo": item.activo_anterior},
            valores_despues=valores_despues,
            resultado=resultado,
            modulo="PAPELERA",
            contexto=contexto,
        ))

    @staticmethod
    def _validar_entidad(entidad):
        if entidad not in ENTIDADES:
            raise ErrorValidacion("Entidad no soportada por la Papelera.")


def _texto(valor, limite):
    texto = str(valor or "").strip()
    if len(texto) > limite:
        raise ErrorValidacion("El valor ingresado supera el largo permitido.")
    return texto or None


def _fecha(valor, etiqueta):
    texto = str(valor or "").strip()
    if not texto:
        return None
    try:
        return date.fromisoformat(texto)
    except ValueError as error:
        raise ErrorValidacion(f"{etiqueta} no es valida.") from error


def _entero(valor, defecto, minimo, maximo):
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        return defecto
    return min(max(numero, minimo), maximo)


def _presentar_filtro(valor):
    return valor.isoformat() if isinstance(valor, date) else (valor or "")


def _resumen_dependencias(entidad, deps):
    if entidad in {"clientes", "categorias", "tipos"}:
        return f"{deps.get('tareas', 0)} tareas asociadas"
    if entidad == "usuarios":
        return f"{deps.get('historial', 0)} referencias historicas"
    if entidad == "tareas":
        return f"{deps.get('scripts', 0)} scripts y {deps.get('programaciones', 0)} programaciones"
    if entidad == "scripts":
        return f"{deps.get('versiones_operativas', 0)} versiones operativas"
    if entidad == "scripts_versiones":
        return "Version activa" if deps.get("version_activa") else "Sin referencia activa"
    return "Sin dependencias operativas"
