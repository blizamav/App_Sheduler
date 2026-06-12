# Seguridad

## Manejo de sesiones

Fase 1 usa sesiones Flask protegidas por `APP_SECRET_KEY`.

## Roles y permisos

Pendiente para Fase 4.

## Variables de entorno

Credenciales, servidores, rutas y secret keys deben vivir en `.env`. El archivo real se excluye con `.gitignore`.

## Validacion de archivos

Pendiente para Fase 7. Los scripts deberan validar extension `.py`, nombre seguro y rutas internas.

## Eliminacion fisica de scripts

En la primera version del sistema no debe existir eliminacion fisica de scripts ni versiones desde la app. Las versiones deben gestionarse por estado:

* `ACTIVA`
* `DISPONIBLE`
* `REEMPLAZADA`
* `INACTIVA`

Toda inactivacion o reemplazo debe registrarse en auditoria y logs de sistema. Cualquier limpieza fisica futura debera ser una funcionalidad posterior, restringida, confirmada y auditable.

## Validacion de rutas

No se deben quemar rutas absolutas. Toda ruta operativa debe venir desde `.env`.

## Logs seguros

Pendiente para Fase 9. Los logs no deben exponer credenciales ni datos sensibles.

## Recomendaciones

Cambiar `APP_SECRET_KEY` y `PASSWORD_ADMIN_DEFECTO` antes de ejecutar en entornos compartidos.
