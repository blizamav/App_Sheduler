# Factory Reset

## Estado

Fase 19C implementa solamente infraestructura preventiva, diagnóstico y preview. No existe endpoint capaz de reconstruir o eliminar la base de datos, no se ejecuta el bootstrap y la segunda confirmación permanece deshabilitada.

## Riesgo y autorización

Factory Reset es una operación reservada a `SUPER_ADMIN` o `SUPER_ADMIN_ENV`. El backend exige además `FACTORY_RESET_EJECUTAR` o permiso global `*`; entregar accidentalmente el permiso a otro rol no habilita la ruta. El bootstrap `19C.0` crea 52 permisos y asigna el nuevo permiso exclusivamente a `SUPER_ADMIN`.

## Lock global externo

El lock vive fuera de SQL Server en `RUTA_CONTROL_RUNTIME/factory_reset.lock`. El valor predeterminado es `runtime_control/`; Docker comparte `./runtime_control:/app/runtime_control` entre web y worker.

Estados:

* `NORMAL`: no existe archivo lock.
* `FACTORY_RESET_PREPARANDO`.
* `FACTORY_RESET_EN_PROGRESO`.
* `FACTORY_RESET_ERROR`.

La adquisición usa creación exclusiva `O_CREAT | O_EXCL`. El JSON registra estado, fecha UTC, PID, host, origen e identificador de operación, sin secretos. Un segundo adquirente es rechazado. La actualización o liberación requiere el mismo identificador.

El timeout predeterminado es 1800 segundos. Un lock expirado, corrupto, no regular o dudoso continúa bloqueando; nunca se libera automáticamente solo por antigüedad o PID. La recuperación manual controlada queda pendiente para la fase operativa.

## Bloqueo de ejecuciones

* La ejecución manual comprueba el lock antes de consultar o crear una ejecución.
* La creación automática repite la misma defensa.
* El worker comprueba el lock antes de cargar configuración y antes de seleccionar candidatos.
* Con lock, el worker no inicia tareas y mantiene heartbeat `BLOQUEADO_FACTORY_RESET` cuando SQL Server está disponible.
* Fase 19C no detiene ni mata procesos existentes.

## Preview

`GET /administracion/factory-reset` muestra la Zona de Peligro. `POST /administracion/factory-reset/preview` genera un diagnóstico de solo lectura.

El preview incluye:

* conteos de las 33 tablas vigentes;
* ejecuciones `EN_EJECUCION`, PID registrados/vivos y procesos hijos conocidos;
* estado del worker y cantidad de tareas candidatas;
* cantidades y bytes aproximados bajo scripts, env, logs de tareas, logs de sistema y logs del worker;
* conteos `.py`, `.env` y `.log`, sin leer contenidos;
* versión, orden, existencia de archivos y validez de `database/bootstrap/manifest.json`;
* marca `BOOTSTRAP_SQL` activa en la BD y coincidencia con la versión del manifiesto;
* disponibilidad segura de `SUPER_ADMIN_ENV`, sin mostrar usuario ni password;
* estado del lock y bloqueos que impiden continuar.

El preview queda `BLOQUEADO` si existe lock, ejecución activa, error de inventario, manifiesto inválido o falta recuperación `SUPER_ADMIN_ENV`.

## CSRF y token firmado

El POST de preview exige un token CSRF aleatorio asociado a la sesión, consumible y con expiración predeterminada de 600 segundos.

El resultado genera un token firmado con `APP_SECRET_KEY` mediante `itsdangerous`. Incluye usuario solicitante, timestamp, hash del resumen, estado del lock e identificador de operación. Expira a los 300 segundos y queda ligado al usuario. No contiene secretos ni autoriza por sí solo un reset.

La futura ejecución deberá validar el token y recalcular inmediatamente lock, ejecuciones activas, worker, bootstrap y recuperación administrativa.

## Confirmaciones

La primera confirmación genera exclusivamente el preview. La UI muestra la frase futura `RESTABLECER APP SCHEDULER`, pero el control y el botón final están deshabilitados. No existe `POST /administracion/factory-reset/ejecutar`.

## Variables

```env
RUTA_CONTROL_RUNTIME=runtime_control
FACTORY_RESET_LOCK_TIMEOUT_SEGUNDOS=1800
FACTORY_RESET_PREVIEW_TTL_SEGUNDOS=300
FACTORY_RESET_CSRF_TTL_SEGUNDOS=600
```

## Pendiente Fase 19D

Fase 19D deberá implementar orquestación destructiva separada, adquisición y transición real del lock, detención coordinada del worker, reconfirmación textual, revalidación inmediata, ejecución segura del manifiesto, recuperación ante fallo y liberación controlada. Ninguna de esas acciones está disponible en Fase 19C.
