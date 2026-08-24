"""Configuracion de evidencia sin ejecutar ni importar scripts de usuario."""

from __future__ import annotations

import ast
from pathlib import Path

from app_scheduler.compartido.auditoria import crear_evento_auditoria
from app_scheduler.compartido.errores import ErrorValidacion
from app_scheduler.compartido.filesystem import AlmacenArchivosProcesos
from app_scheduler.compartido.unidad_trabajo import UnidadTrabajoSQL
from app_scheduler.persistencia.modelos import ConfiguracionEvidenciaTarea
from app_scheduler.persistencia.repositorio_auditoria import RepositorioAuditoria
from app_scheduler.persistencia.repositorio_evidencias import RepositorioEvidencias
from app_scheduler.persistencia.repositorio_tareas import RepositorioTareas


INICIO = "###APP_SCHEDULER_EVIDENCIA_INICIO###"
FIN = "###APP_SCHEDULER_EVIDENCIA_FIN###"


class ServicioEvidencias:
    def __init__(self, proveedor, configuracion, *, fabrica_uow=UnidadTrabajoSQL,
                 repositorio=RepositorioEvidencias, repositorio_tareas=RepositorioTareas,
                 repositorio_auditoria=RepositorioAuditoria, almacen=None):
        self.proveedor = proveedor
        self.configuracion = configuracion
        self.fabrica_uow = fabrica_uow
        self.tipo_repositorio = repositorio
        self.tipo_tareas = repositorio_tareas
        self.tipo_auditoria = repositorio_auditoria
        self.almacen = almacen or AlmacenArchivosProcesos(
            configuracion.ruta_base_scripts, configuracion.ruta_base_env_scripts
        )

    def obtener_para_tarea(self, id_tarea: int):
        with self.proveedor.conexion_lectura() as conexion:
            repo = self.tipo_repositorio(conexion)
            configuracion = repo.obtener_configuracion(id_tarea)
            script = repo.obtener_script_activo(id_tarea)
        return {"configuracion": configuracion,
                "soporte": self._validar_archivo(script),
                "contrato": {"inicio": INICIO, "fin": FIN, "version": "1.0"}}

    def guardar(self, id_tarea: int, formulario, actor, contexto):
        valores = {
            "enviar_evidencia": formulario.get("enviar_evidencia") == "1",
            "adjuntar_archivos_declarados": formulario.get("adjuntar_archivos_declarados") == "1",
            "adjuntar_log_tecnico": formulario.get("adjuntar_log_tecnico") == "1",
        }
        with self.fabrica_uow(self.proveedor) as uow:
            conexion = uow.obtener_conexion()
            tarea = self.tipo_tareas(conexion).obtener_por_id(id_tarea)
            if tarea is None:
                raise ErrorValidacion("Tarea no encontrada.")
            repo = self.tipo_repositorio(conexion)
            actual = repo.obtener_configuracion(id_tarea)
            soporte = self._validar_archivo(repo.obtener_script_activo(id_tarea))
            if valores["enviar_evidencia"] and not soporte["compatible"]:
                raise ErrorValidacion(
                    "No se puede activar la evidencia: " + " ".join(soporte["errores"])
                )
            antes = {
                "enviar_evidencia": actual.enviar_evidencia,
                "adjuntar_archivos_declarados": actual.adjuntar_archivos_declarados,
                "adjuntar_log_tecnico": actual.adjuntar_log_tecnico,
            }
            if antes == valores:
                raise ErrorValidacion("No hay cambios de evidencia para guardar.")
            nueva = ConfiguracionEvidenciaTarea(
                actual.id_config_notificacion, id_tarea, valores["enviar_evidencia"],
                "STDOUT_V1", valores["adjuntar_archivos_declarados"],
                valores["adjuntar_log_tecnico"],
            )
            try:
                repo.guardar(nueva)
            except ValueError as error:
                raise ErrorValidacion("La configuracion de evidencia ya no esta disponible.") from error
            self.tipo_auditoria(conexion).registrar(crear_evento_auditoria(
                usuario=actor.usuario, id_usuario=actor.id_usuario,
                accion="CONFIGURACION_EVIDENCIA_EDITADA",
                entidad="notificaciones_config_tarea", id_entidad=id_tarea,
                nombre_entidad=tarea.nombre_tarea,
                descripcion="Configuracion de captura de evidencia stdout actualizada.",
                valores_antes=antes, valores_despues=valores, contexto=contexto,
                modulo="EVIDENCIAS",
            ))
            uow.confirmar()

    def _validar_archivo(self, script):
        if script is None:
            return _resultado_invalido("La tarea no tiene una version activa de script.")
        try:
            ruta = self.almacen.validar_ruta_persistida(Path(script[0]))
            if ruta.suffix.lower() != ".py" or not ruta.is_file():
                return _resultado_invalido("El archivo activo no esta disponible.")
            if ruta.stat().st_size > self.configuracion.max_script_size_mb * 1024 * 1024:
                return _resultado_invalido("El archivo activo supera el limite permitido.")
            contenido = ruta.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeDecodeError, ErrorValidacion):
            return _resultado_invalido("No fue posible leer el script activo de forma segura.")
        return validar_soporte_estatico(contenido)


def validar_soporte_estatico(contenido: str):
    try:
        arbol = ast.parse(contenido)
    except (SyntaxError, ValueError, TypeError):
        return _resultado_invalido("El script activo no contiene Python valido.")
    declaraciones = {}
    for nodo in arbol.body:
        if isinstance(nodo, (ast.Assign, ast.AnnAssign)):
            objetivos = nodo.targets if isinstance(nodo, ast.Assign) else (nodo.target,)
            valor = nodo.value
            for objetivo in objetivos:
                if isinstance(objetivo, ast.Name):
                    declaraciones[objetivo.id] = valor.value if isinstance(valor, ast.Constant) else None
    strings = {nodo.value for nodo in ast.walk(arbol)
               if isinstance(nodo, ast.Constant) and isinstance(nodo.value, str)}
    validaciones = {
        "declaracion": declaraciones.get("APP_SCHEDULER_EVIDENCIA") is True,
        "version": declaraciones.get("APP_SCHEDULER_EVIDENCIA_VERSION") == "1.0",
        "inicio": INICIO in strings,
        "fin": FIN in strings,
    }
    mensajes = {
        "declaracion": "Falta APP_SCHEDULER_EVIDENCIA = True.",
        "version": 'Falta APP_SCHEDULER_EVIDENCIA_VERSION = "1.0".',
        "inicio": "Falta el delimitador de inicio como string real del codigo.",
        "fin": "Falta el delimitador de fin como string real del codigo.",
    }
    errores = [mensajes[clave] for clave, correcto in validaciones.items() if not correcto]
    return {"compatible": not errores, "validaciones": validaciones, "errores": errores}


def _resultado_invalido(mensaje):
    return {"compatible": False,
            "validaciones": {"declaracion": False, "version": False,
                              "inicio": False, "fin": False},
            "errores": [mensaje]}
