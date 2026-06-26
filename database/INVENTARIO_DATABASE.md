# Inventario database

Fecha de auditoria: 2026-06-26

Fuente oficial de instalacion limpia:

```text
database/release/000_ejecutar_instalacion_completa.sql
```

Los scripts historicos fueron movidos a `database/legacy_pre_release_13B/` para evitar confusion operativa. No se eliminaron archivos.

## Estados

- `FUENTE_OFICIAL_RELEASE`: parte del release final validado.
- `VIGENTE`: archivo actual de apoyo/documentacion.
- `HISTORICO`: referencia de fases anteriores, no usar para instalacion nueva.
- `RESIDUO_CANDIDATO`: duplicado, viejo o confuso; no ejecutar sin revision.
- `NO_CLASIFICADO`: falta evidencia.

## Inventario

| Ruta | Tipo | Proposito inferido | Estado | Accion recomendada | Observacion |
|---|---|---|---|---|---|
| `database/release/000_ejecutar_instalacion_completa.sql` | SQLCMD | Script maestro de instalacion limpia. | FUENTE_OFICIAL_RELEASE | MANTENER | Punto de entrada recomendado; define `DB_NAME` y ejecuta `001` a `006` y `099`. |
| `database/release/000_configuracion_instalacion.sql` | SQLCMD | Referencia de variable `DB_NAME` para flujo avanzado. | FUENTE_OFICIAL_RELEASE | MANTENER | Usar solo si se ejecutan scripts individuales en la misma sesion SQLCMD. |
| `database/release/001_crear_base_datos.sql` | SQL | Crear base parametrizada. | FUENTE_OFICIAL_RELEASE | MANTENER | Usa `[$(DB_NAME)]`. |
| `database/release/002_schema_final.sql` | SQL | Crear schema consolidado final. | FUENTE_OFICIAL_RELEASE | MANTENER | Reemplaza migraciones incrementales para instalacion limpia. |
| `database/release/003_seed_roles_permisos.sql` | SQL | Cargar roles, permisos y matriz real QA. | FUENTE_OFICIAL_RELEASE | MANTENER | Roles reales: `SUPER_ADMIN`, `ADMIN`, `TI`, `TERCERO`. |
| `database/release/004_seed_catalogos_base.sql` | SQL | Cargar catalogos base. | FUENTE_OFICIAL_RELEASE | MANTENER | Reemplaza seeds historicos de catalogos. |
| `database/release/005_seed_configuracion_inicial.sql` | SQL | Cargar configuracion inicial segura. | FUENTE_OFICIAL_RELEASE | MANTENER | Scheduler apagado por defecto. |
| `database/release/006_seed_feriados_base.sql` | SQL | Cargar reglas locales base de feriados irrenunciables. | FUENTE_OFICIAL_RELEASE | MANTENER | No consulta APIs externas. |
| `database/release/099_validacion_instalacion.sql` | SQL | Validar instalacion limpia. | FUENTE_OFICIAL_RELEASE | MANTENER | Solo consultas `SELECT`; compara `DB_NAME()` contra `DB_NAME`. |
| `database/release/README_INSTALACION_SQL.md` | Markdown | Guia de instalacion release. | FUENTE_OFICIAL_RELEASE | MANTENER | Documenta SQLCMD Mode y script maestro. |
| `database/release/AUDITORIA_RELEASE_SQL.md` | Markdown | Auditoria del release SQL. | FUENTE_OFICIAL_RELEASE | MANTENER | Documenta criterios, riesgos y validaciones. |
| `database/legacy_pre_release_13B/README.md` | Markdown | Explicar carpeta historica. | VIGENTE | MANTENER | Advierte que legacy no es fuente oficial. |
| `database/legacy_pre_release_13B/diagnostics/001_diagnostico_tareas_scripts_post_11f.sql` | SQL | Diagnostico puntual post Fase 11F. | HISTORICO | DOCUMENTAR_COMO_HISTORICO | No usar para instalacion nueva. |
| `database/legacy_pre_release_13B/diagnostics/003_diagnostico_desacople_historico.sql` | SQL | Diagnostico puntual de desacople historico. | HISTORICO | DOCUMENTAR_COMO_HISTORICO | Puede apuntar a base de desarrollo. |
| `database/legacy_pre_release_13B/diagnostics/004_validacion_post_desacople_historico.sql` | SQL | Validacion puntual post desacople historico. | HISTORICO | DOCUMENTAR_COMO_HISTORICO | No forma parte del release. |
| `database/legacy_pre_release_13B/migrations/001_crear_base_datos.sql` | SQL | Migracion incremental inicial de base. | HISTORICO | DOCUMENTAR_COMO_HISTORICO | Reemplazada por release; apuntaba a `APP_SCHEDULER_QA`. |
| `database/legacy_pre_release_13B/migrations/002_crear_catalogos.sql` | SQL | Migracion incremental de catalogos. | HISTORICO | DOCUMENTAR_COMO_HISTORICO | Reemplazada por `002_schema_final.sql` y `004_seed_catalogos_base.sql`. |
| `database/legacy_pre_release_13B/migrations/003_crear_tablas_seguridad.sql` | SQL | Migracion incremental de seguridad. | HISTORICO | DOCUMENTAR_COMO_HISTORICO | Reemplazada por release consolidado. |
| `database/legacy_pre_release_13B/migrations/004_crear_tablas_negocio.sql` | SQL | Migracion incremental de negocio. | HISTORICO | DOCUMENTAR_COMO_HISTORICO | Reemplazada por release consolidado. |
| `database/legacy_pre_release_13B/migrations/005_crear_tablas_ejecucion_logs.sql` | SQL | Migracion incremental de ejecuciones/logs. | HISTORICO | DOCUMENTAR_COMO_HISTORICO | Reemplazada por release consolidado. |
| `database/legacy_pre_release_13B/migrations/006_crear_indices.sql` | SQL | Migracion incremental de indices. | HISTORICO | DOCUMENTAR_COMO_HISTORICO | Reemplazada por release consolidado. |
| `database/legacy_pre_release_13B/migrations/007_agregar_control_ejecucion_y_env_scripts.sql` | SQL | Migracion incremental control ejecucion/env scripts. | HISTORICO | DOCUMENTAR_COMO_HISTORICO | Integrada al schema final. |
| `database/legacy_pre_release_13B/migrations/008_ajustar_tareas_y_programaciones_base.sql` | SQL | Ajustes incrementales tareas/programaciones. | HISTORICO | DOCUMENTAR_COMO_HISTORICO | Integrada al schema final. |
| `database/legacy_pre_release_13B/migrations/009_corregir_nombre_script_contenedor.sql` | SQL | Correccion historica de nombre de script. | HISTORICO | DOCUMENTAR_COMO_HISTORICO | Integrada al comportamiento posterior. |
| `database/legacy_pre_release_13B/migrations/010_crear_configuracion_scheduler.sql` | SQL | Migracion configuracion scheduler. | HISTORICO | DOCUMENTAR_COMO_HISTORICO | Integrada al schema final. |
| `database/legacy_pre_release_13B/migrations/011_agregar_control_scheduler_ejecuciones.sql` | SQL | Control scheduler/ejecuciones. | HISTORICO | DOCUMENTAR_COMO_HISTORICO | Integrada al schema final. |
| `database/legacy_pre_release_13B/migrations/012_crear_calendario_feriados.sql` | SQL | Calendario local de feriados. | HISTORICO | DOCUMENTAR_COMO_HISTORICO | Integrada al schema final. |
| `database/legacy_pre_release_13B/migrations/013_crear_reglas_feriados_irrenunciables.sql` | SQL | Reglas irrenunciables. | HISTORICO | DOCUMENTAR_COMO_HISTORICO | Integrada al schema final. |
| `database/legacy_pre_release_13B/migrations/014_crear_scheduler_worker_heartbeat.sql` | SQL | Heartbeat worker. | HISTORICO | DOCUMENTAR_COMO_HISTORICO | Integrada al schema final. |
| `database/legacy_pre_release_13B/migrations/015_crear_eventos_programador.sql` | SQL | Eventos programador. | HISTORICO | DOCUMENTAR_COMO_HISTORICO | Integrada al schema final. |
| `database/legacy_pre_release_13B/migrations/016_agregar_snapshots_historial_borrado_operativo.sql` | SQL | Snapshots historicos para borrado operativo. | HISTORICO | DOCUMENTAR_COMO_HISTORICO | Integrada al schema final. |
| `database/legacy_pre_release_13B/migrations/017_desacople_historico_papelera.sql` | SQL | Desacople historico papelera. | HISTORICO | DOCUMENTAR_COMO_HISTORICO | Integrada al schema final. |
| `database/legacy_pre_release_13B/migrations/018_crear_o_ajustar_auditoria_cambios.sql` | SQL | Auditoria cambios. | HISTORICO | DOCUMENTAR_COMO_HISTORICO | Integrada al schema final. |
| `database/legacy_pre_release_13B/seeds/001_datos_iniciales_catalogos.sql` | SQL | Seeds historicos de catalogos. | HISTORICO | DOCUMENTAR_COMO_HISTORICO | Reemplazado por `004_seed_catalogos_base.sql`. |
| `database/legacy_pre_release_13B/seeds/002_roles_permisos_iniciales.sql` | SQL | Seeds historicos iniciales de roles/permisos. | HISTORICO | DOCUMENTAR_COMO_HISTORICO | Reemplazado por `003_seed_roles_permisos.sql`. |
| `database/legacy_pre_release_13B/seeds/003_permisos_mantenedores.sql` | SQL | Permisos incrementales mantenedores. | HISTORICO | DOCUMENTAR_COMO_HISTORICO | Consolidado en release. |
| `database/legacy_pre_release_13B/seeds/004_permisos_tareas.sql` | SQL | Permisos incrementales tareas. | HISTORICO | DOCUMENTAR_COMO_HISTORICO | Consolidado en release. |
| `database/legacy_pre_release_13B/seeds/005_permisos_scripts.sql` | SQL | Permisos incrementales scripts. | HISTORICO | DOCUMENTAR_COMO_HISTORICO | Consolidado en release. |
| `database/legacy_pre_release_13B/seeds/006_permisos_ejecuciones.sql` | SQL | Permisos incrementales ejecuciones. | HISTORICO | DOCUMENTAR_COMO_HISTORICO | Consolidado en release. |
| `database/legacy_pre_release_13B/seeds/007_permisos_scheduler.sql` | SQL | Permisos incrementales scheduler. | HISTORICO | DOCUMENTAR_COMO_HISTORICO | Consolidado en release. |
| `database/legacy_pre_release_13B/seeds/008_permisos_feriados.sql` | SQL | Permisos incrementales feriados. | HISTORICO | DOCUMENTAR_COMO_HISTORICO | Consolidado en release. |
| `database/legacy_pre_release_13B/seeds/009_reglas_irrenunciables_chile.sql` | SQL | Reglas historicas feriados Chile. | HISTORICO | DOCUMENTAR_COMO_HISTORICO | Consolidado en `006_seed_feriados_base.sql`. |
| `database/legacy_pre_release_13B/seeds/010_permisos_sincronizacion_feriados.sql` | SQL | Permisos sincronizacion feriados. | HISTORICO | DOCUMENTAR_COMO_HISTORICO | Consolidado en release. |
| `database/legacy_pre_release_13B/seeds/011_permisos_papelera.sql` | SQL | Permisos papelera. | HISTORICO | DOCUMENTAR_COMO_HISTORICO | Consolidado en release. |
| `database/legacy_pre_release_13B/seeds/012_permisos_auditoria.sql` | SQL | Permisos auditoria. | HISTORICO | DOCUMENTAR_COMO_HISTORICO | Consolidado en release. |

## Resultado

- No se elimino ningun archivo historico.
- `database/release/` queda como unica fuente oficial para instalacion limpia.
- `database/legacy_pre_release_13B/` conserva trazabilidad pre-release.
- No se detectaron scripts sueltos en la raiz de `database/`.

