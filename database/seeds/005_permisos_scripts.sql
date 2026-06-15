/*
Fase 7 - APP Scheduler
Seed: 005_permisos_scripts.sql
Objetivo: agregar permisos incrementales para gestion de scripts, versiones y env por version.
Nota: ejecutar manualmente en SSMS. No modifica seeds anteriores.
*/

USE APP_SCHEDULER_QA;
GO

MERGE dbo.permisos AS destino
USING (VALUES
    ('SCRIPTS_VER', N'scripts', N'ver', N'Ver scripts y versiones asociadas a tareas.'),
    ('SCRIPTS_CREAR', N'scripts', N'crear', N'Crear script logico y cargar primera version.'),
    ('SCRIPTS_EDITAR', N'scripts', N'editar', N'Editar datos basicos de scripts.'),
    ('SCRIPTS_VERSIONAR', N'scripts', N'versionar', N'Cargar o reemplazar versiones de scripts.'),
    ('SCRIPTS_ACTIVAR_VERSION', N'scripts', N'activar_version', N'Cambiar version activa de un script.'),
    ('SCRIPTS_DESACTIVAR', N'scripts', N'desactivar', N'Desactivar scripts o versiones.'),
    ('SCRIPTS_ELIMINAR', N'scripts', N'eliminar', N'Eliminar scripts o versiones sin historial.'),
    ('SCRIPTS_ENV_GESTIONAR', N'scripts', N'env_gestionar', N'Gestionar archivo env asociado a una version.')
) AS origen(codigo_permiso, modulo, accion, descripcion)
ON destino.codigo_permiso = origen.codigo_permiso
WHEN NOT MATCHED THEN
    INSERT (codigo_permiso, modulo, accion, descripcion, usuario_creacion)
    VALUES (origen.codigo_permiso, origen.modulo, origen.accion, origen.descripcion, N'seed_005');
GO

INSERT INTO dbo.roles_permisos (id_rol, id_permiso, permitido, usuario_creacion)
SELECT r.id_rol, p.id_permiso, 1, N'seed_005'
FROM dbo.roles r
JOIN dbo.permisos p ON p.codigo_permiso IN (
    'SCRIPTS_VER','SCRIPTS_CREAR','SCRIPTS_EDITAR','SCRIPTS_VERSIONAR',
    'SCRIPTS_ACTIVAR_VERSION','SCRIPTS_DESACTIVAR','SCRIPTS_ELIMINAR','SCRIPTS_ENV_GESTIONAR'
)
WHERE r.codigo_rol IN ('SUPER_ADMIN','ADMIN')
  AND NOT EXISTS (
      SELECT 1 FROM dbo.roles_permisos rp
      WHERE rp.id_rol = r.id_rol AND rp.id_permiso = p.id_permiso
  );
GO

INSERT INTO dbo.roles_permisos (id_rol, id_permiso, permitido, usuario_creacion)
SELECT r.id_rol, p.id_permiso, 1, N'seed_005'
FROM dbo.roles r
JOIN dbo.permisos p ON p.codigo_permiso IN (
    'SCRIPTS_VER','SCRIPTS_CREAR','SCRIPTS_EDITAR','SCRIPTS_VERSIONAR',
    'SCRIPTS_ACTIVAR_VERSION','SCRIPTS_ENV_GESTIONAR'
)
WHERE r.codigo_rol = 'TI'
  AND NOT EXISTS (
      SELECT 1 FROM dbo.roles_permisos rp
      WHERE rp.id_rol = r.id_rol AND rp.id_permiso = p.id_permiso
  );
GO

INSERT INTO dbo.roles_permisos (id_rol, id_permiso, permitido, usuario_creacion)
SELECT r.id_rol, p.id_permiso, 1, N'seed_005'
FROM dbo.roles r
JOIN dbo.permisos p ON p.codigo_permiso IN ('SCRIPTS_VER')
WHERE r.codigo_rol = 'TERCERO'
  AND NOT EXISTS (
      SELECT 1 FROM dbo.roles_permisos rp
      WHERE rp.id_rol = r.id_rol AND rp.id_permiso = p.id_permiso
  );
GO
