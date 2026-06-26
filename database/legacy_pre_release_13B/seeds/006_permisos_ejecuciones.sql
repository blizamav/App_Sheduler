/*
Fase 8 - APP Scheduler
Seed: 006_permisos_ejecuciones.sql
Objetivo: agregar permisos incrementales para ejecucion manual, consola y detencion.
Nota: ejecutar manualmente en SSMS. No modifica seeds anteriores.
*/

USE APP_SCHEDULER_QA;
GO

MERGE dbo.permisos AS destino
USING (VALUES
    ('EJECUCIONES_VER', N'ejecuciones', N'ver', N'Ver consola y detalle de ejecuciones.'),
    ('EJECUCIONES_EJECUTAR', N'ejecuciones', N'ejecutar', N'Ejecutar manualmente tareas usando version activa.'),
    ('EJECUCIONES_DETENER', N'ejecuciones', N'detener', N'Detener ejecuciones manualmente.'),
    ('EJECUCIONES_LOG_VER', N'ejecuciones', N'log_ver', N'Ver log de ejecuciones.')
) AS origen(codigo_permiso, modulo, accion, descripcion)
ON destino.codigo_permiso = origen.codigo_permiso
WHEN NOT MATCHED THEN
    INSERT (codigo_permiso, modulo, accion, descripcion, usuario_creacion)
    VALUES (origen.codigo_permiso, origen.modulo, origen.accion, origen.descripcion, N'seed_006');
GO

INSERT INTO dbo.roles_permisos (id_rol, id_permiso, permitido, usuario_creacion)
SELECT r.id_rol, p.id_permiso, 1, N'seed_006'
FROM dbo.roles r
JOIN dbo.permisos p ON p.codigo_permiso IN (
    'EJECUCIONES_VER','EJECUCIONES_EJECUTAR','EJECUCIONES_DETENER','EJECUCIONES_LOG_VER'
)
WHERE r.codigo_rol IN ('SUPER_ADMIN','ADMIN','TI')
  AND NOT EXISTS (
      SELECT 1 FROM dbo.roles_permisos rp
      WHERE rp.id_rol = r.id_rol AND rp.id_permiso = p.id_permiso
  );
GO

INSERT INTO dbo.roles_permisos (id_rol, id_permiso, permitido, usuario_creacion)
SELECT r.id_rol, p.id_permiso, 1, N'seed_006'
FROM dbo.roles r
JOIN dbo.permisos p ON p.codigo_permiso IN ('EJECUCIONES_VER','EJECUCIONES_LOG_VER')
WHERE r.codigo_rol = 'TERCERO'
  AND NOT EXISTS (
      SELECT 1 FROM dbo.roles_permisos rp
      WHERE rp.id_rol = r.id_rol AND rp.id_permiso = p.id_permiso
  );
GO
