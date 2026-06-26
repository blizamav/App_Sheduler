/*
Release SQL limpio - APP Scheduler
Script: 005_seed_configuracion_inicial.sql
Objetivo: cargar configuracion inicial segura.
No incluye credenciales, servidores ni rutas locales.
*/

USE APP_SCHEDULER_TEST_INSTALL;
GO

IF NOT EXISTS (SELECT 1 FROM dbo.configuracion_scheduler WHERE activo = 1)
BEGIN
    INSERT INTO dbo.configuracion_scheduler (
        scheduler_activo,
        intervalo_revision_segundos,
        max_ejecuciones_concurrentes,
        permitir_ejecucion_automatica,
        modo_mantenimiento,
        nombre_worker_principal,
        descripcion,
        activo,
        usuario_actualizacion
    )
    VALUES (
        0,
        60,
        3,
        0,
        0,
        N'worker_default',
        N'Configuracion inicial segura generada por release limpio. Worker apagado por defecto.',
        1,
        N'release_seed'
    );
END;
GO

IF NOT EXISTS (SELECT 1 FROM dbo.configuracion_sistema WHERE clave = N'RELEASE_SQL')
BEGIN
    INSERT INTO dbo.configuracion_sistema (clave, valor, tipo_dato, descripcion, es_sensible, usuario_creacion)
    VALUES (N'RELEASE_SQL', N'13B.1', N'TEXTO', N'Instalacion desde release SQL limpio validado para prueba en base nueva.', 0, N'release_seed');
END;
GO
