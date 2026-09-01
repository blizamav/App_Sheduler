import os
import re
import shutil
import subprocess
from pathlib import Path

from flask import current_app

from app_scheduler.configuracion import RAIZ_PROYECTO, VALORES_PLANTILLA


PREFIJO_APP_SQL = "APP_SCHEDULER"
BASES_SISTEMA = {"master", "model", "msdb", "tempdb"}
PATRON_IDENTIFICADOR = re.compile(r"^[A-Za-z0-9_]+$")
RUTA_RUNNER_IN_PLACE = RAIZ_PROYECTO / "database" / "factory_reset" / "000_reset_in_place.sql"


class ErrorFactoryResetSQL(RuntimeError):
    pass


def parsear_targets_permitidos_factory_reset(valor):
    """Normaliza una allowlist exacta; no admite patrones ni nombres de sistema."""
    permitidos = []
    vistos = set()
    for elemento in str(valor or "").split(","):
        nombre = elemento.strip()
        if not nombre:
            continue
        _validar_nombre_bd(nombre)
        normalizado = nombre.upper()
        if normalizado not in vistos:
            vistos.add(normalizado)
            permitidos.append(nombre)
    return permitidos


def validar_configuracion_factory_reset_sql():
    ejecutable = _resolver_sqlcmd()
    servidor = str(current_app.config.get("FACTORY_RESET_DB_SERVER") or "").strip()
    usuario = str(current_app.config.get("FACTORY_RESET_DB_USER") or "").strip()
    password = str(current_app.config.get("FACTORY_RESET_DB_PASSWORD") or "")
    destino = str(current_app.config.get("FACTORY_RESET_DB_TARGET") or "").strip()
    actual = str(current_app.config.get("DB_DATABASE") or "").strip()
    allowlist_valor = current_app.config.get("FACTORY_RESET_DB_ALLOWED_TARGETS")
    bloqueos = []
    allowlist_invalida = False
    try:
        targets_permitidos = parsear_targets_permitidos_factory_reset(allowlist_valor)
    except ValueError:
        targets_permitidos = []
        allowlist_invalida = True
    allowlist_normalizada = {nombre.upper() for nombre in targets_permitidos}
    destino_normalizado = destino.upper()
    actual_normalizado = actual.upper()
    target_coincide = bool(destino and actual and destino_normalizado == actual_normalizado)
    target_en_allowlist = bool(destino and destino_normalizado in allowlist_normalizada)

    if not current_app.config.get("FACTORY_RESET_HABILITADO", False):
        bloqueos.append("Factory Reset esta deshabilitado por configuracion.")
    if not ejecutable:
        bloqueos.append("SQLCMD no esta disponible en el servidor web.")
    if not servidor or servidor in VALORES_PLANTILLA:
        bloqueos.append("Falta FACTORY_RESET_DB_SERVER.")
    if not usuario or usuario in VALORES_PLANTILLA:
        bloqueos.append("Falta FACTORY_RESET_DB_USER.")
    if not password or password in VALORES_PLANTILLA:
        bloqueos.append("Falta FACTORY_RESET_DB_PASSWORD.")
    try:
        _validar_nombre_bd(destino)
        _validar_nombre_bd(actual)
    except ValueError:
        bloqueos.append("El nombre de base configurado no es seguro.")
    if allowlist_invalida:
        bloqueos.append("FACTORY_RESET_DB_ALLOWED_TARGETS contiene un identificador no permitido.")
    elif not targets_permitidos:
        bloqueos.append("FACTORY_RESET_DB_ALLOWED_TARGETS no esta configurada.")
    if destino and actual and not target_coincide:
        bloqueos.append("FACTORY_RESET_DB_TARGET no coincide exactamente con DB_DATABASE.")
    if destino and not target_en_allowlist:
        bloqueos.append("FACTORY_RESET_DB_TARGET no pertenece a FACTORY_RESET_DB_ALLOWED_TARGETS.")
    if not RUTA_RUNNER_IN_PLACE.is_file():
        bloqueos.append("El runner in-place de Factory Reset no esta disponible.")

    return {
        "disponible": not bloqueos,
        "bloqueos": bloqueos,
        "sqlcmd_disponible": bool(ejecutable),
        "credencial_mantenimiento": bool(usuario and password),
        "target_configurado": destino or None,
        "target_coincide": target_coincide,
        "target_en_allowlist": target_en_allowlist,
        "allowlist_configurada": bool(targets_permitidos) and not allowlist_invalida,
        "targets_permitidos": targets_permitidos,
        "habilitado": bool(current_app.config.get("FACTORY_RESET_HABILITADO", False)),
        "modo": "IN_PLACE",
    }


class EjecutorSQLFactoryReset:
    def __init__(self):
        validacion = validar_configuracion_factory_reset_sql()
        if not validacion["disponible"]:
            raise ErrorFactoryResetSQL("Configuracion de mantenimiento Factory Reset incompleta.")
        self.sqlcmd = _resolver_sqlcmd()
        self.servidor = str(current_app.config["FACTORY_RESET_DB_SERVER"]).strip()
        self.usuario = str(current_app.config["FACTORY_RESET_DB_USER"]).strip()
        self.password = str(current_app.config["FACTORY_RESET_DB_PASSWORD"])
        self.target = _validar_nombre_bd(current_app.config["FACTORY_RESET_DB_TARGET"])
        self.timeout = max(60, int(current_app.config.get("FACTORY_RESET_SQLCMD_TIMEOUT_SEGUNDOS", 900)))

    def validar_entorno_in_place(self):
        target = _literal(self.target)
        consulta = f"""
SET NOCOUNT ON;
SELECT N'FACTORY_INPLACE_ENV|'
    + CASE WHEN DB_NAME() = N'{target}' THEN N'1' ELSE N'0' END + N'|'
    + CASE WHEN DATABASEPROPERTYEX(DB_NAME(), N'Updateability') = N'READ_WRITE' THEN N'1' ELSE N'0' END + N'|'
    + CASE WHEN ISNULL(IS_ROLEMEMBER(N'db_owner'), 0) = 1 THEN N'1' ELSE N'0' END;
"""
        salida = self.ejecutar_consulta(consulta)
        linea = next(
            (item.strip() for item in salida.splitlines() if item.strip().startswith("FACTORY_INPLACE_ENV|")),
            None,
        )
        if not linea:
            raise ErrorFactoryResetSQL("No fue posible confirmar el entorno in-place de Factory Reset.")
        partes = linea.split("|")
        if len(partes) != 4 or any(valor not in {"0", "1"} for valor in partes[1:]):
            raise ErrorFactoryResetSQL("La respuesta del precheck in-place no es valida.")
        contexto_correcto, lectura_escritura, db_owner = (valor == "1" for valor in partes[1:])
        disponible = contexto_correcto and lectura_escritura and db_owner
        return {
            "disponible": disponible,
            "contexto_correcto": contexto_correcto,
            "lectura_escritura": lectura_escritura,
            "db_owner": db_owner,
            "mensaje": (
                "La cuenta SQL de mantenimiento puede reconstruir APP_SCHEDULER_QA in-place."
                if disponible
                else "La cuenta de SQL Server configurada para Factory Reset (FACTORY_RESET_DB_USER) debe pertenecer a db_owner exclusivamente en APP_SCHEDULER_QA. Esta cuenta es distinta del usuario de APP Scheduler."
            ),
        }

    def ejecutar_reset_in_place(self, id_operacion, usuario, version_app):
        runner = RUTA_RUNNER_IN_PLACE.resolve()
        if not runner.is_file() or RAIZ_PROYECTO not in runner.parents:
            raise ErrorFactoryResetSQL("El runner in-place no es un archivo permitido.")
        timeout_lock_ms = max(1000, min(self.timeout * 1000, 60000))
        comando = self._comando_base(self.target) + [
            "-v", f"DB_NAME={self.target}",
            "-v", f"LOCK_TIMEOUT_MS={timeout_lock_ms}",
            "-v", f"OPERATION_ID={_variable_sqlcmd(id_operacion, 80)}",
            "-v", f"RESET_USER={_variable_sqlcmd(usuario, 100)}",
            "-v", f"APP_VERSION={_variable_sqlcmd(version_app, 50)}",
            "-i", str(runner),
        ]
        salida = self._ejecutar(comando, script=runner.name)
        if "FACTORY_IN_PLACE_COMMIT_OK" not in salida:
            raise ErrorFactoryResetSQL("El runner in-place no confirmo el COMMIT final.")
        return True

    def validar_resultado_final(self, id_operacion):
        operacion = _literal(str(id_operacion or "")[:80])
        consulta = f"""
SET NOCOUNT ON;
IF (SELECT COUNT(*) FROM sys.tables t JOIN sys.schemas s ON s.schema_id=t.schema_id WHERE s.name=N'dbo') <> 33
    BEGIN THROW 51000, N'Cantidad de tablas invalida.', 1; END;
IF NOT EXISTS (SELECT 1 FROM dbo.configuracion_sistema WHERE clave=N'BOOTSTRAP_SQL' AND valor=N'19C.1' AND activo=1)
    BEGIN THROW 51000, N'Marca BOOTSTRAP_SQL invalida.', 1; END;
IF NOT EXISTS (SELECT 1 FROM dbo.auditoria_cambios WHERE accion=N'FACTORY_RESET_COMPLETADO' AND id_entidad=N'{operacion}')
    BEGIN THROW 51000, N'Auditoria Factory Reset ausente.', 1; END;
IF EXISTS (SELECT 1 FROM dbo.configuracion_scheduler WHERE activo=1 AND (scheduler_activo<>0 OR permitir_ejecucion_automatica<>0))
    BEGIN THROW 51000, N'Scheduler no quedo deshabilitado.', 1; END;
IF EXISTS (SELECT 1 FROM dbo.configuracion_mail_graph WHERE activo<>0)
    BEGIN THROW 51000, N'Mail Graph no quedo inactivo.', 1; END;
SELECT N'FACTORY_IN_PLACE_FINAL_OK';
"""
        salida = self.ejecutar_consulta(consulta)
        if "FACTORY_IN_PLACE_FINAL_OK" not in salida:
            raise ErrorFactoryResetSQL("La validacion final in-place no entrego confirmacion.")
        return True

    def ejecutar_consulta(self, consulta):
        comando = self._comando_base(self.target) + ["-Q", str(consulta), "-h", "-1", "-W", "-s", "|"]
        return self._ejecutar(comando)

    def _comando_base(self, database):
        comando = [
            self.sqlcmd,
            "-S", self.servidor,
            "-U", self.usuario,
            "-d", _validar_nombre_bd(database),
            "-b",
            "-r", "1",
            "-l", str(min(self.timeout, 120)),
            "-t", str(self.timeout),
        ]
        if _bandera(current_app.config.get("FACTORY_RESET_DB_ENCRYPT")):
            comando.append("-N")
        if _bandera(current_app.config.get("FACTORY_RESET_DB_TRUST_SERVER_CERTIFICATE"), True):
            comando.append("-C")
        return comando

    def _ejecutar(self, comando, script=None):
        entorno = os.environ.copy()
        entorno["SQLCMDPASSWORD"] = self.password
        try:
            resultado = subprocess.run(
                comando,
                cwd=RAIZ_PROYECTO,
                env=entorno,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout,
                shell=False,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise ErrorFactoryResetSQL(f"SQLCMD no pudo ejecutarse: {error.__class__.__name__}.") from error
        finally:
            entorno.pop("SQLCMDPASSWORD", None)
        salida = (resultado.stdout or "") + (resultado.stderr or "")
        if resultado.returncode != 0:
            detalle = _sanitizar_salida_sqlcmd(salida, secretos=(self.password, self.usuario, self.servidor))
            scripts = re.findall(r"FACTORY_SCRIPT\|([^\s|]+)", salida)
            script_fallido = Path(scripts[-1]).name if scripts else Path(script or "runner_in_place").name
            raise ErrorFactoryResetSQL(
                f"SCRIPT: {script_fallido}; RETURNCODE: {resultado.returncode}; ERROR: {detalle or 'SQLCMD no entrego detalle.'}"
            )
        return salida[-20000:]


def _resolver_sqlcmd():
    valor = str(current_app.config.get("FACTORY_RESET_SQLCMD") or "sqlcmd").strip()
    ruta = Path(valor).expanduser()
    if ruta.is_absolute():
        return str(ruta.resolve()) if ruta.is_file() else None
    return shutil.which(valor)


def _validar_nombre_bd(valor):
    nombre = str(valor or "").strip()
    if not nombre or len(nombre) > 128 or not PATRON_IDENTIFICADOR.fullmatch(nombre):
        raise ValueError("Nombre de base no permitido.")
    if nombre.lower() in BASES_SISTEMA:
        raise ValueError("No se permite operar sobre una base de sistema.")
    return nombre


def _literal(valor):
    return str(valor).replace("'", "''")


def _variable_sqlcmd(valor, limite):
    texto = str(valor or "").replace("\r", " ").replace("\n", " ").replace("'", "''")[:limite]
    if not texto:
        raise ErrorFactoryResetSQL("Variable SQLCMD de auditoria no valida.")
    return texto


def _bandera(valor, defecto=False):
    if valor is None:
        return defecto
    return str(valor).strip().lower() in {"1", "true", "yes", "si", "y"}


def _sanitizar_salida_sqlcmd(valor, secretos=()):
    texto = str(valor or "")
    for secreto in secretos:
        secreto = str(secreto or "")
        if secreto:
            texto = re.sub(re.escape(secreto), "***", texto, flags=re.IGNORECASE)
    texto = re.sub(
        r"(?i)\b(password|pwd|client_secret|secret|token|sqlcmdpassword|user|usuario)\b\s*[:=]\s*[^\s;]+",
        lambda coincidencia: f"{coincidencia.group(1)}=***",
        texto,
    )
    texto = re.sub(r"(?i)(login failed for user)\s+'[^']*'", r"\1 '***'", texto)
    lineas = [linea.strip() for linea in texto.splitlines() if linea.strip()]
    return " | ".join(lineas)[-4000:]
