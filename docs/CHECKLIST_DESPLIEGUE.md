# Checklist de despliegue v1.0.0

## Precheck

- [ ] Rama `main` y tag de release esperado.
- [ ] `.env`/`.env.docker` existen localmente y no estan versionados.
- [ ] `DB_DATABASE=APP_SCHEDULER_QA`.
- [ ] Graph y Factory Reset deshabilitados salvo ventana autorizada.
- [ ] `docker compose config --quiet` correcto.
- [ ] Suites, compileall, Jinja y JavaScript correctos.

## QA Docker

- [ ] `docker compose build web worker`.
- [ ] `docker compose up -d web worker`.
- [ ] Web `healthy` y `/salud` responde.
- [ ] Worker `healthy` despues de registrar heartbeat.
- [ ] **Estado del sistema** no muestra lock/mantenimiento inesperado.
- [ ] Logs no exponen secretos.

## Cierre

- [ ] Scheduler queda en el estado operativo aprobado.
- [ ] Graph efectivo queda OFF si no hay ventana de envio.
- [ ] No quedan contenedores o puertos temporales.
- [ ] No se alteraron `database/release/` ni `database/bootstrap/`.
- [ ] Procedimiento detallado revisado en `docs/DESPLIEGUE.md`.
