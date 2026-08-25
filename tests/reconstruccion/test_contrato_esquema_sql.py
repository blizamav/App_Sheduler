from __future__ import annotations

import re
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[2]
FUENTES_DDL = (
    RAIZ / "database/release/002_schema_final.sql",
    RAIZ / "database/bootstrap/007_crear_notificaciones_evidencias.sql",
    RAIZ / "database/bootstrap/008_crear_configuracion_mail_graph.sql",
)
TABLAS_ESPERADAS = {
    "cat_estados_tarea",
    "cat_estados_ejecucion",
    "cat_tipos_programacion",
    "cat_niveles_log",
    "cat_tipos_tarea",
    "cat_estados_version_script",
    "usuarios",
    "roles",
    "permisos",
    "usuarios_roles",
    "roles_permisos",
    "clientes",
    "categorias",
    "tipos",
    "tareas",
    "programaciones",
    "scripts",
    "scripts_versiones",
    "configuracion_sistema",
    "ejecuciones",
    "logs_tareas",
    "logs_sistema",
    "auditoria_cambios",
    "configuracion_scheduler",
    "scheduler_worker_heartbeat",
    "scheduler_eventos",
    "feriados",
    "reglas_feriados_irrenunciables",
    "notificaciones_config_tarea",
    "notificaciones_destinatarios",
    "evidencias_ejecucion",
    "notificaciones_envios",
    "configuracion_mail_graph",
}
COLUMNAS_CONTRATO = {
    "usuarios": {
        "id_usuario",
        "usuario",
        "nombre_completo",
        "email",
        "password_hash",
        "activo",
        "eliminado_operativo",
    },
    "roles": {"id_rol", "codigo_rol", "nombre_rol", "activo"},
    "permisos": {"id_permiso", "codigo_permiso", "modulo", "accion", "activo"},
    "usuarios_roles": {"id_usuario", "id_rol", "activo"},
    "roles_permisos": {"id_rol", "id_permiso", "permitido", "activo"},
    "clientes": {"id_cliente", "nombre_cliente", "nombre_normalizado", "activo"},
    "categorias": {"id_categoria", "nombre_categoria", "nombre_normalizado", "activo"},
    "tipos": {"id_tipo", "nombre_tipo", "nombre_normalizado", "activo"},
    "tareas": {"id_tarea", "id_cliente", "id_categoria", "id_tipo", "estado_tarea"},
    "programaciones": {"id_programacion", "id_tarea", "tipo_programacion"},
    "scripts": {"id_script", "id_tarea", "id_version_activa"},
    "scripts_versiones": {"id_version", "id_script", "numero_version", "es_activa"},
    "ejecuciones": {"id_ejecucion", "id_tarea", "id_script", "id_version"},
}
COLUMNAS_AUDITORIA_REEMPLAZADAS = {
    "fecha_hora": "fecha_evento",
    "tabla_afectada": "entidad",
    "id_registro": "id_entidad",
    "valor_anterior": "valores_antes",
    "valor_nuevo": "valores_despues",
    "ip": "ip_origen",
}
COPIAS_AUDITORIA_COMPATIBILIDAD = (
    "SET fecha_evento = COALESCE(fecha_evento, fecha_hora, SYSDATETIME())",
    "SET entidad = COALESCE(entidad, tabla_afectada, modulo, N''GENERAL'')",
    "SET id_entidad = COALESCE(id_entidad, id_registro)",
    "SET valores_antes = COALESCE(valores_antes, valor_anterior)",
    "SET valores_despues = COALESCE(valores_despues, valor_nuevo)",
    "SET ip_origen = COALESCE(ip_origen, CONVERT(nvarchar(100), ip))",
)


def _esquema() -> tuple[dict[str, set[str]], str]:
    texto = "\n".join(archivo.read_text(encoding="utf-8-sig") for archivo in FUENTES_DDL)
    bloques = re.findall(
        r"CREATE TABLE\s+dbo\.(\w+)\s*\((.*?)\n\s*\);",
        texto,
        flags=re.IGNORECASE | re.DOTALL,
    )
    tablas: dict[str, set[str]] = {}
    patron_columna = re.compile(
        r"^\s{8}([a-z_]\w*)\s+(?:bigint|int|tinyint|bit|varchar|nvarchar|datetime2|datetime|date|time)\b",
        flags=re.IGNORECASE | re.MULTILINE,
    )
    for tabla, cuerpo in bloques:
        tablas[tabla] = set(patron_columna.findall(cuerpo))
    return tablas, texto


def test_bootstrap_declara_exactamente_las_33_tablas_vigentes():
    tablas, _ = _esquema()

    assert set(tablas) == TABLAS_ESPERADAS
    assert len(tablas) == 33
    assert sum(len(columnas) for columnas in tablas.values()) == 457


def test_columnas_consumidas_existen_en_ddl_vigente():
    tablas, _ = _esquema()

    for tabla, columnas in COLUMNAS_CONTRATO.items():
        assert columnas <= tablas[tabla], f"Contrato invalido para dbo.{tabla}"


def test_auditoria_limpia_excluye_columnas_legacy_ya_reemplazadas():
    tablas, _ = _esquema()
    columnas_auditoria = tablas["auditoria_cambios"]

    assert COLUMNAS_AUDITORIA_REEMPLAZADAS.keys().isdisjoint(columnas_auditoria)
    assert set(COLUMNAS_AUDITORIA_REEMPLAZADAS.values()) <= columnas_auditoria

    migracion_compatibilidad = (
        RAIZ
        / "database/legacy_pre_release_13B/migrations/018_crear_o_ajustar_auditoria_cambios.sql"
    ).read_text(encoding="utf-8-sig")
    for columna_legacy in COLUMNAS_AUDITORIA_REEMPLAZADAS:
        assert f"COL_LENGTH('dbo.auditoria_cambios', '{columna_legacy}')" in migracion_compatibilidad
    for copia in COPIAS_AUDITORIA_COMPATIBILIDAD:
        assert copia in migracion_compatibilidad


def test_relaciones_operativas_fundamentales_permanecen_en_bootstrap():
    _, ddl = _esquema()
    relaciones = (
        "FOREIGN KEY (id_usuario) REFERENCES dbo.usuarios(id_usuario)",
        "FOREIGN KEY (id_rol) REFERENCES dbo.roles(id_rol)",
        "FOREIGN KEY (id_permiso) REFERENCES dbo.permisos(id_permiso)",
        "FOREIGN KEY (id_tarea) REFERENCES dbo.tareas(id_tarea)",
        "FOREIGN KEY (id_script) REFERENCES dbo.scripts(id_script)",
        "FOREIGN KEY (id_version_activa) REFERENCES dbo.scripts_versiones(id_version)",
    )

    for relacion in relaciones:
        assert relacion in ddl
    assert len(re.findall(r"FOREIGN KEY\s*\(", ddl, flags=re.IGNORECASE)) == 25


def test_validacion_100_conserva_conteos_del_contrato_publicado():
    validacion = (
        RAIZ / "database/bootstrap/100_validacion_bootstrap_actual.sql"
    ).read_text(encoding="utf-8-sig")

    for cantidad in (33, 457, 25, 39, 118, 120):
        assert f"<> {cantidad}" in validacion


def test_ajuste_notificaciones_separa_exito_y_evidencia_sin_romper_legacy():
    _, ddl = _esquema()
    migracion = (
        RAIZ / "database/migrations/022_separar_notificacion_estado_evidencia.sql"
    ).read_text(encoding="utf-8-sig")

    assert re.search(
        r"notificar_exito_activa\s+bit\s+NOT NULL.*?DEFAULT 0",
        ddl,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert "enviar_evidencia = 0 OR notificar_exito_activa = 1" in ddl
    for tipo in ("NOTIFICACION_EXITOSA", "EVIDENCIA_CLIENTE", "ALERTA_INTERNA"):
        assert tipo in ddl and tipo in migracion
    assert "WHERE enviar_evidencia = 1" in migracion
    assert "SET notificar_exito_activa = 1" in migracion
    assert "SET alerta_error_activa" not in migracion
    assert "DELETE FROM dbo.notificaciones" not in migracion


def test_migracion_022_declara_set_options_y_atomicidad_antes_del_ddl():
    migracion = (
        RAIZ / "database/migrations/022_separar_notificacion_estado_evidencia.sql"
    ).read_text(encoding="utf-8-sig")
    normalizada = re.sub(r"\s+", " ", migracion).upper()

    opciones = (
        "SET ANSI_NULLS ON",
        "SET ANSI_PADDING ON",
        "SET ANSI_WARNINGS ON",
        "SET ARITHABORT ON",
        "SET CONCAT_NULL_YIELDS_NULL ON",
        "SET QUOTED_IDENTIFIER ON",
        "SET NUMERIC_ROUNDABORT OFF",
        "SET XACT_ABORT ON",
    )
    primer_ddl = normalizada.index("ALTER TABLE")
    for opcion in opciones:
        assert opcion in normalizada
        assert normalizada.index(opcion) < primer_ddl

    assert normalizada.index("BEGIN TRANSACTION") < primer_ddl
    assert "BEGIN TRY" in normalizada
    assert "BEGIN CATCH" in normalizada
    assert "ROLLBACK TRANSACTION" in normalizada
    assert "COMMIT TRANSACTION" in normalizada


def test_versiones_y_ejecuciones_conservan_contratos_de_trazabilidad():
    _, ddl = _esquema()

    assert "CHECK (numero_version BETWEEN 1 AND 3)" in ddl
    assert "UNIQUE (id_script, numero_version)" in ddl
    assert "WHERE es_activa = 1" in ddl
    assert re.search(
        r"CREATE TABLE\s+dbo\.ejecuciones\s*\(.*?id_script int NULL,.*?id_version int NULL,",
        ddl,
        flags=re.DOTALL,
    )


def test_repositorios_no_ocultan_commit_ni_usan_select_asterisco():
    archivos = tuple(
        (RAIZ / "src/app_scheduler/persistencia").glob("repositorio*.py")
    )

    for archivo in archivos:
        codigo = archivo.read_text(encoding="utf-8")
        assert ".commit(" not in codigo
        assert not re.search(r"SELECT\s+\*", codigo, flags=re.IGNORECASE)


def test_reconstruccion_no_agrega_orm_ni_importa_runtime_historico():
    dependencias = "\n".join(
        (
            (RAIZ / "pyproject.toml").read_text(encoding="utf-8"),
            (RAIZ / "requirements.txt").read_text(encoding="utf-8"),
            (RAIZ / "requirements-dev.txt").read_text(encoding="utf-8"),
        )
    ).lower()
    codigo = "\n".join(
        archivo.read_text(encoding="utf-8")
        for archivo in (RAIZ / "src/app_scheduler").rglob("*.py")
    )

    assert "sqlalchemy" not in dependencias
    assert "peewee" not in dependencias
    assert not re.search(r"^(?:from|import)\s+app(?:\.|\s|$)", codigo, flags=re.MULTILINE)
