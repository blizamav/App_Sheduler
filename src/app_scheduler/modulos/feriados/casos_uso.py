"""Casos de uso transaccionales del calendario local."""

from __future__ import annotations

import json
import re
from datetime import date, datetime

from app_scheduler.compartido.auditoria import crear_evento_auditoria
from app_scheduler.compartido.errores import ErrorPersistencia, ErrorValidacion
from app_scheduler.compartido.unidad_trabajo import UnidadTrabajoSQL
from app_scheduler.modulos.feriados.cliente_nager import ClienteNagerDate, ErrorNagerDate
from app_scheduler.persistencia.modelos import Paginacion
from app_scheduler.persistencia.repositorio_auditoria import RepositorioAuditoria
from app_scheduler.persistencia.repositorio_feriados import RepositorioFeriados
from app_scheduler.persistencia.repositorio_operacion import RepositorioLogsSistema


ORIGENES = frozenset({"MANUAL", "API", "API_NAGER", "IMPORTACION"})
PATRON_PAIS = re.compile(r"^[A-Z]{2}$")


class ServicioFeriados:
    def __init__(self, proveedor, *, fabrica_uow=UnidadTrabajoSQL,
                 repositorio=RepositorioFeriados,
                 repositorio_auditoria=RepositorioAuditoria,
                 repositorio_logs=RepositorioLogsSistema,
                 cliente_nager=None):
        self.proveedor = proveedor
        self.fabrica_uow = fabrica_uow
        self.tipo_repositorio = repositorio
        self.tipo_auditoria = repositorio_auditoria
        self.tipo_logs = repositorio_logs
        self.cliente_nager = cliente_nager or ClienteNagerDate()

    def listar(self, *, pagina=1, anio=None, pais=None, origen=None, activo=None,
               busqueda=None):
        anio = self._anio_opcional(anio)
        pais = self._pais(pais, opcional=True)
        origen = str(origen or "").strip().upper() or None
        if origen not in ORIGENES | {None}:
            raise ErrorValidacion("El origen seleccionado no es valido.")
        with self.proveedor.conexion_lectura() as conexion:
            return self.tipo_repositorio(conexion).listar(
                Paginacion(pagina, 25), anio=anio, pais=pais, origen=origen,
                activo=activo, busqueda=str(busqueda or "").strip() or None,
            )

    def obtener(self, id_feriado: int):
        with self.proveedor.conexion_lectura() as conexion:
            return self.tipo_repositorio(conexion).obtener(id_feriado)

    def crear(self, datos, actor, contexto) -> int:
        valores = self._validar(datos)
        try:
            with self.fabrica_uow(self.proveedor) as uow:
                conexion = uow.obtener_conexion()
                repo = self.tipo_repositorio(conexion)
                existente = repo.obtener_por_fecha_pais(valores["fecha"], valores["pais"])
                if existente and existente.activo:
                    raise ErrorValidacion("Ya existe un feriado activo para esa fecha y pais.")
                identificador = repo.crear_manual(valores, actor.usuario)
                self._auditar(conexion, actor, contexto, "FERIADO_CREADO", identificador,
                              valores["nombre"], None, valores)
                uow.confirmar()
                return identificador
        except ErrorPersistencia as error:
            self._conflicto(error)
            raise

    def actualizar(self, id_feriado: int, datos, actor, contexto) -> None:
        valores = self._validar(datos)
        try:
            with self.fabrica_uow(self.proveedor) as uow:
                conexion = uow.obtener_conexion()
                repo = self.tipo_repositorio(conexion)
                actual = repo.obtener(id_feriado)
                if actual is None:
                    raise ErrorValidacion("Feriado no encontrado.")
                if actual.origen != "MANUAL":
                    raise ErrorValidacion("Los feriados sincronizados no se editan manualmente.")
                duplicado = repo.obtener_por_fecha_pais(valores["fecha"], valores["pais"])
                if duplicado and duplicado.activo and duplicado.id_feriado != id_feriado:
                    raise ErrorValidacion("Ya existe un feriado activo para esa fecha y pais.")
                antes = self._snapshot(actual)
                despues = {**valores, "activo": actual.activo, "origen": actual.origen}
                if antes == despues:
                    raise ErrorValidacion("No hay cambios para guardar.")
                if not repo.actualizar_manual(id_feriado, valores, actor.usuario):
                    raise ErrorValidacion("El feriado ya no esta disponible para editar.")
                self._auditar(conexion, actor, contexto, "FERIADO_EDITADO", id_feriado,
                              valores["nombre"], antes, despues)
                uow.confirmar()
        except ErrorPersistencia as error:
            self._conflicto(error)
            raise

    def cambiar_estado(self, id_feriado: int, activo: bool, actor, contexto) -> None:
        with self.fabrica_uow(self.proveedor) as uow:
            conexion = uow.obtener_conexion()
            repo = self.tipo_repositorio(conexion)
            actual = repo.obtener(id_feriado)
            if actual is None:
                raise ErrorValidacion("Feriado no encontrado.")
            if actual.activo is activo:
                raise ErrorValidacion("El feriado ya tiene el estado solicitado.")
            if activo:
                duplicado = repo.obtener_por_fecha_pais(actual.fecha, actual.pais)
                if duplicado and duplicado.activo and duplicado.id_feriado != id_feriado:
                    raise ErrorValidacion("Existe otro feriado activo para esa fecha y pais.")
            if not repo.cambiar_estado(id_feriado, activo, actor.usuario):
                raise ErrorValidacion("Feriado no encontrado.")
            self._auditar(conexion, actor, contexto, "FERIADO_ACTIVADO" if activo else
                          "FERIADO_DESACTIVADO", id_feriado, actual.nombre,
                          {"activo": actual.activo}, {"activo": activo})
            uow.confirmar()

    def eliminar(self, id_feriado: int, actor, contexto) -> None:
        with self.fabrica_uow(self.proveedor) as uow:
            conexion = uow.obtener_conexion()
            repo = self.tipo_repositorio(conexion)
            actual = repo.obtener(id_feriado)
            if actual is None:
                raise ErrorValidacion("Feriado no encontrado.")
            if actual.origen != "MANUAL":
                raise ErrorValidacion("Solo los feriados manuales pueden eliminarse; desactiva este registro.")
            if not repo.eliminar_manual(id_feriado):
                raise ErrorValidacion("El feriado ya no esta disponible para eliminar.")
            self._auditar(conexion, actor, contexto, "FERIADO_ELIMINADO", id_feriado,
                          actual.nombre, self._snapshot(actual), None)
            uow.confirmar()

    def previsualizar(self, anio, pais, actor, contexto):
        anio, pais = self._parametros_sync(anio, pais)
        self._registrar_log("NAGER_SYNC_INICIO", "Consulta de feriados iniciada.", actor,
                            contexto, {"anio": anio, "pais": pais})
        try:
            items = self._normalizar_respuesta(self.cliente_nager.consultar(anio, pais), pais)
            preview = self._clasificar(items)
            preview["resumen"]["obtenidos"] = len(items)
        except (ErrorNagerDate, ErrorValidacion) as error:
            self._registrar_log("NAGER_SYNC_ERROR", error.mensaje if isinstance(error, ErrorValidacion)
                                else str(error), actor, contexto,
                                {"anio": anio, "pais": pais}, nivel="ERROR")
            raise ErrorValidacion(str(error)) from error
        self._registrar_log("NAGER_SYNC_PREVIEW", "Vista previa de feriados generada.",
                            actor, contexto, preview["resumen"])
        return preview

    def sincronizar(self, anio, pais, actor, contexto):
        anio, pais = self._parametros_sync(anio, pais)
        try:
            items = self._normalizar_respuesta(self.cliente_nager.consultar(anio, pais), pais)
        except (ErrorNagerDate, ErrorValidacion) as error:
            self._registrar_log("NAGER_SYNC_ERROR", str(error), actor, contexto,
                                {"anio": anio, "pais": pais}, nivel="ERROR")
            raise ErrorValidacion(str(error)) from error
        resumen = self._resumen()
        resumen["obtenidos"] = len(items)
        with self.fabrica_uow(self.proveedor) as uow:
            conexion = uow.obtener_conexion()
            repo = self.tipo_repositorio(conexion)
            for item in items:
                item["irrenunciable"] = repo.obtener_regla_irrenunciable(
                    item["pais"], item["fecha"].month, item["fecha"].day
                )
                existente = repo.obtener_por_fecha_pais(item["fecha"], item["pais"])
                accion = self._accion(item, existente)
                if accion == "INSERTAR":
                    repo.crear_api_nager(item, actor.usuario)
                    resumen["insertados"] += 1
                elif accion == "ACTUALIZAR":
                    repo.actualizar_api_nager(existente.id_feriado, item, actor.usuario)
                    resumen["actualizados"] += 1
                elif accion == "MANUAL":
                    resumen["manuales_preservados"] += 1
                elif accion == "INACTIVO":
                    resumen["inactivos_preservados"] += 1
                else:
                    resumen["sin_cambios"] += 1
            self.tipo_logs(conexion).registrar(
                accion="NAGER_SYNC_OK", modulo="FERIADOS",
                descripcion=f"Sincronizacion Nager.Date completada para {pais} {anio}.",
                usuario=actor.usuario, valor_nuevo=json.dumps(resumen, sort_keys=True),
                ip=contexto.ip_origen, user_agent=contexto.user_agent,
            )
            self.tipo_auditoria(conexion).registrar(crear_evento_auditoria(
                usuario=actor.usuario, id_usuario=actor.id_usuario,
                accion="FERIADOS_SINCRONIZADOS", entidad="feriados",
                nombre_entidad=f"{pais} {anio}", descripcion="Calendario local sincronizado con Nager.Date.",
                valores_despues=resumen, contexto=contexto, modulo="FERIADOS",
            ))
            uow.confirmar()
        return resumen

    def _clasificar(self, items):
        resumen = self._resumen()
        filas = []
        with self.proveedor.conexion_lectura() as conexion:
            repo = self.tipo_repositorio(conexion)
            for item in items:
                item["irrenunciable"] = repo.obtener_regla_irrenunciable(
                    item["pais"], item["fecha"].month, item["fecha"].day
                )
                existente = repo.obtener_por_fecha_pais(item["fecha"], item["pais"])
                accion = self._accion(item, existente)
                clave = {"INSERTAR": "insertados", "ACTUALIZAR": "actualizados",
                         "MANUAL": "manuales_preservados", "INACTIVO": "inactivos_preservados",
                         "SIN_CAMBIOS": "sin_cambios"}[accion]
                resumen[clave] += 1
                filas.append({**item, "accion": accion,
                              "nombre_local": existente.nombre if existente else None,
                              "origen_local": existente.origen if existente else None})
        return {"feriados_preview": tuple(filas), "resumen": resumen,
                "anio": items[0]["fecha"].year if items else None,
                "pais": items[0]["pais"] if items else None}

    @staticmethod
    def _accion(item, existente):
        if existente is None:
            return "INSERTAR"
        if not existente.activo:
            return "INACTIVO"
        if existente.origen == "MANUAL":
            return "MANUAL"
        if existente.origen != "API_NAGER":
            return "INACTIVO"
        actual = (existente.nombre, existente.tipo, existente.irrenunciable,
                  existente.observacion)
        nuevo = (item["nombre"], item["tipo"], item["irrenunciable"], item["observacion"])
        return "ACTUALIZAR" if actual != nuevo else "SIN_CAMBIOS"

    @staticmethod
    def _normalizar_respuesta(datos, pais):
        normalizados = []
        fechas = set()
        for item in datos:
            if not isinstance(item, dict):
                raise ErrorValidacion("Nager.Date entrego un elemento inesperado.")
            try:
                fecha = date.fromisoformat(str(item.get("date") or ""))
            except ValueError as error:
                raise ErrorValidacion("Nager.Date entrego una fecha invalida.") from error
            pais_item = str(item.get("countryCode") or pais).strip().upper()
            nombre = str(item.get("localName") or item.get("name") or "").strip()
            if pais_item != pais or not nombre:
                raise ErrorValidacion("Nager.Date entrego datos incompatibles con la consulta.")
            clave = (fecha, pais_item)
            if clave in fechas:
                raise ErrorValidacion("Nager.Date entrego fechas duplicadas para el mismo pais.")
            fechas.add(clave)
            tipos = item.get("types") if isinstance(item.get("types"), list) else []
            tipo = str(tipos[0]).strip()[:50] if tipos else None
            ingles = str(item.get("name") or "").strip()
            observacion = (
                f"Sincronizado desde Nager.Date. Nombre ingles: {ingles}. "
                f"Global: {item.get('global')}. Fixed: {item.get('fixed')}."
            )[:500]
            normalizados.append({"fecha": fecha, "nombre": nombre[:200], "tipo": tipo,
                                 "pais": pais_item, "irrenunciable": False,
                                 "observacion": observacion})
        if not normalizados:
            raise ErrorValidacion("Nager.Date no retorno feriados para los parametros indicados.")
        return normalizados

    def _registrar_log(self, accion, descripcion, actor, contexto, datos, nivel="INFO"):
        with self.fabrica_uow(self.proveedor) as uow:
            self.tipo_logs(uow.obtener_conexion()).registrar(
                accion=accion, modulo="FERIADOS", descripcion=descripcion, nivel=nivel,
                usuario=actor.usuario, valor_nuevo=json.dumps(datos, sort_keys=True),
                ip=contexto.ip_origen, user_agent=contexto.user_agent,
            )
            uow.confirmar()

    def _auditar(self, conexion, actor, contexto, accion, identificador, nombre, antes, despues):
        self.tipo_auditoria(conexion).registrar(crear_evento_auditoria(
            usuario=actor.usuario, id_usuario=actor.id_usuario, accion=accion,
            entidad="feriados", id_entidad=identificador, nombre_entidad=nombre,
            descripcion="Calendario local actualizado.", valores_antes=antes,
            valores_despues=despues, contexto=contexto, modulo="FERIADOS",
        ))

    @staticmethod
    def _validar(datos):
        try:
            fecha = date.fromisoformat(str(datos.get("fecha") or ""))
        except ValueError as error:
            raise ErrorValidacion("La fecha no es valida.") from error
        nombre = str(datos.get("nombre") or "").strip()
        tipo = str(datos.get("tipo") or "").strip() or None
        pais = ServicioFeriados._pais(datos.get("pais"))
        observacion = str(datos.get("observacion") or "").strip() or None
        if not nombre or len(nombre) > 200:
            raise ErrorValidacion("El nombre es obligatorio y admite hasta 200 caracteres.")
        if tipo and len(tipo) > 50:
            raise ErrorValidacion("El tipo admite hasta 50 caracteres.")
        if observacion and len(observacion) > 500:
            raise ErrorValidacion("La observacion admite hasta 500 caracteres.")
        return {"fecha": fecha, "nombre": nombre, "tipo": tipo, "pais": pais,
                "irrenunciable": str(datos.get("irrenunciable") or "") == "1",
                "observacion": observacion}

    @staticmethod
    def _snapshot(item):
        return {"fecha": item.fecha.isoformat(), "nombre": item.nombre, "tipo": item.tipo,
                "pais": item.pais, "irrenunciable": item.irrenunciable,
                "observacion": item.observacion, "activo": item.activo, "origen": item.origen}

    @staticmethod
    def _pais(valor, opcional=False):
        pais = str(valor or "").strip().upper()
        if opcional and not pais:
            return None
        if not PATRON_PAIS.fullmatch(pais):
            raise ErrorValidacion("El pais debe ser un codigo ISO de dos letras.")
        return pais

    @staticmethod
    def _anio_opcional(valor):
        if not str(valor or "").strip():
            return None
        try:
            anio = int(valor)
        except (TypeError, ValueError) as error:
            raise ErrorValidacion("El ano no es valido.") from error
        if not 2000 <= anio <= 2100:
            raise ErrorValidacion("El ano debe estar entre 2000 y 2100.")
        return anio

    @classmethod
    def _parametros_sync(cls, anio, pais):
        anio = cls._anio_opcional(anio)
        if anio is None:
            raise ErrorValidacion("El ano es obligatorio.")
        return anio, cls._pais(pais)

    @staticmethod
    def _resumen():
        return {"obtenidos": 0, "insertados": 0, "actualizados": 0,
                "sin_cambios": 0, "manuales_preservados": 0,
                "inactivos_preservados": 0, "errores": 0}

    @staticmethod
    def _conflicto(error):
        if "SQLSTATE=23000" in str(error.detalle_tecnico or ""):
            raise ErrorValidacion("Ya existe un feriado activo para esa fecha y pais.") from error
