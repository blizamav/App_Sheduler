# APP Scheduler - Instalacion SQL release limpio

Este directorio contiene una instalacion limpia de base de datos para `APP_SCHEDULER_QA`.

La carpeta `database/migrations/` y `database/seeds/` se conserva como historial de desarrollo. Para una instalacion nueva se debe usar este release consolidado.

## Orden de ejecucion

Ejecutar manualmente en SQL Server Management Studio, en este orden:

1. `001_crear_base_datos.sql`
2. `002_schema_final.sql`
3. `003_seed_roles_permisos.sql`
4. `004_seed_catalogos_base.sql`
5. `005_seed_configuracion_inicial.sql`
6. `006_seed_feriados_base.sql`
7. `099_validacion_instalacion.sql`

## Alcance

El release crea la estructura final actual del sistema:

- Seguridad: usuarios, roles, permisos, usuarios_roles y roles_permisos.
- Catalogos base.
- Mantenedores: clientes, categorias y tipos.
- Tareas y programaciones.
- Scripts y versiones con maximo tres versiones logicas.
- Ejecuciones, logs de tareas y logs de sistema.
- Scheduler: configuracion, heartbeat y eventos del programador.
- Feriados locales y reglas de irrenunciables.
- Papelera operativa mediante marcas de eliminado operativo.
- Auditoria de cambios.

## Datos incluidos

Los seeds incluyen:

- Roles base.
- Permisos base y asignaciones por rol.
- Catalogos del sistema.
- Configuracion inicial segura del scheduler, apagada por defecto.
- Reglas locales de feriados irrenunciables para Chile.

## Datos no incluidos

Este release no incluye:

- Usuarios reales.
- Passwords.
- Servidores.
- Rutas locales.
- Tareas de prueba.
- Scripts cargados.
- Ejecuciones.
- Logs historicos.
- Auditoria historica.
- Feriados sincronizados desde API.

## Seguridad

Los scripts no contienen credenciales ni cadenas de conexion. La conexion de la aplicacion se configura por `.env`, que no debe subirse a Git ni sobrescribirse automaticamente.

## Validacion

`099_validacion_instalacion.sql` solo ejecuta consultas `SELECT`. Sirve para revisar conteos, indices criticos, claves foraneas y restricciones `CHECK`.

No ejecuta `INSERT`, `UPDATE`, `DELETE`, `DROP` ni cambios de datos.
