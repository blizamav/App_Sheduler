/*
Fase 10A - APP Scheduler
Seed: 008_permisos_feriados.sql
Objetivo: agregar permisos incrementales para calendario local de feriados.
Nota: ejecutar manualmente en SSMS. No modifica seeds anteriores.
*/

USE APP_SCHEDULER_QA;
GO

MERGE dbo.permisos AS destino
USING (VALUES
    ('FERIADOS_VER', N'feriados', N'ver', N'Ver calendario local de feriados.'),
    ('FERIADOS_CREAR', N'feriados', N'crear', N'Crear feriados manuales.'),
    ('FERIADOS_EDITAR', N'feriados', N'editar', N'Editar feriados.'),
    ('FERIADOS_ESTADO', N'feriados', N'estado', N'Activar o desactivar feriados.'),
    ('FERIADOS_ELIMINAR', N'feriados', N'eliminar', N'Eliminar feriados sin dependencias.')
) AS origen(codigo_permiso, modulo, accion, descripcion)
ON destino.codigo_permiso = origen.codigo_permiso
WHEN NOT MATCHED THEN
    INSERT (codigo_permiso, modulo, accion, descripcion, usuario_creacion)
    VALUES (origen.codigo_permiso, origen.modulo, origen.accion, origen.descripcion, N'seed_008');
GO

INSERT INTO dbo.roles_permisos (id_rol, id_permiso, permitido, usuario_creacion)
SELECT r.id_rol, p.id_permiso, 1, N'seed_008'
FROM dbo.roles r
JOIN dbo.permisos p ON p.codigo_permiso IN (
    'FERIADOS_VER',
    'FERIADOS_CREAR',
    'FERIADOS_EDITAR',
    'FERIADOS_ESTADO',
    'FERIADOS_ELIMINAR'
)
WHERE r.codigo_rol IN ('SUPER_ADMIN','ADMIN')
  AND NOT EXISTS (
      SELECT 1 FROM dbo.roles_permisos rp
      WHERE rp.id_rol = r.id_rol AND rp.id_permiso = p.id_permiso
  );
GO

INSERT INTO dbo.roles_permisos (id_rol, id_permiso, permitido, usuario_creacion)
SELECT r.id_rol, p.id_permiso, 1, N'seed_008'
FROM dbo.roles r
JOIN dbo.permisos p ON p.codigo_permiso IN (
    'FERIADOS_VER',
    'FERIADOS_CREAR',
    'FERIADOS_EDITAR',
    'FERIADOS_ESTADO'
)
WHERE r.codigo_rol = 'TI'
  AND NOT EXISTS (
      SELECT 1 FROM dbo.roles_permisos rp
      WHERE rp.id_rol = r.id_rol AND rp.id_permiso = p.id_permiso
  );
GO
