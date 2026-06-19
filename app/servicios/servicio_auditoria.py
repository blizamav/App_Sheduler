import json
from math import ceil

from flask import has_request_context, request, session

from app.repositorios.repositorio_auditoria import (
    contar_auditoria,
    listar_auditoria,
    obtener_auditoria,
    registrar_evento_auditoria,
)
from app.servicios.servicio_logs_sistema import registrar_log_sistema


PER_PAGE_OPCIONES = (10, 25, 50, 100)
CLAVES_SENSIBLES = (
    "password",
    "pass",
    "contrasena",
    "contrase\u00f1a",
    "hash",
    "token",
    "secret",
    ".env",
    "pwd",
    "key",
    "api_key",
    "api",
    "credential",
    "credentials",
    "connection",
    "conn",
    "cadena_conexion",
    "client_secret",
    "refresh_token",
    "access_token",
    "smtp_password",
    "db_password",
)

MODULOS_NORMALIZADOS = {
    "USUARIOS": "Usuarios",
    "CLIENTES": "Mantenedores",
    "CATEGORIAS": "Mantenedores",
    "TIPOS": "Mantenedores",
    "TAREAS": "Tareas",
    "SCRIPTS": "Scripts",
    "EJECUCIONES": "Ejecuciones",
    "SCHEDULER": "Programador",
    "FERIADOS": "Feriados",
    "PAPELERA": "Papelera",
    "SEGURIDAD": "Seguridad",
    "AUDITORIA": "Auditoria",
}

ENTIDADES_SINGULAR = {
    "usuarios": "USUARIO",
    "clientes": "CLIENTE",
    "categorias": "CATEGORIA",
    "tipos": "TIPO",
    "tareas": "TAREA",
    "scripts": "SCRIPT",
    "scripts_versiones": "VERSION_SCRIPT",
    "ejecuciones": "EJECUCION",
    "scheduler_config": "PROGRAMADOR",
    "feriados": "FERIADO",
    "papelera": "REGISTRO",
}

ACCIONES_ESPECIFICAS = {
    ("usuarios", "CREAR"): "CREAR_USUARIO",
    ("usuarios", "EDITAR"): "EDITAR_USUARIO",
    ("usuarios", "ACTIVAR"): "ACTIVAR_USUARIO",
    ("usuarios", "DESACTIVAR"): "DESACTIVAR_USUARIO",
    ("usuarios", "BORRAR_OPERATIVO"): "BORRAR_OPERATIVO_USUARIO",
    ("clientes", "CREAR"): "CREAR_CLIENTE",
    ("clientes", "EDITAR"): "EDITAR_CLIENTE",
    ("clientes", "ACTIVAR"): "ACTIVAR_CLIENTE",
    ("clientes", "DESACTIVAR"): "DESACTIVAR_CLIENTE",
    ("clientes", "BORRAR_OPERATIVO"): "BORRAR_OPERATIVO_CLIENTE",
    ("categorias", "CREAR"): "CREAR_CATEGORIA",
    ("categorias", "EDITAR"): "EDITAR_CATEGORIA",
    ("categorias", "ACTIVAR"): "ACTIVAR_CATEGORIA",
    ("categorias", "DESACTIVAR"): "DESACTIVAR_CATEGORIA",
    ("categorias", "BORRAR_OPERATIVO"): "BORRAR_OPERATIVO_CATEGORIA",
    ("tipos", "CREAR"): "CREAR_TIPO",
    ("tipos", "EDITAR"): "EDITAR_TIPO",
    ("tipos", "ACTIVAR"): "ACTIVAR_TIPO",
    ("tipos", "DESACTIVAR"): "DESACTIVAR_TIPO",
    ("tipos", "BORRAR_OPERATIVO"): "BORRAR_OPERATIVO_TIPO",
    ("tareas", "CREAR"): "CREAR_TAREA",
    ("tareas", "EDITAR"): "EDITAR_TAREA",
    ("tareas", "ACTIVAR"): "ACTIVAR_TAREA",
    ("tareas", "DESACTIVAR"): "DESACTIVAR_TAREA",
    ("tareas", "BORRAR_OPERATIVO"): "BORRAR_OPERATIVO_TAREA",
    ("scripts", "SUBIR_VERSION"): "SUBIR_VERSION_SCRIPT",
    ("scripts", "DESACTIVAR"): "DESACTIVAR_SCRIPT",
    ("scripts", "BORRAR_OPERATIVO"): "BORRAR_OPERATIVO_SCRIPT",
    ("scripts_versiones", "ACTIVAR_VERSION"): "CAMBIAR_VERSION_ACTIVA",
    ("scripts_versiones", "DESACTIVAR_VERSION"): "DESACTIVAR_VERSION_SCRIPT",
    ("scripts_versiones", "REEMPLAZAR_VERSION"): "REEMPLAZAR_VERSION_SCRIPT",
    ("scripts_versiones", "BORRAR_OPERATIVO"): "BORRAR_OPERATIVO_VERSION_SCRIPT",
    ("scripts_versiones", "CONFIGURAR_ENV_VERSION"): "EDITAR_ENV_SCRIPT",
    ("scripts_versiones", "ELIMINAR_ENV_VERSION"): "ELIMINAR_ENV_SCRIPT",
    ("ejecuciones", "EJECUTAR_MANUAL"): "EJECUTAR_TAREA_MANUAL",
    ("ejecuciones", "DETENER_EJECUCION"): "DETENER_EJECUCION",
    ("ejecuciones", "VERIFICAR_HUERFANA"): "VERIFICAR_EJECUCION_HUERFANA",
    ("scheduler_config", "CONFIGURAR"): "EDITAR_CONFIG_PROGRAMADOR",
    ("feriados", "CREAR"): "CREAR_FERIADO",
    ("feriados", "EDITAR"): "EDITAR_FERIADO",
    ("feriados", "ACTIVAR"): "ACTIVAR_FERIADO",
    ("feriados", "DESACTIVAR"): "DESACTIVAR_FERIADO",
    ("feriados", "SINCRONIZAR"): "SINCRONIZAR_FERIADOS",
    ("feriados", "PREVISUALIZAR_SINCRONIZACION"): "PREVISUALIZAR_SINCRONIZACION_FERIADOS",
}


def registrar_auditoria(
    accion,
    entidad,
    id_entidad=None,
    nombre_entidad=None,
    descripcion=None,
    valores_antes=None,
    valores_despues=None,
    resultado="OK",
    modulo=None,
    usuario=None,
):
    entidad_normalizada = _normalizar_entidad(entidad)
    accion_normalizada = _normalizar_accion(accion, entidad_normalizada, resultado)
    modulo_normalizado = _normalizar_modulo(modulo or entidad_normalizada)
    evento = {
        "usuario": usuario or _usuario_actual(),
        "id_usuario": _id_usuario_actual(),
        "accion": accion_normalizada[:100],
        "entidad": entidad_normalizada[:100],
        "id_entidad": str(id_entidad)[:100] if id_entidad is not None else None,
        "nombre_entidad": str(nombre_entidad)[:255] if nombre_entidad is not None else None,
        "descripcion": descripcion,
        "valores_antes": _serializar_seguro(valores_antes),
        "valores_despues": _serializar_seguro(valores_despues),
        "resultado": str(resultado or "OK").upper()[:50],
        "modulo": modulo_normalizado[:100],
        "ip_origen": None,
        "user_agent": None,
        "ruta": None,
        "metodo_http": None,
    }
    if has_request_context():
        evento["ip_origen"] = (request.headers.get("X-Forwarded-For") or request.remote_addr or "")[:100] or None
        evento["user_agent"] = (request.headers.get("User-Agent") or "")[:1000] or None
        evento["ruta"] = request.path[:255]
        evento["metodo_http"] = request.method[:20]

    try:
        registrar_evento_auditoria(evento)
    except Exception as error:
        try:
            registrar_log_sistema(
                "AUDITORIA_REGISTRO_ERROR",
                "AUDITORIA",
                "No fue posible registrar auditoria formal.",
                usuario=evento["usuario"],
                nivel="WARNING",
                valor_nuevo=error.__class__.__name__,
            )
        except Exception:
            pass


def listar_auditoria_admin(parametros):
    filtros = {
        "fecha_desde": (parametros.get("fecha_desde") or "").strip(),
        "fecha_hasta": (parametros.get("fecha_hasta") or "").strip(),
        "usuario": (parametros.get("usuario") or "").strip(),
        "accion": (parametros.get("accion") or "").strip(),
        "entidad": (parametros.get("entidad") or "").strip(),
        "resultado": (parametros.get("resultado") or "").strip(),
        "modulo": (parametros.get("modulo") or "").strip(),
        "texto": (parametros.get("texto") or "").strip(),
    }
    filtros = {clave: valor for clave, valor in filtros.items() if valor}
    page = _entero(parametros.get("page"), 1, minimo=1)
    per_page = _entero(parametros.get("per_page"), 25, minimo=10, maximo=100)
    if per_page not in PER_PAGE_OPCIONES:
        per_page = 25

    total = contar_auditoria(filtros)
    total_paginas = max(ceil(total / per_page), 1)
    if page > total_paginas:
        page = total_paginas
    registros = listar_auditoria(filtros, page, per_page)
    return {
        "registros": registros,
        "filtros": filtros,
        "page": page,
        "per_page": per_page,
        "per_page_opciones": PER_PAGE_OPCIONES,
        "total": total,
        "total_paginas": total_paginas,
        "resultados": ("OK", "ERROR", "BLOQUEADO"),
    }


def obtener_detalle_auditoria(id_auditoria):
    registro = obtener_auditoria(id_auditoria)
    if not registro:
        return None
    registro["valores_antes_formateado"] = _formatear_valor_detalle(registro.get("valores_antes"))
    registro["valores_despues_formateado"] = _formatear_valor_detalle(registro.get("valores_despues"))
    return registro


def _usuario_actual():
    if has_request_context():
        return session.get("usuario") or "sistema"
    return "sistema"


def _id_usuario_actual():
    if has_request_context():
        return session.get("id_usuario")
    return None


def _serializar_seguro(valor):
    if valor is None:
        return None
    valor = _limpiar_sensible(valor)
    if isinstance(valor, str):
        return valor[:4000]
    try:
        return json.dumps(valor, ensure_ascii=False, default=str)[:4000]
    except TypeError:
        return str(valor)[:4000]


def _formatear_valor_detalle(valor):
    if valor in (None, ""):
        return "-"
    if not isinstance(valor, str):
        return json.dumps(_limpiar_sensible(valor), ensure_ascii=False, default=str, indent=2)
    texto = valor.strip()
    if not texto:
        return "-"
    try:
        return json.dumps(json.loads(texto), ensure_ascii=False, indent=2)
    except (TypeError, ValueError):
        return texto


def _limpiar_sensible(valor):
    if isinstance(valor, dict):
        limpio = {}
        for clave, item in valor.items():
            clave_texto = str(clave)
            if any(sensible in clave_texto.lower() for sensible in CLAVES_SENSIBLES):
                limpio[clave_texto] = "***"
            else:
                limpio[clave_texto] = _limpiar_sensible(item)
        return limpio
    if isinstance(valor, (list, tuple)):
        return [_limpiar_sensible(item) for item in valor]
    return valor


def _normalizar_entidad(entidad):
    texto = str(entidad or "GENERAL").strip()
    if texto == "configuracion_scheduler":
        return "scheduler_config"
    return texto


def _normalizar_modulo(modulo):
    texto = str(modulo or "GENERAL").strip()
    return MODULOS_NORMALIZADOS.get(texto.upper(), texto)


def _normalizar_accion(accion, entidad, resultado):
    accion_base = str(accion or "ACCION").strip().upper().replace(" ", "_")
    resultado_base = str(resultado or "OK").strip().upper()

    if resultado_base == "BLOQUEADO" and accion_base == "ELIMINAR_PERMANENTE":
        return "BLOQUEO_ELIMINACION_PERMANENTE"
    if resultado_base == "BLOQUEADO" and accion_base == "RESTAURAR":
        return "BLOQUEO_RESTAURAR_REGISTRO"
    if accion_base in ("RESTAURAR", "ELIMINAR_PERMANENTE"):
        singular = ENTIDADES_SINGULAR.get(entidad, "REGISTRO")
        return f"{accion_base}_{singular}"

    return ACCIONES_ESPECIFICAS.get((entidad, accion_base), accion_base)


def _entero(valor, defecto, minimo=None, maximo=None):
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        numero = defecto
    if minimo is not None:
        numero = max(numero, minimo)
    if maximo is not None:
        numero = min(numero, maximo)
    return numero
