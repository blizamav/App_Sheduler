USE APP_SCHEDULER_QA;
GO

/*
    Fase 7.5 - Correccion de nombre de contenedor de scripts.

    Objetivo:
    - Corregir registros existentes donde scripts.nombre_script quedo con el nombre
      del primer archivo .py cargado.
    - Mantener los archivos reales exclusivamente en scripts_versiones.nombre_archivo.

    Importante:
    - No modifica scripts_versiones.
    - No modifica rutas fisicas ni relativas.
    - No toca archivos cargados.
    - Es idempotente: solo actualiza registros cuyo nombre_script parece terminar en .py.
*/

UPDATE s
SET
    s.nombre_script = CONCAT(N'Script de ', t.nombre_tarea),
    s.fecha_actualizacion = SYSDATETIME()
FROM dbo.scripts s
INNER JOIN dbo.tareas t ON t.id_tarea = s.id_tarea
WHERE LOWER(LTRIM(RTRIM(s.nombre_script))) LIKE '%.py';
GO
