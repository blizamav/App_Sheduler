# Modelo minimo de notificaciones y evidencias

## Proposito

Este documento define la propuesta de Fase 15B para soportar evidencias por `stdout`, notificaciones por Microsoft Graph y alertas internas, sin implementar codigo ni SQL en esta fase.

La propuesta respeta el contrato definido en `docs/CONTRATO_EVIDENCIA_STDOUT.md`:

* no se crea JSON fisico persistente;
* no se guarda el JSON completo en base de datos;
* el script emite el bloque por `stdout`;
* la app valida, decide y envia desde un servicio central futuro;
* Graph y destinatarios quedan controlados por la app, no por el script.

## Diagnostico del modelo actual relevante

Tablas actuales relacionadas:

| Tabla | Rol actual |
|---|---|
| `tareas` | Entidad operativa principal. Define cliente, categoria, tipo, estado, ejecucion manual y borrado operativo. |
| `programaciones` | Agenda de ejecucion automatica asociada a una tarea. |
| `scripts` | Contenedor logico de script por tarea. Tiene relacion uno a uno con `tareas` e `id_version_activa`. |
| `scripts_versiones` | Versiones fisicas del script, rutas, hash, estado, `requiere_env` y `.env` por version. |
| `ejecuciones` | Historial de ejecuciones manuales/automaticas. Guarda `id_tarea`, `id_script`, `id_version`, estado, PID, salida, programacion, worker y snapshots historicos. |
| `logs_tareas` | Log tecnico de la ejecucion, ligado a `id_ejecucion`. |
| `logs_sistema` | Eventos operativos generales. |
| `auditoria_cambios` | Auditoria funcional de acciones humanas relevantes. |
| `configuracion_sistema` | Configuracion global simple, con marca `es_sensible`. |

La relacion tecnica mas importante ya existe: cada ejecucion puede indicar exactamente que tarea, script y version se ejecuto. Por eso la evidencia capturada debe colgar de `ejecuciones`, no de logs ni de scripts directamente.

## Decision recomendada

Configurar `Enviar evidencia` a nivel de `tarea`.

Justificacion:

* La tarea/proceso es la unidad operativa que el usuario entiende.
* `scripts` es un contenedor tecnico uno a uno con tarea.
* `scripts_versiones` puede cambiar; la configuracion de envio no deberia perderse por reemplazar version.
* La ejecucion ya guarda `id_version`, por lo que la trazabilidad final sigue sabiendo que archivo emitio la evidencia.
* `programaciones` define cuando ejecutar, no a quien reportar.

No se recomienda configurar por version activa en la primera version. El validador estatico debe revisar la version activa antes de permitir activar la opcion y cada ejecucion debe registrar la version real ejecutada.

Override por programacion: no recomendado en la primera version. Puede agregarse en una fase posterior con una tabla separada si una misma tarea necesita reportes distintos por horario o calendario.

## Tablas nuevas propuestas

Modelo minimo:

1. `notificaciones_config_tarea`
2. `notificaciones_destinatarios`
3. `evidencias_ejecucion`
4. `notificaciones_envios`

Configuracion global:

* usar `configuracion_sistema` para valores no sensibles simples, o
* crear `configuracion_notificaciones_global` si se prefiere UI dedicada.

Recomendacion: para primera implementacion, usar `configuracion_sistema` para parametros no sensibles y variables de entorno para secretos Graph. Crear tabla global dedicada solo si la UI crece.

## Tabla notificaciones_config_tarea

Proposito: configuracion de evidencia y alertas por tarea/proceso.

| Columna | Tipo sugerido | Nulo | Observacion |
|---|---:|---:|---|
| `id_config_notificacion` | int identity | No | PK. |
| `id_tarea` | int | No | FK a `tareas`. |
| `enviar_evidencia` | bit | No | Default `0`. |
| `plantilla_evidencia` | varchar(50) | No | Default `STDOUT_V1`. |
| `asunto_personalizado` | nvarchar(300) | Si | Si existe, puede reemplazar asunto sugerido. |
| `usar_asunto_sugerido_script` | bit | No | Default `1`. |
| `adjuntar_archivos_declarados` | bit | No | Default `1`. |
| `adjuntar_log_tecnico` | bit | No | Default `0`; evitar exponer logs a cliente por defecto. |
| `alerta_error_activa` | bit | No | Default `1`. |
| `usar_alerta_global` | bit | No | Default `1`. |
| `fecha_ultima_validacion_estatica` | datetime2(0) | Si | Momento de ultima validacion del script activo. |
| `estado_validacion_estatica` | varchar(30) | Si | `VALIDA`, `INVALIDA`, `NO_EVALUADA`. |
| `detalle_validacion_estatica` | nvarchar(500) | Si | Mensaje controlado, sin codigo completo ni secretos. |
| `activo` | bit | No | Default `1`. |
| `fecha_creacion` | datetime2(0) | No | Default `SYSDATETIME()`. |
| `fecha_actualizacion` | datetime2(0) | Si | Auditoria tecnica. |
| `usuario_creacion` | nvarchar(100) | Si | Usuario app. |
| `usuario_actualizacion` | nvarchar(100) | Si | Usuario app. |

PK:

* `PK_notificaciones_config_tarea(id_config_notificacion)`.

FK:

* `FK_notificaciones_config_tarea_tareas(id_tarea)` hacia `tareas(id_tarea)`.

Unicidad:

* indice unico filtrado `UX_notif_config_tarea_activa` sobre `id_tarea WHERE activo = 1`.

CHECK:

* `plantilla_evidencia IN ('STDOUT_V1')`.
* `estado_validacion_estatica IS NULL OR estado_validacion_estatica IN ('NO_EVALUADA','VALIDA','INVALIDA')`.

Indices:

* `IX_notif_config_tarea_tarea_activo(id_tarea, activo)`.
* `IX_notif_config_tarea_enviar(enviar_evidencia, activo)`.

## Tabla notificaciones_destinatarios

Proposito: destinatarios por configuracion, separados por tipo de envio y canal.

| Columna | Tipo sugerido | Nulo | Observacion |
|---|---:|---:|---|
| `id_destinatario` | int identity | No | PK. |
| `id_config_notificacion` | int | No | FK a configuracion. |
| `tipo_destinatario` | varchar(20) | No | `EVIDENCIA` o `ALERTA`. |
| `canal` | varchar(10) | No | `TO`, `CC`, `BCC`. |
| `email` | nvarchar(320) | No | Dato personal; enmascarar en UI segun permiso. |
| `nombre` | nvarchar(200) | Si | Nombre visible. |
| `activo` | bit | No | Default `1`. |
| `fecha_creacion` | datetime2(0) | No | Default `SYSDATETIME()`. |
| `fecha_actualizacion` | datetime2(0) | Si | Auditoria tecnica. |
| `usuario_creacion` | nvarchar(100) | Si | Usuario app. |
| `usuario_actualizacion` | nvarchar(100) | Si | Usuario app. |

PK:

* `PK_notificaciones_destinatarios(id_destinatario)`.

FK:

* `FK_notif_dest_config(id_config_notificacion)` hacia `notificaciones_config_tarea(id_config_notificacion)`.

Unicidad:

* indice unico filtrado sobre `(id_config_notificacion, tipo_destinatario, canal, email) WHERE activo = 1`.

CHECK:

* `tipo_destinatario IN ('EVIDENCIA','ALERTA')`.
* `canal IN ('TO','CC','BCC')`.
* `email LIKE '%_@_%._%'` como validacion basica; la validacion real debe estar en servicio.

Indices:

* `IX_notif_dest_config_activo(id_config_notificacion, activo)`.
* `IX_notif_dest_tipo(tipo_destinatario, activo)`.

## Tabla evidencias_ejecucion

Proposito: trazabilidad minima del bloque capturado por `stdout` sin guardar JSON completo.

| Columna | Tipo sugerido | Nulo | Observacion |
|---|---:|---:|---|
| `id_evidencia` | bigint identity | No | PK. |
| `id_ejecucion` | bigint | No | FK a `ejecuciones`. |
| `estado_evidencia` | varchar(40) | No | Estado final de evidencia. |
| `version_contrato` | varchar(20) | Si | Ej. `1.0`; puede ser null si no hubo bloque. |
| `tipo_evidencia` | varchar(80) | Si | Declarado por JSON. |
| `titulo` | nvarchar(300) | Si | Titulo validado, puede mostrarse. |
| `asunto_sugerido` | nvarchar(300) | Si | No cuerpo completo. |
| `hash_evidencia` | varchar(128) | Si | Hash SHA-256/512 del bloque capturado. |
| `cantidad_campos_resumen` | int | No | Default `0`. |
| `cantidad_adjuntos_declarados` | int | No | Default `0`. |
| `cantidad_problemas` | int | No | Default `0`. |
| `bloque_detectado` | bit | No | Default `0`. |
| `delimitador_inicio_detectado` | bit | No | Default `0`. |
| `delimitador_fin_detectado` | bit | No | Default `0`. |
| `adjunto_obligatorio_faltante` | bit | No | Default `0`. |
| `error_validacion` | nvarchar(1000) | Si | Mensaje controlado, sin JSON completo. |
| `fecha_captura` | datetime2(0) | Si | Cuando se detecto/capturo. |
| `fecha_validacion` | datetime2(0) | Si | Cuando se valido. |
| `fecha_creacion` | datetime2(0) | No | Default `SYSDATETIME()`. |
| `activo` | bit | No | Default `1`. |

PK:

* `PK_evidencias_ejecucion(id_evidencia)`.

FK:

* `FK_evidencias_ejecucion_ejecuciones(id_ejecucion)` hacia `ejecuciones(id_ejecucion)`.

Unicidad:

* `UX_evidencias_ejecucion(id_ejecucion)` para permitir cero o una evidencia por ejecucion en V1.

CHECK:

* `estado_evidencia IN ('NO_REQUERIDA','SOPORTE_NO_DECLARADO','DELIMITADORES_NO_DECLARADOS','NO_EMITIDA','CAPTURADA','INVALIDA','ERROR_DECLARADO','ADJUNTO_FALTANTE','VALIDADA')`.
* contadores `>= 0`.
* si `bloque_detectado = 0`, `hash_evidencia` puede ser null.

Indices:

* `IX_evidencias_estado_fecha(estado_evidencia, fecha_creacion DESC)`.
* `IX_evidencias_ejecucion(id_ejecucion)`.

## Tabla notificaciones_envios

Proposito: registrar cada intento de envio por Graph, tanto evidencia a cliente como alerta interna.

| Columna | Tipo sugerido | Nulo | Observacion |
|---|---:|---:|---|
| `id_envio` | bigint identity | No | PK. |
| `id_ejecucion` | bigint | No | FK a `ejecuciones`. |
| `id_evidencia` | bigint | Si | FK a `evidencias_ejecucion`; nullable para alertas sin evidencia valida. |
| `tipo_envio` | varchar(30) | No | `EVIDENCIA_CLIENTE` o `ALERTA_INTERNA`. |
| `estado_envio` | varchar(30) | No | Estado del intento. |
| `asunto` | nvarchar(300) | Si | Asunto final, revisar por datos sensibles. |
| `destinatarios_to` | nvarchar(max) | Si | Lista final serializada simple; enmascarar en UI. |
| `destinatarios_cc` | nvarchar(max) | Si | Lista final serializada simple; enmascarar en UI. |
| `destinatarios_bcc` | nvarchar(max) | Si | Lista final serializada simple; mostrar solo a roles autorizados. |
| `graph_status_code` | int | Si | Codigo HTTP. |
| `graph_request_id` | nvarchar(200) | Si | Correlacion tecnica Graph. |
| `graph_message_id` | nvarchar(200) | Si | Id de mensaje si Graph lo entrega de forma segura. |
| `error_controlado` | nvarchar(1000) | Si | Mensaje resumido, sin respuesta completa sensible. |
| `intento` | int | No | Default `1`. |
| `es_reintento` | bit | No | Default `0`. |
| `id_envio_origen` | bigint | Si | FK a `notificaciones_envios`. |
| `fecha_intento` | datetime2(0) | No | Default `SYSDATETIME()`. |
| `fecha_envio` | datetime2(0) | Si | Solo cuando queda enviado. |
| `usuario_reintento` | nvarchar(100) | Si | Para reintento manual futuro. |
| `fecha_creacion` | datetime2(0) | No | Default `SYSDATETIME()`. |
| `activo` | bit | No | Default `1`. |

PK:

* `PK_notificaciones_envios(id_envio)`.

FK:

* `FK_notif_envios_ejecuciones(id_ejecucion)` hacia `ejecuciones(id_ejecucion)`.
* `FK_notif_envios_evidencias(id_evidencia)` hacia `evidencias_ejecucion(id_evidencia)`.
* `FK_notif_envios_origen(id_envio_origen)` hacia `notificaciones_envios(id_envio)`.

Unicidad para evitar duplicar exitosos:

* indice unico filtrado `UX_notif_envio_exitoso_cliente` sobre `(id_ejecucion, tipo_envio) WHERE tipo_envio = 'EVIDENCIA_CLIENTE' AND estado_envio = 'ENVIADO' AND activo = 1`.

CHECK:

* `tipo_envio IN ('EVIDENCIA_CLIENTE','ALERTA_INTERNA')`.
* `estado_envio IN ('PENDIENTE','ENVIADO','FALLIDO','OMITIDO','NO_REQUERIDO')`.
* `intento >= 1`.
* `graph_status_code IS NULL OR graph_status_code BETWEEN 100 AND 599`.

Indices:

* `IX_notif_envios_ejecucion(id_ejecucion, fecha_intento DESC)`.
* `IX_notif_envios_evidencia(id_evidencia, fecha_intento DESC)`.
* `IX_notif_envios_estado(estado_envio, tipo_envio, fecha_intento DESC)`.
* `IX_notif_envios_reintento(id_envio_origen)`.

## Configuracion global no sensible

Opcion recomendada V1: usar `configuracion_sistema` con claves no sensibles:

| Clave sugerida | Tipo | Uso |
|---|---|---|
| `NOTIF_ALERTAS_DESTINATARIOS_DEFAULT` | string | Lista default de alertas internas si no hay destinatarios por tarea. |
| `NOTIF_GRAPH_MAIL_ENABLED` | boolean | Corte operativo no sensible; tambien debe existir variable env. |
| `NOTIF_REMITENTE_DEFAULT` | string | Buzon visible esperado, sin secreto. |
| `NOTIF_MAX_RESUMEN_CAMPOS` | int | Limite de campos del resumen. |
| `NOTIF_MAX_ADJUNTOS` | int | Limite de adjuntos. |
| `NOTIF_MAX_ADJUNTO_MB` | int | Limite de tamano por adjunto. |

No guardar secretos Graph en `configuracion_sistema`.

Tabla dedicada futura opcional: `configuracion_notificaciones_global`, solo si la UI requiere un formulario especifico con versionado de configuracion.

## Variables de entorno Graph

Deben quedar fuera de BD y fuera de Git:

* `GRAPH_TENANT_ID`
* `GRAPH_CLIENT_ID`
* `GRAPH_CLIENT_SECRET`
* `GRAPH_SCOPE`
* `GRAPH_SEND_MAIL_USER`
* `GRAPH_MAIL_ENABLED`

`GRAPH_MAIL_ENABLED` puede duplicarse como bandera operativa no sensible en `configuracion_sistema`, pero la variable de entorno debe tener prioridad para bloquear envios reales en ambientes no autorizados.

## Estados finales recomendados

`estado_evidencia`:

* `NO_REQUERIDA`: la tarea no tenia evidencia activa.
* `SOPORTE_NO_DECLARADO`: el script no declara soporte.
* `DELIMITADORES_NO_DECLARADOS`: validacion estatica falla por delimitadores.
* `NO_EMITIDA`: estaba activa, pero no aparecio bloque en runtime.
* `CAPTURADA`: bloque detectado antes de validacion final.
* `INVALIDA`: JSON invalido o contrato incompatible.
* `ERROR_DECLARADO`: JSON declara error.
* `ADJUNTO_FALTANTE`: falta adjunto obligatorio.
* `VALIDADA`: evidencia valida y apta para decidir envio.

`estado_envio`:

* `PENDIENTE`
* `ENVIADO`
* `FALLIDO`
* `OMITIDO`
* `NO_REQUERIDO`

`tipo_envio`:

* `EVIDENCIA_CLIENTE`
* `ALERTA_INTERNA`

`tipo_destinatario`:

* `EVIDENCIA`
* `ALERTA`

`canal`:

* `TO`
* `CC`
* `BCC`

Para V1 se recomiendan `CHECK` constraints en vez de catalogos nuevos, porque son listas cortas y acotadas. Si en Fase 15H crecen reglas, mover a catalogos.

## Reglas funcionales soportadas

| Caso | Soporte propuesto |
|---|---|
| Tarea con evidencia desactivada | `notificaciones_config_tarea.enviar_evidencia = 0`; opcional registrar `evidencias_ejecucion.NO_REQUERIDA`. |
| Evidencia activa y script compatible | Config activa + validacion estatica `VALIDA`; runtime puede crear `VALIDADA`. |
| Evidencia activa y script no compatible | Config no se activa o queda `estado_validacion_estatica = INVALIDA`; si ocurre runtime, `SOPORTE_NO_DECLARADO`. |
| Ejecucion OK con evidencia valida | `evidencias_ejecucion.VALIDADA` + envio `EVIDENCIA_CLIENTE`. |
| Ejecucion OK sin bloque | `NO_EMITIDA` + envio `ALERTA_INTERNA`. |
| Ejecucion OK con JSON invalido | `INVALIDA` + envio `ALERTA_INTERNA`. |
| Ejecucion ERROR con o sin bloque | no cliente; envio `ALERTA_INTERNA`. |
| Falta adjunto obligatorio | `ADJUNTO_FALTANTE` + envio `ALERTA_INTERNA`. |
| Envio evidencia exitoso | `notificaciones_envios.ENVIADO`, tipo `EVIDENCIA_CLIENTE`. |
| Envio evidencia fallido | `notificaciones_envios.FALLIDO`, tipo `EVIDENCIA_CLIENTE`; reintento futuro. |
| Envio alerta exitoso | `notificaciones_envios.ENVIADO`, tipo `ALERTA_INTERNA`. |
| Envio alerta fallido | `notificaciones_envios.FALLIDO`, tipo `ALERTA_INTERNA`; visible para operacion. |
| Reintento manual futuro | nuevo registro con `es_reintento = 1`, `id_envio_origen` e `intento` incrementado. |
| Auditoria basica | cambios de configuracion en `auditoria_cambios`; intentos de envio en `notificaciones_envios`. |

## Alerta interna

La alerta interna se modela como un envio real en `notificaciones_envios` con `tipo_envio = 'ALERTA_INTERNA'`.

Puede existir aunque:

* no haya evidencia valida;
* `id_evidencia` sea null;
* el script no declare soporte;
* Graph falle al enviar evidencia cliente;
* el proceso termine con error.

Destinatarios:

1. destinatarios `ALERTA` activos por tarea;
2. si no hay o `usar_alerta_global = 1`, destinatarios globales no sensibles;
3. fallback por variable de entorno futura.

## Evidencia omitida y fallas de contrato

* Evidencia desactivada: `NO_REQUERIDA` o sin fila en `evidencias_ejecucion`; recomendacion V1: registrar fila solo si el modulo de evidencia se evaluo.
* Evidencia activa pero no emitida: crear `evidencias_ejecucion` con `NO_EMITIDA`, `bloque_detectado = 0`, `delimitador_inicio_detectado` y `delimitador_fin_detectado` segun corresponda.
* Delimitadores no declarados en validacion estatica: bloquear activacion; si se detecta en runtime, usar `DELIMITADORES_NO_DECLARADOS`.
* JSON invalido: `INVALIDA`, guardar `hash_evidencia`, no guardar bloque.
* Graph fallido: `notificaciones_envios.FALLIDO`, `graph_status_code`, `graph_request_id` si existe y `error_controlado` resumido.

## Datos que no se deben guardar

No guardar:

* `CLIENT_SECRET`;
* `access_token`;
* `refresh_token`;
* cadenas completas de conexion;
* passwords;
* JSON completo de evidencia;
* cuerpo completo del correo en V1;
* respuesta Graph completa;
* contenido de `.env` de scripts;
* adjuntos binarios en BD;
* HTML libre generado por scripts.

## Datos sensibles o personales a cuidar

Columnas con riesgo:

* `notificaciones_destinatarios.email`;
* `notificaciones_envios.destinatarios_to`;
* `notificaciones_envios.destinatarios_cc`;
* `notificaciones_envios.destinatarios_bcc`;
* `notificaciones_envios.asunto`;
* `evidencias_ejecucion.titulo`;
* `evidencias_ejecucion.asunto_sugerido`;
* `evidencias_ejecucion.error_validacion`;
* `notificaciones_envios.error_controlado`.

En UI:

* enmascarar emails para roles no administradores;
* no mostrar `BCC` salvo permiso alto;
* truncar errores controlados;
* no mostrar hash como dato principal;
* no exponer request completo de Graph.

## Compatibilidad Docker web/worker

El modelo no depende de rutas locales ni archivos persistentes de evidencia. Web y worker comparten SQL Server como fuente de verdad y volumenes existentes solo para scripts/logs/adjuntos.

Reglas:

* `web` y `worker` deben leer la misma base mediante `app/database/conexion.py`.
* secretos Graph deben entrar por `.env` o `.env.docker`, nunca por tablas.
* `GRAPH_MAIL_ENABLED` debe permitir desactivar envio real en Docker QA.
* no se requiere volumen nuevo para JSON de evidencia.
* adjuntos declarados deben validarse contra rutas permitidas y volumenes existentes antes de enviar.

## Migraciones futuras sugeridas

Fase 15C crea la migracion incremental:

* `database/migrations/019_crear_notificaciones_evidencias.sql`

Tablas incluidas:

* `notificaciones_config_tarea`
* `notificaciones_destinatarios`
* `evidencias_ejecucion`
* `notificaciones_envios`

Incluye:

* PK/FK hacia `tareas` y `ejecuciones`.
* FK nullable de `notificaciones_envios.id_evidencia`.
* FK self-reference `notificaciones_envios.id_envio_origen` para reintentos futuros.
* CHECK constraints para estados, tipos, canales, cantidades e HTTP status.
* Indices operativos.
* Indice unico filtrado para impedir mas de un envio exitoso de tipo `EVIDENCIA_CLIENTE` por ejecucion.

Fase 15C creo el script sin ejecutarlo. En Fase 15C.2 la migracion fue ejecutada manualmente en `APP_SCHEDULER_QA` y validada correctamente.

Validacion previa confirmada:

* `dbo.tareas` existe.
* `dbo.ejecuciones` existe.
* `ejecuciones.id_ejecucion` es `bigint`, `max_length = 8`, `is_nullable = 0`.
* `tareas.id_tarea` es `int`, `max_length = 4`, `is_nullable = 0`.

Tablas creadas en `APP_SCHEDULER_QA`:

* `evidencias_ejecucion`
* `notificaciones_config_tarea`
* `notificaciones_destinatarios`
* `notificaciones_envios`

Validaciones posteriores:

* constraints principales PK, FK, CHECK, DEFAULT y UNIQUE validadas.
* indices operativos validados.
* `UX_notif_envio_exitoso_cliente` validado como indice unico filtrado con `([tipo_envio]=N'EVIDENCIA_CLIENTE' AND [estado_envio]=N'ENVIADO')`.
* las tablas quedaron sin datos iniciales reales.
* Docker `web` y `worker` levantaron correctamente despues de la migracion.
* `docker compose down` cerro contenedores y red correctamente.
* no se modifico `database/release/`.
* no se implemento Graph, UI ni capturador de `stdout`.
* no se guardan secretos, JSON completo ni cuerpo completo del correo.

Permisos futuros sugeridos:

* `database/seeds/011_permisos_notificaciones.sql`
  * permisos para ver/editar configuracion, ver evidencias, reintentar envios y administrar destinatarios.

No crear seeds en Fase 15C.

## Archivos que se tocarian en fases posteriores

Implementacion iniciada en Fase 15D:

* `app/repositorios/repositorio_notificaciones.py`
* `app/servicios/servicio_notificaciones.py`
* `app/rutas_tareas.py`
* `app/__init__.py`

Endpoints backend creados:

* `GET /api/tareas/<id_tarea>/notificaciones`
* `POST /api/tareas/<id_tarea>/notificaciones`
* `PUT /api/tareas/<id_tarea>/notificaciones`
* `POST /api/tareas/<id_tarea>/notificaciones/desactivar`

La Fase 15D permite consultar, crear/actualizar y desactivar configuracion de notificaciones por tarea. Valida email basico, destinatarios requeridos, tipos, canales y evita duplicados activos al reemplazar destinatarios. No envia correos, no captura `stdout`, no valida delimitadores del script y no implementa Graph.

## UI minima por tarea

Fase 15E agrega una interfaz minima en `/tareas/<id>/editar` para administrar la configuracion creada en Fase 15D.

Campos disponibles:

* `enviar_evidencia`.
* `usar_asunto_sugerido_script`.
* `asunto_personalizado`.
* `adjuntar_archivos_declarados`.
* `adjuntar_log_tecnico`.
* `alerta_error_activa`.
* `usar_alerta_global`.
* destinatarios `EVIDENCIA` y `ALERTA` con canal `TO`, `CC` o `BCC`.

Reglas aplicadas en UI:

* si `enviar_evidencia` esta activo, debe existir al menos un destinatario `EVIDENCIA` con canal `TO`;
* si `alerta_error_activa` esta activo y `usar_alerta_global` esta desactivado, debe existir al menos un destinatario `ALERTA` con canal `TO`;
* se valida email basico en frontend y el backend mantiene la autoridad final;
* se permite guardar configuracion sin destinatarios cuando el envio de evidencia esta apagado y la alerta usa configuracion global.

Limitaciones vigentes:

* la UI no envia correos;
* no implementa Microsoft Graph;
* no captura ni parsea `stdout`;
* no valida estaticamente todavia que el script declare soporte de evidencia;
* no muestra ni solicita secretos Graph.

## Configuracion global Mail Automatico Graph

Fase 15F separa origen, destino y contenido:

* origen del correo: configuracion global `Mail Automatico / Microsoft Graph`;
* destinatarios de evidencia: configuracion por tarea;
* destinatarios de alerta global: configuracion global Mail Graph;
* contenido/evidencia: bloque emitido por `stdout` del script en fase posterior.

Decision de modelo: se crea tabla especifica `configuracion_mail_graph` mediante la migracion incremental `database/migrations/020_crear_configuracion_mail_graph.sql`.

Se eligio tabla especifica en vez de `configuracion_sistema` porque Mail Graph requiere campos tipados, validaciones propias, estado operativo, usuario de actualizacion y regla explicita de secret por entorno.

Estado de cierre Fase 15F:

* la migracion 020 fue ejecutada manualmente en `APP_SCHEDULER_QA`;
* la tabla `configuracion_mail_graph` quedo disponible;
* `/configuracion/mail-graph` carga correctamente;
* la configuracion inicial queda inactiva por defecto;
* `client_secret_origen` queda en `ENV`;
* `client_secret_configurado` muestra `No configurado` cuando falta `GRAPH_CLIENT_SECRET`;
* no se enviaron correos ni se hicieron llamadas externas.

Ajuste posterior Fase 15F:

* la configuracion Mail Graph es global unica del sistema;
* cada guardado desde `/configuracion/mail-graph` debe actualizar la fila existente;
* no debe insertar una fila nueva por cada cambio de formulario;
* para instalaciones futuras, la migracion 020 incluye `clave_configuracion = MAIL_GRAPH` e indice unico;
* para ambientes ya ejecutados, se preparo `database/diagnostics/005_diagnostico_configuracion_mail_graph.sql` con consultas de diagnostico y propuesta comentada de consolidacion;
* no se borra ni actualiza ninguna fila existente sin autorizacion explicita.

Fase 15F.1 define una migracion incremental correctiva para `APP_SCHEDULER_QA`:

* archivo: `database/migrations/021_consolidar_configuracion_mail_graph_qa.sql`;
* conserva `id_config_mail = 3`;
* elimina solo `id_config_mail IN (1, 2, 4)`;
* valida que exista la tabla y que exista la fila 3;
* valida que la fila 3 tenga `send_mail_user = bpm@soex.cl`;
* agrega `clave_configuracion = MAIL_GRAPH` si falta;
* crea `UX_config_mail_graph_clave` para impedir multiples configuraciones globales;
* no debe ejecutarse sobre otro ambiente sin revisar IDs reales.

## Validacion estatica de soporte de evidencia

Fase 15G agrega validacion estatica del script asociado a una tarea antes de permitir activar `Enviar evidencia`.

Relacion real usada por la validacion:

* `tareas.id_tarea`;
* `scripts.id_tarea`;
* `scripts.id_version_activa`;
* `scripts_versiones.id_version`;
* `scripts_versiones.ruta_relativa`.

La ruta se resuelve internamente desde base de datos y se valida contra `RUTA_BASE_SCRIPTS`. El frontend no envia rutas.

Contrato minimo requerido en el archivo `.py` activo:

* `APP_SCHEDULER_EVIDENCIA = True`;
* `APP_SCHEDULER_EVIDENCIA_VERSION = "1.0"` o `'1.0'`;
* `###APP_SCHEDULER_EVIDENCIA_INICIO###`;
* `###APP_SCHEDULER_EVIDENCIA_FIN###`.

Reglas de seguridad:

* no se ejecuta el script;
* no se importa el script;
* no se usa `exec`, `eval` ni `importlib`;
* no se muestra el contenido del script;
* no se exponen rutas fisicas en UI;
* si `enviar_evidencia = false`, no se bloquea el guardado por falta de soporte;
* si `enviar_evidencia = true`, el backend rechaza el guardado cuando el contrato no se cumple.

Endpoint informativo:

* `GET /api/tareas/<id_tarea>/evidencia/validar-soporte`.

Campos principales:

* `activo`.
* `tenant_id`.
* `client_id`.
* `graph_scope`.
* `send_mail_user`.
* `save_to_sent_items`.
* `alertas_destinatarios_default`.
* `client_secret_origen`.
* `fecha_creacion`.
* `fecha_actualizacion`.
* `usuario_actualizacion`.

Reglas de seguridad:

* `GRAPH_CLIENT_SECRET` vive solo en `.env`, `.env.docker` o variables del servidor;
* no se guarda `client_secret` en SQL Server;
* no se guardan `access_token`, `refresh_token`, passwords ni connection strings;
* la API solo expone `client_secret_configurado: true/false`;
* si llega `client_secret` por payload, se rechaza con error controlado;
* activar Mail Graph exige `GRAPH_CLIENT_SECRET` configurado en entorno;
* Fase 15F no envia correos, no obtiene tokens y no llama a Microsoft Graph.

Implementacion futura pendiente:

* `app/repositorios/repositorio_evidencias.py`
* `app/servicios/servicio_evidencias.py`
* `app/servicios/servicio_graph.py`
* `app/servicios/servicio_ejecuciones.py`
* `app/servicios/servicio_scheduler_worker.py`
* `app/rutas_notificaciones.py`
* templates de configuracion por tarea
* `app/config.py` para variables Graph
* `.env.example` y `.env.docker.example` sin secretos reales

## Riesgos

* Guardar destinatarios y asuntos implica datos personales o sensibles.
* Si se guarda cuerpo de correo o JSON completo, aumenta riesgo de exposicion; por eso queda fuera de V1.
* Reintentos manuales requieren evitar doble envio exitoso al cliente.
* Graph puede responder con errores que contengan datos sensibles; solo guardar resumen controlado.
* Adjuntos declarados por script pueden apuntar a rutas no permitidas; deben validarse antes de enviar.
* La validacion estatica no garantiza que el script emita el bloque en runtime.

## Decisiones pendientes para el usuario

* Confirmar que la configuracion base sera por tarea.
* Confirmar que no habra override por programacion en V1.
* Confirmar si `configuracion_sistema` basta para parametros globales no sensibles o si prefiere tabla dedicada.
* Definir destinatario interno default real para alertas.
* Definir roles/permisos que podran ver destinatarios completos y BCC.
* Definir si se registrara fila `NO_REQUERIDA` para cada ejecucion sin evidencia o solo cuando el modulo de evidencia se evalua.
* Definir limites iniciales: cantidad maxima de destinatarios, adjuntos y tamano por adjunto.
