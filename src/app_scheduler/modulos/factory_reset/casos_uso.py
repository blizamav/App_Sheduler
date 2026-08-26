"""Preview, prechecks y orquestacion del Factory Reset in-place."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app_scheduler.compartido.control_runtime import (
    adquirir_lock_factory_reset,
    actualizar_lock_factory_reset,
    liberar_lock_factory_reset,
    obtener_estado_factory_reset,
    obtener_estado_operacion_factory_reset,
    registrar_evento_factory_reset,
    registrar_marca_factory_reset_completado,
)
from app_scheduler.configuracion import RAIZ_PROYECTO, VALORES_PLANTILLA
from app_scheduler.modulos.factory_reset.contratos import ROOTS_FILESYSTEM
from app_scheduler.modulos.factory_reset.filesystem import (
    eliminar_cuarentena_factory_reset,
    limpiar_roots_factory_reset,
    preparar_roots_factory_reset,
    rollback_roots_factory_reset,
    validar_roots_vacios,
)
from app_scheduler.modulos.factory_reset.sql import (
    EjecutorSQLFactoryReset,
    ErrorFactoryResetSQL,
    validar_configuracion_factory_reset_sql,
)
from app_scheduler.persistencia.repositorio_factory_reset import RepositorioFactoryReset


VERSION_PREVIEW = "1.0"
SALT_PREVIEW = "app-scheduler-factory-reset-reconstruido-v1"


class ServicioFactoryReset:
    def __init__(self, proveedor, configuracion, *, repositorio=RepositorioFactoryReset,
                 fabrica_motor=EjecutorSQLFactoryReset):
        self.proveedor = proveedor
        self.configuracion = configuracion
        self.tipo_repositorio = repositorio
        self.fabrica_motor = fabrica_motor

    def generar_preview(self, identidad):
        generado = datetime.now(timezone.utc)
        lock = self._estado_lock()
        bloqueos: list[str] = []
        errores: list[str] = []
        try:
            with self.proveedor.conexion_lectura() as conexion:
                repo = self.tipo_repositorio(conexion)
                conteos = repo.obtener_conteos()
                version_instalada = repo.obtener_version_bootstrap()
                activas = repo.listar_ejecuciones_activas()
        except Exception as error:
            conteos, version_instalada, activas = {}, None, ()
            bloqueos.append("La base de datos no pudo validarse completamente.")
            errores.append(f"Inventario SQL no disponible ({error.__class__.__name__}).")

        manifiesto = validar_manifiesto_factory_reset()
        manifiesto["version_instalada"] = version_instalada
        manifiesto["version_coincide"] = bool(
            version_instalada and version_instalada == manifiesto.get("version")
        )
        configuracion_sql = validar_configuracion_factory_reset_sql()
        entorno = {
            "disponible": False, "contexto_correcto": False,
            "lectura_escritura": False, "db_owner": False,
            "mensaje": "El entorno in-place no fue evaluado.",
        }
        if configuracion_sql["disponible"]:
            try:
                entorno = self.fabrica_motor().validar_entorno_in_place()
            except Exception as error:
                errores.append(f"Precheck SQL no disponible ({error.__class__.__name__}).")
                entorno["mensaje"] = "No fue posible validar la cuenta SQL de mantenimiento."

        if lock["bloquea"]:
            bloqueos.append("Existe un lock global de Factory Reset activo o dudoso.")
        if activas:
            bloqueos.append("Existen ejecuciones EN_EJECUCION.")
        if not manifiesto["valido"]:
            bloqueos.append("El manifiesto in-place no esta disponible o es invalido.")
        if not self._super_admin_env_disponible():
            bloqueos.append("SUPER_ADMIN_ENV no esta disponible para recuperar acceso.")
        bloqueos.extend(configuracion_sql["bloqueos"])
        if configuracion_sql["disponible"] and not entorno["disponible"]:
            bloqueos.append(entorno["mensaje"])

        filesystem = self._inventariar_filesystem()
        id_operacion = str(uuid4())
        preview = {
            "version_preview": VERSION_PREVIEW,
            "id_operacion": id_operacion,
            "generado_utc": generado.isoformat(),
            "expira_segundos": self.configuracion.factory_reset_preview_ttl_segundos,
            "estado": "BLOQUEADO" if bloqueos else "LISTO",
            "bloqueos": tuple(dict.fromkeys(bloqueos)),
            "errores": tuple(errores),
            "lock": lock,
            "base_datos": {"nombre": self.configuracion.db_database,
                           "conteos": conteos, "total_registros": sum(conteos.values())},
            "ejecuciones_activas": activas,
            "filesystem": filesystem,
            "bootstrap": manifiesto,
            "super_admin_env": self._super_admin_env_disponible(),
            "configuracion_reset": configuracion_sql,
            "entorno_in_place": entorno,
        }
        resumen_hash = _hash_preview(preview)
        preview["resumen_hash"] = resumen_hash
        preview["token_preview"] = self._serializador().dumps({
            "usuario": identidad.usuario,
            "id_operacion": id_operacion,
            "resumen_hash": resumen_hash,
            "estado_lock": lock["estado"],
            "manifest_hash": manifiesto.get("hash_conjunto"),
        })
        return preview

    def validar_token(self, token, identidad, resumen_hash):
        try:
            datos = self._serializador().loads(
                token, max_age=self.configuracion.factory_reset_preview_ttl_segundos
            )
        except SignatureExpired:
            return False, "El preview expiro. Genera uno nuevo.", None
        except (BadSignature, TypeError):
            return False, "El token de preview no es valido.", None
        if datos.get("usuario") != identidad.usuario:
            return False, "El preview pertenece a otra sesion.", None
        if datos.get("resumen_hash") != resumen_hash:
            return False, "El resumen del preview no coincide.", None
        if datos.get("estado_lock") != "NORMAL":
            return False, "El preview no fue generado en estado normal.", None
        return True, "Preview vigente.", datos

    def ejecutar(self, datos_preview, identidad, *, motor=None):
        id_operacion = str((datos_preview or {}).get("id_operacion") or "")
        precheck = self._precheck(datos_preview, motor=motor)
        if not precheck["ok"]:
            return _resultado_error(id_operacion, precheck["mensaje"], "PRECHECK")

        adquirido, estado = adquirir_lock_factory_reset(
            self.configuracion.ruta_control_runtime,
            "FACTORY_RESET_PREPARANDO", "WEB_RECONSTRUIDA",
            id_operacion=id_operacion,
            timeout_segundos=self.configuracion.factory_reset_lock_timeout_segundos,
        )
        if not adquirido:
            return _resultado_error(id_operacion, "Existe otra operacion Factory Reset activa.", estado.get("fase"))

        operaciones_fs = []
        filesystem_aplicado = False
        commit_sql_confirmado = False
        motor = motor or self.fabrica_motor()
        try:
            self._avanzar(id_operacion, "LOCK_ADQUIRIDO", 8, "Lock global externo adquirido.")
            segundo = self._precheck(datos_preview, lock_propio=id_operacion, motor=motor)
            if not segundo["ok"]:
                raise RuntimeError(segundo["mensaje"])

            self._avanzar(id_operacion, "BLOQUEANDO_ACTIVIDAD", 15, "Actividad nueva bloqueada y condiciones recalculadas.")
            operaciones_fs = preparar_roots_factory_reset(id_operacion)
            self._avanzar(id_operacion, "CUARENTENA_FILESYSTEM", 25, "Respaldando y limpiando archivos runtime.")
            limpiar_roots_factory_reset(operaciones_fs)
            filesystem_aplicado = True
            if not validar_roots_vacios(operaciones_fs):
                raise RuntimeError("Los roots runtime no quedaron vacios.")

            self._revalidar(id_operacion, precheck["manifiesto"], operaciones_fs)
            self._avanzar(id_operacion, "ADQUIRIENDO_APPLOCK", 35, "Iniciando sesion SQL transaccional.")
            self._avanzar(id_operacion, "EJECUTANDO_RESET_IN_PLACE", 48, "Reconstruyendo la base autorizada in-place.")
            origen = "ENV" if identidad.es_super_admin_env else "BD"
            motor.ejecutar_reset_in_place(
                id_operacion, f"{identidad.usuario} [{origen}]", self.configuracion.app_version
            )
            commit_sql_confirmado = True
            self._avanzar(id_operacion, "CONFIRMANDO_COMMIT", 78, "COMMIT SQL confirmado por el runner.")
            self._avanzar(id_operacion, "VALIDANDO_RESULTADO", 88, "Validando instalacion reconstruida.")
            motor.validar_resultado_final(id_operacion)
            self._avanzar(id_operacion, "LIMPIANDO_CUARENTENA", 95, "Eliminando cuarentena final.")
            if not eliminar_cuarentena_factory_reset(operaciones_fs)["ok"]:
                raise RuntimeError("No pudo eliminarse toda la cuarentena filesystem.")
            registrar_marca_factory_reset_completado(
                self.configuracion.ruta_control_runtime, id_operacion
            )
            self._avanzar(id_operacion, "COMPLETADO", 100, "Factory Reset in-place completado.", completado=True)
            if not liberar_lock_factory_reset(
                self.configuracion.ruta_control_runtime, id_operacion,
                self.configuracion.factory_reset_lock_timeout_segundos,
            ):
                raise RuntimeError("El lock externo requiere revision manual.")
            return {"ok": True, "mensaje": "APP Scheduler fue restablecido in-place correctamente.",
                    "id_operacion": id_operacion, "modo": "IN_PLACE"}
        except Exception as error:
            rollback_fs = None
            if filesystem_aplicado and not commit_sql_confirmado:
                rollback_fs = rollback_roots_factory_reset(operaciones_fs)["ok"]
            mensaje = _mensaje_error_seguro(error)
            registrar_evento_factory_reset(
                self.configuracion.ruta_control_runtime, id_operacion, "ERROR", mensaje,
                "ERROR", {"commit_sql_confirmado": commit_sql_confirmado,
                          "filesystem_aplicado": filesystem_aplicado,
                          "rollback_filesystem": rollback_fs},
            )
            detalle = (
                " SQL confirmo COMMIT; no se reintrodujeron archivos antiguos."
                if commit_sql_confirmado
                else f" Rollback filesystem={_estado_bool(rollback_fs)}."
            )
            actualizar_lock_factory_reset(
                self.configuracion.ruta_control_runtime, id_operacion,
                "FACTORY_RESET_ERROR", fase="ERROR", progreso=0,
                mensaje="Factory Reset en error; requiere revision manual." + detalle,
                error_seguro=mensaje,
                timeout_segundos=self.configuracion.factory_reset_lock_timeout_segundos,
            )
            return {"ok": False, "mensaje": mensaje + detalle,
                    "id_operacion": id_operacion, "requiere_revision_manual": True,
                    "commit_sql_confirmado": commit_sql_confirmado}

    def estado_operacion(self, id_operacion):
        return obtener_estado_operacion_factory_reset(
            self.configuracion.ruta_control_runtime, id_operacion
        )

    def estado_lock(self):
        return self._estado_lock()

    def _precheck(self, datos_preview, *, lock_propio=None, motor=None):
        configuracion = validar_configuracion_factory_reset_sql()
        if not configuracion["disponible"]:
            return {"ok": False, "mensaje": configuracion["bloqueos"][0], "manifiesto": None}
        try:
            entorno = (motor or self.fabrica_motor()).validar_entorno_in_place()
        except Exception:
            return {"ok": False, "mensaje": "No fue posible validar la cuenta SQL de mantenimiento.", "manifiesto": None}
        if not entorno["disponible"]:
            return {"ok": False, "mensaje": entorno["mensaje"], "manifiesto": None}
        lock = self._estado_lock()
        if lock["bloquea"] and lock.get("id_operacion") != lock_propio:
            return {"ok": False, "mensaje": "Existe un lock Factory Reset activo o dudoso.", "manifiesto": None}
        manifiesto = validar_manifiesto_factory_reset()
        if not manifiesto["valido"]:
            return {"ok": False, "mensaje": "El manifiesto in-place no es valido.", "manifiesto": manifiesto}
        if manifiesto["hash_conjunto"] != (datos_preview or {}).get("manifest_hash"):
            return {"ok": False, "mensaje": "El runner cambio despues del preview.", "manifiesto": manifiesto}
        if not self._super_admin_env_disponible():
            return {"ok": False, "mensaje": "SUPER_ADMIN_ENV no esta disponible.", "manifiesto": manifiesto}
        try:
            with self.proveedor.conexion_lectura() as conexion:
                activas = self.tipo_repositorio(conexion).listar_ejecuciones_activas()
        except Exception:
            return {"ok": False, "mensaje": "No fue posible recalcular el estado operativo.", "manifiesto": manifiesto}
        if activas:
            return {"ok": False, "mensaje": "Existen ejecuciones EN_EJECUCION.", "manifiesto": manifiesto}
        try:
            preparar_roots_factory_reset((datos_preview or {}).get("id_operacion"))
        except Exception:
            return {"ok": False, "mensaje": "Los roots runtime no superaron la validacion de seguridad.", "manifiesto": manifiesto}
        return {"ok": True, "mensaje": "Precheck in-place correcto.", "manifiesto": manifiesto}

    def _revalidar(self, id_operacion, manifiesto_previo, operaciones_fs):
        lock = self._estado_lock()
        actual = validar_manifiesto_factory_reset()
        if lock.get("id_operacion") != id_operacion or lock.get("dudoso"):
            raise RuntimeError("El lock dejo de ser confiable.")
        if not actual["valido"] or actual["hash_conjunto"] != manifiesto_previo["hash_conjunto"]:
            raise RuntimeError("El runner cambio durante la operacion.")
        with self.proveedor.conexion_lectura() as conexion:
            if self.tipo_repositorio(conexion).listar_ejecuciones_activas():
                raise RuntimeError("Se detecto actividad operativa antes del reset.")
        if not validar_roots_vacios(operaciones_fs):
            raise RuntimeError("Los roots runtime cambiaron antes del reset.")

    def _avanzar(self, id_operacion, fase, progreso, mensaje, completado=False):
        estado = "FACTORY_RESET_PREPARANDO" if fase == "LOCK_ADQUIRIDO" else "FACTORY_RESET_EN_PROGRESO"
        if not actualizar_lock_factory_reset(
            self.configuracion.ruta_control_runtime, id_operacion, estado,
            fase=fase, progreso=progreso, mensaje=mensaje, completado=completado,
            timeout_segundos=self.configuracion.factory_reset_lock_timeout_segundos,
        ):
            raise RuntimeError("No fue posible actualizar el lock global.")

    def _estado_lock(self):
        return obtener_estado_factory_reset(
            self.configuracion.ruta_control_runtime,
            self.configuracion.factory_reset_lock_timeout_segundos,
        )

    def _super_admin_env_disponible(self):
        return bool(
            self.configuracion.usuario_admin_defecto
            and self.configuracion.password_admin_defecto
            and self.configuracion.usuario_admin_defecto not in VALORES_PLANTILLA
            and self.configuracion.password_admin_defecto not in VALORES_PLANTILLA
        )

    def _serializador(self):
        return URLSafeTimedSerializer(self.configuracion.app_secret_key, salt=SALT_PREVIEW)

    def _inventariar_filesystem(self):
        roots = []
        for nombre, clave, defecto in ROOTS_FILESYSTEM:
            valor = getattr(self.configuracion, clave.lower(), Path(defecto))
            ruta = Path(valor).expanduser()
            if not ruta.is_absolute():
                ruta = RAIZ_PROYECTO / ruta
            roots.append(_inventariar_root(nombre, ruta.resolve()))
        return {
            "roots": tuple(roots),
            "total_archivos": sum(item["archivos"] for item in roots),
            "bytes_aproximados": sum(item["bytes_aproximados"] for item in roots),
        }


def validar_manifiesto_factory_reset():
    ruta = RAIZ_PROYECTO / "database" / "factory_reset" / "manifest.json"
    resultado = {"valido": False, "version": None, "cantidad_scripts": 0,
                 "orden": (), "faltantes": (), "hash_conjunto": None,
                 "modo": None, "runner": None}
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        scripts = datos.get("scripts") or []
        orden = [int(item["order"]) for item in scripts]
        archivos = [str(item["file"]) for item in scripts]
        controles = [str(datos.get("runner") or ""), str(datos.get("cleanup_script") or "")]
        faltantes = []
        hasher = hashlib.sha256(ruta.read_bytes())
        for archivo in [*controles, *archivos]:
            relativa = Path(archivo)
            absoluta = (RAIZ_PROYECTO / relativa).resolve()
            if (not archivo or relativa.is_absolute() or ".." in relativa.parts
                    or RAIZ_PROYECTO not in absoluta.parents
                    or absoluta.suffix.lower() != ".sql" or not absoluta.is_file()
                    or absoluta.is_symlink()):
                faltantes.append(relativa.name or "archivo_control")
                continue
            hasher.update(str(relativa).replace("\\", "/").encode("utf-8"))
            hasher.update(absoluta.read_bytes())
        runner = (RAIZ_PROYECTO / controles[0]).read_text(encoding="utf-8") if controles[0] and not faltantes else ""
        esperados = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 100]
        inclusiones = [controles[1], *archivos]
        runner_valido = bool(
            runner and all(runner.count(f":r ./{archivo}") == 1 for archivo in inclusiones)
            and "database/release/001_crear_base_datos.sql" not in runner
            and ":on error exit" in runner.lower()
            and "BEGIN TRANSACTION" in runner and "COMMIT TRANSACTION" in runner
            and "sp_getapplock" in runner
        )
        resultado.update({
            "valido": bool(orden == esperados and len(set(archivos)) == len(archivos)
                           and str(datos.get("mode") or "").lower() == "in_place"
                           and runner_valido and not faltantes),
            "version": str(datos.get("version") or "")[:30],
            "cantidad_scripts": len(scripts), "orden": tuple(orden),
            "faltantes": tuple(faltantes), "hash_conjunto": hasher.hexdigest() if not faltantes else None,
            "modo": str(datos.get("mode") or "").upper(), "runner": controles[0],
        })
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        pass
    return resultado


def _inventariar_root(nombre, ruta):
    resumen = {"nombre": nombre, "existe": ruta.is_dir(), "archivos": 0,
               "carpetas": 0, "bytes_aproximados": 0}
    if not ruta.is_dir() or ruta.is_symlink():
        return resumen
    for actual, carpetas, archivos in os.walk(ruta, followlinks=False):
        resumen["carpetas"] += len(carpetas)
        for archivo in archivos:
            resumen["archivos"] += 1
            try:
                resumen["bytes_aproximados"] += (Path(actual) / archivo).stat().st_size
            except OSError:
                pass
    return resumen


def _hash_preview(preview):
    contenido = json.dumps(preview, ensure_ascii=True, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(contenido.encode("utf-8")).hexdigest()


def _mensaje_error_seguro(error):
    detalle = f" {error}" if isinstance(error, ErrorFactoryResetSQL) else ""
    return f"Factory Reset no pudo completarse ({error.__class__.__name__}).{detalle}"[:4500]


def _resultado_error(id_operacion, mensaje, fase):
    return {"ok": False, "mensaje": mensaje, "id_operacion": id_operacion or None, "fase": fase}


def _estado_bool(valor):
    return "NO_APLICA" if valor is None else ("OK" if valor else "ERROR")
