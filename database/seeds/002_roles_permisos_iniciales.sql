/*
Fase 3B - APP Scheduler
Seed: 002_roles_permisos_iniciales.sql
Objetivo: crear roles, permisos y relaciones base.
Nota: no crea usuarios.
*/

USE APP_SCHEDULER_QA;
GO

MERGE dbo.roles AS destino
USING (VALUES
    ('SUPER_ADMIN', N'Super Admin', N'Acceso total al sistema.', 1),
    ('ADMIN', N'Admin', N'Administracion general sin privilegios reservados.', 1),
    ('TI', N'TI', N'Operacion tecnica de tareas y ejecuciones.', 1),
    ('TERCERO', N'Tercero', N'Acceso limitado y controlado.', 1)
) AS origen(codigo_rol, nombre_rol, descripcion, es_sistema)
ON destino.codigo_rol = origen.codigo_rol
WHEN NOT MATCHED THEN
    INSERT (codigo_rol, nombre_rol, descripcion, es_sistema, usuario_creacion)
    VALUES (origen.codigo_rol, origen.nombre_rol, origen.descripcion, origen.es_sistema, N'seed');
GO

MERGE dbo.permisos AS destino
USING (VALUES
    ('PANEL_VER', N'panel', N'ver', N'Ver panel principal.'),
    ('TAREAS_VER', N'tareas', N'ver', N'Ver tareas.'),
    ('TAREAS_CREAR', N'tareas', N'crear', N'Crear tareas.'),
    ('TAREAS_EDITAR', N'tareas', N'editar', N'Editar tareas.'),
    ('TAREAS_ACTIVAR', N'tareas', N'activar', N'Activar tareas.'),
    ('TAREAS_SUSPENDER', N'tareas', N'suspender', N'Suspender tareas.'),
    ('TAREAS_EJECUTAR', N'tareas', N'ejecutar', N'Ejecutar tareas.'),
    ('SCRIPTS_VER', N'scripts', N'ver', N'Ver scripts.'),
    ('SCRIPTS_CARGAR', N'scripts', N'cargar', N'Cargar versiones de script.'),
    ('SCRIPTS_REEMPLAZAR', N'scripts', N'reemplazar', N'Reemplazar versiones de script.'),
    ('LOGS_VER', N'logs', N'ver', N'Ver logs.'),
    ('AUDITORIA_VER', N'auditoria', N'ver', N'Ver auditoria.'),
    ('USUARIOS_ADMIN', N'usuarios', N'administrar', N'Administrar usuarios.'),
    ('CONFIGURACION_ADMIN', N'configuracion', N'administrar', N'Administrar configuracion.')
) AS origen(codigo_permiso, modulo, accion, descripcion)
ON destino.codigo_permiso = origen.codigo_permiso
WHEN NOT MATCHED THEN
    INSERT (codigo_permiso, modulo, accion, descripcion, usuario_creacion)
    VALUES (origen.codigo_permiso, origen.modulo, origen.accion, origen.descripcion, N'seed');
GO

-- SUPER_ADMIN: todos los permisos.
INSERT INTO dbo.roles_permisos (id_rol, id_permiso, permitido, usuario_creacion)
SELECT r.id_rol, p.id_permiso, 1, N'seed'
FROM dbo.roles r
CROSS JOIN dbo.permisos p
WHERE r.codigo_rol = 'SUPER_ADMIN'
  AND NOT EXISTS (
      SELECT 1 FROM dbo.roles_permisos rp
      WHERE rp.id_rol = r.id_rol AND rp.id_permiso = p.id_permiso
  );
GO

-- ADMIN: permisos operativos y administrativos, sin configuracion critica reservada.
INSERT INTO dbo.roles_permisos (id_rol, id_permiso, permitido, usuario_creacion)
SELECT r.id_rol, p.id_permiso, 1, N'seed'
FROM dbo.roles r
JOIN dbo.permisos p ON p.codigo_permiso IN (
    'PANEL_VER','TAREAS_VER','TAREAS_CREAR','TAREAS_EDITAR','TAREAS_ACTIVAR',
    'TAREAS_SUSPENDER','TAREAS_EJECUTAR','SCRIPTS_VER','SCRIPTS_CARGAR',
    'SCRIPTS_REEMPLAZAR','LOGS_VER','AUDITORIA_VER','USUARIOS_ADMIN'
)
WHERE r.codigo_rol = 'ADMIN'
  AND NOT EXISTS (
      SELECT 1 FROM dbo.roles_permisos rp
      WHERE rp.id_rol = r.id_rol AND rp.id_permiso = p.id_permiso
  );
GO

-- TI: operacion tecnica.
INSERT INTO dbo.roles_permisos (id_rol, id_permiso, permitido, usuario_creacion)
SELECT r.id_rol, p.id_permiso, 1, N'seed'
FROM dbo.roles r
JOIN dbo.permisos p ON p.codigo_permiso IN (
    'PANEL_VER','TAREAS_VER','TAREAS_EDITAR','TAREAS_ACTIVAR',
    'TAREAS_SUSPENDER','TAREAS_EJECUTAR','SCRIPTS_VER','SCRIPTS_CARGAR',
    'SCRIPTS_REEMPLAZAR','LOGS_VER'
)
WHERE r.codigo_rol = 'TI'
  AND NOT EXISTS (
      SELECT 1 FROM dbo.roles_permisos rp
      WHERE rp.id_rol = r.id_rol AND rp.id_permiso = p.id_permiso
  );
GO

-- TERCERO: acceso minimo.
INSERT INTO dbo.roles_permisos (id_rol, id_permiso, permitido, usuario_creacion)
SELECT r.id_rol, p.id_permiso, 1, N'seed'
FROM dbo.roles r
JOIN dbo.permisos p ON p.codigo_permiso IN ('PANEL_VER','TAREAS_VER','TAREAS_EJECUTAR','LOGS_VER')
WHERE r.codigo_rol = 'TERCERO'
  AND NOT EXISTS (
      SELECT 1 FROM dbo.roles_permisos rp
      WHERE rp.id_rol = r.id_rol AND rp.id_permiso = p.id_permiso
  );
GO
