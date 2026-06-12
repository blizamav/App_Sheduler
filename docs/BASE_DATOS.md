# Base de datos

## Nombre de la base

`APP_SCHEDULER_QA`, configurable mediante `DB_DATABASE`.

## Estado

Pendiente de implementacion. En Fase 1 no se crean tablas ni conexion activa.

## Tablas objetivo

* usuarios
* roles
* permisos
* usuarios_roles
* clientes
* categorias
* tipos
* tareas
* programaciones
* scripts
* ejecuciones
* logs_tareas
* logs_sistema
* auditoria_cambios
* configuracion_sistema

## Relaciones

Pendiente de propuesta formal en Fase 3.

## Campos e indices

Todas las tablas deberan incluir claves primarias, claves foraneas, indices pertinentes y campos de auditoria `created_at` y `updated_at`.

## Scripts SQL

Pendientes para Fase 3.

## Consideraciones de integridad

No se permitiran registros huerfanos. La normalizacion de clientes, categorias y tipos evitara duplicados innecesarios.
