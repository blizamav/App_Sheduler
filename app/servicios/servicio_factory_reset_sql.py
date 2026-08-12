import os
import re
import shutil
import subprocess
from pathlib import Path

from flask import current_app

from app.config import BASE_DIR, VALORES_PLANTILLA


PREFIJO_APP_SQL = "APP_SCHEDULER"
BASES_SISTEMA = {"master", "model", "msdb", "tempdb"}
PATRON_IDENTIFICADOR = re.compile(r"^[A-Za-z0-9_]+$")


class ErrorFactoryResetSQL(RuntimeError):
    pass


def parsear_targets_permitidos_factory_reset(valor):
    """Normaliza una allowlist exacta de bases; rechaza patrones e identificadores invalidos."""
    permitidos = []
    vistos = set()
    for elemento in str(valor or "").split(","):
        nombre = elemento.strip()
        if not nombre:
            continue
        _validar_nombre_bd(nombre)
        normalizado = nombre.upper()
        if normalizado in vistos:
            continue
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
    prefijo_app = str(current_app.config.get("FACTORY_RESET_APP_NAME_PREFIX") or PREFIJO_APP_SQL).strip()
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
    if not prefijo_app or len(prefijo_app) > 100 or not re.fullmatch(r"[A-Za-z0-9_-]+", prefijo_app):
        bloqueos.append("FACTORY_RESET_APP_NAME_PREFIX no es valido.")
    return {
        "disponible": not bloqueos,
        "bloqueos": bloqueos,
        "sqlcmd_disponible": bool(ejecutable),
        "credencial_administrativa": bool(usuario and password),
        "target_configurado": destino or None,
        "target_coincide": target_coincide,
        "target_en_allowlist": target_en_allowlist,
        "allowlist_configurada": bool(targets_permitidos) and not allowlist_invalida,
        "targets_permitidos": targets_permitidos,
        "habilitado": bool(current_app.config.get("FACTORY_RESET_HABILITADO", False)),
    }


class EjecutorSQLFactoryReset:
    def __init__(self):
        validacion = validar_configuracion_factory_reset_sql()
        if not validacion["disponible"]:
            raise ErrorFactoryResetSQL("Configuracion administrativa Factory Reset incompleta.")
        self.sqlcmd = _resolver_sqlcmd()
        self.servidor = str(current_app.config["FACTORY_RESET_DB_SERVER"]).strip()
        self.usuario = str(current_app.config["FACTORY_RESET_DB_USER"]).strip()
        self.password = str(current_app.config["FACTORY_RESET_DB_PASSWORD"])
        self.timeout = max(60, int(current_app.config.get("FACTORY_RESET_SQLCMD_TIMEOUT_SEGUNDOS", 900)))
        self.prefijo_app = str(current_app.config.get("FACTORY_RESET_APP_NAME_PREFIX") or PREFIJO_APP_SQL).strip()[:100]

    def existe_base(self, nombre_bd):
        nombre = _validar_nombre_bd(nombre_bd)
        salida = self.ejecutar_consulta(
            f"SET NOCOUNT ON; SELECT CONCAT('FACTORY_EXISTS|', CASE WHEN DB_ID(N'{_literal(nombre)}') IS NULL THEN 0 ELSE 1 END);"
        )
        return "FACTORY_EXISTS|1" in salida

    def ejecutar_bootstrap(self, nombre_bd, manifiesto):
        nombre = _validar_nombre_bd(nombre_bd)
        if self.existe_base(nombre):
            raise ErrorFactoryResetSQL("La base temporal ya existe; no se reutiliza.")
        for item in manifiesto["scripts"]:
            ruta = (BASE_DIR / item["file"]).resolve()
            if BASE_DIR not in ruta.parents or not ruta.is_file():
                raise ErrorFactoryResetSQL("El manifiesto contiene un script no permitido.")
            self.ejecutar_archivo(ruta, nombre)

    def ejecutar_archivo(self, ruta, nombre_bd):
        nombre = _validar_nombre_bd(nombre_bd)
        comando = self._comando_base("master") + ["-v", f"DB_NAME={nombre}", "-i", str(Path(ruta).resolve())]
        return self._ejecutar(comando)

    def ejecutar_consulta(self, consulta, database="master"):
        base = _validar_database_conexion(database)
        comando = self._comando_base(base) + ["-Q", str(consulta), "-h", "-1", "-W", "-s", "|"]
        return self._ejecutar(comando)

    def validar_bootstrap(self, nombre_bd, ruta_validacion):
        salida = self.ejecutar_archivo(ruta_validacion, nombre_bd)
        if "BOOTSTRAP_ACTUAL" not in salida or "OK" not in salida:
            raise ErrorFactoryResetSQL("La validacion 100 no confirmo un bootstrap valido.")
        return True

    def listar_sesiones(self, nombre_bd):
        nombre = _validar_nombre_bd(nombre_bd)
        salida = self.ejecutar_consulta(
            "SET NOCOUNT ON; "
            "SELECT CONCAT('FACTORY_SESSION|', session_id, '|', "
            "REPLACE(ISNULL(program_name, ''), '|', '/'), '|', REPLACE(ISNULL(host_name, ''), '|', '/')) "
            f"FROM sys.dm_exec_sessions WHERE database_id = DB_ID(N'{_literal(nombre)}');"
        )
        sesiones = []
        for linea in salida.splitlines():
            linea = linea.strip()
            if not linea.startswith("FACTORY_SESSION|"):
                continue
            partes = linea.split("|", 3)
            sesiones.append({"session_id": int(partes[1]), "program_name": partes[2], "host_name": partes[3]})
        return sesiones

    def intercambiar_bases(self, actual, nueva, anterior):
        actual = _validar_nombre_bd(actual)
        nueva = _validar_nombre_bd(nueva)
        anterior = _validar_nombre_bd(anterior)
        sesiones = self.listar_sesiones(actual)
        ajenas = [s for s in sesiones if not s["program_name"].upper().startswith(self.prefijo_app.upper())]
        if ajenas:
            raise ErrorFactoryResetSQL("Existen conexiones SQL ajenas a APP Scheduler; intercambio cancelado.")
        consulta = f"""
SET NOCOUNT ON;
SET LOCK_TIMEOUT 10000;
IF DB_ID(N'{_literal(actual)}') IS NULL BEGIN ;THROW 51000, N'Base actual no disponible.', 1; END;
IF DB_ID(N'{_literal(nueva)}') IS NULL BEGIN ;THROW 51000, N'Base temporal no disponible.', 1; END;
IF DB_ID(N'{_literal(anterior)}') IS NOT NULL BEGIN ;THROW 51000, N'Nombre OLD ya existe.', 1; END;
IF EXISTS (
    SELECT 1 FROM sys.dm_exec_sessions
    WHERE database_id = DB_ID(N'{_literal(actual)}')
          AND LEFT(UPPER(ISNULL(program_name, N'')), {len(self.prefijo_app)}) <> N'{_literal(self.prefijo_app.upper())}'
) BEGIN ;THROW 51000, N'Conexion ajena detectada antes del intercambio.', 1; END;
DECLARE @kill nvarchar(max) = N'';
SELECT @kill = @kill + N'KILL ' + CONVERT(nvarchar(20), session_id) + N';'
FROM sys.dm_exec_sessions
WHERE database_id = DB_ID(N'{_literal(actual)}')
  AND LEFT(UPPER(ISNULL(program_name, N'')), {len(self.prefijo_app)}) = N'{_literal(self.prefijo_app.upper())}';
IF LEN(@kill) > 0 EXEC sys.sp_executesql @kill;
ALTER DATABASE [{actual}] SET SINGLE_USER;
ALTER DATABASE [{actual}] MODIFY NAME = [{anterior}];
ALTER DATABASE [{anterior}] SET MULTI_USER;
ALTER DATABASE [{nueva}] SET SINGLE_USER;
ALTER DATABASE [{nueva}] MODIFY NAME = [{actual}];
ALTER DATABASE [{actual}] SET MULTI_USER;
SELECT N'FACTORY_SWAP_OK';
"""
        salida = self.ejecutar_consulta(consulta)
        if "FACTORY_SWAP_OK" not in salida:
            raise ErrorFactoryResetSQL("El intercambio no entrego confirmacion.")

    def rollback_intercambio(self, actual, nueva, anterior, fallida):
        actual = _validar_nombre_bd(actual)
        nueva = _validar_nombre_bd(nueva)
        anterior = _validar_nombre_bd(anterior)
        fallida = _validar_nombre_bd(fallida)
        consulta = f"""
SET NOCOUNT ON;
SET LOCK_TIMEOUT 10000;
IF DB_ID(N'{_literal(anterior)}') IS NOT NULL
BEGIN
    IF EXISTS (
        SELECT 1 FROM sys.dm_exec_sessions
        WHERE database_id = DB_ID(N'{_literal(actual)}')
          AND LEFT(UPPER(ISNULL(program_name, N'')), {len(self.prefijo_app)}) <> N'{_literal(self.prefijo_app.upper())}'
    ) BEGIN ;THROW 51000, N'Conexion ajena impide rollback.', 1; END;
    DECLARE @kill nvarchar(max) = N'';
    SELECT @kill = @kill + N'KILL ' + CONVERT(nvarchar(20), session_id) + N';'
    FROM sys.dm_exec_sessions
    WHERE database_id = DB_ID(N'{_literal(actual)}')
      AND LEFT(UPPER(ISNULL(program_name, N'')), {len(self.prefijo_app)}) = N'{_literal(self.prefijo_app.upper())}';
    IF LEN(@kill) > 0 EXEC sys.sp_executesql @kill;
    IF DB_ID(N'{_literal(actual)}') IS NOT NULL
    BEGIN
        ALTER DATABASE [{actual}] SET SINGLE_USER;
        ALTER DATABASE [{actual}] MODIFY NAME = [{fallida}];
        ALTER DATABASE [{fallida}] SET MULTI_USER;
    END;
    ALTER DATABASE [{anterior}] SET SINGLE_USER;
    ALTER DATABASE [{anterior}] MODIFY NAME = [{actual}];
    ALTER DATABASE [{actual}] SET MULTI_USER;
END;
SELECT N'FACTORY_ROLLBACK_OK';
"""
        salida = self.ejecutar_consulta(consulta)
        if "FACTORY_ROLLBACK_OK" not in salida:
            raise ErrorFactoryResetSQL("Rollback SQL sin confirmacion.")

    def registrar_reset_completado(self, nombre_bd, usuario, id_operacion, version_app):
        nombre = _validar_nombre_bd(nombre_bd)
        usuario = _literal(str(usuario or "SUPER_ADMIN_ENV")[:100])
        operacion = _literal(str(id_operacion)[:80])
        version = _literal(str(version_app or "local")[:50])
        consulta = f"""
SET NOCOUNT ON;
USE [{nombre}];
INSERT INTO dbo.logs_sistema (usuario, accion, modulo, descripcion, valor_nuevo, nivel)
VALUES (N'{usuario}', N'FACTORY_RESET_COMPLETADO', N'FACTORY_RESET',
        N'APP Scheduler fue restablecido correctamente.', N'operation_id={operacion};version={version}', N'INFO');
INSERT INTO dbo.auditoria_cambios
    (usuario, accion, entidad, id_entidad, descripcion, valores_despues, resultado, modulo, activo)
VALUES (N'{usuario}', N'FACTORY_RESET_COMPLETADO', N'SISTEMA', N'{operacion}',
        N'Instalacion reconstruida desde bootstrap oficial.', N'version={version}', N'OK', N'Factory Reset', 1);
SELECT N'FACTORY_AUDIT_OK';
"""
        salida = self.ejecutar_consulta(consulta)
        if "FACTORY_AUDIT_OK" not in salida:
            raise ErrorFactoryResetSQL("No se confirmo la auditoria post reset.")

    def validar_resultado_final(self, nombre_bd, id_operacion):
        nombre = _validar_nombre_bd(nombre_bd)
        operacion = _literal(str(id_operacion)[:80])
        consulta = f"""
SET NOCOUNT ON;
USE [{nombre}];
IF (SELECT COUNT(*) FROM sys.tables t JOIN sys.schemas s ON s.schema_id=t.schema_id WHERE s.name=N'dbo') <> 33
    BEGIN ;THROW 51000, N'Cantidad de tablas invalida.', 1; END;
IF (SELECT COUNT(*) FROM dbo.permisos WHERE activo=1) <> 52
    BEGIN ;THROW 51000, N'Cantidad de permisos invalida.', 1; END;
IF NOT EXISTS (SELECT 1 FROM dbo.auditoria_cambios WHERE accion=N'FACTORY_RESET_COMPLETADO' AND id_entidad=N'{operacion}')
    BEGIN ;THROW 51000, N'Auditoria Factory Reset ausente.', 1; END;
IF EXISTS (SELECT 1 FROM dbo.configuracion_scheduler WHERE activo=1 AND (scheduler_activo<>0 OR permitir_ejecucion_automatica<>0))
    BEGIN ;THROW 51000, N'Scheduler no quedo deshabilitado.', 1; END;
IF EXISTS (SELECT 1 FROM dbo.configuracion_mail_graph WHERE activo<>0)
    BEGIN ;THROW 51000, N'Mail Graph no quedo inactivo.', 1; END;
SELECT N'FACTORY_FINAL_OK';
"""
        salida = self.ejecutar_consulta(consulta)
        if "FACTORY_FINAL_OK" not in salida:
            raise ErrorFactoryResetSQL("Validacion final sin confirmacion.")

    def _comando_base(self, database):
        comando = [
            self.sqlcmd,
            "-S", self.servidor,
            "-U", self.usuario,
            "-d", database,
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

    def _ejecutar(self, comando):
        entorno = os.environ.copy()
        entorno["SQLCMDPASSWORD"] = self.password
        try:
            resultado = subprocess.run(
                comando,
                cwd=BASE_DIR,
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
            raise ErrorFactoryResetSQL(f"SQLCMD finalizo con error ({resultado.returncode}).")
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


def _validar_database_conexion(valor):
    nombre = str(valor or "").strip()
    if nombre.lower() == "master":
        return "master"
    return _validar_nombre_bd(nombre)


def _literal(valor):
    return str(valor).replace("'", "''")


def _bandera(valor, defecto=False):
    if valor is None:
        return defecto
    return str(valor).strip().lower() in {"1", "true", "yes", "si", "y"}
