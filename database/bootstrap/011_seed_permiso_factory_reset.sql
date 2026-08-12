/* Permiso exclusivo para la infraestructura preventiva de Factory Reset. */

USE [$(DB_NAME)];
GO

MERGE dbo.permisos AS destino
USING (VALUES
    (N'FACTORY_RESET_EJECUTAR', N'factory_reset', N'ejecutar', N'Preparar y ejecutar Factory Reset bajo controles exclusivos', CAST(1 AS bit))
) AS origen(codigo_permiso, modulo, accion, descripcion, activo)
ON destino.codigo_permiso = origen.codigo_permiso
WHEN MATCHED THEN
    UPDATE SET modulo = origen.modulo,
               accion = origen.accion,
               descripcion = origen.descripcion,
               activo = origen.activo,
               fecha_actualizacion = SYSDATETIME(),
               usuario_actualizacion = N'bootstrap_19C'
WHEN NOT MATCHED THEN
    INSERT (codigo_permiso, modulo, accion, descripcion, activo, usuario_creacion)
    VALUES (origen.codigo_permiso, origen.modulo, origen.accion, origen.descripcion, origen.activo, N'bootstrap_19C');
GO

MERGE dbo.roles_permisos AS destino
USING (
    SELECT r.id_rol, p.id_permiso
    FROM dbo.roles r
    INNER JOIN dbo.permisos p ON p.codigo_permiso = N'FACTORY_RESET_EJECUTAR'
    WHERE r.codigo_rol = N'SUPER_ADMIN'
) AS origen
ON destino.id_rol = origen.id_rol AND destino.id_permiso = origen.id_permiso
WHEN MATCHED THEN
    UPDATE SET permitido = 1, activo = 1
WHEN NOT MATCHED THEN
    INSERT (id_rol, id_permiso, permitido, usuario_creacion)
    VALUES (origen.id_rol, origen.id_permiso, 1, N'bootstrap_19C');
GO

UPDATE dbo.configuracion_sistema
SET valor = N'19C.0',
    descripcion = N'Version del bootstrap limpio vigente validado para infraestructura Factory Reset.',
    fecha_actualizacion = SYSDATETIME(),
    usuario_actualizacion = N'bootstrap_19C'
WHERE clave = N'BOOTSTRAP_SQL';
GO
