# Operacion del worker y consola de monitoreo

## Proposito

Este documento define el diseno operativo del `scheduler_worker.py` y la consola visual de monitoreo futura dentro de la app.

Estado vigente: Fase 14E corrige la claridad visual del monitor del programador, agrega panel lateral redimensionable, elimina la mezcla con ejecuciones generales, separa detencion explicita versus ausencia de senal y deja preparada la operacion separada con Docker Compose. Fase 14F.1 agrega trazabilidad segura en `/panel` para detectar cuando el problema real es conectividad SQL Server y no el worker. Fase 14F.2 normaliza la cadena ODBC en `app/database/conexion.py` con `Encrypt`, `TrustServerCertificate` y `Connection Timeout` explicitos. Fase 14F.5 corrige el desfase horario Docker/SQL Server en el monitor y hace que `docker compose stop worker` deje una marca explicita `DETENIDO`. systemd sigue como alternativa documental.

Fase 15A.1 agrega solo el contrato documental de evidencia por `stdout`. El worker y el servicio de ejecuciones aun no capturan ni interpretan bloques de evidencia; esa integracion queda pendiente para fases posteriores.

## Estado actual validado

El worker automatico ya existe como proceso separado:

```powershell
python scheduler_worker.py
```

Validaciones previas:

- Ejecuta tareas automaticas.
- Cierra ejecuciones como `EXITOSA`, `ERROR` o `DETENIDA_MANUALMENTE` segun corresponda.
- No deja ejecuciones `EN_EJECUCION` colgadas en condiciones normales validadas.
- Respeta cierre seguro.
- No registra ruido operativo normal en `scheduler_eventos`.
- Registra eventos importantes en `scheduler_eventos`.
- Actualiza heartbeat en `scheduler_worker_heartbeat`.
- Desde Fase 14B.1 escribe salida operativa tambien en `logs/worker_console.log` como buffer visual limitado.
- Desde Fase 14C existen endpoints internos de solo lectura en `/api/worker/*` para consultar estado, consola, eventos y ejecuciones recientes.
- Desde Fase 15A.1 queda documentado que una futura evidencia de reporte se capturara desde `stdout` entre delimitadores oficiales, sin crear JSON persistente y sin guardar el JSON completo en BD.

## Endpoints internos de monitoreo

Rutas disponibles:

- `GET /api/worker/estado`
- `GET /api/worker/consola`
- `GET /api/worker/monitor`
- `GET /api/worker/eventos`
- `GET /api/worker/ejecuciones`

Reglas:

- Requieren sesion autenticada con permiso `SCHEDULER_CONFIG_VER`.
- No inician ni detienen el worker.
- No ejecutan comandos.
- No exponen rutas absolutas, passwords ni contenido de `.env`.
- `GET /api/worker/consola` solo lee `logs/worker_console.log`.
- `limit` en consola se acota entre `10` y `200`; por defecto responde `100` lineas.

Respuesta controlada si la consola no existe:

```json
{
  "archivo_disponible": false,
  "lineas": [],
  "mensaje": "Consola del worker no disponible. El worker aun no ha iniciado o el buffer fue limpiado."
}
```

## Panel Logs de la app

Desde Fase 14D el boton superior `Logs` deja de mostrar un registro estatico y pasa a consumir la API interna del worker.

Desde Fase 14D.3:

- el estado de la vista queda separado del estado real del programador;
- desaparece el texto ambiguo `Conectado`;
- la UI usa `Ultima senal` en vez de `heartbeat`;
- la actividad reciente usa solo eventos del programador;
- la lista independiente de `Ultimas ejecuciones` deja de mostrarse en el panel;
- `DETENIDO` solo aparece cuando el worker dejo marca explicita en `scheduler_worker_heartbeat`;
- `SIN SENAL` solo representa ausencia critica de heartbeat sin marca explicita de detencion;
- la consola reciente queda como apoyo diagnostico;
- el panel puede redimensionarse horizontalmente en escritorio.

Comportamiento:

- Abre el panel lateral derecho existente.
- Consulta `GET /api/worker/monitor`.
- Muestra estado del worker, estado del scheduler, alertas operativas, actividad reciente del programador y consola reciente.
- Permite `Actualizar`, `Pausar/Reanudar` auto-refresh y `Copiar` el registro visible.
- Permite elegir `50`, `100` o `200` lineas visibles, siempre dentro del limite ya controlado por la API.
- Refresca cada `5` segundos solo mientras el panel esta abierto.
- Al cerrar el panel, el polling se detiene.
- En escritorio permite redimensionar el ancho arrastrando el borde izquierdo del panel.

Reglas de seguridad:

- Solo lectura.
- No ejecuta comandos.
- No inicia, detiene ni reinicia el worker.
- No limpia logs.
- No expone rutas absolutas ni `.env`.
- No compite con el modulo `Ejecuciones` ni resume actividad manual de usuarios.

## Problema que resuelve

El worker evalua programaciones y lanza ejecuciones automaticas sin depender de una accion manual del usuario. Permite separar el ciclo automatico de la web Flask y mantener trazabilidad operativa.

## Que no debe hacer el worker

- No debe vivir dentro del proceso Flask.
- No debe consultar APIs externas en tiempo real para decidir feriados.
- No debe guardar secretos.
- No debe exponer `.env`.
- No debe registrar ciclos normales como ruido masivo en `scheduler_eventos`.
- No debe sustituir auditoria funcional.
- No debe enviar evidencias al cliente si el contrato futuro falla, si el bloque no aparece o si el proceso termina con error.

## Evidencia futura por stdout

Referencia oficial:

```text
docs/CONTRATO_EVIDENCIA_STDOUT.md
```

Reglas vigentes de diseno:

- La evidencia se emitira por `stdout`.
- El bloque debera estar entre `###APP_SCHEDULER_EVIDENCIA_INICIO###` y `###APP_SCHEDULER_EVIDENCIA_FIN###`.
- Antes de activar `Enviar evidencia`, la app debera validar estaticamente el script.
- Si la opcion esta activa y el bloque no aparece en ejecucion, corresponde alerta interna y no correo al cliente.
- La captura real, parseo JSON, validacion, Graph y alertas internas aun no estan implementados.

## Por que no debe ejecutarse dentro de Flask

No hacer:

```text
python run.py
  Flask
  worker interno
```

Riesgos:

- Worker duplicado por debug/reloader.
- Reinicios de Flask podrian duplicar procesos.
- Caida de web podria afectar al worker.
- Caida del worker podria afectar a la web.
- Monitoreo mas dificil.
- Operacion menos profesional.

Diseno correcto:

```text
Proceso 1: python run.py
Proceso 2: python scheduler_worker.py
```

En Docker Compose:

```yaml
services:
  web:
    command: python run.py
  worker:
    command: python scheduler_worker.py
```

## Ambientes

### Desarrollo local

Recomendacion: ejecucion manual controlada.

```powershell
python scheduler_worker.py
```

Uso:

- Validar una tarea controlada.
- Ver salida directa en terminal.
- Detener con interrupcion controlada del proceso.

### QA

Recomendacion: proceso separado del web.

Preferencia:

- Docker Compose con servicios `web` y `worker`.

Alternativa:

- `systemd` si se despliega directamente en Ubuntu sin Docker.

### Produccion

Recomendacion:

- Docker Compose con servicio `web` y servicio `worker` separados.
- No escalar `worker` con replicas mayores a `1` salvo que exista control distribuido explicito.

Alternativa:

- `systemd` con unidad dedicada para el worker.

## Opciones evaluadas

| Opcion | Uso recomendado | Ventajas | Riesgos |
|---|---|---|---|
| Ejecucion manual `python scheduler_worker.py` | Desarrollo local | Simple, visible, facil de detener | No es operacion profesional para QA/Produccion |
| Tarea programada Windows | Alternativa local/Windows | Puede iniciar proceso al arrancar sesion/equipo | Menos portable, monitoreo limitado |
| Servicio Windows con NSSM | Windows operativo | Mejor que tarea manual, reinicio automatico | Agrega dependencia externa y configuracion manual |
| Linux `systemd` | Ubuntu sin Docker | Servicio nativo, logs con `journalctl`, reinicio controlado | Requiere administrar unidad y permisos del sistema |
| Docker Compose `web` + `worker` | QA/Produccion recomendado | Separacion clara, logs por servicio, despliegue repetible | Requiere definir imagen, volumenes y variables por ambiente |

## Recomendacion tecnica

- Desarrollo local: ejecucion manual controlada.
- QA/Produccion: worker separado del proceso web.
- Preferencia: Docker Compose con servicios separados `web` y `worker`.
- Alternativa: `systemd` si se despliega en Ubuntu sin Docker.

## Docker Compose operativo

Archivos incorporados en Fase 14E:

- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`

Modelo operativo:

- `web`: ejecuta `python run.py`
- `worker`: ejecuta `python scheduler_worker.py`
- ambos usan el mismo helper de conexion SQL
- por defecto ambos leen `.env`, pero Docker puede apuntar a otro archivo mediante `DOCKER_ENV_FILE`
- ambos comparten `logs/`, `logs_tareas/`, `logs_sistema/`, `scripts/` y `env_scripts/`

Reglas:

- no levantar el worker desde Flask;
- no levantar dos workers en el mismo ambiente;
- no usar replicas mayores a `1` para `worker`;
- `logs/worker_console.log` debe quedar visible para `web` y escribible por `worker`.
- si una variable sensible contiene `$`, Docker Compose puede requerir escape en el archivo usado por contenedores; documentar el ajuste por ambiente y no reutilizarlo automaticamente como configuracion local.
- si se necesita escape distinto para Docker, usar `DOCKER_ENV_FILE` apuntando a un archivo separado basado en `.env.docker.example`.

Comandos operativos recomendados:

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f web
docker compose logs -f worker
docker compose restart worker
docker compose stop worker
docker compose up -d worker
docker compose down
```

Detalle de runtime:

- `web` fuerza `APP_HOST=0.0.0.0` dentro del contenedor para exponer Flask correctamente.
- `worker` no publica puertos.
- ambos servicios usan `restart: unless-stopped`.
- ambos servicios usan `init: true` para manejo mas limpio de senales del proceso.

Validacion minima esperada:

- `docker compose up -d --build` levanta `web` y `worker` por separado.
- `docker compose logs -f worker` muestra actividad del programador.
- la app sigue leyendo `logs/worker_console.log` mediante el volumen compartido.
- el panel `Logs` debe reflejar heartbeat, eventos y consola del worker separado.

Validacion real Fase 14F.4 antes de tocar `worker`:

- `DOCKER_ENV_FILE=.env.docker` quedo validado como flujo oficial.
- `web` conecto correctamente a SQL Server con el helper real de la app.
- login y `/panel` quedaron validados en Docker.
- `worker` no se levanto en esa fase porque la regla exigia autorizacion adicional despues de confirmar conexion y web.

Validacion real Fase 14F.5:

- `DOCKER_ENV_FILE=.env.docker` se uso explicitamente para `web` y `worker`.
- Se confirmo que el problema `SIN_SENAL` no era caida real del worker, sino comparacion entre heartbeat SQL en hora local y contenedor Docker en UTC.
- `docker-compose.yml` ahora inyecta `TZ` desde `ZONA_HORARIA` para ambos servicios.
- `app/servicios/servicio_worker_heartbeat.py` interpreta fechas del heartbeat segun `ZONA_HORARIA`, no segun la zona implicita del contenedor.
- `docker compose up -d --build web worker`: OK.
- `GET /api/worker/monitor`: `ACTIVO` con `zona_horaria=America/Santiago`.
- `docker compose stop worker`: OK.
- `GET /api/worker/monitor` posterior: `DETENIDO`.
- `scheduler_worker.py` registra `SIGTERM` y `SIGINT` como detencion controlada para no degradar a timeout cuando Docker detiene el contenedor.

Validacion final Fase 14G:

- Se repite validacion completa usando `$env:DOCKER_ENV_FILE='.env.docker'`.
- `web` valida login y `/panel` sin `08001`, sin `18456` y sin placeholder visible.
- `worker` valida inicio continuo, heartbeat, configuracion y resumen de ciclo sin traceback.
- `logs/worker_console.log` confirma buffer visual reciente correcto.
- El monitor del panel `Logs` queda validado operativamente en:
  - `ACTIVO` con worker corriendo;
  - `DETENIDO` despues de `docker compose stop worker`.
- `docker compose down` deja el stack sin contenedores activos.

## Arquitectura recomendada

```text
Usuario
  |
  v
Flask web (python run.py)
  |
  +--> SQL Server
  +--> lectura de paneles, configuracion, ejecuciones, logs

Worker (python scheduler_worker.py)
  |
  +--> SQL Server
  +--> lee configuracion_scheduler
  +--> actualiza scheduler_worker_heartbeat
  +--> registra scheduler_eventos importantes
  +--> crea ejecuciones automaticas
```

La web monitorea. El worker ejecuta. La base de datos coordina configuracion, estado y trazabilidad.

## Riesgo de workers duplicados

Riesgo principal: dos workers activos en el mismo ambiente pueden evaluar la misma programacion.

Controles existentes:

- `scheduler_worker_heartbeat` registra nombre, estado y senal de vida del worker.
- `configuracion_scheduler` controla si el scheduler esta activo.
- `permitir_ejecucion_automatica` controla lanzamientos automaticos.
- `max_ejecuciones_concurrentes` limita concurrencia.
- `clave_programacion` evita duplicados por slot automatico.
- Control de ejecucion en curso evita repetir una tarea activa.
- `scheduler_eventos` registra decisiones relevantes.

Controles recomendados para fases futuras:

- Un solo servicio `worker` por ambiente.
- No usar replicas `worker > 1` en Docker Compose.
- `nombre_worker` configurable por ambiente.
- Deteccion visible de heartbeat multiple.
- Alerta si hay mas de un worker activo reciente.
- Regla de bloqueo o liderazgo si en el futuro se permite alta disponibilidad.

## Estado inicial seguro

En instalacion limpia el scheduler debe quedar seguro:

- `scheduler_activo = 0`.
- `permitir_ejecucion_automatica = 0`.
- `scheduler_apagado = 1` en validacion `099`.
- `automatica_deshabilitada = 1` en validacion `099`.

Esto significa que el worker puede estar vivo, pero no debe ejecutar tareas automaticas si la configuracion de base de datos lo mantiene apagado.

## Monitoreo

Hay cuatro niveles de monitoreo:

1. Consola real del proceso:
   - Terminal local.
   - `docker compose logs -f worker`.
   - `journalctl` si se usa `systemd`.

2. Salida operativa persistida para la app:
   - Logging estandar de Python.
   - Archivo log controlado.
   - Tabla controlada si se justifica.
   - Ultimas lineas visibles en panel Logs.

3. Base de datos:
   - `scheduler_worker_heartbeat`.
   - Estado del worker.
   - Ultima senal.
   - Ciclos ejecutados.
   - Tareas evaluadas, ejecutadas y omitidas.

4. Eventos importantes:
   - `scheduler_eventos`.
   - Tarea ejecutada.
   - Error scheduler.
   - Omisiones relevantes.
   - No registrar ruido operativo normal.

Distinciones:

- `stdout/terminal`: salida viva del proceso.
- Log persistido: fuente controlada para que la app muestre consola visual.
- Heartbeat: estado de vida frecuente del worker.
- `scheduler_eventos`: hechos importantes.
- `ejecuciones` y `logs_tareas`: ejecucion real de scripts.
- Consola visual: vista operativa controlada dentro de la app.

## Consola visual de monitoreo en la app

La app ya tiene un boton superior `Logs` que abre un panel lateral derecho. Ese panel debe evolucionar desde registro visual estatico hacia una consola operativa real del worker.

Nombre sugerido:

- Consola del worker.
- Monitor del programador.
- Registro operativo del worker.
- Estado del programador.

La consola visual debe tener dos dimensiones:

1. Salida operativa tipo terminal.
2. Estado de vida del worker.

## Salida operativa tipo terminal

Debe mostrar lineas recientes equivalentes a lo que hoy ve el operador al ejecutar:

```powershell
python scheduler_worker.py
```

Formato esperado:

```text
[2026-06-30 10:15:01] INFO WORKER Worker iniciado.
[2026-06-30 10:15:02] INFO CONFIG Configuracion scheduler leida.
[2026-06-30 10:15:03] INFO HEARTBEAT Senal de vida actualizada.
[2026-06-30 10:16:03] INFO CICLO Revision de tareas programadas.
[2026-06-30 10:16:04] WARN SCHEDULER Scheduler apagado. No se ejecutan tareas.
[2026-06-30 10:17:10] INFO EJECUCION Tarea enviada a ejecucion automatica 47.
[2026-06-30 10:17:12] INFO EJECUCION Ejecucion 47 finalizada EXITOSA.
[2026-06-30 10:18:00] ERROR WORKER Error controlado en ciclo del worker.
```

Campos:

- Timestamp.
- Nivel.
- Origen.
- Mensaje.

Funciones futuras posibles:

- Auto-refresh.
- Pausar auto-refresh.
- Copiar registro visible.
- Filtrar por nivel.
- Ver ultimos 50, 100 o 200 registros.

## Fuente tecnica recomendada

No leer una terminal abierta del sistema operativo.

No depender de capturar CMD, PowerShell, bash ni sesiones manuales.

Alternativas:

| Fuente | Evaluacion |
|---|---|
| Logging estandar Python | Recomendado. Permite escribir a stdout y a destino persistido controlado. |
| Archivo buffer acotado | Recomendado en esta etapa. `logs/worker_console.log` como buffer visual reciente sin historial acumulativo. |
| `logs_sistema` | Util para eventos generales, no para cada ciclo normal. |
| `scheduler_eventos` | Mantener solo eventos importantes; no llenarla de ruido operativo. |
| Tabla futura `worker_logs` | No recomendada en esta etapa; solo evaluar si el buffer visual ya no alcanza en una fase posterior. |
| stdout Docker | Util para `docker compose logs -f worker`, pero la app no debe depender del Docker socket. |

Recomendacion:

- Usar logging estandar de Python.
- Mantener stdout para terminal real y Docker logs.
- Persistir salida controlada en buffer visual reciente para que la app lea ultimas lineas.
- Evitar llenar `scheduler_eventos` con ciclos normales.
- Usar heartbeat para estado de vida.
- Usar `scheduler_eventos` para eventos importantes.

Implementacion actual de Fase 14B.1:

- Modulo: `app/servicios/servicio_logging_worker.py`.
- Archivo persistido: `logs/worker_console.log`.
- Handlers: `StreamHandler` y handler propio de buffer acotado.
- Formato: `timestamp | nivel | origen | mensaje`.
- Politica: archivo unico, maximo 300 lineas, reinicio por nueva sesion y sin backups.
- La carpeta `logs/` se crea de forma segura si no existe.
- No se usan rutas absolutas locales ni se exponen secretos.
- No se usa Notepad como mecanismo operativo; el archivo existe solo como fuente tecnica para futura lectura segura desde la app.

Distincion operativa vigente:

- `logs/worker_console.log`: buffer visual reciente para futura consola.
- `scheduler_worker_heartbeat`: estado de vida y ultimo ciclo.
- `scheduler_eventos`: hechos importantes del programador.
- `ejecuciones` y `logs_tareas`: ejecucion real de scripts.

Reglas del buffer visual:

- Debe reiniciarse al iniciar una nueva sesion del worker.
- Debe conservar como maximo 300 lineas.
- No debe crear `worker_console.log.1`, `worker_console.log.2` ni archivos equivalentes.
- No debe convertirse en historico operativo, auditoria ni fuente de verdad.
- La futura UI podra mostrar solo las ultimas 100 lineas, aunque la fuente completa no supere 300.

## Estado de vida del worker

Fuente principal:

```text
scheduler_worker_heartbeat
```

Datos esperados:

- `nombre_worker`.
- `estado`.
- `ultimo_heartbeat`.
- Segundos desde ultimo heartbeat.
- Ciclos ejecutados.
- Tareas evaluadas.
- Tareas ejecutadas.
- Tareas omitidas.
- Errores recientes si existen.
- Activo/inactivo.

Interpretacion sugerida:

- Vivo: ultimo heartbeat dentro del umbral esperado.
- Advertencia: heartbeat atrasado, pero dentro de margen tolerable.
- Caido o sin senal: heartbeat muy antiguo o inexistente.

Los umbrales exactos se definiran en fase de implementacion.

## Estado del scheduler

Fuente:

```text
configuracion_scheduler
```

Datos esperados:

- `scheduler_activo`.
- `permitir_ejecucion_automatica`.
- `modo_mantenimiento`.
- `intervalo_revision_segundos`.
- `max_ejecuciones_concurrentes`.

Interpretacion:

- Si `scheduler_activo = 0`, el worker puede estar vivo, pero no ejecutara tareas.
- Si `permitir_ejecucion_automatica = 0`, el worker puede estar vivo, pero no lanzara ejecuciones automaticas.
- Si `modo_mantenimiento = 1`, el worker debe permanecer seguro y no operar segun reglas vigentes.

## UX esperada del panel Logs

Evolucion sugerida:

1. Mantener boton `Logs` en topbar.
2. Abrir panel lateral derecho.
3. Renombrar o seccionar como `Consola del worker`.
4. Mostrar chips de estado:
   - Worker vivo/inactivo/sin senal.
   - Scheduler activo/apagado.
   - Automatica habilitada/deshabilitada.
   - Ultimo heartbeat.
   - Hace X segundos/minutos.
5. Mostrar bloque visual tipo terminal:
   - Timestamp.
   - Nivel.
   - Origen.
   - Mensaje.
6. Acciones seguras:
   - Actualizar.
   - Pausar auto-refresh.
   - Copiar registro visible.
   - Filtrar nivel.
   - Ver ultimos 50/100/200.

No implementar acciones destructivas en esta fase.

## Que no debe permitir la consola visual

La consola visual no debe ser una terminal real del sistema.

No permitir:

- Escribir comandos libres.
- Ejecutar `cmd`.
- Ejecutar PowerShell.
- Ejecutar bash.
- Ejecutar Python arbitrario.
- Enviar instrucciones directas al sistema operativo.
- Exponer rutas sensibles.
- Mostrar secretos.
- Mostrar valores completos de `.env`.
- Conectarse al Docker socket.
- Reiniciar contenedores directamente.
- Detener procesos del sistema.
- Iniciar, detener o reiniciar el worker en esta fase.
- Ejecutar scripts.
- Limpiar logs.
- Borrar datos.

## Permisos

Permisos actuales que pueden aplicar en una fase futura:

- `LOGS_VER`: ver consola basica.
- `SCHEDULER_CONFIG_VER`: ver estado scheduler.
- `EJECUCIONES_VER`: ver ultimas ejecuciones.
- `EJECUCIONES_LOG_VER`: ver logs de ejecucion.

No crear permisos nuevos en Fase 14A.

Permisos futuros a evaluar:

- `WORKER_MONITOREAR`: monitoreo especifico del worker.
- `WORKER_OPERAR`: acciones operativas futuras, si se autorizan con controles estrictos.

## Comandos previstos

### Desarrollo local

```powershell
python run.py
```

En otra terminal:

```powershell
python scheduler_worker.py
```

Una vuelta controlada:

```powershell
python scheduler_worker.py --once
```

### Docker Compose futuro

Documental, no implementado aun:

```powershell
docker compose up web worker
docker compose logs -f worker
```

### systemd futuro

Documental, no implementado aun:

```bash
sudo systemctl start app-scheduler-worker
sudo systemctl status app-scheduler-worker
journalctl -u app-scheduler-worker -f
```

## Criterio de aprobacion para pasar a Fase 14C

Antes de implementar endpoints o consola visual real:

- Decision web/worker separados aceptada.
- Fuente de salida operativa implementada.
- Umbrales de heartbeat definidos.
- Permisos confirmados.
- Riesgo de worker duplicado cubierto.
- No depender de terminal real del SO.
- No depender de Docker socket desde la app.
- Estado inicial seguro validado.

## Pendientes de decision

- Politica exacta de limpieza cuando la futura UI solo consuma ultimas 100 lineas.
- Umbrales exactos de vivo/advertencia/caido.
- Permiso especifico `WORKER_MONITOREAR` o reutilizacion de permisos actuales.
- Alcance de acciones futuras: solo monitoreo o tambien operacion controlada.

## Proximas fases sugeridas

- Fase 14C: implementar endpoints de solo lectura y evolucionar panel Logs a consola visual real.
- Fase 14D: definir Docker Compose o systemd operativo.
- Fase 14E: alertas, retencion y reportes operativos.
