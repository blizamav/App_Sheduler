/*
Release SQL limpio - APP Scheduler
Script: 006_seed_feriados_base.sql
Objetivo: cargar reglas base de feriados irrenunciables.
No carga feriados por fecha ni consulta APIs externas.
*/

USE APP_SCHEDULER_TEST_INSTALL;
GO

MERGE dbo.reglas_feriados_irrenunciables AS destino
USING (VALUES
    (N'CL', 1, 1, N'Ano Nuevo', 1, N'Regla local Chile.'),
    (N'CL', 5, 1, N'Dia del Trabajo', 1, N'Regla local Chile.'),
    (N'CL', 9, 18, N'Fiestas Patrias / Independencia Nacional', 1, N'Regla local Chile.'),
    (N'CL', 9, 19, N'Dia de las Glorias del Ejercito', 1, N'Regla local Chile.'),
    (N'CL', 12, 25, N'Navidad', 1, N'Regla local Chile.')
) AS origen(pais, mes, dia, nombre_referencia, irrenunciable, observacion)
ON destino.pais = origen.pais
   AND destino.mes = origen.mes
   AND destino.dia = origen.dia
   AND destino.activo = 1
WHEN MATCHED THEN
    UPDATE SET nombre_referencia = origen.nombre_referencia,
               irrenunciable = origen.irrenunciable,
               observacion = origen.observacion,
               fecha_actualizacion = SYSDATETIME(),
               usuario_actualizacion = N'release_seed'
WHEN NOT MATCHED THEN
    INSERT (pais, mes, dia, nombre_referencia, irrenunciable, activo, observacion, usuario_creacion)
    VALUES (origen.pais, origen.mes, origen.dia, origen.nombre_referencia, origen.irrenunciable, 1, origen.observacion, N'release_seed');
GO
