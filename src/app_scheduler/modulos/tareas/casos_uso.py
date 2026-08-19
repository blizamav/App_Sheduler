"""Casos de uso de tareas sin programacion ni ejecucion."""

from __future__ import annotations

from app_scheduler.compartido.auditoria import crear_evento_auditoria
from app_scheduler.compartido.errores import ErrorValidacion
from app_scheduler.compartido.unidad_trabajo import UnidadTrabajoSQL
from app_scheduler.persistencia.modelos import Paginacion
from app_scheduler.persistencia.repositorio_auditoria import RepositorioAuditoria
from app_scheduler.persistencia.repositorio_tareas import RepositorioTareas


ESTADOS_TAREA = frozenset({"ACTIVA", "INACTIVA", "SUSPENDIDA"})


class ServicioTareas:
    def __init__(self, proveedor, *, fabrica_uow=UnidadTrabajoSQL,
                 repositorio=RepositorioTareas, repositorio_auditoria=RepositorioAuditoria):
        self.proveedor = proveedor
        self.fabrica_uow = fabrica_uow
        self.tipo_repositorio = repositorio
        self.tipo_auditoria = repositorio_auditoria

    def listar(self, *, pagina=1, por_pagina=25, busqueda=None, estado=None, id_cliente=None):
        if estado and estado not in ESTADOS_TAREA:
            raise ErrorValidacion("El estado de tarea no es valido.")
        with self.proveedor.conexion_lectura() as conexion:
            return self.tipo_repositorio(conexion).listar_paginado(
                Paginacion(pagina, por_pagina), busqueda=busqueda, estado=estado,
                id_cliente=id_cliente,
            )

    def obtener(self, id_tarea: int):
        with self.proveedor.conexion_lectura() as conexion:
            return self.tipo_repositorio(conexion).obtener_por_id(id_tarea)

    def catalogos(self):
        with self.proveedor.conexion_lectura() as conexion:
            return self.tipo_repositorio(conexion).catalogos_activos()

    def crear(self, datos, actor, contexto) -> int:
        valores = self._validar(datos)
        with self.fabrica_uow(self.proveedor) as uow:
            repo = self.tipo_repositorio(uow.obtener_conexion())
            self._validar_catalogos(repo, valores)
            if repo.existe_clave(valores["nombre_tarea"], valores["id_cliente"], valores["id_categoria"], valores["id_tipo"]):
                raise ErrorValidacion("Ya existe una tarea con el mismo nombre y clasificacion.")
            id_tarea = repo.crear(valores, actor.usuario)
            self.tipo_auditoria(uow.obtener_conexion()).registrar(crear_evento_auditoria(
                usuario=actor.usuario, id_usuario=actor.id_usuario, accion="TAREA_CREADA",
                entidad="tareas", id_entidad=id_tarea, nombre_entidad=valores["nombre_tarea"],
                descripcion="Tarea manual creada.", valores_despues=valores,
                contexto=contexto, modulo="TAREAS",
            ))
            uow.confirmar()
            return id_tarea

    def actualizar(self, id_tarea: int, datos, actor, contexto) -> None:
        valores = self._validar(datos, incluir_estado=False)
        with self.fabrica_uow(self.proveedor) as uow:
            repo = self.tipo_repositorio(uow.obtener_conexion())
            actual = repo.obtener_por_id(id_tarea)
            if actual is None:
                raise ErrorValidacion("Tarea no encontrada.")
            self._validar_catalogos(repo, valores)
            if repo.existe_clave(valores["nombre_tarea"], valores["id_cliente"], valores["id_categoria"], valores["id_tipo"], excluir_id=id_tarea):
                raise ErrorValidacion("Ya existe una tarea con el mismo nombre y clasificacion.")
            antes = self._valores_tarea(actual)
            despues = {**valores, "estado_tarea": actual.estado_tarea}
            if antes == despues:
                raise ErrorValidacion("No hay cambios para guardar.")
            repo.actualizar(id_tarea, valores, actor.usuario)
            self.tipo_auditoria(uow.obtener_conexion()).registrar(crear_evento_auditoria(
                usuario=actor.usuario, id_usuario=actor.id_usuario, accion="TAREA_EDITADA",
                entidad="tareas", id_entidad=id_tarea, nombre_entidad=valores["nombre_tarea"],
                descripcion="Datos base de la tarea actualizados.", valores_antes=antes,
                valores_despues=despues, contexto=contexto, modulo="TAREAS",
            ))
            uow.confirmar()

    def cambiar_estado(self, id_tarea: int, estado: str, actor, contexto) -> None:
        if estado not in ESTADOS_TAREA:
            raise ErrorValidacion("El estado solicitado no es valido.")
        with self.fabrica_uow(self.proveedor) as uow:
            repo = self.tipo_repositorio(uow.obtener_conexion())
            actual = repo.obtener_por_id(id_tarea)
            if actual is None:
                raise ErrorValidacion("Tarea no encontrada.")
            if actual.estado_tarea == estado:
                raise ErrorValidacion("La tarea ya tiene ese estado.")
            repo.cambiar_estado(id_tarea, estado, actor.usuario)
            self.tipo_auditoria(uow.obtener_conexion()).registrar(crear_evento_auditoria(
                usuario=actor.usuario, id_usuario=actor.id_usuario, accion="TAREA_ESTADO_CAMBIADO",
                entidad="tareas", id_entidad=id_tarea, nombre_entidad=actual.nombre_tarea,
                descripcion="Estado operativo de tarea actualizado.",
                valores_antes={"estado_tarea": actual.estado_tarea},
                valores_despues={"estado_tarea": estado}, contexto=contexto, modulo="TAREAS",
            ))
            uow.confirmar()

    @staticmethod
    def _validar(datos, incluir_estado=True):
        nombre = str(datos.get("nombre_tarea") or "").strip()
        descripcion = str(datos.get("descripcion") or "").strip() or None
        observacion = str(datos.get("observacion_tecnica") or "").strip() or None
        try:
            ids = {clave: int(datos.get(clave)) for clave in ("id_cliente", "id_categoria", "id_tipo")}
        except (TypeError, ValueError):
            raise ErrorValidacion("Cliente, categoria y tipo son obligatorios.") from None
        estado = str(datos.get("estado_tarea") or "ACTIVA").upper() if incluir_estado else "ACTIVA"
        errores = []
        if not nombre or len(nombre) > 200: errores.append("El nombre es obligatorio y admite hasta 200 caracteres.")
        if descripcion and len(descripcion) > 1000: errores.append("La descripcion admite hasta 1000 caracteres.")
        if observacion and len(observacion) > 1000: errores.append("La observacion tecnica admite hasta 1000 caracteres.")
        if any(valor < 1 for valor in ids.values()): errores.append("Los catalogos seleccionados no son validos.")
        if estado not in {"ACTIVA", "INACTIVA"}: errores.append("El estado inicial no es valido.")
        if errores: raise ErrorValidacion(" ".join(errores))
        return {"nombre_tarea": nombre, "descripcion": descripcion,
                "observacion_tecnica": observacion, **ids, "estado_tarea": estado}

    @staticmethod
    def _valores_tarea(tarea):
        return {"nombre_tarea": tarea.nombre_tarea, "descripcion": tarea.descripcion,
                "observacion_tecnica": tarea.observacion_tecnica, "id_cliente": tarea.id_cliente,
                "id_categoria": tarea.id_categoria, "id_tipo": tarea.id_tipo,
                "estado_tarea": tarea.estado_tarea}

    @staticmethod
    def _validar_catalogos(repositorio, valores):
        if not repositorio.catalogos_validos(
            valores["id_cliente"], valores["id_categoria"], valores["id_tipo"]
        ):
            raise ErrorValidacion("Cliente, categoria y tipo deben existir y estar activos.")
