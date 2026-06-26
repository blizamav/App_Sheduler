/*
Fase 10B - APP Scheduler
Seed: 009_reglas_irrenunciables_chile.sql
Objetivo: cargar reglas locales iniciales de feriados irrenunciables para Chile.
Nota: ejecutar manualmente en SSMS. No modifica seeds anteriores.
*/

USE APP_SCHEDULER_QA;
GO

MERGE dbo.reglas_feriados_irrenunciables AS destino
USING (VALUES
    ('CL', 1, 1, 'Ano Nuevo', 1, 'Regla local Chile.'),
    ('CL', 5, 1, 'Dia del Trabajo', 1, 'Regla local Chile.'),
    ('CL', 9, 18, 'Fiestas Patrias / Independencia Nacional', 1, 'Regla local Chile.'),
    ('CL', 9, 19, 'Dia de las Glorias del Ejercito', 1, 'Regla local Chile.'),
    ('CL', 12, 25, 'Navidad', 1, 'Regla local Chile.')
) AS origen(pais, mes, dia, nombre_referencia, irrenunciable, observacion)
ON destino.pais = origen.pais
   AND destino.mes = origen.mes
   AND destino.dia = origen.dia
   AND destino.activo = 1
WHEN MATCHED THEN
    UPDATE SET
        nombre_referencia = origen.nombre_referencia,
        irrenunciable = origen.irrenunciable,
        observacion = origen.observacion,
        fecha_actualizacion = SYSDATETIME(),
        usuario_actualizacion = N'seed_009'
WHEN NOT MATCHED THEN
    INSERT (pais, mes, dia, nombre_referencia, irrenunciable, activo, observacion, usuario_creacion)
    VALUES (origen.pais, origen.mes, origen.dia, origen.nombre_referencia, origen.irrenunciable, 1, origen.observacion, N'seed_009');
GO
