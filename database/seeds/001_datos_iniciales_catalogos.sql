/*
Fase 3B - APP Scheduler
Seed: 001_datos_iniciales_catalogos.sql
Objetivo: poblar catalogos base de forma idempotente.
*/

USE APP_SCHEDULER_QA;
GO

MERGE dbo.cat_estados_tarea AS destino
USING (VALUES
    ('ACTIVA', N'Activa', N'Tarea disponible para ejecucion.'),
    ('INACTIVA', N'Inactiva', N'Tarea deshabilitada.'),
    ('SUSPENDIDA', N'Suspendida', N'Tarea pausada temporalmente.'),
    ('EN_EJECUCION', N'En ejecucion', N'Tarea ejecutandose.'),
    ('ERROR', N'Error', N'Tarea con error reciente.'),
    ('FINALIZADA', N'Finalizada', N'Tarea finalizada.')
) AS origen(codigo, nombre, descripcion)
ON destino.codigo = origen.codigo
WHEN NOT MATCHED THEN
    INSERT (codigo, nombre, descripcion, usuario_creacion)
    VALUES (origen.codigo, origen.nombre, origen.descripcion, N'seed');
GO

MERGE dbo.cat_estados_ejecucion AS destino
USING (VALUES
    ('PENDIENTE', N'Pendiente', N'Ejecucion pendiente.'),
    ('EN_EJECUCION', N'En ejecucion', N'Ejecucion en curso.'),
    ('EXITOSA', N'Exitosa', N'Ejecucion terminada correctamente.'),
    ('ERROR', N'Error', N'Ejecucion con error.'),
    ('CANCELADA', N'Cancelada', N'Ejecucion cancelada.'),
    ('OMITIDA', N'Omitida', N'Ejecucion omitida.'),
    ('OMITIDA_FERIADO', N'Omitida por feriado', N'Ejecucion omitida por feriado.'),
    ('OMITIDA_FIN_SEMANA', N'Omitida fin de semana', N'Ejecucion omitida por fin de semana.')
) AS origen(codigo, nombre, descripcion)
ON destino.codigo = origen.codigo
WHEN NOT MATCHED THEN
    INSERT (codigo, nombre, descripcion, usuario_creacion)
    VALUES (origen.codigo, origen.nombre, origen.descripcion, N'seed');
GO

MERGE dbo.cat_tipos_programacion AS destino
USING (VALUES
    ('DIARIA', N'Diaria', N'Ejecucion diaria a una hora.'),
    ('SEMANAL', N'Semanal', N'Ejecucion semanal.'),
    ('MENSUAL', N'Mensual', N'Ejecucion mensual.'),
    ('FECHAS_ESPECIFICAS', N'Fechas especificas', N'Ejecucion en fechas definidas.'),
    ('INTERVALO_DIARIO', N'Intervalo diario', N'Ejecucion por intervalo en rango horario.'),
    ('MANUAL', N'Manual', N'Sin programacion automatica.')
) AS origen(codigo, nombre, descripcion)
ON destino.codigo = origen.codigo
WHEN NOT MATCHED THEN
    INSERT (codigo, nombre, descripcion, usuario_creacion)
    VALUES (origen.codigo, origen.nombre, origen.descripcion, N'seed');
GO

MERGE dbo.cat_niveles_log AS destino
USING (VALUES
    ('INFO', N'Informativo', N'Evento informativo.'),
    ('WARNING', N'Advertencia', N'Evento de advertencia.'),
    ('ERROR', N'Error', N'Evento de error.'),
    ('CRITICAL', N'Critico', N'Evento critico.')
) AS origen(codigo, nombre, descripcion)
ON destino.codigo = origen.codigo
WHEN NOT MATCHED THEN
    INSERT (codigo, nombre, descripcion, usuario_creacion)
    VALUES (origen.codigo, origen.nombre, origen.descripcion, N'seed');
GO

MERGE dbo.cat_tipos_tarea AS destino
USING (VALUES
    ('PROGRAMADA', N'Programada', N'Tarea con ejecucion automatica.'),
    ('MANUAL', N'Manual', N'Tarea de ejecucion manual.')
) AS origen(codigo, nombre, descripcion)
ON destino.codigo = origen.codigo
WHEN NOT MATCHED THEN
    INSERT (codigo, nombre, descripcion, usuario_creacion)
    VALUES (origen.codigo, origen.nombre, origen.descripcion, N'seed');
GO

MERGE dbo.cat_estados_version_script AS destino
USING (VALUES
    ('ACTIVA', N'Activa', N'Version usada por ejecucion automatica.'),
    ('DISPONIBLE', N'Disponible', N'Version seleccionable manualmente.'),
    ('REEMPLAZADA', N'Reemplazada', N'Version conservada para trazabilidad, no cuenta como disponible.'),
    ('INACTIVA', N'Inactiva', N'Version deshabilitada.')
) AS origen(codigo, nombre, descripcion)
ON destino.codigo = origen.codigo
WHEN NOT MATCHED THEN
    INSERT (codigo, nombre, descripcion, usuario_creacion)
    VALUES (origen.codigo, origen.nombre, origen.descripcion, N'seed');
GO
