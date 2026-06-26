/*
Release SQL limpio - APP Scheduler
Script: 000_ejecutar_instalacion_completa.sql
Objetivo: ejecutar la instalacion completa desde un unico script maestro.

IMPORTANTE:
- Activar en SSMS: Query > SQLCMD Mode.
- Cambiar DB_NAME solo en este archivo para instalar en otra base.
- No apuntar a APP_SCHEDULER_QA salvo decision explicita, manual y con respaldo.
- No ejecutar sobre bases con datos reales sin respaldo.
- Ejecutar este archivo desde la carpeta database/release/ para que las rutas :r relativas funcionen.
*/

:setvar DB_NAME "APP_SCHEDULER_TEST_INSTALL"

SELECT
    N'$(DB_NAME)' AS base_destino_configurada,
    N'Inicio de instalacion completa APP Scheduler release SQL.' AS resultado;
GO

:r .\001_crear_base_datos.sql
:r .\002_schema_final.sql
:r .\003_seed_roles_permisos.sql
:r .\004_seed_catalogos_base.sql
:r .\005_seed_configuracion_inicial.sql
:r .\006_seed_feriados_base.sql
:r .\099_validacion_instalacion.sql
