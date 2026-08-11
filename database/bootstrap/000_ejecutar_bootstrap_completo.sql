/*
    Bootstrap limpio oficial de APP Scheduler.

    Ejecutar desde la raiz del repositorio con SQLCMD Mode habilitado.
    Cambiar solo DB_NAME. Usar exclusivamente una base nueva/desechable.
*/

:on error exit
:setvar DB_NAME "APP_SCHEDULER_BOOTSTRAP_TEST"

:r .\database\release\001_crear_base_datos.sql
:r .\database\release\002_schema_final.sql
:r .\database\release\003_seed_roles_permisos.sql
:r .\database\release\004_seed_catalogos_base.sql
:r .\database\release\005_seed_configuracion_inicial.sql
:r .\database\release\006_seed_feriados_base.sql
:r .\database\bootstrap\007_crear_notificaciones_evidencias.sql
:r .\database\bootstrap\008_crear_configuracion_mail_graph.sql
:r .\database\bootstrap\009_seed_configuracion_mail_graph.sql
:r .\database\bootstrap\010_seed_permisos_mantenedores.sql
:r .\database\bootstrap\100_validacion_bootstrap_actual.sql
