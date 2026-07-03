import hashlib
import io
import json
import re
import tokenize
from pathlib import Path

from flask import current_app

from app.config import BASE_DIR
from app.repositorios.repositorio_evidencias import registrar_evidencia_ejecucion
from app.repositorios.repositorio_notificaciones import obtener_configuracion_notificacion
from app.repositorios.repositorio_scripts import listar_versiones, obtener_script_por_tarea
from app.servicios.servicio_archivos import resolver_ruta_segura


DELIMITADOR_INICIO = "###APP_SCHEDULER_EVIDENCIA_INICIO###"
DELIMITADOR_FIN = "###APP_SCHEDULER_EVIDENCIA_FIN###"
VERSION_CONTRATO = "1.0"
RE_DECLARA_EVIDENCIA = re.compile(r"^\s*APP_SCHEDULER_EVIDENCIA\s*=\s*True\s*(?:#.*)?$", re.MULTILINE)
RE_DECLARA_VERSION = re.compile(
    r"^\s*APP_SCHEDULER_EVIDENCIA_VERSION\s*=\s*['\"]1\.0['\"]\s*(?:#.*)?$",
    re.MULTILINE,
)


def obtener_script_evidencia_tarea(id_tarea):
    script = obtener_script_por_tarea(id_tarea)
    if not script:
        return None, "La tarea no tiene script asociado."
    if not script.get("id_version_activa"):
        return None, "La tarea no tiene version activa de script."

    versiones = listar_versiones(script["id_script"])
    version_activa = next(
        (version for version in versiones if version.get("id_version") == script.get("id_version_activa")),
        None,
    )
    if not version_activa:
        return None, "No se encontro la version activa del script."
    if version_activa.get("estado_version") != "ACTIVA" or not bool(version_activa.get("es_activa")):
        return None, "La version activa del script no esta en estado ACTIVA."

    return {
        "script": script,
        "version": version_activa,
        "ruta_relativa": version_activa.get("ruta_relativa"),
        "nombre_archivo": version_activa.get("nombre_archivo"),
    }, None


def validar_soporte_evidencia_script_por_tarea(id_tarea):
    contexto, error = obtener_script_evidencia_tarea(id_tarea)
    if error:
        return _resultado_no_soportado([error])

    try:
        ruta_script = validar_archivo_script_seguro(contexto.get("ruta_relativa"))
        contenido = leer_script_seguro(ruta_script)
        return validar_contenido_script_evidencia(contenido)
    except ValueError as error_validacion:
        return _resultado_no_soportado([str(error_validacion)])


def validar_archivo_script_seguro(ruta_relativa):
    if not ruta_relativa:
        raise ValueError("La version activa no tiene ruta de script registrada.")

    ruta = resolver_ruta_segura(Path(ruta_relativa))
    base_scripts = (BASE_DIR / current_app.config.get("RUTA_BASE_SCRIPTS", "scripts")).resolve()
    if base_scripts not in ruta.parents and ruta != base_scripts:
        raise ValueError("La ruta del script no esta dentro del directorio permitido.")
    if ruta.suffix.lower() != ".py":
        raise ValueError("El archivo activo no es un script Python .py.")
    if not ruta.exists() or not ruta.is_file():
        raise ValueError("El archivo del script activo no existe.")
    return ruta


def leer_script_seguro(ruta_script):
    with open(ruta_script, "r", encoding="utf-8", errors="replace") as archivo:
        return archivo.read()


def validar_contenido_script_evidencia(contenido):
    strings_codigo = _strings_reales_codigo(contenido or "")
    validaciones = {
        "declara_evidencia": bool(RE_DECLARA_EVIDENCIA.search(contenido or "")),
        "declara_version": bool(RE_DECLARA_VERSION.search(contenido or "")),
        "delimitador_inicio": DELIMITADOR_INICIO in strings_codigo,
        "delimitador_fin": DELIMITADOR_FIN in strings_codigo,
    }
    errores = []
    if not validaciones["declara_evidencia"]:
        errores.append("El script no declara APP_SCHEDULER_EVIDENCIA = True.")
    if not validaciones["declara_version"]:
        errores.append('El script no declara APP_SCHEDULER_EVIDENCIA_VERSION = "1.0".')
    if not validaciones["delimitador_inicio"]:
        errores.append("El script no contiene el delimitador de inicio como string real del codigo.")
    if not validaciones["delimitador_fin"]:
        errores.append("El script no contiene el delimitador de fin como string real del codigo.")

    return {
        "soporta_evidencia": not errores,
        "version_contrato": VERSION_CONTRATO if not errores else None,
        "validaciones": validaciones,
        "errores": errores,
    }


def _strings_reales_codigo(contenido):
    strings = []
    try:
        tokens = tokenize.generate_tokens(io.StringIO(contenido or "").readline)
        for token in tokens:
            if token.type == tokenize.STRING:
                try:
                    valor = _literal_string(token.string)
                except Exception:
                    valor = token.string
                strings.append(str(valor))
    except tokenize.TokenError:
        return ""
    return "\n".join(strings)


def _literal_string(texto_token):
    import ast

    valor = ast.literal_eval(texto_token)
    return valor if isinstance(valor, str) else str(valor)


def extraer_bloque_evidencia_stdout(lineas_stdout):
    resultado = {
        "bloque_detectado": False,
        "delimitador_inicio_detectado": False,
        "delimitador_fin_detectado": False,
        "texto_bloque": "",
    }
    capturando = False
    lineas_bloque = []
    for linea in lineas_stdout or []:
        texto = str(linea).rstrip("\r\n")
        if not capturando and DELIMITADOR_INICIO in texto:
            resultado["delimitador_inicio_detectado"] = True
            resultado["bloque_detectado"] = True
            capturando = True
            despues_inicio = texto.split(DELIMITADOR_INICIO, 1)[1].strip()
            if DELIMITADOR_FIN in despues_inicio:
                antes_fin = despues_inicio.split(DELIMITADOR_FIN, 1)[0].strip()
                if antes_fin:
                    lineas_bloque.append(antes_fin)
                resultado["delimitador_fin_detectado"] = True
                capturando = False
                break
            if despues_inicio:
                lineas_bloque.append(despues_inicio)
            continue
        if capturando:
            if DELIMITADOR_FIN in texto:
                antes_fin = texto.split(DELIMITADOR_FIN, 1)[0].strip()
                if antes_fin:
                    lineas_bloque.append(antes_fin)
                resultado["delimitador_fin_detectado"] = True
                break
            lineas_bloque.append(texto)
    resultado["texto_bloque"] = "\n".join(lineas_bloque).strip()
    return resultado


def parsear_evidencia_stdout(texto_bloque):
    datos = json.loads(texto_bloque or "")
    if not isinstance(datos, dict):
        raise ValueError("El bloque de evidencia debe ser un objeto JSON.")
    return datos


def validar_contrato_evidencia(evidencia, exit_code=0):
    errores = []
    estado_evidencia = "VALIDADA"
    version = evidencia.get("version_contrato")
    estado = evidencia.get("estado")
    tipo = evidencia.get("tipo_evidencia")
    titulo = evidencia.get("titulo")
    resumen = evidencia.get("resumen")
    problemas = evidencia.get("problemas", [])
    adjuntos = evidencia.get("adjuntos", [])

    if version != VERSION_CONTRATO:
        errores.append('version_contrato debe ser "1.0".')
    if not estado:
        errores.append("estado es obligatorio.")
    if not tipo:
        errores.append("tipo_evidencia es obligatorio.")
    if not titulo:
        errores.append("titulo es obligatorio.")
    if not isinstance(resumen, list):
        errores.append("resumen debe ser una lista.")
    if problemas is not None and not isinstance(problemas, list):
        errores.append("problemas debe ser una lista.")
    if adjuntos is not None and not isinstance(adjuntos, list):
        errores.append("adjuntos debe ser una lista.")

    if errores:
        estado_evidencia = "INVALIDA"
    elif estado != "EXITOSO" or int(exit_code or 0) != 0:
        estado_evidencia = "ERROR_DECLARADO"
        if estado != "EXITOSO":
            errores.append("La evidencia declara estado distinto de EXITOSO.")
        if int(exit_code or 0) != 0:
            errores.append("El proceso finalizo con codigo distinto de 0.")
    elif problemas:
        estado_evidencia = "ERROR_DECLARADO"
        errores.append("La evidencia declara problemas.")
    else:
        adjuntos_faltantes = _adjuntos_obligatorios_faltantes(adjuntos)
        if adjuntos_faltantes:
            estado_evidencia = "ADJUNTO_FALTANTE"
            errores.append("Existen adjuntos obligatorios no disponibles o con ruta no permitida.")

    return {
        "estado_evidencia": estado_evidencia,
        "errores": errores,
        "version_contrato": version if version == VERSION_CONTRATO else None,
        "tipo_evidencia": _texto_max(tipo, 100),
        "titulo": _texto_max(titulo, 255),
        "asunto_sugerido": _texto_max(evidencia.get("asunto_sugerido"), 255),
        "cantidad_campos_resumen": len(resumen) if isinstance(resumen, list) else 0,
        "cantidad_adjuntos_declarados": len(adjuntos) if isinstance(adjuntos, list) else 0,
        "cantidad_problemas": len(problemas) if isinstance(problemas, list) else 0,
    }


def calcular_hash_evidencia(texto_bloque):
    try:
        datos = json.loads(texto_bloque or "")
        normalizado = json.dumps(datos, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    except Exception:
        normalizado = texto_bloque or ""
    return hashlib.sha256(normalizado.encode("utf-8", errors="replace")).hexdigest()


def construir_registro_evidencia(id_ejecucion, extraccion, validacion=None, texto_bloque=None):
    validacion = validacion or {}
    errores = validacion.get("errores") or []
    return {
        "id_ejecucion": id_ejecucion,
        "estado_evidencia": validacion.get("estado_evidencia", "INVALIDA"),
        "version_contrato": validacion.get("version_contrato"),
        "tipo_evidencia": validacion.get("tipo_evidencia"),
        "titulo": validacion.get("titulo"),
        "asunto_sugerido": validacion.get("asunto_sugerido"),
        "hash_evidencia": calcular_hash_evidencia(texto_bloque) if texto_bloque else None,
        "cantidad_campos_resumen": int(validacion.get("cantidad_campos_resumen") or 0),
        "cantidad_adjuntos_declarados": int(validacion.get("cantidad_adjuntos_declarados") or 0),
        "cantidad_problemas": int(validacion.get("cantidad_problemas") or 0),
        "bloque_detectado": bool(extraccion.get("bloque_detectado")),
        "delimitador_inicio_detectado": bool(extraccion.get("delimitador_inicio_detectado")),
        "delimitador_fin_detectado": bool(extraccion.get("delimitador_fin_detectado")),
        "error_validacion": _texto_max("; ".join(errores), 1000),
    }


def procesar_evidencia_ejecucion(id_ejecucion, id_tarea, exit_code, stdout_capturado):
    config = obtener_configuracion_notificacion(id_tarea)
    if not config or not bool(config.get("enviar_evidencia")):
        return None

    extraccion = extraer_bloque_evidencia_stdout(stdout_capturado)
    if not extraccion["delimitador_inicio_detectado"]:
        registro = construir_registro_evidencia(
            id_ejecucion,
            extraccion,
            {
                "estado_evidencia": "NO_EMITIDA",
                "errores": ["La tarea requiere evidencia, pero el script no emitio el bloque stdout."],
            },
        )
        registro["id_evidencia"] = registrar_evidencia_ejecucion(registro)
        return registro
    if not extraccion["delimitador_fin_detectado"]:
        registro = construir_registro_evidencia(
            id_ejecucion,
            extraccion,
            {
                "estado_evidencia": "INVALIDA",
                "errores": ["El bloque de evidencia no contiene delimitador de fin."],
            },
            extraccion.get("texto_bloque"),
        )
        registro["id_evidencia"] = registrar_evidencia_ejecucion(registro)
        return registro

    texto_bloque = extraccion.get("texto_bloque") or ""
    try:
        evidencia = parsear_evidencia_stdout(texto_bloque)
        validacion = validar_contrato_evidencia(evidencia, exit_code)
    except Exception as error:
        validacion = {
            "estado_evidencia": "INVALIDA",
            "errores": [f"JSON de evidencia invalido: {error.__class__.__name__}."],
        }
    registro = construir_registro_evidencia(id_ejecucion, extraccion, validacion, texto_bloque)
    registro["id_evidencia"] = registrar_evidencia_ejecucion(registro)
    return registro


def _adjuntos_obligatorios_faltantes(adjuntos):
    faltantes = []
    if not isinstance(adjuntos, list):
        return faltantes
    for adjunto in adjuntos:
        if not isinstance(adjunto, dict) or not _booleano(adjunto.get("obligatorio")):
            continue
        ruta = adjunto.get("ruta")
        if not ruta or not _ruta_adjunto_segura_existe(ruta):
            faltantes.append(adjunto.get("nombre") or ruta or "adjunto obligatorio")
    return faltantes


def _ruta_adjunto_segura_existe(ruta):
    try:
        ruta_path = Path(str(ruta))
        destino = ruta_path.resolve() if ruta_path.is_absolute() else (BASE_DIR / ruta_path).resolve()
        base = BASE_DIR.resolve()
        if base not in destino.parents and destino != base:
            return False
        return destino.exists() and destino.is_file()
    except Exception:
        return False


def _booleano(valor):
    if isinstance(valor, bool):
        return valor
    return str(valor or "").strip().lower() in {"1", "true", "si", "yes", "on"}


def _texto_max(valor, maximo):
    texto = str(valor or "").strip()
    if not texto:
        return None
    return texto[:maximo]


def _resultado_no_soportado(errores):
    return {
        "soporta_evidencia": False,
        "version_contrato": None,
        "validaciones": {
            "declara_evidencia": False,
            "declara_version": False,
            "delimitador_inicio": False,
            "delimitador_fin": False,
        },
        "errores": errores,
    }
