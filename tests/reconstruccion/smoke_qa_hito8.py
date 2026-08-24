"""Smoke QA real del Hito 8; no cambia esquema ni confirma escrituras."""

from __future__ import annotations

import sys
from pathlib import Path

from app_scheduler import crear_aplicacion
from app_scheduler.compartido.base_datos import ProveedorConexionesSQLServer
from app_scheduler.configuracion import ConfiguracionAplicacion
from app_scheduler.modulos.configuracion_operativa.casos_uso import ServicioConfiguracionOperativa
from app_scheduler.modulos.operacion.casos_uso import ServicioLogsSistema, ServicioObservabilidad


BASE_AUTORIZADA = "APP_SCHEDULER_QA"
MARCADOR_LOGIN = "QA_HITO8_LOGIN_INEXISTENTE"
TABLAS = {
    "usuarios", "roles", "permisos", "usuarios_roles", "roles_permisos",
    "clientes", "categorias", "tipos", "tareas", "scripts",
    "scripts_versiones", "programaciones", "ejecuciones", "logs_tareas",
    "logs_sistema", "auditoria_cambios", "configuracion_sistema",
    "configuracion_scheduler", "scheduler_worker_heartbeat",
    "notificaciones_config_tarea", "evidencias_ejecucion",
}
COLUMNAS = {
    "logs_sistema": {"id", "usuario", "accion", "modulo", "descripcion", "fecha_hora", "nivel"},
    "configuracion_scheduler": {"id_configuracion", "scheduler_activo", "intervalo_revision_segundos", "max_ejecuciones_concurrentes", "permitir_ejecucion_automatica", "modo_mantenimiento", "activo"},
    "scheduler_worker_heartbeat": {"id_worker", "nombre_worker", "estado", "fecha_ultimo_heartbeat", "activo"},
    "notificaciones_config_tarea": {"id_config_notificacion", "id_tarea", "enviar_evidencia", "plantilla_evidencia", "activo"},
}
INDICES = {
    "IX_logs_sistema_fecha",
    "UX_configuracion_scheduler_activa",
    "UX_scheduler_worker_heartbeat_nombre_activo",
    "UX_notif_config_tarea_activa",
}


class UnidadTrabajoRollback:
    """Permite probar login real sin persistir su auditoria controlada."""

    def __init__(self, proveedor):
        self.proveedor = proveedor
        self.conexion = None

    def __enter__(self):
        self.conexion = self.proveedor.abrir()
        return self

    def obtener_conexion(self):
        return self.conexion

    def confirmar(self):
        return None

    def __exit__(self, *_):
        try:
            self.conexion.rollback()
        finally:
            self.conexion.close()
        return False


def _consulta_lista(conexion, sql, parametros=()):
    cursor = conexion.cursor()
    try:
        cursor.execute(sql, parametros)
        return list(cursor.fetchall())
    finally:
        cursor.close()


def _consulta_escalar(conexion, sql, parametros=()):
    filas = _consulta_lista(conexion, sql, parametros)
    return None if not filas else filas[0][0]


def _validar_contrato(proveedor):
    with proveedor.conexion_lectura() as conexion:
        actual = str(_consulta_escalar(conexion, "SELECT DB_NAME()") or "")
        if actual != BASE_AUTORIZADA:
            raise RuntimeError("La conexion no apunta a la unica base QA autorizada.")
        version = str(_consulta_escalar(
            conexion, "SELECT CONVERT(varchar(30), SERVERPROPERTY('ProductVersion'))"
        ) or "no disponible")
        tablas = {str(f[0]) for f in _consulta_lista(conexion,
            "SELECT name FROM sys.tables WHERE schema_id = SCHEMA_ID('dbo')")}
        faltantes = sorted(TABLAS - tablas)
        if faltantes:
            raise RuntimeError("Faltan tablas requeridas por Hito 8: " + ", ".join(faltantes))
        for tabla, esperadas in COLUMNAS.items():
            reales = {str(f[0]) for f in _consulta_lista(conexion,
                "SELECT name FROM sys.columns WHERE object_id = OBJECT_ID(?)", (f"dbo.{tabla}",))}
            if esperadas - reales:
                raise RuntimeError(f"Contrato de columnas incompatible en {tabla}.")
        indices = {str(f[0]) for f in _consulta_lista(conexion,
            "SELECT name FROM sys.indexes WHERE name IS NOT NULL")}
        if INDICES - indices:
            raise RuntimeError("Faltan indices criticos del Hito 8.")
        fk_notif = int(_consulta_escalar(conexion, """SELECT COUNT(1)
FROM sys.foreign_keys WHERE parent_object_id = OBJECT_ID('dbo.notificaciones_config_tarea')
AND referenced_object_id = OBJECT_ID('dbo.tareas')""") or 0)
        fk_logs = int(_consulta_escalar(conexion, """SELECT COUNT(1)
FROM sys.foreign_keys WHERE parent_object_id = OBJECT_ID('dbo.logs_sistema')
AND referenced_object_id = OBJECT_ID('dbo.cat_niveles_log')""") or 0)
        if fk_notif != 1 or fk_logs != 1:
            raise RuntimeError("Las FK criticas del Hito 8 no coinciden con bootstrap.")
        residuo = int(_consulta_escalar(conexion, """SELECT
(SELECT COUNT(1) FROM dbo.usuarios WHERE usuario LIKE 'QA_HITO8[_]%') +
(SELECT COUNT(1) FROM dbo.tareas WHERE nombre_tarea LIKE 'QA_HITO8[_]%') +
(SELECT COUNT(1) FROM dbo.clientes WHERE nombre_cliente LIKE 'QA_HITO8[_]%')""") or 0)
    print(f"PRECHECK_OK database={BASE_AUTORIZADA} sql_version={version}")
    print(f"CONTRATO_OK tablas_minimas={len(TABLAS)} indices_criticos={len(INDICES)} fk_criticas=2")
    print(f"RESIDUOS_QA_HITO8={residuo}")
    return residuo


def _validar_lecturas(proveedor):
    logs = ServicioLogsSistema(proveedor).listar(pagina=1)
    estado = ServicioObservabilidad(proveedor).obtener_estado()
    configuracion = ServicioConfiguracionOperativa(proveedor).obtener()
    print(f"LECTURAS_OK logs_pagina={len(logs['pagina'].elementos)} logs_total={logs['pagina'].total}")
    print(f"OBSERVABILIDAD_OK worker={estado['estado_worker']['codigo']} scheduler_config={estado['configuracion'] is not None}")
    print(f"CONFIGURACION_OK claves={len(configuracion['configuraciones'])} scheduler={configuracion['scheduler'] is not None}")


def _validar_login_rollback(configuracion, proveedor):
    app = crear_aplicacion(configuracion, ajustes={"TESTING": True})
    servicio = app.extensions["servicio_autenticacion"]
    servicio.fabrica_uow = UnidadTrabajoRollback
    cliente = app.test_client()
    cliente.get("/login")
    with cliente.session_transaction() as sesion:
        token = sesion["_csrf"]["token"]
    invalido = cliente.post("/login", data={
        "csrf_token": token, "usuario": MARCADOR_LOGIN, "password": "valor-invalido-no-real",
    })
    if invalido.status_code != 200 or b"Usuario o contrasena incorrectos" not in invalido.data:
        raise RuntimeError("El login invalido no regreso al formulario con mensaje generico.")
    cliente.get("/login")
    with cliente.session_transaction() as sesion:
        token = sesion["_csrf"]["token"]
    admin = cliente.post("/login", data={
        "csrf_token": token,
        "usuario": configuracion.usuario_admin_defecto,
        "password": configuracion.password_admin_defecto,
    })
    if admin.status_code != 302:
        raise RuntimeError("SUPER_ADMIN_ENV no pudo completar el login controlado.")
    with proveedor.conexion_lectura() as conexion:
        residuo = int(_consulta_escalar(conexion,
            "SELECT COUNT(1) FROM dbo.auditoria_cambios WHERE usuario = ?",
            (MARCADOR_LOGIN,)) or 0)
    if residuo:
        raise RuntimeError("El smoke de login dejo auditoria residual.")
    print("LOGIN_INVALIDO_OK mensaje_generico=true persistencia_error=false")
    print("LOGIN_SUPER_ADMIN_ENV_OK=true LOGIN_SQL_VALIDO=NO_EJECUTADO_SIN_CREDENCIAL_APP_AUTORIZADA")
    print("CLEANUP_LOGIN_OK residuos=0")


def _validar_filesystem(configuracion):
    rutas = (configuracion.ruta_base_scripts, configuracion.ruta_base_env_scripts,
             configuracion.ruta_base_logs_tareas)
    disponibles = sum(1 for ruta in rutas if Path(ruta).resolve().exists())
    print(f"FILESYSTEM_READ_ONLY_OK rutas_disponibles={disponibles}/{len(rutas)}")


def main():
    configuracion = ConfiguracionAplicacion.desde_entorno()
    configuracion.validar("autenticacion")
    if configuracion.db_database != BASE_AUTORIZADA:
        raise RuntimeError("DB_DATABASE no corresponde a APP_SCHEDULER_QA.")
    if configuracion.db_user.strip().lower() != "user_scheduler":
        raise RuntimeError("DB_USER no corresponde a la cuenta operativa autorizada.")
    proveedor = ProveedorConexionesSQLServer(configuracion)
    residuos = _validar_contrato(proveedor)
    if residuos:
        raise RuntimeError("Existen residuos QA_HITO8 previos; no se continua.")
    _validar_lecturas(proveedor)
    _validar_login_rollback(configuracion, proveedor)
    _validar_filesystem(configuracion)
    print("SMOKE_QA_HITO8_OK writes_confirmados=0 scheduler_ciclos=0 scripts_ejecutados=0")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"SMOKE_QA_HITO8_ERROR tipo={error.__class__.__name__}", file=sys.stderr)
        raise SystemExit(1)
