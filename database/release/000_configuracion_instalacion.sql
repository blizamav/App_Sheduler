/*
Release SQL limpio - APP Scheduler
Script: 000_configuracion_instalacion.sql
Objetivo: definir la base destino del paquete release mediante SQLCMD.

IMPORTANTE:
- Activar en SSMS: Query > SQLCMD Mode.
- Cambiar DB_NAME para instalar en otra base.
- Ejecutar los scripts del release en la misma sesion SQLCMD.
- No apuntar a APP_SCHEDULER_QA salvo decision explicita, manual y con respaldo.
- No ejecutar sobre bases con datos reales sin respaldo.
*/

:setvar DB_NAME "APP_SCHEDULER_TEST_INSTALL"

SELECT
    N'$(DB_NAME)' AS base_destino_configurada,
    N'Variable SQLCMD DB_NAME configurada. Continuar con 001_crear_base_datos.sql.' AS resultado;
GO
