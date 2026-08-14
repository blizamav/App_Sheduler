"""Casos de uso transaccionales de los catalogos base."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Callable, Mapping

from app_scheduler.compartido.auditoria import ContextoAuditoria, crear_evento_auditoria
from app_scheduler.compartido.autorizacion import IdentidadSesion
from app_scheduler.compartido.errores import ErrorPersistencia, ErrorValidacion
from app_scheduler.compartido.unidad_trabajo import UnidadTrabajoSQL
from app_scheduler.persistencia.modelos import Pagina, Paginacion
from app_scheduler.persistencia.repositorio_auditoria import RepositorioAuditoria
from app_scheduler.persistencia.repositorio_catalogos import (
    RepositorioCategorias,
    RepositorioClientes,
    RepositorioTipos,
)


@dataclass(frozen=True, slots=True)
class DefinicionCatalogo:
    clave: str
    singular: str
    plural: str
    modulo: str
    atributo_id: str
    repositorio: type
    permiso_ver: str
    permiso_crear: str
    permiso_editar: str
    permiso_estado: str


CATALOGOS = {
    "clientes": DefinicionCatalogo(
        "clientes", "cliente", "Clientes", "CLIENTES", "id_cliente",
        RepositorioClientes, "CLIENTES_VER", "CLIENTES_CREAR",
        "CLIENTES_EDITAR", "CLIENTES_ESTADO",
    ),
    "categorias": DefinicionCatalogo(
        "categorias", "categoria", "Categorias", "CATEGORIAS", "id_categoria",
        RepositorioCategorias, "CATEGORIAS_VER", "CATEGORIAS_CREAR",
        "CATEGORIAS_EDITAR", "CATEGORIAS_ESTADO",
    ),
    "tipos": DefinicionCatalogo(
        "tipos", "tipo", "Tipos", "TIPOS", "id_tipo",
        RepositorioTipos, "TIPOS_VER", "TIPOS_CREAR", "TIPOS_EDITAR",
        "TIPOS_ESTADO",
    ),
}


def normalizar_nombre(nombre: str) -> str:
    texto = unicodedata.normalize("NFKD", nombre.strip())
    sin_diacriticos = "".join(
        caracter for caracter in texto if not unicodedata.combining(caracter)
    )
    return " ".join(sin_diacriticos.upper().split())


class ServicioCatalogos:
    def __init__(
        self,
        proveedor,
        *,
        fabrica_uow: Callable = UnidadTrabajoSQL,
        repositorio_auditoria=RepositorioAuditoria,
        catalogos: Mapping[str, DefinicionCatalogo] = CATALOGOS,
    ):
        self.proveedor = proveedor
        self.fabrica_uow = fabrica_uow
        self.tipo_repositorio_auditoria = repositorio_auditoria
        self.catalogos = dict(catalogos)

    def definicion(self, clave: str) -> DefinicionCatalogo:
        try:
            return self.catalogos[clave]
        except KeyError as error:
            raise ErrorValidacion("El catalogo solicitado no es valido.") from error

    def listar(
        self,
        clave: str,
        *,
        pagina: int = 1,
        por_pagina: int = 25,
        activo: bool | None = None,
        busqueda: str | None = None,
    ) -> Pagina:
        definicion = self.definicion(clave)
        with self.proveedor.conexion_lectura() as conexion:
            return definicion.repositorio(conexion).listar_paginado(
                Paginacion(pagina, por_pagina),
                activo=activo,
                busqueda=busqueda,
            )

    def obtener(self, clave: str, identificador: int):
        definicion = self.definicion(clave)
        with self.proveedor.conexion_lectura() as conexion:
            return definicion.repositorio(conexion).obtener_por_id(identificador)

    def crear(
        self,
        clave: str,
        datos: Mapping[str, object],
        actor: IdentidadSesion,
        contexto: ContextoAuditoria,
    ) -> int:
        definicion = self.definicion(clave)
        valores = self._validar_datos(datos)
        try:
            with self.fabrica_uow(self.proveedor) as uow:
                conexion = uow.obtener_conexion()
                repositorio = definicion.repositorio(conexion)
                auditoria = self.tipo_repositorio_auditoria(conexion)
                self._validar_unicidad(repositorio, definicion, valores["nombre_normalizado"])
                identificador = repositorio.crear(
                    valores["nombre"], valores["nombre_normalizado"],
                    valores["descripcion"], actor.usuario,
                )
                auditoria.registrar(
                    crear_evento_auditoria(
                        usuario=actor.usuario,
                        id_usuario=actor.id_usuario,
                        accion=f"{definicion.singular.upper()}_CREADO",
                        entidad=definicion.clave,
                        id_entidad=identificador,
                        nombre_entidad=valores["nombre"],
                        descripcion=f"{definicion.singular.capitalize()} creado.",
                        valores_despues=valores,
                        contexto=contexto,
                        modulo=definicion.modulo,
                    )
                )
                uow.confirmar()
                return identificador
        except ErrorPersistencia as error:
            self._traducir_conflicto(error)
            raise

    def actualizar(
        self,
        clave: str,
        identificador: int,
        datos: Mapping[str, object],
        actor: IdentidadSesion,
        contexto: ContextoAuditoria,
    ) -> None:
        definicion = self.definicion(clave)
        valores = self._validar_datos(datos)
        try:
            with self.fabrica_uow(self.proveedor) as uow:
                conexion = uow.obtener_conexion()
                repositorio = definicion.repositorio(conexion)
                auditoria = self.tipo_repositorio_auditoria(conexion)
                actual = repositorio.obtener_por_id(identificador)
                if actual is None:
                    raise ErrorValidacion(f"{definicion.singular.capitalize()} no encontrado.")
                self._validar_unicidad(
                    repositorio,
                    definicion,
                    valores["nombre_normalizado"],
                    excluir_id=identificador,
                )
                if actual.nombre == valores["nombre"] and actual.descripcion == valores["descripcion"]:
                    raise ErrorValidacion("No hay cambios para guardar.")
                if not repositorio.actualizar(
                    identificador,
                    valores["nombre"],
                    valores["nombre_normalizado"],
                    valores["descripcion"],
                    actor.usuario,
                ):
                    raise ErrorValidacion(f"{definicion.singular.capitalize()} no encontrado.")
                auditoria.registrar(
                    crear_evento_auditoria(
                        usuario=actor.usuario,
                        id_usuario=actor.id_usuario,
                        accion=f"{definicion.singular.upper()}_EDITADO",
                        entidad=definicion.clave,
                        id_entidad=identificador,
                        nombre_entidad=valores["nombre"],
                        descripcion=f"{definicion.singular.capitalize()} editado.",
                        valores_antes={"nombre": actual.nombre, "descripcion": actual.descripcion},
                        valores_despues=valores,
                        contexto=contexto,
                        modulo=definicion.modulo,
                    )
                )
                uow.confirmar()
        except ErrorPersistencia as error:
            self._traducir_conflicto(error)
            raise

    def cambiar_estado(
        self,
        clave: str,
        identificador: int,
        activo: bool,
        actor: IdentidadSesion,
        contexto: ContextoAuditoria,
    ) -> None:
        definicion = self.definicion(clave)
        with self.fabrica_uow(self.proveedor) as uow:
            conexion = uow.obtener_conexion()
            repositorio = definicion.repositorio(conexion)
            auditoria = self.tipo_repositorio_auditoria(conexion)
            actual = repositorio.obtener_por_id(identificador)
            if actual is None:
                raise ErrorValidacion(f"{definicion.singular.capitalize()} no encontrado.")
            if actual.activo is activo:
                estado = "activo" if activo else "inactivo"
                raise ErrorValidacion(f"El registro ya se encuentra {estado}.")
            if not repositorio.cambiar_estado(identificador, activo, actor.usuario):
                raise ErrorValidacion(f"{definicion.singular.capitalize()} no encontrado.")
            accion = "ACTIVADO" if activo else "DESACTIVADO"
            auditoria.registrar(
                crear_evento_auditoria(
                    usuario=actor.usuario,
                    id_usuario=actor.id_usuario,
                    accion=f"{definicion.singular.upper()}_{accion}",
                    entidad=definicion.clave,
                    id_entidad=identificador,
                    nombre_entidad=actual.nombre,
                    descripcion=f"Estado de {definicion.singular} actualizado.",
                    valores_antes={"activo": actual.activo},
                    valores_despues={"activo": activo},
                    contexto=contexto,
                    modulo=definicion.modulo,
                )
            )
            uow.confirmar()

    @staticmethod
    def _validar_datos(datos: Mapping[str, object]) -> dict[str, str | None]:
        nombre = str(datos.get("nombre") or "").strip()
        descripcion = str(datos.get("descripcion") or "").strip() or None
        errores = []
        if not nombre:
            errores.append("El nombre es obligatorio.")
        elif len(nombre) > 150:
            errores.append("El nombre admite hasta 150 caracteres.")
        if descripcion and len(descripcion) > 300:
            errores.append("La descripcion admite hasta 300 caracteres.")
        nombre_normalizado = normalizar_nombre(nombre) if nombre else ""
        if len(nombre_normalizado) > 150:
            errores.append("El nombre normalizado admite hasta 150 caracteres.")
        if errores:
            raise ErrorValidacion(" ".join(errores))
        return {
            "nombre": nombre,
            "nombre_normalizado": nombre_normalizado,
            "descripcion": descripcion,
        }

    @staticmethod
    def _validar_unicidad(
        repositorio,
        definicion: DefinicionCatalogo,
        nombre_normalizado: str,
        *,
        excluir_id: int | None = None,
    ) -> None:
        existente = repositorio.buscar_por_clave(nombre_normalizado)
        if existente is None:
            return
        id_existente = getattr(existente, definicion.atributo_id)
        if excluir_id is None or id_existente != excluir_id:
            raise ErrorValidacion(
                "Ya existe un registro con ese nombre, incluso si esta retirado de la operacion."
            )

    @staticmethod
    def _traducir_conflicto(error: ErrorPersistencia) -> None:
        if "SQLSTATE=23000" in str(error.detalle_tecnico or ""):
            raise ErrorValidacion("Ya existe un registro con ese nombre.") from error
