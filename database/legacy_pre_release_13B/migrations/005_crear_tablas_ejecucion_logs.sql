/*
Fase 3B - APP Scheduler
Script: 005_crear_tablas_ejecucion_logs.sql
Objetivo: crear tablas de ejecuciones, logs y auditoria.
*/

USE APP_SCHEDULER_QA;
GO

IF OBJECT_ID(N'dbo.ejecuciones', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.ejecuciones (
        id_ejecucion bigint IDENTITY(1,1) NOT NULL,
        id_tarea int NOT NULL,
        id_script int NOT NULL,
        id_version int NOT NULL,
        origen_ejecucion varchar(20) NOT NULL,
        estado_ejecucion varchar(30) NOT NULL,
        fecha_hora_inicio datetime2(0) NOT NULL,
        fecha_hora_termino datetime2(0) NULL,
        duracion_segundos int NULL,
        codigo_salida int NULL,
        mensaje_error nvarchar(max) NULL,
        usuario_ejecucion nvarchar(100) NULL,
        pid_proceso int NULL,
        fecha_creacion datetime2(0) NOT NULL CONSTRAINT DF_ejecuciones_fecha_creacion DEFAULT SYSDATETIME(),
        CONSTRAINT PK_ejecuciones PRIMARY KEY (id_ejecucion),
        CONSTRAINT FK_ejecuciones_tareas FOREIGN KEY (id_tarea) REFERENCES dbo.tareas(id_tarea),
        CONSTRAINT FK_ejecuciones_scripts FOREIGN KEY (id_script) REFERENCES dbo.scripts(id_script),
        CONSTRAINT FK_ejecuciones_scripts_versiones FOREIGN KEY (id_version) REFERENCES dbo.scripts_versiones(id_version),
        CONSTRAINT FK_ejecuciones_cat_estados_ejecucion FOREIGN KEY (estado_ejecucion) REFERENCES dbo.cat_estados_ejecucion(codigo),
        CONSTRAINT CK_ejecuciones_origen CHECK (origen_ejecucion IN ('MANUAL','AUTOMATICA')),
        CONSTRAINT CK_ejecuciones_duracion CHECK (duracion_segundos IS NULL OR duracion_segundos >= 0)
    );
END;
GO

IF OBJECT_ID(N'dbo.logs_tareas', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.logs_tareas (
        id_log bigint IDENTITY(1,1) NOT NULL,
        id_tarea int NOT NULL,
        id_ejecucion bigint NOT NULL,
        nombre_tarea nvarchar(200) NOT NULL,
        nombre_script nvarchar(255) NOT NULL,
        nombre_archivo_log nvarchar(255) NOT NULL,
        ruta_fisica_log nvarchar(500) NOT NULL,
        ruta_relativa_log nvarchar(500) NOT NULL,
        fecha_hora_inicio datetime2(0) NOT NULL,
        fecha_hora_termino datetime2(0) NULL,
        duracion_segundos int NULL,
        estado_final varchar(30) NOT NULL,
        codigo_salida int NULL,
        mensaje_error nvarchar(max) NULL,
        usuario_ejecucion nvarchar(100) NULL,
        fecha_creacion datetime2(0) NOT NULL CONSTRAINT DF_logs_tareas_fecha_creacion DEFAULT SYSDATETIME(),
        CONSTRAINT PK_logs_tareas PRIMARY KEY (id_log),
        CONSTRAINT FK_logs_tareas_tareas FOREIGN KEY (id_tarea) REFERENCES dbo.tareas(id_tarea),
        CONSTRAINT FK_logs_tareas_ejecuciones FOREIGN KEY (id_ejecucion) REFERENCES dbo.ejecuciones(id_ejecucion),
        CONSTRAINT FK_logs_tareas_cat_estado_final FOREIGN KEY (estado_final) REFERENCES dbo.cat_estados_ejecucion(codigo),
        CONSTRAINT CK_logs_tareas_duracion CHECK (duracion_segundos IS NULL OR duracion_segundos >= 0)
    );
END;
GO

IF OBJECT_ID(N'dbo.logs_sistema', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.logs_sistema (
        id bigint IDENTITY(1,1) NOT NULL,
        usuario nvarchar(100) NULL,
        accion nvarchar(100) NOT NULL,
        modulo nvarchar(100) NOT NULL,
        descripcion nvarchar(max) NOT NULL,
        valor_anterior nvarchar(max) NULL,
        valor_nuevo nvarchar(max) NULL,
        ip varchar(45) NULL,
        user_agent nvarchar(500) NULL,
        fecha_hora datetime2(0) NOT NULL CONSTRAINT DF_logs_sistema_fecha_hora DEFAULT SYSDATETIME(),
        nivel varchar(30) NOT NULL,
        fecha_creacion datetime2(0) NOT NULL CONSTRAINT DF_logs_sistema_fecha_creacion DEFAULT SYSDATETIME(),
        CONSTRAINT PK_logs_sistema PRIMARY KEY (id),
        CONSTRAINT FK_logs_sistema_cat_niveles_log FOREIGN KEY (nivel) REFERENCES dbo.cat_niveles_log(codigo),
        CONSTRAINT CK_logs_sistema_nivel CHECK (nivel IN ('INFO','WARNING','ERROR','CRITICAL'))
    );
END;
GO

IF OBJECT_ID(N'dbo.auditoria_cambios', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.auditoria_cambios (
        id_auditoria bigint IDENTITY(1,1) NOT NULL,
        tabla_afectada nvarchar(100) NOT NULL,
        id_registro nvarchar(100) NOT NULL,
        accion nvarchar(50) NOT NULL,
        valor_anterior nvarchar(max) NULL,
        valor_nuevo nvarchar(max) NULL,
        usuario nvarchar(100) NOT NULL,
        ip varchar(45) NULL,
        user_agent nvarchar(500) NULL,
        fecha_hora datetime2(0) NOT NULL CONSTRAINT DF_auditoria_cambios_fecha_hora DEFAULT SYSDATETIME(),
        modulo nvarchar(100) NOT NULL,
        CONSTRAINT PK_auditoria_cambios PRIMARY KEY (id_auditoria)
    );
END;
GO
