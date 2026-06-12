/*
Fase 3B - APP Scheduler
Script: 003_crear_tablas_seguridad.sql
Objetivo: crear tablas de usuarios, roles y permisos.
Nota: no crea usuario inicial blizama; el login inicial sigue desde .env.
*/

USE APP_SCHEDULER_QA;
GO

IF OBJECT_ID(N'dbo.usuarios', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.usuarios (
        id_usuario int IDENTITY(1,1) NOT NULL,
        usuario nvarchar(100) NOT NULL,
        nombre_completo nvarchar(200) NOT NULL,
        email nvarchar(200) NULL,
        password_hash nvarchar(300) NOT NULL,
        debe_cambiar_password bit NOT NULL CONSTRAINT DF_usuarios_debe_cambiar_password DEFAULT 0,
        ultimo_login datetime2(0) NULL,
        intentos_fallidos int NOT NULL CONSTRAINT DF_usuarios_intentos_fallidos DEFAULT 0,
        bloqueado bit NOT NULL CONSTRAINT DF_usuarios_bloqueado DEFAULT 0,
        fecha_creacion datetime2(0) NOT NULL CONSTRAINT DF_usuarios_fecha_creacion DEFAULT SYSDATETIME(),
        fecha_actualizacion datetime2(0) NULL,
        usuario_creacion nvarchar(100) NULL,
        usuario_actualizacion nvarchar(100) NULL,
        activo bit NOT NULL CONSTRAINT DF_usuarios_activo DEFAULT 1,
        CONSTRAINT PK_usuarios PRIMARY KEY (id_usuario),
        CONSTRAINT UX_usuarios_usuario UNIQUE (usuario)
    );
END;
GO

IF OBJECT_ID(N'dbo.roles', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.roles (
        id_rol int IDENTITY(1,1) NOT NULL,
        codigo_rol varchar(50) NOT NULL,
        nombre_rol nvarchar(100) NOT NULL,
        descripcion nvarchar(300) NULL,
        es_sistema bit NOT NULL CONSTRAINT DF_roles_es_sistema DEFAULT 0,
        fecha_creacion datetime2(0) NOT NULL CONSTRAINT DF_roles_fecha_creacion DEFAULT SYSDATETIME(),
        fecha_actualizacion datetime2(0) NULL,
        usuario_creacion nvarchar(100) NULL,
        usuario_actualizacion nvarchar(100) NULL,
        activo bit NOT NULL CONSTRAINT DF_roles_activo DEFAULT 1,
        CONSTRAINT PK_roles PRIMARY KEY (id_rol),
        CONSTRAINT UX_roles_codigo_rol UNIQUE (codigo_rol)
    );
END;
GO

IF OBJECT_ID(N'dbo.permisos', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.permisos (
        id_permiso int IDENTITY(1,1) NOT NULL,
        codigo_permiso varchar(120) NOT NULL,
        modulo nvarchar(80) NOT NULL,
        accion nvarchar(80) NOT NULL,
        descripcion nvarchar(300) NULL,
        fecha_creacion datetime2(0) NOT NULL CONSTRAINT DF_permisos_fecha_creacion DEFAULT SYSDATETIME(),
        fecha_actualizacion datetime2(0) NULL,
        usuario_creacion nvarchar(100) NULL,
        usuario_actualizacion nvarchar(100) NULL,
        activo bit NOT NULL CONSTRAINT DF_permisos_activo DEFAULT 1,
        CONSTRAINT PK_permisos PRIMARY KEY (id_permiso),
        CONSTRAINT UX_permisos_codigo_permiso UNIQUE (codigo_permiso),
        CONSTRAINT UX_permisos_modulo_accion UNIQUE (modulo, accion)
    );
END;
GO

IF OBJECT_ID(N'dbo.usuarios_roles', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.usuarios_roles (
        id_usuario_rol int IDENTITY(1,1) NOT NULL,
        id_usuario int NOT NULL,
        id_rol int NOT NULL,
        fecha_creacion datetime2(0) NOT NULL CONSTRAINT DF_usuarios_roles_fecha_creacion DEFAULT SYSDATETIME(),
        usuario_creacion nvarchar(100) NULL,
        activo bit NOT NULL CONSTRAINT DF_usuarios_roles_activo DEFAULT 1,
        CONSTRAINT PK_usuarios_roles PRIMARY KEY (id_usuario_rol),
        CONSTRAINT UX_usuarios_roles_usuario_rol UNIQUE (id_usuario, id_rol),
        CONSTRAINT FK_usuarios_roles_usuarios FOREIGN KEY (id_usuario) REFERENCES dbo.usuarios(id_usuario),
        CONSTRAINT FK_usuarios_roles_roles FOREIGN KEY (id_rol) REFERENCES dbo.roles(id_rol)
    );
END;
GO

IF OBJECT_ID(N'dbo.roles_permisos', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.roles_permisos (
        id_rol_permiso int IDENTITY(1,1) NOT NULL,
        id_rol int NOT NULL,
        id_permiso int NOT NULL,
        permitido bit NOT NULL CONSTRAINT DF_roles_permisos_permitido DEFAULT 1,
        fecha_creacion datetime2(0) NOT NULL CONSTRAINT DF_roles_permisos_fecha_creacion DEFAULT SYSDATETIME(),
        usuario_creacion nvarchar(100) NULL,
        activo bit NOT NULL CONSTRAINT DF_roles_permisos_activo DEFAULT 1,
        CONSTRAINT PK_roles_permisos PRIMARY KEY (id_rol_permiso),
        CONSTRAINT UX_roles_permisos_rol_permiso UNIQUE (id_rol, id_permiso),
        CONSTRAINT FK_roles_permisos_roles FOREIGN KEY (id_rol) REFERENCES dbo.roles(id_rol),
        CONSTRAINT FK_roles_permisos_permisos FOREIGN KEY (id_permiso) REFERENCES dbo.permisos(id_permiso)
    );
END;
GO
