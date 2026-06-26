# Legacy pre release 13B

Esta carpeta conserva scripts historicos previos al release SQL oficial de Fase 13B.

Estos archivos:

- No son la fuente oficial para una instalacion nueva.
- Se conservan por trazabilidad tecnica de fases anteriores.
- Pueden apuntar directamente a bases antiguas como `APP_SCHEDULER_QA`.
- No deben ejecutarse sin revision tecnica previa.

La fuente oficial de instalacion limpia esta en:

```text
database/release/
```

El punto de entrada recomendado es:

```text
database/release/000_ejecutar_instalacion_completa.sql
```

Para instalar en otra base se debe cambiar `DB_NAME` en el script maestro y ejecutar con `Query > SQLCMD Mode` activo en SQL Server Management Studio.

## Contenido

- `migrations/`: migraciones incrementales historicas usadas durante el desarrollo.
- `seeds/`: seeds incrementales historicos reemplazados por el release consolidado.
- `diagnostics/`: scripts de diagnostico puntual usados en fases operativas anteriores.

