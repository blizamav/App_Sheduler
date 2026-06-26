/*
Release SQL limpio - APP Scheduler
Script: 004_seed_catalogos_base.sql
Objetivo: cargar catalogos base del sistema.
No incluye datos de negocio, tareas, scripts ni ejecuciones.
*/

USE APP_SCHEDULER_TEST_INSTALL;
GO

MERGE dbo.cat_estados_tarea AS destino
USING (VALUES
    (N'ACTIVA', N'Activa', N'Tarea habilitada para uso.'),
    (N'INACTIVA', N'Inactiva', N'Tarea no disponible.'),
    (N'SUSPENDIDA', N'Suspendida', N'Tarea suspendida temporalmente.'),
    (N'ELIMINADA', N'Eliminada', N'Tarea marcada como eliminada operativamente.')
) AS origen(codigo, nombre, descripcion)
ON destino.codigo = origen.codigo
WHEN MATCHED THEN
    UPDATE SET nombre = origen.nombre,
               descripcion = origen.descripcion,
               fecha_actualizacion = SYSDATETIME(),
               usuario_actualizacion = N'release_seed'
WHEN NOT MATCHED THEN
    INSERT (codigo, nombre, descripcion, usuario_creacion)
    VALUES (origen.codigo, origen.nombre, origen.descripcion, N'release_seed');
GO

MERGE dbo.cat_estados_ejecucion AS destino
USING (VALUES
    (N'PENDIENTE', N'Pendiente', N'Ejecucion creada y pendiente.'),
    (N'EN_EJECUCION', N'En ejecucion', N'Ejecucion actualmente en curso.'),
    (N'EXITOSA', N'Exitosa', N'Ejecucion finalizada correctamente.'),
    (N'ERROR', N'Error', N'Ejecucion finalizada con error.'),
    (N'CANCELADA', N'Cancelada', N'Ejecucion cancelada.'),
    (N'DETENIDA_MANUALMENTE', N'Detenida manualmente', N'Ejecucion detenida por accion manual.')
) AS origen(codigo, nombre, descripcion)
ON destino.codigo = origen.codigo
WHEN MATCHED THEN
    UPDATE SET nombre = origen.nombre,
               descripcion = origen.descripcion,
               fecha_actualizacion = SYSDATETIME(),
               usuario_actualizacion = N'release_seed'
WHEN NOT MATCHED THEN
    INSERT (codigo, nombre, descripcion, usuario_creacion)
    VALUES (origen.codigo, origen.nombre, origen.descripcion, N'release_seed');
GO

MERGE dbo.cat_tipos_programacion AS destino
USING (VALUES
    (N'MANUAL', N'Manual', N'Ejecucion manual.'),
    (N'DIARIA', N'Diaria', N'Ejecucion diaria.'),
    (N'SEMANAL', N'Semanal', N'Ejecucion semanal.'),
    (N'MENSUAL', N'Mensual', N'Ejecucion mensual.'),
    (N'FECHA_ESPECIFICA', N'Fecha especifica', N'Ejecucion en una fecha especifica.'),
    (N'FECHAS_ESPECIFICAS', N'Fechas especificas', N'Ejecucion en fechas especificas.')
) AS origen(codigo, nombre, descripcion)
ON destino.codigo = origen.codigo
WHEN MATCHED THEN
    UPDATE SET nombre = origen.nombre,
               descripcion = origen.descripcion,
               fecha_actualizacion = SYSDATETIME(),
               usuario_actualizacion = N'release_seed'
WHEN NOT MATCHED THEN
    INSERT (codigo, nombre, descripcion, usuario_creacion)
    VALUES (origen.codigo, origen.nombre, origen.descripcion, N'release_seed');
GO

MERGE dbo.cat_niveles_log AS destino
USING (VALUES
    (N'INFO', N'Informativo', N'Informacion general.'),
    (N'WARNING', N'Advertencia', N'Advertencia operativa.'),
    (N'ERROR', N'Error', N'Error controlado.'),
    (N'CRITICAL', N'Critico', N'Evento critico.'),
    (N'DEBUG', N'Debug', N'Detalle tecnico.')
) AS origen(codigo, nombre, descripcion)
ON destino.codigo = origen.codigo
WHEN MATCHED THEN
    UPDATE SET nombre = origen.nombre,
               descripcion = origen.descripcion,
               fecha_actualizacion = SYSDATETIME(),
               usuario_actualizacion = N'release_seed'
WHEN NOT MATCHED THEN
    INSERT (codigo, nombre, descripcion, usuario_creacion)
    VALUES (origen.codigo, origen.nombre, origen.descripcion, N'release_seed');
GO

MERGE dbo.cat_tipos_tarea AS destino
USING (VALUES
    (N'MANUAL', N'Manual', N'Tarea de ejecucion manual.'),
    (N'PROGRAMADA', N'Programada', N'Tarea con programacion automatica.')
) AS origen(codigo, nombre, descripcion)
ON destino.codigo = origen.codigo
WHEN MATCHED THEN
    UPDATE SET nombre = origen.nombre,
               descripcion = origen.descripcion,
               fecha_actualizacion = SYSDATETIME(),
               usuario_actualizacion = N'release_seed'
WHEN NOT MATCHED THEN
    INSERT (codigo, nombre, descripcion, usuario_creacion)
    VALUES (origen.codigo, origen.nombre, origen.descripcion, N'release_seed');
GO

MERGE dbo.cat_estados_version_script AS destino
USING (VALUES
    (N'ACTIVA', N'Activa', N'Version activa para ejecucion automatica.'),
    (N'DISPONIBLE', N'Disponible', N'Version disponible para seleccion manual o activacion.'),
    (N'REEMPLAZADA', N'Reemplazada', N'Version reemplazada; no cuenta como disponible.'),
    (N'INACTIVA', N'Inactiva', N'Version deshabilitada sin eliminacion fisica.')
) AS origen(codigo, nombre, descripcion)
ON destino.codigo = origen.codigo
WHEN MATCHED THEN
    UPDATE SET nombre = origen.nombre,
               descripcion = origen.descripcion,
               fecha_actualizacion = SYSDATETIME(),
               usuario_actualizacion = N'release_seed'
WHEN NOT MATCHED THEN
    INSERT (codigo, nombre, descripcion, usuario_creacion)
    VALUES (origen.codigo, origen.nombre, origen.descripcion, N'release_seed');
GO
