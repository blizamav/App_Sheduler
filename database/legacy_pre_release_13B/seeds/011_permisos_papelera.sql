/*
Seed: 011_permisos_papelera.sql
Objetivo: agregar permisos incrementales para Fase 11G - Papelera operativa.
Ejecucion: manual en SQL Server Management Studio. No ejecutar automaticamente.
*/

USE APP_SCHEDULER_QA;
GO

MERGE dbo.permisos AS destino
USING (VALUES
    ('PAPELERA_VER', N'papelera', N'ver', N'Ver papelera operativa.'),
    ('PAPELERA_RESTAURAR', N'papelera', N'restaurar', N'Restaurar registros retirados como inactivos.'),
    ('PAPELERA_ELIMINAR_PERMANENTE', N'papelera', N'eliminar_permanente', N'Eliminar permanentemente registros de tablas operativas cuando sea seguro.')
) AS origen(codigo_permiso, modulo, accion, descripcion)
ON destino.codigo_permiso = origen.codigo_permiso
WHEN NOT MATCHED THEN
    INSERT (codigo_permiso, modulo, accion, descripcion, usuario_creacion)
    VALUES (origen.codigo_permiso, origen.modulo, origen.accion, origen.descripcion, N'seed_011');
GO

-- SUPER_ADMIN: acceso completo a papelera.
INSERT INTO dbo.roles_permisos (id_rol, id_permiso, permitido, usuario_creacion)
SELECT r.id_rol, p.id_permiso, 1, N'seed_011'
FROM dbo.roles r
JOIN dbo.permisos p ON p.codigo_permiso IN (
    'PAPELERA_VER', 'PAPELERA_RESTAURAR', 'PAPELERA_ELIMINAR_PERMANENTE'
)
WHERE r.codigo_rol = 'SUPER_ADMIN'
  AND NOT EXISTS (
      SELECT 1 FROM dbo.roles_permisos rp
      WHERE rp.id_rol = r.id_rol AND rp.id_permiso = p.id_permiso
  );
GO

-- ADMIN: ver y restaurar desde papelera. La eliminacion permanente queda reservada.
INSERT INTO dbo.roles_permisos (id_rol, id_permiso, permitido, usuario_creacion)
SELECT r.id_rol, p.id_permiso, 1, N'seed_011'
FROM dbo.roles r
JOIN dbo.permisos p ON p.codigo_permiso IN ('PAPELERA_VER', 'PAPELERA_RESTAURAR')
WHERE r.codigo_rol = 'ADMIN'
  AND NOT EXISTS (
      SELECT 1 FROM dbo.roles_permisos rp
      WHERE rp.id_rol = r.id_rol AND rp.id_permiso = p.id_permiso
  );
GO

-- TI: solo lectura operativa si corresponde.
INSERT INTO dbo.roles_permisos (id_rol, id_permiso, permitido, usuario_creacion)
SELECT r.id_rol, p.id_permiso, 1, N'seed_011'
FROM dbo.roles r
JOIN dbo.permisos p ON p.codigo_permiso = 'PAPELERA_VER'
WHERE r.codigo_rol = 'TI'
  AND NOT EXISTS (
      SELECT 1 FROM dbo.roles_permisos rp
      WHERE rp.id_rol = r.id_rol AND rp.id_permiso = p.id_permiso
  );
GO
