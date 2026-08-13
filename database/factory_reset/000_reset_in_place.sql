/* Factory Reset in-place transaccional. Ejecutar solo mediante el motor APP Scheduler. */
:on error exit

USE [$(DB_NAME)];
GO

SET NOCOUNT ON;
SET XACT_ABORT ON;
SET LOCK_TIMEOUT $(LOCK_TIMEOUT_MS);

IF DB_NAME() <> N'$(DB_NAME)'
BEGIN
    THROW 51000, N'El contexto de base no coincide con el target autorizado.', 1;
END;
IF DATABASEPROPERTYEX(DB_NAME(), N'Updateability') <> N'READ_WRITE'
BEGIN
    THROW 51000, N'La base objetivo no esta en modo READ_WRITE.', 1;
END;
IF ISNULL(IS_ROLEMEMBER(N'db_owner'), 0) <> 1
BEGIN
    THROW 51000, N'La cuenta SQL de mantenimiento no pertenece a db_owner en la base objetivo.', 1;
END;

BEGIN TRANSACTION;

DECLARE @resultado_applock int;
EXEC @resultado_applock = sys.sp_getapplock
    @Resource = N'APP_SCHEDULER_FACTORY_RESET_IN_PLACE',
    @LockMode = N'Exclusive',
    @LockOwner = N'Transaction',
    @LockTimeout = $(LOCK_TIMEOUT_MS);
IF @resultado_applock < 0
BEGIN
    THROW 51000, N'No fue posible adquirir el bloqueo exclusivo interno de Factory Reset.', 1;
END;
GO

PRINT N'FACTORY_SCRIPT|001_eliminar_esquema_aplicativo.sql';
:r ./database/factory_reset/001_eliminar_esquema_aplicativo.sql
PRINT N'FACTORY_SCRIPT|002_schema_final.sql';
:r ./database/release/002_schema_final.sql
PRINT N'FACTORY_SCRIPT|003_seed_roles_permisos.sql';
:r ./database/release/003_seed_roles_permisos.sql
PRINT N'FACTORY_SCRIPT|004_seed_catalogos_base.sql';
:r ./database/release/004_seed_catalogos_base.sql
PRINT N'FACTORY_SCRIPT|005_seed_configuracion_inicial.sql';
:r ./database/release/005_seed_configuracion_inicial.sql
PRINT N'FACTORY_SCRIPT|006_seed_feriados_base.sql';
:r ./database/release/006_seed_feriados_base.sql
PRINT N'FACTORY_SCRIPT|007_crear_notificaciones_evidencias.sql';
:r ./database/bootstrap/007_crear_notificaciones_evidencias.sql
PRINT N'FACTORY_SCRIPT|008_crear_configuracion_mail_graph.sql';
:r ./database/bootstrap/008_crear_configuracion_mail_graph.sql
PRINT N'FACTORY_SCRIPT|009_seed_configuracion_mail_graph.sql';
:r ./database/bootstrap/009_seed_configuracion_mail_graph.sql
PRINT N'FACTORY_SCRIPT|010_seed_permisos_mantenedores.sql';
:r ./database/bootstrap/010_seed_permisos_mantenedores.sql
PRINT N'FACTORY_SCRIPT|011_seed_permiso_factory_reset.sql';
:r ./database/bootstrap/011_seed_permiso_factory_reset.sql
PRINT N'FACTORY_SCRIPT|100_validacion_bootstrap_actual.sql';
:r ./database/bootstrap/100_validacion_bootstrap_actual.sql

INSERT INTO dbo.logs_sistema (usuario, accion, modulo, descripcion, valor_nuevo, nivel)
VALUES (N'$(RESET_USER)', N'FACTORY_RESET_COMPLETADO', N'FACTORY_RESET',
        N'APP Scheduler fue restablecido in-place.', N'operation_id=$(OPERATION_ID);version=$(APP_VERSION)', N'INFO');

INSERT INTO dbo.auditoria_cambios
    (usuario, accion, entidad, id_entidad, descripcion, valores_despues, resultado, modulo, activo)
VALUES (N'$(RESET_USER)', N'FACTORY_RESET_COMPLETADO', N'SISTEMA', N'$(OPERATION_ID)',
        N'Instalacion reconstruida in-place desde bootstrap oficial.', N'version=$(APP_VERSION)',
        N'OK', N'Factory Reset', 1);

COMMIT TRANSACTION;
SELECT N'FACTORY_IN_PLACE_COMMIT_OK' AS resultado, DB_NAME() AS base_restaurada;
GO
