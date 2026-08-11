# Bootstrap de instalacion limpia

## Estado

El bootstrap actual fue ejecutado manualmente desde cero sobre `APP_SCHEDULER_BOOTSTRAP_TEST`. Los scripts 001-010 finalizaron correctamente y, tras alinear la matriz de catalogos del script 100 con el seed oficial 004, la validacion final retorno `BOOTSTRAP_ACTUAL | OK | APP_SCHEDULER_BOOTSTRAP_TEST | 33` sin `THROW`.

El smoke test Flask tambien fue completado: login `SUPER_ADMIN_ENV`, rutas principales, alta integral de tarea con script v1, vista real de scripts por tarea y eliminacion permanente funcionaron contra la base bootstrap. La base y el filesystem regresaron a estado virgen y el script 100 volvio a finalizar `OK`. Fase 19B queda validada; Factory Reset aun no esta implementado.

## Fuente de verdad

La fuente ejecutable es `database/bootstrap/manifest.json`. El script `000_ejecutar_bootstrap_completo.sql` refleja el mismo orden para SQLCMD.

El bootstrap reutiliza `database/release/001-006` como base publicada e inmutable. Las funcionalidades posteriores se agregan mediante definiciones limpias en `database/bootstrap/`; no se altera el release historico ni se ejecutan migraciones correctivas de ambiente.

## Orden

| Orden | Archivo | Tipo | Objetivo |
|---:|---|---|---|
| 1 | `database/release/001_crear_base_datos.sql` | DDL | Crear la base nueva. |
| 2 | `database/release/002_schema_final.sql` | DDL | Crear 28 tablas del esquema consolidado base. |
| 3 | `database/release/003_seed_roles_permisos.sql` | Seed | Roles, permisos y relaciones. |
| 4 | `database/release/004_seed_catalogos_base.sql` | Seed | Catalogos tecnicos. |
| 5 | `database/release/005_seed_configuracion_inicial.sql` | Seed | Scheduler y configuracion de sistema. |
| 6 | `database/release/006_seed_feriados_base.sql` | Seed | Reglas irrenunciables de Chile. |
| 7 | `database/bootstrap/007_crear_notificaciones_evidencias.sql` | DDL | Cuatro tablas de notificaciones/evidencias. |
| 8 | `database/bootstrap/008_crear_configuracion_mail_graph.sql` | DDL | Tabla global Mail Graph. |
| 9 | `database/bootstrap/009_seed_configuracion_mail_graph.sql` | Seed | Fila global segura y marca de version del bootstrap. |
| 10 | `database/bootstrap/010_seed_permisos_mantenedores.sql` | Seed | Completar la matriz vigente de mantenedores. |
| 100 | `database/bootstrap/100_validacion_bootstrap_actual.sql` | Validacion | Validacion del esquema actual de 33 tablas. |

## Migrations frente a bootstrap

`database/migrations/` contiene cambios incrementales para ambientes existentes. No representa por si sola una cadena de instalacion limpia. El bootstrap transforma el resultado final de `019` y `020` en DDL parametrizado para una base nueva.

`021_consolidar_configuracion_mail_graph_qa.sql` queda expresamente excluida: es una correccion de filas e IDs concretos de QA. No ejecutar en instalaciones limpias ni en Factory Reset.

## Seeds y estado inicial

Se crean los roles `SUPER_ADMIN`, `ADMIN`, `TI` y `TERCERO`, 51 permisos y su matriz vigente: `SUPER_ADMIN=51`, `ADMIN=49`, `TI=34`, `TERCERO=7`. El seed complementario incorpora la politica historica de mantenedores: administracion completa para SUPER_ADMIN/ADMIN y lectura para TI. Tambien se crean catalogos tecnicos, configuracion scheduler inactiva y reglas base de feriados. No se crean usuarios, clientes, categorias, tipos de negocio, tareas, scripts, ejecuciones, logs ni auditoria.

Mail Graph queda con una sola fila `MAIL_GRAPH`, inactiva, `client_secret_origen = ENV` y sin tenant, client ID, remitente ni destinatarios. Ningun secreto se persiste desde SQL.

`SUPER_ADMIN_ENV` sigue dependiendo exclusivamente de `USUARIO_ADMIN_DEFECTO` y `PASSWORD_ADMIN_DEFECTO`; no requiere usuario en BD.

## Inventario comparado

El inventario read-only de QA encontro 33 tablas, 462 columnas, 25 FK, 39 CHECK, 118 DEFAULT y 121 indices. El bootstrap limpio esperado tiene 33 tablas, 456 columnas, 25 FK, 38 CHECK, 117 DEFAULT y 119 indices. La diferencia corresponde a compatibilidad historica que no requiere el codigo actual: seis columnas antiguas de `auditoria_cambios`, su DEFAULT y dos indices, mas un CHECK redundante de `ejecuciones` cuyo contrato ya esta cubierto de forma mas estricta por el release.

* `notificaciones_config_tarea`
* `notificaciones_destinatarios`
* `evidencias_ejecucion`
* `notificaciones_envios`
* `configuracion_mail_graph`

No existen vistas ni procedimientos almacenados propios. Las columnas, FK, CHECK e indices de estas cinco tablas coinciden funcionalmente con `019/020`. La posicion ordinal de `clave_configuracion` en QA difiere por haber sido agregada mediante correccion incremental; no afecta el contrato funcional.

Se detecto ademas un drift funcional de seeds: QA tiene 39 permisos y carece de los 12 permisos de mantenedores exigidos por el backend. El release ya define los 51 permisos, pero no asigna esos 12 en su matriz. El bootstrap lo corrige fuera del release mediante `010_seed_permisos_mantenedores.sql`. El `099` historico no se ejecuta porque valida la matriz anterior; `100_validacion_bootstrap_actual.sql` lo reemplaza para el estado vigente.

## Validacion en base temporal

Nombre validado: `APP_SCHEDULER_BOOTSTRAP_TEST`.

1. El bootstrap 001-010 fue ejecutado manualmente sin errores sobre la base temporal.
2. El script 100 se corrigio para validar el contrato vigente de `004_seed_catalogos_base.sql`, sin alterar el seed ni el release.
3. La ejecucion aislada final del script 100 retorno `BOOTSTRAP_ACTUAL | OK | APP_SCHEDULER_BOOTSTRAP_TEST | 33`.
4. Flask uso un override de proceso `DB_DATABASE=APP_SCHEDULER_BOOTSTRAP_TEST` y un adaptador temporal en memoria por la incidencia ODBC `08001`; no se modificaron `.env` ni la capa de conexion permanente.
5. `SUPER_ADMIN_ENV` inicio sesion con `id_usuario = None`, rol esperado y permisos globales. Las rutas principales respondieron sin errores `500` ni incompatibilidades de tablas o columnas.
6. La gestion de scripts no posee listado global `/scripts/`. Su ruta real es `/tareas/<id_tarea>/scripts` y fue validada con HTTP `200` usando una tarea temporal creada por Flask.
7. El alta integral creo tarea, programacion, script y v1 activa con archivo `.py`; el borrado operativo y la eliminacion permanente retiraron los registros y el archivo mediante los flujos normales.
8. El dry-run final registro cero `.py` y `.env` huerfanos, cero carpetas vacias y cero rutas rechazadas. Tras el rollback del arnes, las tablas operativas, logs y auditoria quedaron nuevamente vacias.
9. Una ultima ejecucion exclusiva del script 100 confirmo `BOOTSTRAP_ACTUAL | OK | APP_SCHEDULER_BOOTSTRAP_TEST | 33`.

El bootstrap se define para una base nueva. Los scripts mantienen defensas de existencia, pero no se ofrece como mecanismo para reparar drift en una base usada.

## Relacion con Factory Reset

El futuro Factory Reset debe leer `manifest.json`; no debe mantener otra lista hardcodeada. Bootstrap, validaciones SQL y smoke test Flask ya fueron comprobados. Esta validacion no implementa Factory Reset ni inicia Fase 19C.
