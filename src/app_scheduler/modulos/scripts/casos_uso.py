"""Casos de uso de scripts, slots versionados y .env por version."""

from __future__ import annotations

from pathlib import Path

from app_scheduler.compartido.auditoria import crear_evento_auditoria
from app_scheduler.compartido.errores import ErrorValidacion
from app_scheduler.compartido.filesystem import AlmacenArchivosProcesos, validar_env, validar_script
from app_scheduler.compartido.unidad_trabajo import UnidadTrabajoSQL
from app_scheduler.persistencia.repositorio_auditoria import RepositorioAuditoria
from app_scheduler.persistencia.repositorio_scripts import RepositorioScripts
from app_scheduler.persistencia.repositorio_tareas import RepositorioTareas
from app_scheduler.persistencia.modelos import Paginacion


class ServicioScripts:
    def __init__(self, proveedor, configuracion, *, fabrica_uow=UnidadTrabajoSQL,
                 repositorio=RepositorioScripts, repositorio_tareas=RepositorioTareas,
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

    def listar(self, pagina=1, busqueda=None, estado=None, version_activa=None):
        texto = str(busqueda or "").strip() or None
        if texto and len(texto) > 100:
            raise ErrorValidacion("La busqueda admite hasta 100 caracteres.")
        estado_normalizado = str(estado or "").strip().upper() or None
        if estado_normalizado not in {None, "ACTIVO", "INACTIVO"}:
            raise ErrorValidacion("El estado seleccionado no es valido.")
        version_normalizada = None
        if str(version_activa or "").strip():
            try:
                version_normalizada = int(version_activa)
            except (TypeError, ValueError) as error:
                raise ErrorValidacion("La version activa seleccionada no es valida.") from error
            if version_normalizada not in {1, 2, 3}:
                raise ErrorValidacion("La version activa debe corresponder a v1, v2 o v3.")
        paginacion = Paginacion(int(pagina), 18)
        with self.proveedor.conexion_lectura() as conexion:
            return self.tipo_repositorio(conexion).listar_paginado(
                paginacion,
                busqueda=texto,
                activo=None if estado_normalizado is None else estado_normalizado == "ACTIVO",
                version_activa=version_normalizada,
            )

    def detalle(self, id_tarea: int):
        with self.proveedor.conexion_lectura() as conexion:
            tarea = self.tipo_tareas(conexion).obtener_por_id(id_tarea)
            if tarea is None: raise ErrorValidacion("Tarea no encontrada.")
            repo = self.tipo_repositorio(conexion)
            script = repo.obtener_por_tarea(id_tarea)
            versiones = () if script is None else repo.listar_versiones(script.id_script)
            referencias = {v.id_version: repo.contar_referencias_version(v.id_version) for v in versiones}
            versiones_por_slot = {v.numero_version: v for v in versiones}
            return {"tarea": tarea, "script": script, "versiones": versiones,
                    "referencias": referencias, "slots_libres": tuple(n for n in (1, 2, 3)
                    if n not in versiones_por_slot),
                    "slots_versiones": tuple(versiones_por_slot.get(n) for n in (1, 2, 3))}

    def subir_version(self, id_tarea: int, nombre_archivo: str, contenido: bytes,
                      observacion, actor, contexto) -> int:
        validar_script(nombre_archivo, contenido, self.configuracion.max_script_size_mb * 1024 * 1024)
        cambio = None; confirmado = False
        try:
            with self.fabrica_uow(self.proveedor) as uow:
                conexion = uow.obtener_conexion(); tareas = self.tipo_tareas(conexion)
                tarea = tareas.obtener_por_id(id_tarea)
                if tarea is None: raise ErrorValidacion("Tarea no encontrada.")
                repo = self.tipo_repositorio(conexion); script = repo.obtener_por_tarea(id_tarea)
                versiones = () if script is None else repo.listar_versiones(script.id_script)
                ocupados = {v.numero_version for v in versiones}
                libres = [n for n in (1, 2, 3) if n not in ocupados]
                if not libres: raise ErrorValidacion("El script ya ocupa los tres slots. Selecciona un slot reemplazable.")
                numero = libres[0]; primera = script is None
                segmentos = self._segmentos(tarea)
                destino = self.almacen.ruta_script(segmentos, numero, nombre_archivo)
                cambio = self.almacen.preparar(destino, contenido); cambio.aplicar()
                if script is None:
                    id_script = repo.crear_script(id_tarea, f"Script de {tarea.nombre_tarea}", None, actor.usuario)
                else: id_script = script.id_script
                id_version = repo.crear_version(id_script, numero, nombre_archivo, str(destino),
                    self.almacen.relativa(destino), self.almacen.hash(contenido), primera,
                    self._observacion(observacion), actor.usuario)
                if primera: repo.establecer_version_activa(id_script, id_version, actor.usuario)
                self._auditar(conexion, actor, contexto, "SCRIPT_VERSION_CARGADA", id_version,
                    tarea.nombre_tarea, {"id_tarea": id_tarea, "numero_version": numero,
                    "nombre_archivo": nombre_archivo, "es_activa": primera})
                uow.confirmar(); confirmado = True; cambio.confirmar(); return id_version
        except Exception:
            if cambio and not confirmado: cambio.revertir()
            raise

    def reemplazar(self, id_tarea: int, id_version: int, nombre_archivo: str,
                   contenido: bytes, observacion, actor, contexto) -> None:
        validar_script(nombre_archivo, contenido, self.configuracion.max_script_size_mb * 1024 * 1024)
        cambios = []; confirmado = False
        try:
            with self.fabrica_uow(self.proveedor) as uow:
                conexion = uow.obtener_conexion(); tarea = self.tipo_tareas(conexion).obtener_por_id(id_tarea)
                repo = self.tipo_repositorio(conexion); version = repo.obtener_version(id_version)
                if tarea is None or version is None: raise ErrorValidacion("Tarea o version no encontrada.")
                script = repo.obtener(version.id_script)
                if script is None or script.id_tarea != id_tarea: raise ErrorValidacion("La version no pertenece a la tarea.")
                if version.es_activa: raise ErrorValidacion("No se puede reemplazar la version activa.")
                if repo.contar_referencias_version_para_reemplazo(id_version):
                    raise ErrorValidacion("La version tiene historial y no puede reemplazarse.")
                destino = self.almacen.ruta_script(self._segmentos(tarea), version.numero_version, nombre_archivo)
                cambio = self.almacen.preparar(destino, contenido, permitir_reemplazo=True); cambio.aplicar(); cambios.append(cambio)
                anterior = Path(version.ruta_fisica)
                if anterior.resolve(strict=False) != destino.resolve(strict=False):
                    retiro_script = self.almacen.preparar_retiro(anterior)
                    retiro_script.aplicar(); cambios.append(retiro_script)
                if version.ruta_env_fisica:
                    retiro_env = self.almacen.preparar_retiro(Path(version.ruta_env_fisica))
                    retiro_env.aplicar(); cambios.append(retiro_env)
                if not repo.reemplazar_version(id_version, nombre_archivo, str(destino),
                    self.almacen.relativa(destino), self.almacen.hash(contenido),
                    self._observacion(observacion), actor.usuario):
                    raise ErrorValidacion("La version ya no puede reemplazarse.")
                self._auditar(conexion, actor, contexto, "SCRIPT_VERSION_REEMPLAZADA", id_version,
                    tarea.nombre_tarea, {"slot": version.numero_version,
                    "archivo_anterior": version.nombre_archivo, "archivo_nuevo": nombre_archivo,
                    "sha256_anterior": version.hash_archivo,
                    "sha256_nuevo": self.almacen.hash(contenido)})
                uow.confirmar(); confirmado = True
                for operacion in cambios: operacion.confirmar()
        except Exception:
            if not confirmado:
                for operacion in reversed(cambios): operacion.revertir()
            raise

    def activar(self, id_tarea: int, id_version: int, actor, contexto) -> None:
        with self.fabrica_uow(self.proveedor) as uow:
            conexion = uow.obtener_conexion(); repo = self.tipo_repositorio(conexion)
            script = repo.obtener_por_tarea(id_tarea); version = repo.obtener_version(id_version)
            if script is None or version is None or version.id_script != script.id_script:
                raise ErrorValidacion("Version no encontrada para la tarea.")
            if version.es_activa: raise ErrorValidacion("La version ya esta activa.")
            if version.estado_version not in {"DISPONIBLE", "INACTIVA"}:
                raise ErrorValidacion("El estado de la version no permite activarla.")
            try: repo.establecer_version_activa(script.id_script, id_version, actor.usuario)
            except ValueError as error: raise ErrorValidacion("La version no puede activarse.") from error
            self._auditar(conexion, actor, contexto, "SCRIPT_VERSION_ACTIVADA", id_version,
                script.nombre_script, {"numero_version": version.numero_version})
            uow.confirmar()

    def desactivar(self, id_tarea: int, id_version: int, actor, contexto) -> None:
        with self.fabrica_uow(self.proveedor) as uow:
            conexion = uow.obtener_conexion(); repo = self.tipo_repositorio(conexion)
            script = repo.obtener_por_tarea(id_tarea); version = repo.obtener_version(id_version)
            if script is None or version is None or version.id_script != script.id_script:
                raise ErrorValidacion("Version no encontrada para la tarea.")
            if version.es_activa: raise ErrorValidacion("La version activa no puede desactivarse.")
            if not repo.desactivar_version(id_version): raise ErrorValidacion("Solo una version disponible puede desactivarse.")
            self._auditar(conexion, actor, contexto, "SCRIPT_VERSION_DESACTIVADA", id_version,
                script.nombre_script, {"numero_version": version.numero_version})
            uow.confirmar()

    def guardar_env(self, id_tarea: int, id_version: int, contenido: bytes, actor, contexto) -> None:
        validar_env(contenido, self.configuracion.max_env_size_kb * 1024)
        cambio = None; confirmado = False
        try:
            with self.fabrica_uow(self.proveedor) as uow:
                conexion = uow.obtener_conexion(); tarea = self.tipo_tareas(conexion).obtener_por_id(id_tarea)
                repo = self.tipo_repositorio(conexion); version = repo.obtener_version(id_version)
                script = None if version is None else repo.obtener(version.id_script)
                if tarea is None or version is None or script is None or script.id_tarea != id_tarea:
                    raise ErrorValidacion("Version no encontrada para la tarea.")
                destino = self.almacen.ruta_env(self._segmentos(tarea), version.numero_version)
                cambio = self.almacen.preparar(destino, contenido, permitir_reemplazo=True); cambio.aplicar()
                repo.actualizar_env(id_version, True, str(destino), self.almacen.relativa(destino))
                self._auditar(conexion, actor, contexto, "SCRIPT_ENV_CONFIGURADO", id_version,
                    script.nombre_script, {"requiere_env": True, "contenido": "[PROTEGIDO]"})
                uow.confirmar(); confirmado = True; cambio.confirmar()
        except Exception:
            if cambio and not confirmado: cambio.revertir()
            raise

    def quitar_env(self, id_tarea: int, id_version: int, actor, contexto) -> None:
        retiro = None; confirmado = False
        try:
            with self.fabrica_uow(self.proveedor) as uow:
                conexion = uow.obtener_conexion(); repo = self.tipo_repositorio(conexion)
                script = repo.obtener_por_tarea(id_tarea); version = repo.obtener_version(id_version)
                if script is None or version is None or version.id_script != script.id_script:
                    raise ErrorValidacion("Version no encontrada para la tarea.")
                if not version.ruta_env_fisica:
                    raise ErrorValidacion("La version no tiene configuracion .env.")
                retiro = self.almacen.preparar_retiro(Path(version.ruta_env_fisica))
                retiro.aplicar()
                repo.actualizar_env(id_version, False, None, None)
                self._auditar(conexion, actor, contexto, "SCRIPT_ENV_RETIRADO", id_version,
                    script.nombre_script, {"requiere_env": False})
                uow.confirmar(); confirmado = True; retiro.confirmar()
        except Exception:
            if retiro and not confirmado: retiro.revertir()
            raise

    def obtener_descarga(self, id_tarea: int, id_version: int):
        with self.proveedor.conexion_lectura() as conexion:
            repo = self.tipo_repositorio(conexion); script = repo.obtener_por_tarea(id_tarea)
            version = repo.obtener_version(id_version)
            if script is None or version is None or version.id_script != script.id_script:
                raise ErrorValidacion("Version no encontrada para la tarea.")
            ruta = self.almacen.validar_ruta_persistida(Path(version.ruta_fisica))
            if ruta.suffix.lower() != ".py" or not ruta.is_file():
                raise ErrorValidacion("El archivo de la version no esta disponible.")
            return ruta, version.nombre_archivo

    @staticmethod
    def _segmentos(tarea):
        return (tarea.categoria, tarea.tipo, tarea.cliente, tarea.nombre_tarea)

    @staticmethod
    def _observacion(valor):
        texto = str(valor or "").strip() or None
        if texto and len(texto) > 1000: raise ErrorValidacion("La observacion admite hasta 1000 caracteres.")
        return texto

    def _auditar(self, conexion, actor, contexto, accion, identificador, nombre, valores):
        self.tipo_auditoria(conexion).registrar(crear_evento_auditoria(
            usuario=actor.usuario, id_usuario=actor.id_usuario, accion=accion,
            entidad="scripts_versiones", id_entidad=identificador, nombre_entidad=nombre,
            descripcion="Operacion controlada sobre version de script.", valores_despues=valores,
            contexto=contexto, modulo="SCRIPTS",
        ))
