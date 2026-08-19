"""Casos de uso y validacion de programaciones."""

from __future__ import annotations

import json
import re
from datetime import date, datetime, time
from types import SimpleNamespace

from app_scheduler.compartido.auditoria import crear_evento_auditoria
from app_scheduler.compartido.errores import ErrorValidacion
from app_scheduler.compartido.unidad_trabajo import UnidadTrabajoSQL
from app_scheduler.modulos.programaciones.calculo import DIAS, calcular_proxima_ejecucion, zona_valida
from app_scheduler.persistencia.modelos import Paginacion
from app_scheduler.persistencia.repositorio_auditoria import RepositorioAuditoria
from app_scheduler.persistencia.repositorio_programaciones import RepositorioProgramaciones
from app_scheduler.persistencia.repositorio_tareas import RepositorioTareas


TIPOS = frozenset({"DIARIA", "SEMANAL", "MENSUAL", "FECHA_ESPECIFICA", "FECHAS_ESPECIFICAS"})
MODOS = frozenset({"UNA_VEZ", "INTERVALO"})
ORDEN_DIAS = tuple(DIAS)


class ServicioProgramaciones:
    def __init__(self, proveedor, configuracion, *, fabrica_uow=UnidadTrabajoSQL,
                 repositorio=RepositorioProgramaciones, repositorio_tareas=RepositorioTareas,
                 repositorio_auditoria=RepositorioAuditoria, reloj=datetime.now):
        self.proveedor = proveedor; self.configuracion = configuracion; self.fabrica_uow = fabrica_uow
        self.tipo_repositorio = repositorio; self.tipo_tareas = repositorio_tareas
        self.tipo_auditoria = repositorio_auditoria; self.reloj = reloj

    def listar(self, *, pagina=1, por_pagina=25, id_tarea=None, tipo=None, activo=None):
        if tipo and tipo not in TIPOS: raise ErrorValidacion("El tipo de programacion no es valido.")
        with self.proveedor.conexion_lectura() as conexion:
            return self.tipo_repositorio(conexion).listar_paginado(
                Paginacion(pagina, por_pagina), id_tarea=id_tarea, tipo=tipo, activo=activo)

    def obtener(self, id_programacion):
        with self.proveedor.conexion_lectura() as conexion:
            return self.tipo_repositorio(conexion).obtener(id_programacion)

    def crear(self, id_tarea, datos, actor, contexto):
        valores = self._validar(datos)
        with self.fabrica_uow(self.proveedor) as uow:
            conexion = uow.obtener_conexion(); repo = self.tipo_repositorio(conexion)
            tarea = self.tipo_tareas(conexion).obtener_por_id(id_tarea)
            if tarea is None or not repo.bloquear_tarea(id_tarea): raise ErrorValidacion("Tarea no encontrada.")
            if valores["activo"] and tarea.estado_tarea != "ACTIVA":
                raise ErrorValidacion("Solo una tarea activa puede tener programacion activa.")
            if valores["activo"]:
                self._validar_ocurrencia_futura(self._modelo(0, tarea, valores))
            if valores["activo"] and repo.existe_otra_activa(id_tarea):
                raise ErrorValidacion("La tarea ya tiene una programacion activa.")
            id_programacion = repo.crear(id_tarea, valores, actor.usuario)
            modelo = self._modelo(id_programacion, tarea, valores)
            self._actualizar_resumen(repo, id_tarea, actor.usuario, adicional=modelo)
            self._auditar(conexion, actor, contexto, "PROGRAMACION_CREADA", modelo, None, valores)
            uow.confirmar(); return id_programacion

    def actualizar(self, id_tarea, id_programacion, datos, actor, contexto):
        valores = self._validar(datos)
        with self.fabrica_uow(self.proveedor) as uow:
            conexion = uow.obtener_conexion(); repo = self.tipo_repositorio(conexion)
            actual = repo.obtener(id_programacion); tarea = self.tipo_tareas(conexion).obtener_por_id(id_tarea)
            if actual is None or tarea is None or actual.id_tarea != id_tarea:
                raise ErrorValidacion("Programacion no encontrada para la tarea.")
            repo.bloquear_tarea(id_tarea)
            if valores["activo"] and tarea.estado_tarea != "ACTIVA":
                raise ErrorValidacion("Solo una tarea activa puede tener programacion activa.")
            if valores["activo"]:
                self._validar_ocurrencia_futura(self._modelo(id_programacion, tarea, valores))
            if valores["activo"] and repo.existe_otra_activa(id_tarea, id_programacion):
                raise ErrorValidacion("La tarea ya tiene otra programacion activa.")
            antes = self._valores(actual)
            if antes == valores: raise ErrorValidacion("No hay cambios para guardar.")
            repo.actualizar(id_programacion, valores, actor.usuario)
            modelo = self._modelo(id_programacion, tarea, valores)
            self._actualizar_resumen(repo, id_tarea, actor.usuario, reemplazo=modelo)
            self._auditar(conexion, actor, contexto, "PROGRAMACION_EDITADA", modelo, antes, valores)
            uow.confirmar()

    def cambiar_estado(self, id_tarea, id_programacion, activo, actor, contexto):
        activo = bool(activo)
        with self.fabrica_uow(self.proveedor) as uow:
            conexion = uow.obtener_conexion(); repo = self.tipo_repositorio(conexion)
            actual = repo.obtener(id_programacion)
            if actual is None or actual.id_tarea != id_tarea: raise ErrorValidacion("Programacion no encontrada.")
            if actual.activo == activo: raise ErrorValidacion("La programacion ya tiene ese estado.")
            repo.bloquear_tarea(id_tarea)
            if activo and actual.estado_tarea != "ACTIVA":
                raise ErrorValidacion("Solo una tarea activa puede tener programacion activa.")
            if activo:
                self._validar_ocurrencia_futura(actual)
            if activo and repo.existe_otra_activa(id_tarea, id_programacion):
                raise ErrorValidacion("La tarea ya tiene otra programacion activa.")
            repo.cambiar_estado(id_programacion, activo, actor.usuario)
            modelo = SimpleNamespace(**{**actual.__dict__, "activo": activo}) if hasattr(actual, "__dict__") else self._modelo_desde_actual(actual, activo)
            self._actualizar_resumen(repo, id_tarea, actor.usuario, reemplazo=modelo)
            accion = "PROGRAMACION_ACTIVADA" if activo else "PROGRAMACION_DESACTIVADA"
            self._auditar(conexion, actor, contexto, accion, modelo,
                          {"activo": actual.activo}, {"activo": activo})
            uow.confirmar()

    def _actualizar_resumen(self, repo, id_tarea, actor, adicional=None, reemplazo=None):
        activas = list(repo.listar_activas_tarea(id_tarea))
        if reemplazo:
            activas = [reemplazo if item.id_programacion == reemplazo.id_programacion else item for item in activas]
            if reemplazo.activo and all(item.id_programacion != reemplazo.id_programacion for item in activas):
                activas.append(reemplazo)
            if not reemplazo.activo: activas = [item for item in activas if item.id_programacion != reemplazo.id_programacion]
        if adicional and adicional.activo and all(
            item.id_programacion != adicional.id_programacion for item in activas
        ):
            activas.append(adicional)
        proximas = [calcular_proxima_ejecucion(item, self.reloj()) for item in activas]
        proximas = [item for item in proximas if item is not None]
        repo.actualizar_resumen_tarea(id_tarea, bool(activas), min(proximas) if proximas else None, actor)

    def _auditar(self, conexion, actor, contexto, accion, programa, antes, despues):
        self.tipo_auditoria(conexion).registrar(crear_evento_auditoria(
            usuario=actor.usuario, id_usuario=actor.id_usuario, accion=accion,
            entidad="programaciones", id_entidad=programa.id_programacion,
            nombre_entidad=programa.nombre_tarea,
            descripcion="Configuracion temporal de tarea actualizada.", valores_antes=antes,
            valores_despues=despues, contexto=contexto, modulo="TAREAS"))

    def _validar_ocurrencia_futura(self, programa):
        if calcular_proxima_ejecucion(programa, self.reloj()) is None:
            raise ErrorValidacion("La programacion activa no tiene ocurrencias futuras.")

    @staticmethod
    def _modelo(id_programacion, tarea, datos):
        return SimpleNamespace(id_programacion=id_programacion, id_tarea=tarea.id_tarea,
            nombre_tarea=tarea.nombre_tarea, estado_tarea=tarea.estado_tarea, **datos)

    @staticmethod
    def _modelo_desde_actual(actual, activo):
        datos = {campo: getattr(actual, campo) for campo in (
            "id_programacion", "id_tarea", "nombre_tarea", "estado_tarea", "tipo_programacion",
            "modo_ejecucion_dia", "hora_inicio", "hora_termino", "hora_ejecucion",
            "intervalo_minutos", "dias_semana", "dia_mes", "fecha_especifica",
            "fechas_especificas", "ejecutar_en_feriados", "zona_horaria",
            "fecha_inicio_vigencia", "fecha_fin_vigencia")}
        return SimpleNamespace(**datos, activo=activo)

    @staticmethod
    def _valores(item):
        return {campo: getattr(item, campo) for campo in (
            "tipo_programacion", "modo_ejecucion_dia", "hora_inicio", "hora_termino",
            "hora_ejecucion", "intervalo_minutos", "dias_semana", "dia_mes",
            "fecha_especifica", "fechas_especificas", "ejecutar_en_feriados",
            "zona_horaria", "fecha_inicio_vigencia", "fecha_fin_vigencia", "activo")}

    def _validar(self, datos):
        tipo = str(datos.get("tipo_programacion") or "").strip().upper()
        modo = str(datos.get("modo_ejecucion_dia") or "").strip().upper()
        if tipo not in TIPOS: raise ErrorValidacion("Selecciona un tipo de programacion automatica valido.")
        if modo not in MODOS: raise ErrorValidacion("Selecciona un modo de ejecucion valido.")
        hora_ejecucion = _hora(datos.get("hora_ejecucion")) if modo == "UNA_VEZ" else None
        hora_inicio = _hora(datos.get("hora_inicio")) if modo == "INTERVALO" else None
        hora_termino = _hora(datos.get("hora_termino")) if modo == "INTERVALO" else None
        intervalo = _entero(datos.get("intervalo_minutos")) if modo == "INTERVALO" else None
        if modo == "UNA_VEZ" and hora_ejecucion is None: raise ErrorValidacion("La hora de ejecucion es obligatoria.")
        if modo == "INTERVALO" and (hora_inicio is None or hora_termino is None or not intervalo):
            raise ErrorValidacion("Completa inicio, termino e intervalo.")
        if modo == "INTERVALO" and (hora_inicio > hora_termino or intervalo > 1440):
            raise ErrorValidacion("La ventana o intervalo no es valido.")
        dias = _dias(datos.get("dias_semana")) if tipo == "SEMANAL" else None
        dia_mes = _entero(datos.get("dia_mes")) if tipo == "MENSUAL" else None
        fecha = _fecha(datos.get("fecha_especifica")) if tipo == "FECHA_ESPECIFICA" else None
        fechas = _lista_fechas(datos.get("fechas_especificas")) if tipo == "FECHAS_ESPECIFICAS" else None
        if tipo == "SEMANAL" and not dias: raise ErrorValidacion("Selecciona al menos un dia de semana.")
        if tipo == "MENSUAL" and not (dia_mes and 1 <= dia_mes <= 31): raise ErrorValidacion("El dia mensual debe estar entre 1 y 31.")
        if tipo == "FECHA_ESPECIFICA" and fecha is None: raise ErrorValidacion("La fecha especifica es obligatoria.")
        if tipo == "FECHAS_ESPECIFICAS" and not fechas: raise ErrorValidacion("Ingresa al menos una fecha especifica.")
        inicio = _fecha(datos.get("fecha_inicio_vigencia")); fin = _fecha(datos.get("fecha_fin_vigencia"))
        if inicio and fin and inicio > fin: raise ErrorValidacion("La vigencia inicial no puede superar la final.")
        zona = str(datos.get("zona_horaria") or self.configuracion.zona_horaria).strip()
        zona_valida(zona)
        return {"tipo_programacion": tipo, "modo_ejecucion_dia": modo,
            "hora_inicio": hora_inicio, "hora_termino": hora_termino,
            "hora_ejecucion": hora_ejecucion, "intervalo_minutos": intervalo,
            "dias_semana": dias, "dia_mes": dia_mes, "fecha_especifica": fecha,
            "fechas_especificas": json.dumps(fechas) if fechas else None,
            "ejecutar_en_feriados": bool(datos.get("ejecutar_en_feriados")),
            "zona_horaria": zona, "fecha_inicio_vigencia": inicio,
            "fecha_fin_vigencia": fin, "activo": bool(datos.get("activo", True))}


def _hora(valor):
    if isinstance(valor, time): return valor.replace(second=0, microsecond=0)
    try: return time.fromisoformat(str(valor).strip()[:5]) if valor else None
    except ValueError: raise ErrorValidacion("El formato de hora no es valido.") from None


def _fecha(valor):
    if isinstance(valor, date): return valor
    try: return date.fromisoformat(str(valor).strip()) if valor else None
    except ValueError: raise ErrorValidacion("El formato de fecha no es valido.") from None


def _entero(valor):
    try: return int(valor) if valor not in (None, "") else None
    except (TypeError, ValueError): raise ErrorValidacion("El valor numerico no es valido.") from None


def _dias(valor):
    items = valor if isinstance(valor, (list, tuple)) else str(valor or "").split(",")
    seleccion = {str(item).strip().upper() for item in items if str(item).strip()}
    if not seleccion.issubset(DIAS): raise ErrorValidacion("Los dias seleccionados no son validos.")
    return ",".join(item for item in ORDEN_DIAS if item in seleccion) or None


def _lista_fechas(valor):
    items = re.split(r"[,;\s]+", str(valor or "").strip())
    fechas = sorted({_fecha(item).isoformat() for item in items if item})
    return fechas
