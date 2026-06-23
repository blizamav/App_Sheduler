/*
Release SQL limpio - APP Scheduler
Script: 005_seed_configuracion_inicial.sql
Objetivo: cargar configuracion inicial segura.
No incluye credenciales, servidores ni rutas locales.
*/

USE APP_SCHEDULER_QA;
GO

IF NOT EXISTS (SELECT 1 FROM dbo.configuracion_scheduler WHERE activo = 1)
BEGIN
    INSERT INTO dbo.configuracion_scheduler (
        scheduler_activo,
        permitir_ejecucion_automatica,
        intervalo_revision_segundos,
        max_ejecuciones_concurrentes,
        modo_mantenimiento,
        observacion,
        activo,
        usuario_creacion
    )
    VALUES (
        0,
        0,
        60,
        3,
        0,
        N'Configuracion inicial segura generada por release limpio. Worker apagado por defecto.',
        1,
        N'release_seed'
    );
END;
GO

IF NOT EXISTS (SELECT 1 FROM dbo.configuracion_sistema WHERE clave = N'RELEASE_SQL')
BEGIN
    INSERT INTO dbo.configuracion_sistema (clave, valor, descripcion, usuario_creacion)
    VALUES (N'RELEASE_SQL', N'13A', N'Instalacion desde release SQL limpio.', N'release_seed');
END;
GO
