/*
Release SQL limpio - APP Scheduler
Script: 001_crear_base_datos.sql
Objetivo: crear la base de datos vacia para instalacion desde cero.

Ejecucion manual en SQL Server Management Studio.
No incluye usuarios SQL, passwords, servidores ni rutas locales.
*/

IF DB_ID(N'$(DB_NAME)') IS NULL
BEGIN
    CREATE DATABASE [$(DB_NAME)];
END;
GO

USE [$(DB_NAME)];
GO

SELECT
    DB_NAME() AS base_actual,
    N'Base de datos disponible para ejecutar 002_schema_final.sql' AS resultado;
GO
