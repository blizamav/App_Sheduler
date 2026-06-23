/*
Release SQL limpio - APP Scheduler
Script: 004_seed_catalogos_base.sql
Objetivo: cargar catalogos base del sistema.
No incluye datos de negocio, tareas, scripts ni ejecuciones.
*/

USE APP_SCHEDULER_QA;
GO

MERGE dbo.cat_estados_tarea AS destino
USING (VALUES
    (N'ACTIVA', N'Tarea habilitada para uso.'),
    (N'INACTIVA', N'Tarea no disponible.'),
    (N'SUSPENDIDA', N'Tarea suspendida temporalmente.'),
    (N'ELIMINADA', N'Tarea marcada como eliminada operativamente.')
) AS origen(codigo, descripcion)
ON destino.codigo = origen.codigo
WHEN MATCHED THEN UPDATE SET descripcion = origen.descripcion, fecha_actualizacion = SYSDATETIME()
WHEN NOT MATCHED THEN INSERT (codigo, descripcion) VALUES (origen.codigo, origen.descripcion);
GO

MERGE dbo.cat_estados_ejecucion AS destino
USING (VALUES
    (N'PENDIENTE', N'Ejecucion creada y pendiente.'),
    (N'EN_EJECUCION', N'Ejecucion actualmente en curso.'),
    (N'EXITOSA', N'Ejecucion finalizada correctamente.'),
    (N'ERROR', N'Ejecucion finalizada con error.'),
    (N'CANCELADA', N'Ejecucion cancelada.'),
    (N'DETENIDA_MANUALMENTE', N'Ejecucion detenida por accion manual.')
) AS origen(codigo, descripcion)
ON destino.codigo = origen.codigo
WHEN MATCHED THEN UPDATE SET descripcion = origen.descripcion, fecha_actualizacion = SYSDATETIME()
WHEN NOT MATCHED THEN INSERT (codigo, descripcion) VALUES (origen.codigo, origen.descripcion);
GO

MERGE dbo.cat_tipos_programacion AS destino
USING (VALUES
    (N'MANUAL', N'Ejecucion manual.'),
    (N'UNICA', N'Ejecucion una sola vez.'),
    (N'DIARIA', N'Ejecucion diaria.'),
    (N'SEMANAL', N'Ejecucion semanal.'),
    (N'MENSUAL', N'Ejecucion mensual.'),
    (N'FECHAS_ESPECIFICAS', N'Ejecucion en fechas especificas.'),
    (N'FECHA_ESPECIFICA', N'Ejecucion en una fecha especifica.')
) AS origen(codigo, descripcion)
ON destino.codigo = origen.codigo
WHEN MATCHED THEN UPDATE SET descripcion = origen.descripcion, fecha_actualizacion = SYSDATETIME()
WHEN NOT MATCHED THEN INSERT (codigo, descripcion) VALUES (origen.codigo, origen.descripcion);
GO

MERGE dbo.cat_niveles_log AS destino
USING (VALUES
    (N'INFO', N'Informacion general.'),
    (N'WARNING', N'Advertencia.'),
    (N'ERROR', N'Error.'),
    (N'DEBUG', N'Detalle tecnico.')
) AS origen(codigo, descripcion)
ON destino.codigo = origen.codigo
WHEN MATCHED THEN UPDATE SET descripcion = origen.descripcion, fecha_actualizacion = SYSDATETIME()
WHEN NOT MATCHED THEN INSERT (codigo, descripcion) VALUES (origen.codigo, origen.descripcion);
GO

MERGE dbo.cat_tipos_tarea AS destino
USING (VALUES
    (N'PYTHON', N'Script Python.'),
    (N'BAT', N'Archivo batch Windows.'),
    (N'POWERSHELL', N'Script PowerShell.'),
    (N'OTRO', N'Otro tipo de tarea.')
) AS origen(codigo, descripcion)
ON destino.codigo = origen.codigo
WHEN MATCHED THEN UPDATE SET descripcion = origen.descripcion, fecha_actualizacion = SYSDATETIME()
WHEN NOT MATCHED THEN INSERT (codigo, descripcion) VALUES (origen.codigo, origen.descripcion);
GO

MERGE dbo.cat_estados_version_script AS destino
USING (VALUES
    (N'ACTIVA', N'Version activa para ejecucion automatica.'),
    (N'DISPONIBLE', N'Version disponible para seleccion manual o activacion.'),
    (N'REEMPLAZADA', N'Version reemplazada; no cuenta como disponible.'),
    (N'INACTIVA', N'Version deshabilitada sin eliminacion fisica.')
) AS origen(codigo, descripcion)
ON destino.codigo = origen.codigo
WHEN MATCHED THEN UPDATE SET descripcion = origen.descripcion, fecha_actualizacion = SYSDATETIME()
WHEN NOT MATCHED THEN INSERT (codigo, descripcion) VALUES (origen.codigo, origen.descripcion);
GO
