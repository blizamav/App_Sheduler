/*
    Fase 12A - Permisos de Auditoria

    Ejecucion manual en SQL Server Management Studio.
*/

USE APP_SCHEDULER_QA;
GO

MERGE dbo.permisos AS destino
USING (VALUES
    ('AUDITORIA_VER', N'auditoria', N'ver', N'Ver auditoria de acciones humanas.'),
    ('AUDITORIA_DETALLE', N'auditoria', N'detalle', N'Ver detalle de un evento de auditoria.')
) AS origen(codigo_permiso, modulo, accion, descripcion)
ON destino.codigo_permiso = origen.codigo_permiso
WHEN MATCHED THEN
    UPDATE SET modulo = origen.modulo,
               accion = origen.accion,
               descripcion = origen.descripcion,
               fecha_actualizacion = SYSDATETIME(),
               usuario_actualizacion = N'seed'
WHEN NOT MATCHED THEN
    INSERT (codigo_permiso, modulo, accion, descripcion, usuario_creacion)
    VALUES (origen.codigo_permiso, origen.modulo, origen.accion, origen.descripcion, N'seed');
GO

INSERT INTO dbo.roles_permisos (id_rol, id_permiso, permitido, usuario_creacion)
SELECT r.id_rol, p.id_permiso, 1, N'seed'
FROM dbo.roles r
INNER JOIN dbo.permisos p ON p.codigo_permiso IN ('AUDITORIA_VER', 'AUDITORIA_DETALLE')
WHERE r.codigo_rol IN ('SUPER_ADMIN', 'ADMIN', 'TI')
  AND NOT EXISTS (
      SELECT 1
      FROM dbo.roles_permisos rp
      WHERE rp.id_rol = r.id_rol
        AND rp.id_permiso = p.id_permiso
  );
GO
