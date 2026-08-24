"""Casos de uso read-only del navegador global de auditoria."""

from __future__ import annotations

import json
from datetime import date

from app_scheduler.compartido.errores import ErrorValidacion
from app_scheduler.persistencia.modelos import Paginacion
from app_scheduler.persistencia.repositorio_auditoria import RepositorioAuditoria


class ServicioConsultaAuditoria:
    def __init__(self, proveedor, *, repositorio=RepositorioAuditoria):
        self.proveedor = proveedor
        self.tipo_repositorio = repositorio

    def listar(self, parametros):
        filtros = {
            "fecha_desde": _fecha(parametros.get("fecha_desde"), "Fecha desde"),
            "fecha_hasta": _fecha(parametros.get("fecha_hasta"), "Fecha hasta"),
            "usuario": _texto(parametros.get("usuario"), 100),
            "accion": _texto(parametros.get("accion"), 100),
            "entidad": _texto(parametros.get("entidad"), 100),
            "id_entidad": _texto(parametros.get("id_entidad"), 100),
            "busqueda": _texto(parametros.get("buscar"), 200),
        }
        if filtros["fecha_desde"] and filtros["fecha_hasta"]:
            if filtros["fecha_desde"] > filtros["fecha_hasta"]:
                raise ErrorValidacion("La fecha desde no puede ser posterior a la fecha hasta.")
        pagina = _entero(parametros.get("pagina"), 1, 1, 100000)
        with self.proveedor.conexion_lectura() as conexion:
            repo = self.tipo_repositorio(conexion)
            resultado = repo.listar(Paginacion(pagina, 25), **filtros)
            acciones, entidades = repo.opciones_filtros()
        return {
            "resultado": resultado,
            "filtros": {clave: _presentar(valor) for clave, valor in filtros.items()},
            "acciones": acciones,
            "entidades": entidades,
        }

    def obtener(self, id_auditoria: int):
        if id_auditoria < 1:
            return None
        with self.proveedor.conexion_lectura() as conexion:
            registro = self.tipo_repositorio(conexion).obtener(id_auditoria)
        if registro is None:
            return None
        return {
            "registro": registro,
            "valores_antes": _formatear_estructura(registro.valores_antes),
            "valores_despues": _formatear_estructura(registro.valores_despues),
        }


def _texto(valor, limite):
    texto = str(valor or "").strip()
    if len(texto) > limite:
        raise ErrorValidacion("Uno de los filtros supera el largo permitido.")
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


def _presentar(valor):
    return valor.isoformat() if isinstance(valor, date) else (valor or "")


def _formatear_estructura(valor):
    if not valor:
        return "-"
    try:
        return json.dumps(json.loads(valor), ensure_ascii=False, indent=2, sort_keys=True)
    except (TypeError, ValueError):
        return str(valor)
