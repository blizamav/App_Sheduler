/*
Fase 5 - APP Scheduler
Seed: 003_permisos_mantenedores.sql
Objetivo: crear permisos incrementales para mantenedores de clientes, categorias y tipos.
Nota: no modifica seeds ya ejecutados; ejecutar manualmente en SSMS cuando se apruebe.
*/

USE APP_SCHEDULER_QA;
GO

MERGE dbo.permisos AS destino
USING (VALUES
    ('CLIENTES_VER', N'clientes', N'ver', N'Ver clientes.'),
    ('CLIENTES_CREAR', N'clientes', N'crear', N'Crear clientes.'),
    ('CLIENTES_EDITAR', N'clientes', N'editar', N'Editar clientes.'),
    ('CLIENTES_ESTADO', N'clientes', N'estado', N'Activar o desactivar clientes.'),
    ('CATEGORIAS_VER', N'categorias', N'ver', N'Ver categorias.'),
    ('CATEGORIAS_CREAR', N'categorias', N'crear', N'Crear categorias.'),
    ('CATEGORIAS_EDITAR', N'categorias', N'editar', N'Editar categorias.'),
    ('CATEGORIAS_ESTADO', N'categorias', N'estado', N'Activar o desactivar categorias.'),
    ('TIPOS_VER', N'tipos', N'ver', N'Ver tipos.'),
    ('TIPOS_CREAR', N'tipos', N'crear', N'Crear tipos.'),
    ('TIPOS_EDITAR', N'tipos', N'editar', N'Editar tipos.'),
    ('TIPOS_ESTADO', N'tipos', N'estado', N'Activar o desactivar tipos.')
) AS origen(codigo_permiso, modulo, accion, descripcion)
ON destino.codigo_permiso = origen.codigo_permiso
WHEN NOT MATCHED THEN
    INSERT (codigo_permiso, modulo, accion, descripcion, usuario_creacion)
    VALUES (origen.codigo_permiso, origen.modulo, origen.accion, origen.descripcion, N'seed_003');
GO

-- SUPER_ADMIN y ADMIN: administracion completa de mantenedores.
INSERT INTO dbo.roles_permisos (id_rol, id_permiso, permitido, usuario_creacion)
SELECT r.id_rol, p.id_permiso, 1, N'seed_003'
FROM dbo.roles r
JOIN dbo.permisos p ON p.codigo_permiso IN (
    'CLIENTES_VER','CLIENTES_CREAR','CLIENTES_EDITAR','CLIENTES_ESTADO',
    'CATEGORIAS_VER','CATEGORIAS_CREAR','CATEGORIAS_EDITAR','CATEGORIAS_ESTADO',
    'TIPOS_VER','TIPOS_CREAR','TIPOS_EDITAR','TIPOS_ESTADO'
)
WHERE r.codigo_rol IN ('SUPER_ADMIN','ADMIN')
  AND NOT EXISTS (
      SELECT 1 FROM dbo.roles_permisos rp
      WHERE rp.id_rol = r.id_rol AND rp.id_permiso = p.id_permiso
  );
GO

-- TI: lectura de mantenedores para preparar tareas.
INSERT INTO dbo.roles_permisos (id_rol, id_permiso, permitido, usuario_creacion)
SELECT r.id_rol, p.id_permiso, 1, N'seed_003'
FROM dbo.roles r
JOIN dbo.permisos p ON p.codigo_permiso IN ('CLIENTES_VER','CATEGORIAS_VER','TIPOS_VER')
WHERE r.codigo_rol = 'TI'
  AND NOT EXISTS (
      SELECT 1 FROM dbo.roles_permisos rp
      WHERE rp.id_rol = r.id_rol AND rp.id_permiso = p.id_permiso
  );
GO
