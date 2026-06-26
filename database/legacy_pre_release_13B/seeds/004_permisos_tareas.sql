/*
Fase 6 - APP Scheduler
Seed: 004_permisos_tareas.sql
Objetivo: agregar permisos incrementales de tareas para estado y eliminacion.
Nota: no modifica seeds anteriores. Ejecutar manualmente en SSMS despues de aprobar Fase 6.
*/

USE APP_SCHEDULER_QA;
GO

MERGE dbo.permisos AS destino
USING (VALUES
    ('TAREAS_ESTADO', N'tareas', N'estado', N'Activar o desactivar tareas.'),
    ('TAREAS_ELIMINAR', N'tareas', N'eliminar', N'Eliminar tareas sin dependencias.')
) AS origen(codigo_permiso, modulo, accion, descripcion)
ON destino.codigo_permiso = origen.codigo_permiso
WHEN NOT MATCHED THEN
    INSERT (codigo_permiso, modulo, accion, descripcion, usuario_creacion)
    VALUES (origen.codigo_permiso, origen.modulo, origen.accion, origen.descripcion, N'seed_004');
GO

-- SUPER_ADMIN y ADMIN: administracion completa de tareas.
INSERT INTO dbo.roles_permisos (id_rol, id_permiso, permitido, usuario_creacion)
SELECT r.id_rol, p.id_permiso, 1, N'seed_004'
FROM dbo.roles r
JOIN dbo.permisos p ON p.codigo_permiso IN (
    'TAREAS_VER','TAREAS_CREAR','TAREAS_EDITAR','TAREAS_ESTADO','TAREAS_ELIMINAR'
)
WHERE r.codigo_rol IN ('SUPER_ADMIN','ADMIN')
  AND NOT EXISTS (
      SELECT 1 FROM dbo.roles_permisos rp
      WHERE rp.id_rol = r.id_rol AND rp.id_permiso = p.id_permiso
  );
GO

-- TI: opera tareas, pero no elimina fisicamente.
INSERT INTO dbo.roles_permisos (id_rol, id_permiso, permitido, usuario_creacion)
SELECT r.id_rol, p.id_permiso, 1, N'seed_004'
FROM dbo.roles r
JOIN dbo.permisos p ON p.codigo_permiso IN (
    'TAREAS_VER','TAREAS_CREAR','TAREAS_EDITAR','TAREAS_ESTADO'
)
WHERE r.codigo_rol = 'TI'
  AND NOT EXISTS (
      SELECT 1 FROM dbo.roles_permisos rp
      WHERE rp.id_rol = r.id_rol AND rp.id_permiso = p.id_permiso
  );
GO

-- TERCERO: solo lectura.
INSERT INTO dbo.roles_permisos (id_rol, id_permiso, permitido, usuario_creacion)
SELECT r.id_rol, p.id_permiso, 1, N'seed_004'
FROM dbo.roles r
JOIN dbo.permisos p ON p.codigo_permiso IN ('TAREAS_VER')
WHERE r.codigo_rol = 'TERCERO'
  AND NOT EXISTS (
      SELECT 1 FROM dbo.roles_permisos rp
      WHERE rp.id_rol = r.id_rol AND rp.id_permiso = p.id_permiso
  );
GO
