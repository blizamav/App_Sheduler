# Operacion del Worker v1.0.0

## Responsabilidad

El Worker reconstruido es el unico ejecutor de solicitudes manuales y
automaticas. El Scheduler decide cuando reservar automaticas; la Web reserva
manuales. Ambos persisten `PENDIENTE` y nunca inician subprocess directamente.

## Comandos oficiales

```powershell
python -m app_scheduler.worker.aplicacion
python -m app_scheduler.worker.aplicacion --queue-only
python -m app_scheduler.worker.aplicacion --queue-only --once
python -m app_scheduler.worker.aplicacion --check
python -m app_scheduler.worker.aplicacion --healthcheck
```

* normal: Scheduler + cola;
* `--queue-only`: solo consume reservas existentes;
* `--queue-only --once`: un ciclo y espera de los trabajos reclamados;
* `--check`: valida configuracion sin SQL ni ciclos;
* `--healthcheck`: lee heartbeat SQL del hostname, sin reclamar cola.

## Estados

`PENDIENTE` es una solicitud durable aun no reclamada. El claim atomico cambia
a `EN_EJECUCION`, asigna Worker/PID y evita doble consumo. El motor termina en
`EXITOSA`, `ERROR` o `DETENIDA_MANUALMENTE` segun resultado.

El semaforo de UI usa:

* `OPERATIVO`: heartbeat reciente;
* `ATENCION`: señal degradada o cola que requiere revision;
* `DETENIDO`: parada explicita;
* `DESCONOCIDO`: no existe señal suficiente.

## Diagnostico

1. Abrir **Estado del sistema**.
2. Confirmar si Worker esta detenido o solo Scheduler esta OFF.
3. Revisar antiguedad y estado del heartbeat.
4. Revisar logs del servicio y la ejecucion.
5. Para recuperar pendientes sin crear automaticas, iniciar `--queue-only`.
6. No modificar estados mediante SQL manual.

## Mantenimiento y Factory Reset

Modo mantenimiento y lock Factory Reset bloquean nuevas reservas/claims segun
el flujo seguro. No deben confundirse con una caida de proceso. Factory Reset
requiere Worker detenido y permanece deshabilitado por defecto.

## Docker

Compose inicia el Worker normal y usa `restart: unless-stopped`. El healthcheck
consulta solo heartbeat. Para una parada controlada:

```powershell
docker compose stop worker
docker compose up -d worker
docker compose logs --tail 200 worker
```

## Limitacion conocida

Una fila aun `PENDIENTE` se recupera. Si el proceso cae abruptamente despues del
claim, una ejecucion puede quedar `EN_EJECUCION`. v1.0.0 no la relanza de forma
automatica para evitar duplicar efectos no idempotentes. Deben revisarse PID,
log y efectos externos antes de intervenir.
