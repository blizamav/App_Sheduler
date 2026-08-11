/* Completa la matriz vigente de permisos de mantenedores. */

USE [$(DB_NAME)];
GO

/* SUPER_ADMIN y ADMIN administran mantenedores completos. */
INSERT INTO dbo.roles_permisos (id_rol, id_permiso, permitido, usuario_creacion)
SELECT r.id_rol, p.id_permiso, 1, N'bootstrap_19B'
FROM dbo.roles r
INNER JOIN dbo.permisos p ON p.codigo_permiso IN (
    N'CLIENTES_VER', N'CLIENTES_CREAR', N'CLIENTES_EDITAR', N'CLIENTES_ESTADO',
    N'CATEGORIAS_VER', N'CATEGORIAS_CREAR', N'CATEGORIAS_EDITAR', N'CATEGORIAS_ESTADO',
    N'TIPOS_VER', N'TIPOS_CREAR', N'TIPOS_EDITAR', N'TIPOS_ESTADO'
)
WHERE r.codigo_rol IN (N'SUPER_ADMIN', N'ADMIN')
  AND NOT EXISTS (
      SELECT 1 FROM dbo.roles_permisos rp
      WHERE rp.id_rol = r.id_rol AND rp.id_permiso = p.id_permiso
  );
GO

/* TI requiere lectura de maestros para preparar tareas. */
INSERT INTO dbo.roles_permisos (id_rol, id_permiso, permitido, usuario_creacion)
SELECT r.id_rol, p.id_permiso, 1, N'bootstrap_19B'
FROM dbo.roles r
INNER JOIN dbo.permisos p ON p.codigo_permiso IN (N'CLIENTES_VER', N'CATEGORIAS_VER', N'TIPOS_VER')
WHERE r.codigo_rol = N'TI'
  AND NOT EXISTS (
      SELECT 1 FROM dbo.roles_permisos rp
      WHERE rp.id_rol = r.id_rol AND rp.id_permiso = p.id_permiso
  );
GO
