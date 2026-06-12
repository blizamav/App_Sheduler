/*
Fase 3B - APP Scheduler
Script: 001_crear_base_datos.sql
Objetivo: crear la base APP_SCHEDULER_QA si no existe.
Ejecucion: manual desde SQL Server Management Studio.
*/

IF DB_ID(N'APP_SCHEDULER_QA') IS NULL
BEGIN
    CREATE DATABASE APP_SCHEDULER_QA;
END;
GO

USE APP_SCHEDULER_QA;
GO

-- Confirmacion informativa para ejecucion manual.
SELECT DB_NAME() AS base_datos_actual;
GO
