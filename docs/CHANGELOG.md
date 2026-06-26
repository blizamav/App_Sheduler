# Changelog

## 2026-06-26 - Fase 13A.1B paginacion dinamica de eventos scheduler

### Implementado

* Se creo un parcial para el historial de eventos y su paginacion.
* `/scheduler/eventos` puede responder solo el parcial cuando recibe una peticion `fetch`.
* Los enlaces `Primero`, `Anterior`, `Siguiente` y `Ultimo` se interceptan con JavaScript.
* La actualizacion reemplaza solo el bloque de historial de eventos.
* Se mantiene la posicion visual del usuario y no se reinicia el bloque de limpieza.
* Los links conservan fallback normal si JavaScript falla o esta desactivado.

### Reglas

* No se modifico la logica de limpieza.
* No se modificaron permisos, auditoria, scheduler ni SQL.
* No se modifico `.env`.
* No se ejecuto SQL.
* No se avanzo a Fase 13B ni Fase 14.

## 2026-06-26 - Fase 13A.1B multiselect visible de limpieza scheduler

### Implementado

* Se elimino el selector `Alcance` como control principal de limpieza en `/scheduler/eventos`.
* Las categorias permitidas quedan siempre visibles como checkboxes compactos.
* Se agregan atajos pequenos: `Ruido operativo`, `Seleccionar todo` y `Deseleccionar todo`.
* El resumen distingue sin categorias, una categoria, varias categorias o todas las categorias seleccionadas.
* La previsualizacion y el modal siguen usando las categorias marcadas.

### Reglas

* No se modifico whitelist backend.
* No se modificaron permisos, auditoria, scheduler ni SQL.
* No se modifico `.env`.
* No se ejecuto SQL.
* No se avanzo a Fase 13B ni Fase 14.

## 2026-06-23 - Fase 13A.1B rediseno visual por presets de limpieza scheduler

### Implementado

* Se rediseno la seccion `Limpieza de eventos` en `/scheduler/eventos` como flujo administrativo: alcance, previsualizacion y confirmacion.
* El periodo, preset de alcance y accion `Previsualizar` quedan en una fila compacta.
* Se reemplazo la lista visible de categorias por presets: ruido operativo, eventos de ejecucion, errores y bloqueos, calendario y programacion, todas las categorias permitidas y personalizado.
* El modo `Personalizado` muestra categorias individuales como lista compacta con checkboxes normales, sin tarjetas.
* El resumen de seleccion se muestra en una franja discreta.
* La previsualizacion queda oculta hasta que el usuario la solicite.
* El modal corporativo, el checkbox obligatorio y la previsualizacion previa se mantienen sin cambios funcionales.

### Reglas

* No se modificaron repositorios, servicios ni rutas para este ajuste visual.
* No se cambio whitelist backend, permisos, auditoria ni logica de limpieza.
* No se modifico `.env`.
* No se ejecuto SQL.
* No se avanzo a Fase 13B ni Fase 14.

## 2026-06-23 - Fase 13A.1B limpieza parametrizable de eventos scheduler

### Implementado

* La limpieza de `/scheduler/eventos` ahora permite seleccionar categorias especificas mediante whitelist backend.
* Se agrego previsualizacion protegida en `POST /scheduler/eventos/limpiar/previsualizar`.
* La previsualizacion retorna total, fecha limite y detalle por categoria antes de eliminar.
* La limpieza final recalcula y elimina solo las categorias seleccionadas dentro del periodo permitido.
* El modal de confirmacion muestra periodo, fecha limite, categorias, total y detalle por categoria, con checkbox obligatorio.
* Se mantiene el permiso existente `SCHEDULER_CONFIG_EDITAR`.

### Categorias permitidas

* Ciclos iniciados.
* Ciclos finalizados.
* Omitidas por fuera de ventana.
* Tareas ejecutadas.
* Errores del scheduler.
* Omitidas por feriado.
* Duplicado de slot.
* Limite de concurrencia.
* Modo mantenimiento.
* Scheduler inactivo o ejecucion automatica deshabilitada.

### Reglas

* No se aceptan tipos libres desde frontend.
* No se uso `TRUNCATE`.
* No se borra sin periodo ni categorias.
* No se borra fuera de `scheduler_eventos`.
* No se creo migracion ni seed.
* No se modifico `database/release/`.
* No se modifico `.env`.
* No se ejecuto SQL automaticamente.
* No se avanzo a Fase 13B ni Fase 14.

## 2026-06-23 - Fase 13A.1 optimizacion de eventos del scheduler

### Implementado

* Se redujo el ruido futuro en `scheduler_eventos`: ya no se persisten `CICLO_INICIADO`, `CICLO_FINALIZADO` ni `TAREA_OMITIDA` con motivo `FUERA_DE_VENTANA`.
* Se mantienen eventos relevantes: ejecuciones, errores, feriados, duplicados, limite de concurrencia, mantenimiento, scheduler inactivo, ejecucion automatica deshabilitada y omisiones importantes.
* Se agrego limpieza controlada en `/scheduler/eventos` para eliminar eventos informativos antiguos de `scheduler_eventos`.
* La limpieza permite periodos de 20, 30, 60 y 90 dias, muestra conteo previo por opcion y usa modal corporativo con checkbox obligatorio.
* La accion usa permiso existente `SCHEDULER_CONFIG_EDITAR` y registra auditoria/log de sistema.

### Reglas

* La limpieza solo afecta `scheduler_eventos`.
* No borra ejecuciones, `logs_tareas`, `logs_sistema`, auditoria, heartbeat, tareas, scripts, usuarios, configuraciones, papelera ni snapshots.
* No se creo seed ni migracion.
* No se modifico `database/release/` porque no hubo cambio de schema ni permisos.
* No se ejecuto SQL.
* No se modifico `.env`.
* No se avanzo a Fase 13B ni Fase 14.

## 2026-06-23 - Fase 13A consolidacion SQL release limpio

### Implementado

* Se creo `database/release/` como paquete SQL consolidado para instalar `APP_SCHEDULER_QA` desde cero.
* Se agrego script de creacion de base, esquema final, seeds consolidados y validacion de instalacion.
* El esquema final integra las migraciones vigentes de seguridad, mantenedores, tareas, scripts versionados, ejecuciones, logs, scheduler, feriados, papelera operativa, snapshots y auditoria.
* Los seeds consolidados cargan roles, permisos, asignaciones, catalogos, configuracion inicial segura del scheduler y reglas base de feriados irrenunciables.
* `database/migrations/` y `database/seeds/` se mantienen como historial de desarrollo.

### Reglas

* No se incluyeron usuarios reales, passwords, servidores, rutas locales, tareas de prueba, scripts, ejecuciones, logs historicos ni auditoria historica.
* No se ejecuto SQL.
* No se modifico `.env`.
* No se cambio backend, frontend, scheduler, auditoria, papelera, roles funcionales ni ejecuciones.
* No se hizo commit ni push.
* No se avanzo a Fase 13B, Fase 14 ni fases posteriores.

## 2026-06-19 - Fase 12B.2 validacion real del scheduler_worker

### Validacion

* Se ejecuto `python scheduler_worker.py --once`.
* Se ejecuto arranque continuo breve de `python scheduler_worker.py` y se detuvo desde wrapper de prueba.
* En este entorno la validacion real contra SQL Server quedo bloqueada por error ODBC local de cifrado/credenciales: `Encryption not supported on the client` y `SSL Provider: No hay credenciales disponibles en el paquete de seguridad`.
* No se pudieron validar tareas elegibles, duplicado de slot, concurrencia, feriados, registros reales en `scheduler_eventos`, `ejecuciones`, `logs_tareas` ni heartbeat persistido.

### Corregido

* La ejecucion automatica ya no usa hilo daemon. Esto evita que `scheduler_worker.py --once` termine el proceso antes de que el monitor cierre la ejecucion automatica.
* El cierre garantizado del monitor ahora cubre tambien ejecuciones automaticas si quedan `EN_EJECUCION` por una salida anomala del monitor.
* Los fallos al registrar heartbeat/logs del worker ya no propagan excepcion cuando SQL Server no esta disponible; el worker informa error controlado por consola.

### Reglas

* No se modifico `.env`.
* No se ejecuto SQL manual ni consultas SQL desde Codex.
* No se crearon migraciones ni seeds.
* No se borro historial, auditoria, ejecuciones, logs, eventos del programador ni snapshots.
* No se cambio Papelera, roles, duplicados ni reglas de ejecucion manual.
* No se implemento Docker, systemd, Celery ni Redis.
* No se avanzo a Fase 12C ni Fase 13.

## 2026-06-19 - Fase 12B.1D Papelera: eliminacion permanente masiva segura

### Implementado

* Se agrego accion `Eliminar permanentemente todo` en `/papelera`, visible solo para usuarios con `PAPELERA_ELIMINAR_PERMANENTE` o permisos totales.
* La accion usa modal corporativo `danger`, resumen previo por entidad y checkbox obligatorio antes de habilitar la confirmacion.
* El backend ejecuta la eliminacion item por item reutilizando `eliminar_registro_permanente(...)`; no usa `DELETE` masivo bruto ni cambia reglas individuales.
* Los registros bloqueados permanecen en Papelera y el proceso continua con los siguientes registros.
* El resultado muestra encontrados, eliminados, no eliminados, errores y motivos seguros de los primeros bloqueos.
* Se registra auditoria de accion masiva `ELIMINAR_PERMANENTE_TODO_PAPELERA` y se conservan las auditorias individuales existentes por cada registro procesado.

### Reglas

* No se ejecuto SQL automaticamente.
* No se crearon migraciones ni seeds.
* No se modifico `.env`.
* No se borro historial, auditoria, ejecuciones, logs, eventos del programador ni snapshots.
* No se agrego `DELETE CASCADE` ni `ON DELETE CASCADE`.
* No se usaron `alert()`, `confirm()`, `prompt()` ni reload completo.
* No se avanzo a Fase 12B.2, 12C ni Fase 13.

## 2026-06-19 - Fase 12B.1F correccion definitiva del sidebar, encabezado y tablas

### Diagnostico

* El sidebar podia seguir viendose cortado con zoom alto porque la navegacion tenia overflow propio, pero no era la region flexible principal del aside; header, menu y footer competian por altura dentro de `100vh`.
* La topbar mantenia redundancia visual al mostrar marca y titulo mientras las vistas ya tienen contexto propio en el bloque principal.
* La eliminacion del titulo global habia dejado una topbar flotante poco integrada, con boton de sidebar suelto y espacio superior mal aprovechado.
* El hover de tablas usaba una sombra interna celeste por celda, generando rayas verticales invasivas en listados.

### Mejorado

* Sidebar fijo en desktop, desacoplado del alto del contenido, con altura `100dvh`, max-height controlado, header/footer no flexibles y navegacion como region flexible con scroll interno independiente.
* Sidebar mas compacto y estable en desktop, con ancho revisado, estado colapsado mas limpio y comportamiento off-canvas preservado en mobile.
* Contenido principal con margen izquierdo equivalente al sidebar, evitando que el menu dependa de `.app-shell` o del alto renderizado de la pagina.
* Topbar global convertida en acciones flotantes: se elimina el titulo global y la pantalla comienza con el contenido real de cada vista.
* Ajuste puntual posterior: la topbar vuelve al flujo normal como barra compacta, con toggle del sidebar a la izquierda y acciones a la derecha, sin titulo redundante ni franja vacia.
* Botones primarios, secundarios, compactos e iconicos con mejores bordes, sombras, hover, active, focus y disabled.
* Cards, contenedores y bloques con superficie mas refinada, sombra sutil, borde consistente y microinteraccion ligera.
* Tablas con encabezados mas legibles, hover suave de fila completa y sin rayas/bordes celestes verticales.
* Inputs, selects y textareas con foco mas pulido.
* Badges con borde por estado para mejorar contraste y consistencia.
* Overlay mobile, Escape y resize mantienen el sidebar en un estado visual estable sin alterar reglas funcionales.

### Validacion visual

* Se valido `/login` en anchos 390, 820 y 1280 px sin overflow horizontal global ni errores JavaScript.
* Las rutas internas no se validaron visualmente desde navegador por login requerido y sin lectura de credenciales desde `.env`.

### Reglas

* No se cambio logica funcional, rutas, servicios, consultas SQL, permisos, roles, Scheduler, Papelera, ejecuciones ni auditoria.
* No se ejecuto SQL automaticamente.
* No se crearon migraciones ni seeds.
* No se modifico `.env`.
* No se agregaron dependencias externas.
* No se usaron `alert()`, `confirm()`, `prompt()` ni reload completo.
* No se avanzo a Fase 12B.2, 12C ni Fase 13.

## 2026-06-19 - Fase 12B.1E rediseno visual profundo del shell

### Mejorado

* Sidebar redisenado con iconos textuales compactos y etiquetas persistentes, reemplazando numeracion rigida por senales visuales de modulo.
* Topbar compacta sin bloque redundante de ambiente; mantiene marca, titulo de pantalla, acciones de logs, usuario y salida.
* Fondo, sidebar, espaciados, altura de navegacion y bienvenida ajustados para una experiencia mas pulida y menos pesada.
* Estado colapsado del sidebar mantiene solo iconos textuales en desktop y recupera etiquetas completas en vista compacta.
* Se preservaron agrupaciones, permisos, rutas y visibilidad condicional del menu.

### Validacion visual

* Se valido `/login` en anchos 390, 820 y 1280 px sin overflow horizontal global ni errores JavaScript.
* Las rutas internas no se validaron visualmente desde navegador por login requerido y sin lectura de credenciales desde `.env`.

### Reglas

* No se cambio logica funcional, rutas, servicios, consultas SQL, permisos, roles, Scheduler, Papelera, ejecuciones ni auditoria.
* No se ejecuto SQL automaticamente.
* No se crearon migraciones ni seeds.
* No se modifico `.env`.
* No se agregaron dependencias externas.
* No se usaron `alert()`, `confirm()`, `prompt()` ni reload completo.
* No se avanzo a Fase 12B.2, 12C ni Fase 13.

## 2026-06-19 - Fase 12B.1D modernizacion visual general y layout responsive

### Mejorado

* App shell con sidebar de ancho variable, colapso desktop y off-canvas en pantallas compactas.
* Sidebar con scroll interno para que el menu no quede inaccesible en zoom alto o pantallas bajas.
* Boton de menu visible en topbar: en desktop colapsa/expande el sidebar y en tablet/mobile abre el menu lateral.
* Cierre automatico del sidebar al seleccionar una opcion en vista compacta.
* Tablas con overflow horizontal interno y ancho minimo controlado para evitar scroll horizontal global.
* Grillas de filtros, formularios, tarjetas y ejecuciones ajustadas para degradar mejor en tablet/mobile.
* Panel lateral de logs con scroll propio y sidebar estable para zoom alto.

### Validacion visual

* Se valido `/login` en anchos 390, 820 y 1280 px sin overflow horizontal global.
* Las rutas internas no se validaron visualmente desde navegador por login requerido y sin lectura de credenciales desde `.env`.

### Reglas

* No se cambio logica funcional, rutas, servicios, consultas SQL, motor de ejecucion, Scheduler, Papelera, roles ni duplicados.
* No se ejecuto SQL automaticamente.
* No se crearon migraciones.
* No se modifico `.env`.
* No se agregaron dependencias externas.
* No se usaron `alert()`, `confirm()`, `prompt()` ni reload completo.
* No se avanzo a Fase 12B.1E, 12B.2, 12C ni Fase 13.

## 2026-06-19 - Fase 12B.1C validacion operativa de ejecucion manual

### Validacion

* Se inicio fase de pruebas reales intensivas de ejecucion manual.
* La app local responde en `http://127.0.0.1:5000/`, pero redirige a `/login`; no se leyeron credenciales desde `.env`.
* La consulta de tareas ejecutables mediante la capa de servicios quedo bloqueada por error ODBC local de cifrado/credenciales.
* No se pudieron ejecutar desde este entorno las pruebas reales de ejecucion rapida, larga, error controlado, detencion manual, apertura de finalizadas ni verificacion sobre finalizada.

### Validaciones tecnicas realizadas

* `python -m compileall app scheduler_worker.py`.
* Contrato de polling validado para `EXITOSA`, `ERROR` y `DETENIDA_MANUALMENTE`.
* Busqueda sin coincidencias de `location.reload()`, `window.location.reload()`, `alert()`, `window.confirm()`, `confirm()` y `prompt()` en `app`.
* Busqueda sin coincidencias de `DELETE CASCADE` en `app` y `database`.
* `git diff --check`.

### Reglas

* No se ejecuto SQL automaticamente.
* No se crearon migraciones.
* No se modifico `.env`.
* No se cambio el cierre garantizado de Fase 12B.1A ni la sincronizacion visual de Fase 12B.1B.
* No se cambio `scheduler_worker.py`.
* No se avanzo a Fase 12B.1D, 12B.2, 12C ni Fase 13.

## 2026-06-19 - Fase 12B.1B sincronizacion visual de consola

### Corregido

* La consola ya no depende solo del estado renderizado al abrir la pagina.
* El polling de `/ejecuciones/<id_ejecucion>/log` ahora entrega estado actual, bandera final, codigo de salida, fecha de termino, alias `fecha_hora_fin`, duracion y mensaje de error.
* La pantalla actualiza sin recarga completa el titulo de estado, badge superior, indicador de consola, termino, duracion, codigo de salida y acciones disponibles.
* Al llegar a `EXITOSA`, `ERROR` o `DETENIDA_MANUALMENTE`, el boton de detencion/verificacion en curso se oculta o deshabilita.
* Se muestra toast no bloqueante una sola vez cuando una ejecucion abierta pasa a estado final.
* La detencion y verificacion desde consola pueden enviarse por `fetch` para evitar refresh completo y sincronizar la UI con el mismo polling.

### Diagnostico

* El backend de Fase 12B.1A cerraba correctamente la ejecucion como `EXITOSA`, pero el frontend solo refrescaba el contenido del log.
* El badge superior y algunos datos de resumen seguian mostrando el estado inicial `EN_EJECUCION`, generando contradiccion visual con el log final.

### Reglas

* No se ejecuto SQL automaticamente.
* No se crearon migraciones.
* No se modifico `.env`.
* No se cambio el motor de ejecucion ni la correccion de cierre garantizado de Fase 12B.1A.
* No se cambio `scheduler_worker.py`.
* No se agregaron `alert()`, `confirm()`, `prompt()` ni recarga completa de pagina.
* No se avanzo a Fase 12B.1C, 12B.1D, 12C ni Fase 13.

## 2026-06-19 - Fase 12B.1A cierre garantizado de ejecucion manual

### Corregido

* El hilo de ejecucion manual deja de ser `daemon`, para reducir riesgo de cierre abrupto por ciclo de vida del proceso Flask.
* El monitor manual ahora tiene cierre defensivo en `finally`: si sale y la ejecucion sigue `EN_EJECUCION`, la cierra como `ERROR`.
* Si falla el monitor de ejecucion, se intenta terminar el proceso hijo y se marca la ejecucion como `ERROR` con mensaje controlado.
* El cierre normal sigue usando `process.wait()`: returncode `0` deja `EXITOSA`; returncode distinto de `0` deja `ERROR`.
* Detenciones manuales existentes no se sobrescriben porque el cierre solo actua si la ejecucion sigue `EN_EJECUCION`.

### Diagnostico

* El proceso se lanza con `subprocess.Popen` desde `servicio_procesos.iniciar_proceso_python()`.
* La ejecucion manual se monitorea en `_ejecutar_en_segundo_plano()` dentro de `servicio_ejecuciones.py`.
* La causa probable era la combinacion de hilo `daemon=True` y ausencia de cierre garantizado en `finally`; si el monitor terminaba o era interrumpido antes de cerrar estado, la ejecucion podia quedar huerfana hasta usar `Verificar`.

### Reglas

* No se ejecuto SQL automaticamente.
* No se crearon migraciones.
* No se modifico `.env`.
* No se cambio el programador automatico ni `scheduler_worker.py`.
* No se borro historial, auditoria, ejecuciones, logs, eventos ni snapshots.
* No se avanzo a Fase 12C ni Fase 13.

## 2026-06-19 - Fase 12B cobertura ampliada de auditoria

### Agregado

* Normalizacion central de acciones de auditoria hacia nombres especificos como `CREAR_USUARIO`, `EDITAR_CONFIG_PROGRAMADOR`, `EJECUTAR_TAREA_MANUAL` y `ELIMINAR_PERMANENTE_TAREA`.
* Auditoria de bloqueos por permisos con `BLOQUEO_PERMISO` y resultado `BLOQUEADO`.
* Auditoria de bloqueos de ejecucion manual no ejecutable y detencion no permitida.
* Auditoria de errores controlados en ejecucion manual, detencion, verificacion de huerfanas y configuracion del programador.
* Auditoria de previsualizacion de sincronizacion de feriados, incluyendo errores controlados.
* Auditoria de restauracion bloqueada en Papelera.
* Auditoria de bloqueo por maximo de versiones y bloqueos operativos de versiones activas/unicas.

### Seguridad

* Sanitizacion ampliada para claves sensibles: `pass`, `key`, `api_key`, `api`, `credential`, `connection`, `conn`, `cadena_conexion`, `client_secret`, `refresh_token`, `access_token`, `smtp_password`, `db_password`, entre otras.
* Los cambios de `.env` por version siguen auditando solo metadatos, rutas/estado y presencia de archivo; no se guarda contenido ni valores.
* Auditoria sigue siendo best-effort: si falla el registro, no rompe la accion principal y deja log tecnico cuando es posible.

### Reglas

* No se ejecuto SQL automaticamente.
* No se crearon migraciones.
* No se modifico `.env`.
* No se borro historial, ejecuciones, logs, eventos, snapshots ni auditoria.
* No se agrego `DELETE CASCADE`.
* No se implementaron exportaciones, notificaciones ni reportes.
* No se avanzo a Fase 12C ni Fase 13.

## 2026-06-18 - Fase 12A.2 validacion transversal de duplicados con Papelera

### Corregido

* La validacion de duplicados ahora considera registros activos, inactivos y en Papelera Operativa antes de insertar o actualizar.
* Usuarios valida `usuario` y `email` con mensajes controlados.
* Mantenedores (`clientes`, `categorias`, `tipos`) validan `nombre_normalizado` incluyendo Papelera.
* Tareas validan la clave de negocio `nombre_tarea + cliente + categoria + tipo` incluyendo Papelera.
* Scripts bloquea la creacion de un nuevo contenedor si ya existe uno para la tarea en Papelera.
* Versiones de scripts calculan `v1`, `v2` y `v3` considerando versiones en Papelera para no reutilizar numeros reservados por `UNIQUE(id_script, numero_version)`.

### Seguridad y auditoria

* Se agrego servicio comun para clasificar duplicados como activos, inactivos, en Papelera o error de integridad SQL.
* Los bloqueos registran auditoria `BLOQUEO_DUPLICADO` con resultado `BLOQUEADO` cuando la auditoria esta disponible.
* Los errores de integridad por duplicado se traducen a mensaje amigable sin exponer `pyodbc`, constraints ni traceback.

### Reglas

* No se ejecuto SQL automaticamente.
* No se crearon migraciones.
* No se modifico `.env`.
* No se borro historial, ejecuciones, logs, eventos, snapshots ni auditoria.
* No se agrego `DELETE CASCADE`.
* No se avanzo a Fase 12B ni Fase 13.

## 2026-06-18 - Fase 12A.1 correccion visual auditoria y roles

### Corregido

* Detalle de `/auditoria/<id>` reorganizado en bloques de usuario, entidad, descripcion y valores antes/despues.
* Valores de auditoria formateados como JSON legible cuando corresponde y protegidos contra desbordes visuales.
* Reglas backend de jerarquia de roles para impedir escalamiento indebido a `SUPER_ADMIN`.
* La regla de ultimo administrador ahora permite que `SUPER_ADMIN` administre usuarios `ADMIN` si queda capacidad administrativa activa.

### Seguridad

* Solo `SUPER_ADMIN` puede asignar o quitar rol `SUPER_ADMIN`.
* `ADMIN` no puede editar, desactivar ni eliminar usuarios `SUPER_ADMIN`.
* No se puede desactivar ni borrar el usuario conectado.
* No se puede desactivar ni borrar el ultimo `SUPER_ADMIN` activo.
* El usuario definido en `.env` se mantiene como bootstrap tecnico fuera de `/usuarios`.

### Reglas

* No se ejecuto SQL automaticamente.
* No se modifico `.env`.
* No se borro historial, ejecuciones, logs, eventos, snapshots ni auditoria.
* No se avanzo a Fase 12B ni Fase 13.

## 2026-06-18 - Fase 12A auditoria base

### Agregado

* Migracion manual e idempotente `database/migrations/018_crear_o_ajustar_auditoria_cambios.sql`.
* Seed manual `database/seeds/012_permisos_auditoria.sql` para `AUDITORIA_VER` y `AUDITORIA_DETALLE`.
* Modulo `/auditoria` con filtros, paginacion y detalle.
* Servicio central `registrar_auditoria(...)` con sanitizacion de secretos.
* Registro inicial de auditoria para acciones humanas criticas: papelera, borrados operativos, usuarios, mantenedores, tareas, scripts/versiones/env, ejecucion manual, detencion, verificacion huerfana, scheduler y feriados.

### Reglas

* No se ejecuto SQL automaticamente.
* No se modifico `.env`.
* No se borro historial, ejecuciones, logs, eventos, snapshots ni auditoria.
* No se agrego `DELETE CASCADE`.
* No se avanzo a Fase 12B ni Fase 13.

## 2026-06-18 - Fase 11I revision integral post desacople historico

### Agregado

* Diagnostico manual de solo lectura `database/diagnostics/004_validacion_post_desacople_historico.sql`.
* Indicador discreto `Snapshot historico` en historial y consola cuando la ejecucion ya no tiene maestro operativo.

### Corregido

* `/ejecuciones` y `/ejecuciones/<id>` usan fallback claro para tarea, cliente, categoria, tipo, script, archivo, version y usuario cuando los IDs historicos son `NULL`.
* El filtro de usuario en ejecuciones considera `usuario_ejecucion_snapshot`.
* `/panel`, panel del programador y `/scheduler/eventos` muestran `Tarea eliminada` si el maestro operativo ya no existe.

### Reglas

* No se crearon migraciones.
* No se ejecuto SQL automaticamente.
* No se modifico `.env`.
* No se borro historial.
* No se implemento Auditoria.
* No se avanzo a Fase 12A.

## 2026-06-18 - Fase 11H desacople historico para eliminacion permanente real

### Agregado

* Migracion manual `database/migrations/017_desacople_historico_papelera.sql`.
* Diagnostico manual `database/diagnostics/003_diagnostico_desacople_historico.sql`.
* Validacion en `/papelera` para bloquear eliminacion permanente de tareas, scripts y versiones si falta la migracion 017.

### Cambiado

* La eliminacion permanente desde papelera ahora asegura snapshots, nulifica IDs historicos anulables en `ejecuciones`, `logs_tareas` y `scheduler_eventos`, y luego borra solo filas operativas.
* `ejecuciones.id_tarea`, `ejecuciones.id_script`, `ejecuciones.id_version` y `logs_tareas.id_tarea` quedan definidos por migracion como referencias historicas anulables.
* Se documenta el desacople entre historial y tablas operativas en roadmap, base de datos, flujos, modulos y seguridad.

### Reglas

* No se borra `ejecuciones`, `logs_tareas`, `logs_sistema`, `scheduler_eventos`, snapshots, auditoria futura ni archivos historicos.
* No se ejecuto SQL.
* No se modifico `.env`.
* No se implemento Auditoria.
* No se avanzo a Fase 12A.

## 2026-06-18 - Correccion post Fase 11G suma BIT en papelera

### Corregido

* `/papelera` ya no falla al calcular dependencias de tareas cuando cliente, categoria o tipo tienen `eliminado_operativo`.
* En `repositorio_papelera._dependencias_tarea()` se reemplazo la suma directa de columnas `bit` por conversion explicita a `INT`.

### Causa

* SQL Server no permite sumar columnas `bit` directamente con el operador `+`.

### Reglas

* No se cambio la logica funcional de papelera.
* No se crearon migraciones.
* No se ejecuto SQL.
* No se modifico `.env`.
* No se borro historial.
* No se implemento Auditoria.
* No se avanzo a Fase 11H ni Fase 12A.

## 2026-06-18 - Fase 11G papelera operativa funcional

### Agregado

* Ruta `GET /papelera`.
* Rutas `POST /papelera/<entidad>/<id>/restaurar` y `POST /papelera/<entidad>/<id>/eliminar-permanente`.
* Repositorio `app/repositorios/repositorio_papelera.py`.
* Servicio `app/servicios/servicio_papelera.py`.
* Template `app/templates/papelera/listado.html`.
* Seed manual `database/seeds/011_permisos_papelera.sql`.
* Acceso `Papelera operativa` en sidebar dentro de Administracion.

### Cambiado

* Sidebar reorganizado por grupos: Administracion, Operacion, Programador y Control y trazabilidad.
* Borrado normal de usuarios, clientes, categorias, tipos, tareas, scripts y versiones queda como borrado operativo.
* La eliminacion permanente queda centralizada en Papelera operativa.

### Reglas

* Restaurar deja registros como inactivos.
* Eliminar permanentemente borra solo tablas operativas o maestras si es seguro.
* No se borran `ejecuciones`, `logs_tareas`, `logs_sistema`, `scheduler_eventos`, snapshots historicos, auditoria futura ni archivos historicos.
* No se ejecuto SQL automaticamente.
* No se modifico `.env`.
* No se implemento Auditoria.
* No se avanzo a Fase 11H ni Fase 12A.

## 2026-06-18 - Ajuste diseno Fase 11G eliminacion permanente segura

### Documentado

* Se aclara que Fase 11G debe incluir `Restaurar` y `Eliminar permanentemente` desde `/papelera`.
* Se define que la eliminacion permanente borra fisicamente solo de tablas operativas o maestras cuando sea seguro.
* Se explicita que no debe borrar `ejecuciones`, `logs_tareas`, `logs_sistema`, `scheduler_eventos`, snapshots historicos, futura `auditoria_cambios` ni archivos historicos de log.
* Se documenta el modal corporativo obligatorio y el mensaje de bloqueo por dependencias operativas no historicas.

### Reglas

* No se modifico codigo funcional.
* No se crearon migraciones.
* No se ejecuto SQL.
* No se modifico `.env`.
* No se implemento Auditoria.
* No se avanzo a Fase 12A.

## 2026-06-18 - Reorganizacion formal del roadmap

### Documentado

* Se crea `docs/ROADMAP.md` como fuente formal para fases 11 a 14.
* Se actualiza el estado actual a Fase 11F con robustez operativa interna parcialmente completada.
* Se separan pendientes criticos, operativos y de mejora.
* Se documenta que eventos del programador, ejecuciones y logs no reemplazan Auditoria.
* Se explicita que `eliminado_operativo` retira de operacion normal sin eliminar fisicamente de base de datos.

### Roadmap

* Fase 11: robustez operativa interna.
* Fase 12: Auditoria.
* Fase 13: operacion y despliegue.
* Fase 14: mantenimiento avanzado.

### Reglas

* No se modifico codigo funcional.
* No se crearon migraciones.
* No se ejecuto SQL.
* No se modifico `.env`.
* No se implemento Auditoria.
* No se avanzo a Fase 12A.

## 2026-06-18 - Diagnostico disponibilidad tareas post Fase 11F

### Corregido

* El motivo de disponibilidad en `/tareas` distingue `Sin script asociado` cuando no existe fila en `scripts`.
* Se mantiene `Script inactivo` solo cuando existe script asociado y `scripts.activo = 0`.

### Agregado

* Consulta manual de diagnostico en `database/diagnostics/001_diagnostico_tareas_scripts_post_11f.sql`.
* La consulta usa los campos reales del modelo: `estado_version` y `es_activa`.

### Reglas

* No se crearon migraciones.
* No se ejecuto SQL.
* No se modifico `.env`.
* No se implemento Auditoria.
* No se avanzo a Fase 12A.

## 2026-06-18 - Correccion UX ejecutar ahora en listado de tareas

### Corregido

* `/tareas` calcula la disponibilidad de ejecucion manual en el servicio y no con una condicion parcial en el template.
* El listado distingue tarea inactiva, ejecucion en curso, script faltante/inactivo/borrado y version faltante/no disponible/borrada.
* El boton `Ejecutar ahora` deshabilitado ahora muestra el motivo exacto con `No ejecutable: ...`.

### Reglas

* No se crearon migraciones.
* No se ejecuto SQL.
* No se modifico `.env`.
* No se implemento Auditoria.
* No se avanzo a Fase 12A.

## 2026-06-18 - Correccion validacion ejecucion manual post Fase 11F

### Corregido

* `obtener_contexto_tarea_ejecucion()` ya no oculta registros por `eliminado_operativo` antes de validar; ahora devuelve el contexto y deja que el servicio genere el mensaje correcto.
* `_validar_contexto_ejecucion()` separa las validaciones de tarea activa, tarea borrada operativamente, estado de tarea, script activo, script borrado, version activa, version borrada y ejecucion en curso.
* Una tarea con `activo = 1` y `eliminado_operativo = 0` ya no se clasifica como inactiva por problemas de script, version o estado.

### Reglas

* No se crearon migraciones.
* No se ejecuto SQL.
* No se modifico `.env`.
* No se implemento Auditoria.
* No se avanzo a Fase 12A.

## 2026-06-17 - Fase 11F borrado operativo seguro con snapshots

### Agregado

* Migracion `database/migrations/016_agregar_snapshots_historial_borrado_operativo.sql`.
* Campos snapshot en `ejecuciones` para tarea, cliente, categoria, tipo, script, archivo, version y usuario.
* Campos snapshot en `scheduler_eventos` para tarea, cliente, categoria y tipo.
* Campo `eliminado_operativo` y metadatos de retiro en tareas, scripts, versiones, usuarios, clientes, categorias y tipos.
* Ruta `POST /usuarios/<id>/eliminar`.
* Borrado operativo para tareas, scripts, versiones, usuarios, clientes, categorias y tipos.

### Cambiado

* Tareas con historial se retiran de la operacion normal, pero sus ejecuciones siguen visibles usando snapshots.
* Scripts/versiones con historial se retiran de operacion sin borrar ejecuciones ni logs.
* Usuarios con historial se bloquean, se ocultan del mantenedor y conservan nombre/login historico.
* Clientes/categorias/tipos usados por tareas se ocultan de listados/selects conservando nombres historicos.
* `/panel`, scheduler, panel del programador y selects operativos excluyen registros con `eliminado_operativo = 1`.
* `/ejecuciones` y consola usan `COALESCE(snapshot, maestro)` para seguir mostrando datos legibles.

### Reglas

* No se borra historial de ejecuciones.
* No se borran logs historicos.
* No se borran eventos del programador.
* No se ejecuta SQL automaticamente.
* No se modifica `.env`.
* No se implementa Auditoria.
* No se avanza a Fase 12A.

## 2026-06-17 - Control de ejecuciones huerfanas

### Agregado

* Servicio `app/servicios/servicio_control_ejecuciones.py`.
* Funcion `proceso_existe(pid)` compatible con Windows y POSIX cuando es posible.
* Funcion `verificar_ejecucion(id_ejecucion)` para validar una ejecucion puntual.
* Funcion `detectar_ejecuciones_huerfanas()` para revision controlada de ejecuciones en curso.
* Accion `Verificar ejecucion` en la consola de ejecucion.

### Corregido

* Si una ejecucion queda `EN_EJECUCION` pero su `pid_proceso` ya no existe, puede marcarse como `ERROR` con mensaje controlado.
* `/panel` solicita explicitamente solo las ultimas 6 ejecuciones.

### Reglas

* No se matan procesos automaticamente.
* No se crean ejecuciones nuevas.
* No se ejecuta SQL automaticamente.
* No se modifica `.env`.
* No se implementa Auditoria.
* No se avanza a Fase 12A.

## 2026-06-17 - Fase 11D.2 historial filtrable eventos programador

### Agregado

* Ruta `/scheduler/eventos`.
* Template `app/templates/scheduler/eventos.html`.
* Listado paginado server-side de eventos activos del programador.
* Filtros por fecha desde, fecha hasta, tarea, tipo evento, decision, motivo, proceso y texto en detalle.
* Acceso desde sidebar y desde `/scheduler/panel`.

### Reglas

* La vista consulta solo `scheduler_eventos` con `activo = 1`.
* La paginacion usa `OFFSET / FETCH` y no carga todos los registros en memoria.
* No se crean ejecuciones para omisiones.
* No se implementa Auditoria.
* No se crearon migraciones.
* No se ejecuto SQL.
* No se modifico `.env`.
* No se avanzo a Fase 12A.

## 2026-06-17 - Fase 11D.1 resumen inteligente eventos programador

### Agregado

* Resumen de eventos del programador en `/scheduler/panel`.
* Conteos del dia: eventos hoy, tareas ejecutadas, tareas omitidas y errores del programador.
* Desglose de omisiones por motivo del dia.
* Tabla compacta de ultimos 10 eventos relevantes.
* Funcion `limpiar_eventos_antiguos(dias_retencion=90)` para retencion logica.

### Criterio de relevancia

* Se priorizan `ERROR_SCHEDULER`, `TAREA_EJECUTADA` y omisiones por `FERIADO`, `EJECUCION_EN_CURSO`, `DUPLICADO_SLOT` y `LIMITE_CONCURRENCIA`.
* `CICLO_INICIADO`, `CICLO_FINALIZADO` y `FUERA_DE_VENTANA` quedan como resumen para evitar ruido visual.

### Reglas

* No se crea `/scheduler/eventos`.
* No se implementan filtros avanzados ni exportacion.
* No se ejecuta limpieza automatica.
* No se eliminan eventos fisicamente; la retencion marca `activo = 0`.
* No se crearon migraciones.
* No se ejecuto SQL.
* No se modifico `.env`.
* No se implemento Auditoria.
* No se avanzo a Fase 12A.

## 2026-06-17 - Correccion Fase 11D visualizacion eventos programador

### Corregido

* `/scheduler/panel` ahora renderiza explicitamente `eventos_programador`.
* La seccion `Eventos recientes del programador` queda visible debajo del estado del proceso programador.
* La tabla muestra fecha, tarea, tipo evento, decision, motivo, detalle y proceso.
* El mensaje sin datos queda como `Sin eventos recientes del programador`.

### Reglas

* Los datos se leen desde `scheduler_eventos`.
* No se crearon migraciones nuevas.
* No se ejecuto SQL.
* No se modifico `.env`.
* No se implemento Auditoria.
* No se avanzo a Fase 12A.

## 2026-06-17 - Fase 11D eventos y omisiones del programador

### Agregado

* Migracion `database/migrations/015_crear_eventos_programador.sql`.
* Repositorio `app/repositorios/repositorio_scheduler_eventos.py`.
* Servicio `app/servicios/servicio_scheduler_eventos.py`.
* Registro de eventos de ciclo iniciado, ciclo finalizado, tarea ejecutada, tarea omitida y error controlado del programador.
* Visualizacion de eventos recientes en `/scheduler/panel`.

### Decisiones

* Las tareas omitidas no crean registros en `ejecuciones`.
* Las tareas omitidas no crean `logs_tareas`.
* `logs_sistema` no se usa para cada omision operativa del programador.
* El heartbeat se mantiene separado en `scheduler_worker_heartbeat`.
* La migracion 015 queda pendiente de ejecucion manual en SQL Server.

### Reglas

* No se ejecuto SQL.
* No se modifico `.env`.
* No se implemento auditoria funcional.
* No se avanzo a Fase 12A.

## 2026-06-17 - Fase 11C modernizacion visual UI/UX general

### Cambiado

* Modernizacion visual general de sidebar, topbar, botones, cards, tablas, formularios, filtros, modales, toasts, consola e historial agrupado.
* Correccion de textos visibles: `Scheduler` pasa a `Programador`, `Worker` a `Proceso programador` y `Heartbeat` a `Senal de vida` donde corresponde en UI.
* Retiro de etiquetas visibles de fase en pantallas operativas, reemplazadas por lenguaje de operacion.
* Botones tipo enlace quedan sin subrayado y con estados hover/focus consistentes.
* La consola de ejecucion mantiene polling y formato de logs, pero recibe estilo terminal mas profesional.

### Reglas

* No se modifico logica funcional.
* No se crearon migraciones.
* No se ejecuto SQL.
* No se modifico `.env`.
* No se avanzo a otra fase funcional.

## 2026-06-17 - Fase 11B heartbeat worker scheduler

### Agregado

* Migracion `database/migrations/014_crear_scheduler_worker_heartbeat.sql`.
* Repositorio `app/repositorios/repositorio_worker_heartbeat.py`.
* Servicio `app/servicios/servicio_worker_heartbeat.py`.
* Registro de inicio, inicio de ciclo, fin de ciclo, error y detencion controlada del worker.
* Seccion `Estado del worker` en `/scheduler/panel`.

### Cambiado

* `scheduler_worker.py --once` ejecuta un ciclo y marca salida controlada como `DETENIDO`.
* `servicio_scheduler_worker.py` actualiza heartbeat y contadores del ultimo ciclo.
* `/panel` deja de informar que el heartbeat esta pendiente y muestra estado del worker desde la nueva capa de servicio.

### Reglas

* No se registra un log de sistema por cada heartbeat.
* `logs_sistema` queda reservado para inicio, detencion, error, recuperacion o fallos al actualizar heartbeat.
* No se implementa iniciar/detener worker desde la app.
* No se avanza a Fase 11C.

## 2026-06-17 - Fase 11A.1 panel principal general

### Cambiado

* `/panel` deja de mostrar textos simulados o referencias a fases antiguas.
* El panel principal ahora carga metricas reales desde SQL Server mediante `app/repositorios/repositorio_panel.py` y `app/servicios/servicio_panel.py`.
* Se muestran total de tareas, tareas activas, scripts activos, tareas con script asociado, ejecuciones del dia, exitosas, errores, en curso, feriados del anio y ultima ejecucion.
* Se agregan accesos rapidos a tareas, ejecuciones, panel scheduler, configuracion scheduler, feriados y sincronizacion de feriados segun permisos.
* Se agregan ultimas ejecuciones con enlace a consola.
* En ese momento se mantenia aviso explicito de que el heartbeat del worker quedaba pendiente; fue resuelto en Fase 11B.

### No implementado

* No se ejecutaron migraciones.
* No se modifico `.env`.
* No se agrego heartbeat del worker.
* No se avanzo a Fase 11B.

## 2026-06-17 - Fase 11A panel operativo scheduler

### Agregado

* Ruta `/scheduler/panel`.
* Template `app/templates/scheduler/panel.html`.
* Repositorio `app/repositorios/repositorio_panel_scheduler.py`.
* Servicio `app/servicios/servicio_panel_scheduler.py`.
* Accesos separados en sidebar para panel operativo y configuracion scheduler.

### Incluye

* Configuracion actual del scheduler.
* Estado activo/inactivo, ejecucion automatica, mantenimiento, intervalo y concurrencia.
* Ultimas ejecuciones automaticas.
* Errores recientes del scheduler.
* Tareas programadas candidatas.
* Estado del calendario local de feriados.

### No implementado

* No inicia ni detiene el worker.
* No edita configuracion desde el panel.
* No conecta nuevas APIs externas.
* No implementa notificaciones.
* No avanza a Fase 11B.

## 2026-06-17 - Correccion preview Fase 10B

### Corregido

* Se corrigio error en `feriados/sincronizar.html` causado por `preview.items`.
* La estructura `preview` ahora usa la clave `feriados_preview` para evitar conflicto con `dict.items` de Python/Jinja.
* La aplicacion de sincronizacion tambien usa `preview["feriados_preview"]`.

### Validado

* `python -m compileall app scheduler_worker.py`.
* Render de vista previa de sincronizacion con feriados simulados.
* Aplicacion simulada de sincronizacion con insercion `API_NAGER`.
* Validacion real en la app: `/feriados/sincronizar` carga correctamente.
* Consulta real desde la app para `2026 / CL` sin `TypeError`.
* Vista previa renderizada correctamente usando `preview.feriados_preview`.
* Feriados retornados por Nager.Date visibles en pantalla.
* Aplicar sincronizacion validado correctamente desde la app.
* No se duplican fecha + pais.
* Sin referencias a Nager.Date o `requests` desde `scheduler_worker.py`.
* Sin `alert()`, `window.confirm()` ni `prompt()`.

## 2026-06-17 - Fase 10B sincronizacion Nager.Date

### Agregado

* Migracion `database/migrations/013_crear_reglas_feriados_irrenunciables.sql`.
* Seed `database/seeds/009_reglas_irrenunciables_chile.sql`.
* Seed `database/seeds/010_permisos_sincronizacion_feriados.sql`.
* Dependencia `requests`.
* Cliente `app/servicios/cliente_nager_date.py`.
* Servicio `app/servicios/servicio_sincronizacion_feriados.py`.
* Repositorio `app/repositorios/repositorio_reglas_feriados.py`.
* Rutas `/feriados/sincronizar`, `/feriados/sincronizar/preview` y `/feriados/sincronizar/confirmar`.
* Template `app/templates/feriados/sincronizar.html`.

### Validado

* `python -m compileall app scheduler_worker.py`.
* Rutas `/feriados/sincronizar`, `/feriados/sincronizar/preview` y `/feriados/sincronizar/confirmar`.
* Render de pantalla de sincronizacion.
* Consulta real a Nager.Date para `2026/CL`, con 17 feriados retornados.
* Calculo de irrenunciable por regla local simulado.
* Clasificacion `NUEVO`, `MANUAL_NO_SOBRESCRIBE`, `ACTUALIZAR` y `SIN_CAMBIOS`.
* Busqueda sin `alert()`, `window.confirm()` ni `prompt()`.
* Verificacion de que `scheduler_worker.py` no importa ni consulta Nager.Date.

### Cambiado

* `/feriados` agrega boton `Sincronizar feriados`.
* `repositorio_feriados.py` soporta buscar por fecha + pais, insertar `API_NAGER` y actualizar feriados `API_NAGER`.
* Documentacion actualizada para Nager.Date, reglas locales, prioridad `MANUAL` y permiso `FERIADOS_SINCRONIZAR`.

### No implementado

* No se implemento sincronizacion automatica programada.
* No se conecto Nager.Date al scheduler.
* No se implementaron notificaciones.
* No se avanzo a Fase 10C.

## 2026-06-16 - Fase 10A calendario local de feriados

### Validado localmente

* Se ejecuto `database/migrations/012_crear_calendario_feriados.sql` en SQL Server local.
* Se ejecuto `database/seeds/008_permisos_feriados.sql` en SQL Server local.
* La tabla `feriados` fue creada correctamente.
* Los permisos `FERIADOS_*` fueron insertados.
* `/feriados` carga correctamente.
* Se valido crear, editar, activar y desactivar feriados manuales.
* Se valido bloqueo de duplicado para fecha + pais activa.
* `servicio_calendario.es_feriado` retorna `True` con feriado activo y `False` sin feriado activo.
* El scheduler omite tareas automaticas en feriado cuando `ejecutar_en_feriados = 0`.
* El scheduler permite ejecutar en feriado cuando `ejecutar_en_feriados = 1`.
* La ejecucion manual no se bloquea por feriados.

### Agregado

* Migracion `database/migrations/012_crear_calendario_feriados.sql`.
* Seed `database/seeds/008_permisos_feriados.sql`.
* Modulo web `/feriados` con listado, filtros, creacion, edicion, activacion/desactivacion y eliminacion controlada.
* Repositorio `app/repositorios/repositorio_feriados.py`.
* Rutas `app/rutas_feriados.py`.
* Templates `app/templates/feriados/listado.html` y `app/templates/feriados/formulario.html`.
* Servicio calendario con `es_feriado`, `obtener_feriado`, `listar_feriados` y `validar_fecha_laboral`.
* Integracion del worker para omitir tareas automaticas en feriado cuando `ejecutar_en_feriados = 0`.

### Cambiado

* Sidebar agrega acceso a Feriados.
* `servicio_scheduler_worker.py` consulta calendario local antes de iniciar ejecuciones automaticas.
* Documentacion actualizada para separar Fase 10A local de Fase 10B externa.

### No implementado

* No se conecto API externa de feriados.
* No se implemento sincronizacion automatica externa.
* No se implementaron notificaciones.
* No se avanzo a Fase 10B.

## 2026-06-16 - Ajuste visual Fase 9D

### Cambiado

* Se elimino de `/ejecuciones` el bloque visual de resumen `Total`, `Exitosas`, `Errores`, `En ejecucion` y `Detenidas`.
* Se mantiene el total discreto en header/paginacion.
* Se mantienen filtros, paginacion, agrupacion ano/mes/dia y accion `Ver consola`.

### No implementado

* No se creo migracion.
* No se avanzo a Fase 10.

## 2026-06-16 - Fase 9D historial agrupado de ejecuciones

### Agregado

* Vista `/ejecuciones` agrupada por ano, mes y dia.
* Filtros por ID, tarea, origen, estado, ano, mes, dia, fecha desde/hasta, usuario y worker.
* Paginacion server-side con `page` y `per_page`.
* Resumen por filtro: total, exitosas, errores, en ejecucion y detenidas.
* Meses en espanol.

### Cambiado

* `repositorio_ejecuciones.py` agrega consulta paginada, `COUNT` y resumen por estado con los mismos filtros.
* `servicio_ejecuciones.py` valida filtros y agrupa solo la pagina actual.
* `ejecuciones/listado.html` deja de ser tabla plana y pasa a vista historica agrupada.

### No implementado

* No se creo migracion.
* No se conecto API de feriados.
* No se implementaron notificaciones.
* No se implemento dashboard avanzado.
* No se avanzo a Fase 10.

## 2026-06-16 - Fase 9C timestamps por linea en logs de ejecucion

### Agregado

* Servicio `app/servicios/servicio_logs_ejecucion.py`.
* Formato estandar por linea: `YYYY-MM-DD HH:mm:ss | NIVEL | mensaje`.
* Timestamps para inicio, origen, tarea, script, version, `.env`, PID, salida de script, codigo de salida, estado final y detencion manual.

### Cambiado

* `servicio_ejecuciones.py` escribe logs de ejecucion usando servicio centralizado.
* Consola y polling muestran las lineas ya formateadas desde el archivo fisico.

### No implementado

* No se creo migracion.
* No se conecto API de feriados.
* No se implementaron notificaciones.
* No se implemento dashboard avanzado.
* No se avanzo a Fase 10.

## 2026-06-16 - Fase 9B worker automatico separado

### Agregado

* `scheduler_worker.py` como proceso separado.
* Servicio `servicio_scheduler_worker.py`.
* Servicio `servicio_programador.py` para evaluar programaciones.
* Repositorio `repositorio_scheduler.py`.
* Placeholder `servicio_calendario.py`.
* Migracion `011_agregar_control_scheduler_ejecuciones.sql`.
* Ejecuciones automaticas con `fecha_programada`, `clave_programacion` y `nombre_worker`.
* Listado basico `/ejecuciones`.
* Sidebar con acceso a ejecuciones.

### Cambiado

* `servicio_ejecuciones.py` reutiliza el motor de Fase 8 para ejecuciones automaticas.
* `repositorio_ejecuciones.py` soporta listado y campos opcionales de Fase 9B.
* La consola muestra origen, worker y fecha programada.

### No implementado

* No se conecto API de feriados.
* No se implementaron notificaciones.
* No se implemento dashboard avanzado del scheduler.
* No se avanzo a Fase 10.

## 2026-06-16 - Fase 9A validada localmente

### Validado

* Se ejecuto `database/migrations/010_crear_configuracion_scheduler.sql` en SQL Server local.
* Se ejecuto `database/seeds/007_permisos_scheduler.sql` en SQL Server local.
* La tabla `configuracion_scheduler` fue creada correctamente.
* Existe un registro inicial activo con defaults seguros.
* `scheduler_activo` quedo apagado por defecto.
* `permitir_ejecucion_automatica` quedo deshabilitado por defecto.
* `intervalo_revision_segundos` quedo en 60.
* `max_ejecuciones_concurrentes` quedo en 3.
* `modo_mantenimiento` quedo desactivado.
* Los permisos `SCHEDULER_CONFIG_VER` y `SCHEDULER_CONFIG_EDITAR` fueron insertados.
* La ruta `/scheduler/configuracion` carga correctamente.
* La pantalla permite editar configuracion.
* Guardar cambios muestra modal corporativo con resumen.
* Guardar sin cambios muestra toast.
* Las validaciones bloquean valores fuera de rango.
* Los cambios quedan registrados en `logs_sistema`.

### No implementado

* No se implemento worker automatico.
* No se ejecutan tareas automaticas.
* No se conecto API de feriados.
* No se avanzo a Fase 9B.

## 2026-06-15 - Fase 9A configuracion scheduler

### Agregado

* Modulo `/scheduler/configuracion`.
* Migracion `010_crear_configuracion_scheduler.sql`.
* Seed `007_permisos_scheduler.sql`.
* Tabla `configuracion_scheduler` con defaults seguros.
* Pantalla para ver y editar scheduler activo, ejecucion automatica, intervalo, maximo concurrentes, modo mantenimiento, worker y descripcion.
* Modal corporativo con resumen de cambios.
* Toast `No hay cambios para guardar.` cuando no hay diferencias.
* Logs de sistema para cambios.

### No implementado

* No se implemento worker automatico.
* No se ejecutan tareas automaticas.
* No se conecto API de feriados.
* No se avanzo a Fase 9B.

## 2026-06-15 - Fase 8 validada localmente

### Validado

* Se ejecuto `database/seeds/006_permisos_ejecuciones.sql` en SQL Server local.
* Los permisos `EJECUCIONES_*` fueron insertados correctamente.
* La ejecucion manual de tarea con script activo funciona.
* La consola muestra stdout y el polling actualiza el log.
* La ejecucion finaliza como `EXITOSA` cuando el script termina bien.
* La detencion manual deja la ejecucion en `DETENIDA_MANUALMENTE`.
* Se registra `pid_proceso`.
* Se genera archivo de log en `logs_tareas/`.
* Se valido ejecucion sin `.env` y con `.env` de prueba usando `os.getenv()`.
* No se mostraron secretos.

### No implementado

* No se implemento scheduler automatico.
* No se conecto API de feriados.
* No se avanzo a Fase 9.

## 2026-06-15 - Fase 8 ejecucion manual con consola

### Agregado

* Modulo de ejecuciones manuales.
* Boton `Ejecutar ahora` en tareas y scripts.
* Validaciones previas de tarea, script, version activa, archivo `.py`, `.env` requerido y ejecucion simultanea.
* Registro en `ejecuciones` con origen `MANUAL`, estado y `pid_proceso`.
* Archivo de log por ejecucion en `logs_tareas/AAAA/MM/DD/`.
* Vista `/ejecuciones/<id_ejecucion>` con consola visual.
* Polling HTTP cada 3 segundos en `/ejecuciones/<id_ejecucion>/log`.
* Boton `Detener ejecucion` con modal corporativo.
* Seed incremental `database/seeds/006_permisos_ejecuciones.sql`.

### Seguridad

* No se muestra contenido de `.env`.
* No se usa `shell=True`.
* No se implemento scheduler automatico.
* No se conecto API de feriados.
* No se avanzo a Fase 9.

## 2026-06-15 - Migracion 009 validada localmente

### Validado

* Se ejecuto `009_corregir_nombre_script_contenedor.sql` en SQL Server local sin errores.
* La migracion afecto 0 filas porque no existian scripts antiguos con `nombre_script` terminado en `.py`.
* Este resultado es correcto para el ambiente local actual.
* La nueva logica aplica para los proximos scripts cargados.

### No implementado

* No se avanzo a Fase 8.
* No se ejecutan scripts.
* No se implemento scheduler.

## 2026-06-15 - Fase 7.5 contenedor de script y archivo versionado

### Corregido

* Al asociar el primer archivo `.py`, `scripts.nombre_script` deja de tomar el nombre del archivo cargado.
* El contenedor `scripts` ahora usa nombre descriptivo `Script de {nombre_tarea}`.
* Los nombres reales de archivos `.py` quedan exclusivamente en `scripts_versiones.nombre_archivo`.
* La vista de scripts mantiene como protagonista el archivo activo real desde la version activa.
* Se agrega migracion correctiva `009_corregir_nombre_script_contenedor.sql` para registros antiguos cuyo `nombre_script` termine en `.py`.

### No implementado

* La migracion 009 no se ejecuto automaticamente desde Codex; fue ejecutada manualmente y validada localmente.
* No se modifico SQL ya ejecutado.
* No se ejecutan scripts.
* No se implemento scheduler.
* No se avanzo a Fase 8.

## 2026-06-15 - Fase 7.4 eliminacion clara de scripts y versiones

### Corregido

* El boton superior ahora dice `Eliminar script completo` para aclarar que afecta el contenedor de script y todas sus versiones.
* El modal de script completo advierte que la accion afecta todas las versiones cargadas.
* En la tabla, los botones ahora dicen `Activar version`, `Desactivar version` y `Eliminar version`.
* El modal de `Eliminar version` aclara que solo afecta la version seleccionada y no las demas.
* La eliminacion de version activa se bloquea y pide activar otra version antes.
* La eliminacion de la unica version se bloquea y sugiere usar `Eliminar script completo`.
* Los bloqueos y eliminaciones quedan diferenciados en `logs_sistema`.

### No implementado

* No se modifico SQL.
* No se ejecutan scripts.
* No se implemento scheduler.
* No se avanzo a Fase 8.

## 2026-06-15 - Fase 7.3 simplificacion de script activo

### Corregido

* El bloque superior de `Scripts de tarea` deja de mostrar el nombre logico del script.
* La vista principal muestra solo el archivo activo real, version activa, estado `.env` y estado del script.
* El nombre logico se mantiene internamente en base de datos y servicios, sin exponerse por defecto al usuario operativo.

### No implementado

* No se modifico SQL.
* No se ejecutan scripts.
* No se implemento scheduler.
* No se avanzo a Fase 8.

## 2026-06-15 - Fase 7.2 script activo visible

### Corregido

* El bloque superior de `Scripts de tarea` ahora muestra el archivo activo real desde `scripts_versiones`.
* El nombre logico del script se mantenia como dato secundario hasta Fase 7.3.
* Se muestra version activa, estado `.env` y estado del script en badges.
* Si no hay script asociado, el bloque indica `Sin script asociado todavia`.

### No implementado

* No se modifico SQL.
* No se ejecutan scripts.
* No se implemento scheduler.
* No se avanzo a Fase 8.

## 2026-06-15 - Fase 7.1 mensajes contextuales de scripts

### Corregido

* Cuando una tarea no tiene script, el formulario ahora indica `Asociar script` y el modal explica que se creara v1 activa.
* Cuando ya existe v1 o v2, el modal indica que se creara v2 o v3 segun corresponda.
* Cuando ya existen tres versiones, la pantalla indica que se debe reemplazar una version existente y no sugiere crear v4.
* Los modales de reemplazo de version, cambio de version activa y gestion de `.env` usan textos contextuales.

### No implementado

* No se modifico SQL.
* No se ejecutan scripts.
* No se implemento scheduler.
* No se avanzo a Fase 8.

## 2026-06-15 - Fase 7 gestion de scripts versiones y env

### Agregado

* Modulo de scripts por tarea en `/tareas/<id_tarea>/scripts`.
* Carga segura de archivos `.py` dentro de `scripts/`.
* Versionamiento v1, v2 y v3 por script logico.
* Bloqueo de cuarta version directa; se debe reemplazar una existente.
* Cambio de version activa con modal corporativo.
* Reemplazo, desactivacion y eliminacion controlada de versiones.
* Gestion de `.env` por version dentro de `env_scripts/`, sin mostrar contenido.
* Seed incremental `database/seeds/005_permisos_scripts.sql`.

### Seguridad

* Validacion de extension, tamano y rutas internas.
* No se ejecutan scripts cargados.
* No se lee ni muestra contenido de `.env`.
* No se guardan secretos en base de datos; solo rutas.

### No implementado

* No se implemento scheduler.
* No se implemento ejecucion real.
* No se implemento consola en vivo.
* No se avanzo a Fase 8.

## 2026-06-15 - Fase 6.2 ajuste visual de aviso sin cambios

### Cambiado

* El aviso `No hay cambios para guardar.` deja de mostrarse incrustado dentro del formulario.
* Se agrega componente `toast` corporativo flotante para avisos ligeros del sistema.
* El toast aparece sin recargar la pagina, con animacion suave, cierre manual y autocierre.

### No implementado

* No se modifico SQL.
* No se ejecutan scripts.
* No se implemento scheduler.
* No se avanzo a Fase 7.

## 2026-06-15 - Fase 6.2 deteccion de cambios reales en tareas

### Corregido

* Al editar una tarea sin modificar datos ya no se muestra modal de confirmacion.
* El formulario no se envia si no existen cambios reales.
* Se muestra mensaje visual: `No hay cambios para guardar.`
* El backend tambien detecta POST sin cambios y evita `UPDATE`, logs de edicion y cambio de `fecha_actualizacion`.

### Tecnico

* Comparacion normalizada de textos, selects, booleanos, programacion y dias de semana.
* La deteccion aplica solo a edicion; la creacion sigue mostrando resumen siempre.

### No implementado

* No se modifico SQL.
* No se ejecutan scripts.
* No se implemento scheduler.
* No se avanzo a Fase 7.

## 2026-06-15 - Fase 6.1 resumen de confirmacion de tareas

### Agregado

* Modal de confirmacion enriquecido al crear y editar tareas.
* Resumen previo con datos generales, programacion, feriados y estado.
* Validacion frontend previa para no mostrar resumen con programacion incompleta.
* Soporte reutilizable en el modal global para contenido de resumen generado por JS.

### No implementado

* No se modifico SQL.
* No se ejecutan scripts.
* No se implemento scheduler.
* No se avanzo a Fase 7.

## 2026-06-15 - Fase 6 tareas con programacion base

### Agregado

* Modulo `/tareas` con listado, filtros, creacion, edicion, activacion, desactivacion y eliminacion controlada.
* Programacion base declarativa: `MANUAL`, `DIARIA`, `SEMANAL`, `MENSUAL` y `FECHA_ESPECIFICA`.
* Modos del dia `UNA_VEZ` e `INTERVALO`.
* Campo `ejecutar_en_feriados` como dato declarativo.
* Migracion propuesta `database/migrations/008_ajustar_tareas_y_programaciones_base.sql`.
* Seed incremental `database/seeds/004_permisos_tareas.sql`.

### Seguridad

* Permisos `TAREAS_VER`, `TAREAS_CREAR`, `TAREAS_EDITAR`, `TAREAS_ESTADO` y `TAREAS_ELIMINAR`.
* Eliminacion fisica de tareas solo si no existen scripts, ejecuciones ni logs asociados.
* Acciones criticas protegidas con modal corporativo reutilizable.

### No implementado

* No se implemento scheduler real.
* No se ejecutan scripts.
* No se implemento carga/versionamiento funcional de scripts.
* No se avanzo a Fase 7.

## 2026-06-13 - Fase 5.1 eliminacion controlada en mantenedores

### Agregado

* Eliminacion fisica controlada para clientes, categorias y tipos.
* Validacion de dependencias contra `tareas` antes de eliminar.
* Modal corporativo fuerte para eliminacion definitiva.
* Bloqueo con mensaje amigable cuando existen dependencias.
* Logs de sistema para eliminacion confirmada e intento bloqueado.

### Seguridad

* No se eliminan registros usados por tareas.
* Si hay dependencias, se sugiere desactivar el registro.
* Se usan permisos existentes `CLIENTES_ESTADO`, `CATEGORIAS_ESTADO` y `TIPOS_ESTADO`.

### Validado

* `python -m compileall app`.
* Rutas `/clientes/<id>/eliminar`, `/categorias/<id>/eliminar` y `/tipos/<id>/eliminar` registradas.
* Login `.env` redirige a `/panel`.
* `/clientes/`, `/categorias/` y `/tipos/` responden 200.

### No implementado

* No se avanzo a Fase 6.
* No se implementaron tareas.
* No se implemento carga de scripts.
* No se implemento scheduler.
* No se modifico SQL.

## 2026-06-12 - Fase 5 mantenedores clientes categorias tipos

### Agregado

* Mantenedor `/clientes`.
* Mantenedor `/categorias`.
* Mantenedor `/tipos`.
* Repositorio y servicio generico para mantenedores base.
* Templates reutilizables de listado y formulario.
* Sidebar con accesos a Clientes, Categorias y Tipos.
* Seed incremental `database/seeds/003_permisos_mantenedores.sql`.

### Funcionalidad

* Listar, filtrar, crear, editar, activar y desactivar.
* Filtro por estado y busqueda por nombre/descripcion.
* Validacion de nombre obligatorio.
* Validacion de duplicados por nombre normalizado.
* Sin eliminacion fisica en Fase 5 inicial; ajustado en Fase 5.1 para permitir eliminacion controlada solo sin dependencias.
* Logs de sistema por creacion, edicion, activacion y desactivacion.
* Confirmaciones con modal corporativo.

### Validado

* `python -m compileall app`.
* Login `.env` redirige a `/panel`.
* `/clientes/`, `/clientes/nuevo`, `/categorias/`, `/categorias/nuevo`, `/tipos/`, `/tipos/nuevo` responden 200.
* Filtros de listados responden 200.

### No implementado

* No se avanzo a Fase 6.
* No se implementaron tareas.
* No se implemento carga de scripts.
* No se implemento scheduler.

## 2026-06-12 - Migracion 007 validada localmente

### Validado Manualmente

* Migracion `database/migrations/007_agregar_control_ejecucion_y_env_scripts.sql` ejecutada correctamente en SQL Server local.
* Confirmado estado `DETENIDA_MANUALMENTE` en `cat_estados_ejecucion`.
* Confirmados campos `requiere_env`, `ruta_env_fisica` y `ruta_env_relativa` en `scripts_versiones`.
* Confirmados campos `usuario_detencion`, `fecha_hora_detencion`, `motivo_detencion` y `fue_detencion_forzada` en `ejecuciones`.

### No implementado

* No se avanzo a Fase 5.
* No se implementaron tareas, scripts ni scheduler.

## 2026-06-12 - Fase 4.3 definiciones de ejecucion segura

### Agregado

* Definicion tecnica para detener ejecuciones en curso.
* Definicion tecnica para `.env` propio por script/version.
* Estructura fisica recomendada `scripts/`, `env_scripts/` y `logs_tareas/`.
* Migracion propuesta `database/migrations/007_agregar_control_ejecucion_y_env_scripts.sql`.
* Variable de plantilla `RUTA_BASE_ENV_SCRIPTS`.
* Exclusiones `env_scripts/` y `**/.env` en `.gitignore`.

### Base de datos

* `scripts_versiones`: propuesta de `requiere_env`, `ruta_env_fisica`, `ruta_env_relativa`.
* `ejecuciones`: propuesta de `usuario_detencion`, `fecha_hora_detencion`, `motivo_detencion`, `fue_detencion_forzada`.
* Catalogo `DETENIDA_MANUALMENTE` para `cat_estados_ejecucion`.

### Seguridad

* No guardar contenido de `.env` de scripts en BD.
* No mostrar ni registrar secretos.
* Separar `.env` principal de `.env` por script.
* Validar rutas para evitar path traversal.
* Detencion de ejecuciones solo para usuarios autorizados y con confirmacion.

### No implementado

* No se implementaron tareas.
* No se implemento scheduler.
* No se implemento carga funcional de scripts.
* No se ejecuto SQL desde Codex.

## 2026-06-12 - Fase 4.2 modal corporativo de confirmacion

### Corregido

* Los formularios de crear y editar usuario ahora tambien requieren modal de confirmacion antes de guardar.
* Edicion de usuario detecta cambio de rol y muestra confirmacion especial.
* Edicion de usuario detecta nueva contrasena y muestra confirmacion especial.
* Si cambian rol y contrasena juntos, se muestra confirmacion de cambios criticos.
* Se registra cambio de contrasena en `logs_sistema` sin valores sensibles.

### Agregado

* Modal global reutilizable de confirmacion en `base.html`.
* Variantes visuales `danger`, `warning`, `info` y `success`.
* Cierre por boton cancelar, clic en overlay y tecla ESC.
* Atributos `data-*` para configurar titulo, mensaje, botones y tipo visual.

### Cambiado

* Activar/deshabilitar usuario ya no usa `window.confirm()`.
* Las acciones de usuarios abren modal propio y solo envian el formulario al confirmar.

### Validado

* `python -m compileall app`.
* Busqueda sin coincidencias de `window.confirm` ni `confirm(` en `app/static/js` y `app/templates`.
* Login `.env` redirige a `/panel`.
* `/panel`, `/usuarios/`, `/usuarios/?estado=activo`, `/usuarios/?rol=TI` y `/usuarios/nuevo` responden 200.

### No implementado

* No se avanzo a Fase 5.
* No se implementaron tareas, scripts ni scheduler.
* No se modifico SQL ni permisos.

## 2026-06-12 - Seguridad .env y comandos de configuracion

### Corregido

* Reemplazadas instrucciones inseguras que copiaban `.env.example` sobre `.env`.
* Agregados comandos seguros para PowerShell y CMD que solo crean `.env` si no existe.
* Documentada regla de no sobrescribir `.env` real.
* Agregada validacion controlada de variables criticas de configuracion.
* Login muestra advertencia amigable si `.env` falta o contiene valores de plantilla.

### Seguridad

* `.env` se mantiene excluido por `.gitignore`.
* `.env.example` se mantiene como plantilla.
* No se agregaron credenciales reales a codigo, README, docs ni logs.
* No se modifico `.env`.

## 2026-06-12 - Fase 4.1 mejoras UX modulo usuarios

### Agregado

* Filtros en `/usuarios` por estado, rol y busqueda general.
* Contador de resultados del listado de usuarios.
* Boton para limpiar filtros.
* Confirmacion antes de activar o deshabilitar usuarios.
* Advertencia visual al cambiar rol de usuario.
* Advertencia visual al ingresar nueva contrasena en edicion.

### Mejorado

* Visualizacion de roles con nombre amigable, sin codigo redundante.
* Badges de rol y estado.
* Mensajes amigables de login, permisos y acciones de usuarios.
* Registro separado de cambio de rol en `logs_sistema`.

### Validado

* `python -m compileall app`.
* Login `.env` redirige a `/panel`.
* `/usuarios/` responde 200.
* `/usuarios/?estado=activo` responde 200.
* `/usuarios/?estado=inactivo` responde 200.
* `/usuarios/?rol=TI` responde 200.
* `/usuarios/?rol=ADMIN` responde 200.
* `/usuarios/?buscar=test` responde 200.
* `/usuarios/nuevo` responde 200.

### No implementado

* No se modificaron scripts SQL.
* No se cambio estructura de base de datos.
* No se avanzo a Fase 5.
* No se implementaron tareas, scripts ni scheduler.

## 2026-06-12 - Fase 4 usuarios, roles y permisos iniciales

### Agregado

* Login hibrido: primero `.env`, luego tabla `usuarios`.
* Decoradores `login_requerido` y `permiso_requerido`.
* Sesion con roles y permisos.
* Modulo `/usuarios` para listar, crear, editar, activar y desactivar usuarios.
* Repositorios y servicios para usuarios, roles, permisos y logs de sistema.
* Registro inicial en `logs_sistema` para login y cambios de usuarios.
* Templates `usuarios/listado.html` y `usuarios/formulario.html`.

### Seguridad

* Contrasenas de usuarios de base de datos con `generate_password_hash` y `check_password_hash`.
* Sin eliminacion fisica de usuarios.
* Usuario inicial de `.env` mantiene acceso total y no se crea en base de datos.

### Validado

* `python -m compileall app`.
* GET `/login` responde 200.
* Login por `.env` redirige a `/panel`.
* GET `/panel` responde 200.
* GET `/usuarios/` responde 200 con sesion `.env`.

### No implementado

* CRUD de tareas.
* Carga real de scripts.
* Scheduler.
* Panel funcional de logs/auditoria.

## 2026-06-12 - README actualizado

### Documentado

* README principal actualizado al estado Fase 3D.
* Estado actual, stack, funcionalidades actuales y pendientes.
* Ejecucion local en Windows.
* Variables de entorno principales.
* Ubicacion y orden de scripts SQL.
* Referencias a `docs/` y `log_codex.md`.

## 2026-06-12 - Fase 3D conexion Flask SQL Server

### Agregado

* Dependencia `pyodbc`.
* Modulo `app/database/conexion.py`.
* Funcion `probar_conexion_bd()`.
* Ruta temporal `/diagnostico/bd` disponible solo en `LOCAL` y `QA`.
* Template de diagnostico de conexion.

### Validado

* La app sigue levantando.
* Login desde `.env` sigue funcionando.
* `/panel` sigue funcionando.
* `/diagnostico/bd` responde sin exponer credenciales.

### Pendiente

* Resolver cualquier error local de driver/red/cifrado que aparezca en `/diagnostico/bd`.
* No hay CRUD, usuarios en base de datos ni scheduler.

## 2026-06-12 - Fase 3B scripts SQL versionados

### Validado Manualmente

* Scripts `001` a `006` ejecutados correctamente en SQL Server local.
* Seeds `001` y `002` ejecutados correctamente.
* Base `APP_SCHEDULER_QA` creada.
* Tablas creadas y verificadas.
* Catalogos con datos iniciales cargados.
* Roles, permisos y relaciones iniciales cargados.
* Confirmado que no se creo el usuario `blizama` en base de datos.
* Flask aun no se conecta a SQL Server.

### Revisado

* Revision tecnica previa de scripts SQL antes de ejecucion manual en SSMS.
* Confirmado orden de claves foraneas y FK diferida `scripts.id_version_activa`.
* Ajustada documentacion de `logs_tareas.nombre_archivo_log` y `logs_sistema.nivel varchar(30)`.

### Agregado

* Carpeta `database/migrations/`.
* Carpeta `database/seeds/`.
* Script `001_crear_base_datos.sql`.
* Script `002_crear_catalogos.sql`.
* Script `003_crear_tablas_seguridad.sql`.
* Script `004_crear_tablas_negocio.sql`.
* Script `005_crear_tablas_ejecucion_logs.sql`.
* Script `006_crear_indices.sql`.
* Seed `001_datos_iniciales_catalogos.sql`.
* Seed `002_roles_permisos_iniciales.sql`.

### Incluye

* Tablas catalogo, seguridad, negocio, ejecucion, logs y auditoria.
* `scripts` y `scripts_versiones` con versionamiento controlado.
* Foreign keys desde estados/tipos operativos hacia catalogos.
* `CHECK(numero_version BETWEEN 1 AND 3)`.
* `UNIQUE(id_script, numero_version)`.
* Indice unico filtrado para una sola version activa.
* FK diferida `scripts.id_version_activa` en script de indices por dependencia circular.
* Seeds de catalogos, roles, permisos y roles_permisos.

### No implementado

* No se ejecuto SQL.
* No se conecto Flask a SQL Server.
* No se creo usuario `blizama` en base de datos.
* No se implemento CRUD ni scheduler.

### Documentacion

* `docs/BASE_DATOS.md`
* `docs/ARQUITECTURA.md`
* `docs/MODULOS.md`
* `docs/DESPLIEGUE.md`
* `docs/CHANGELOG.md`
* `log_codex.md`

## 2026-06-12 - Fase 3A ajuste versionamiento scripts

### Aprobado

* Se aprueba mantener `scripts` + `scripts_versiones`.
* Se aprueba mantener `id_version_activa` en `scripts`.
* Versiones `REEMPLAZADA` no cuentan dentro del maximo de 3 versiones disponibles.
* Primera version controla maximo 3 en capa de servicio.
* Base de datos se refuerza con `CHECK(numero_version BETWEEN 1 AND 3)`, `UNIQUE(id_script, numero_version)` e indice unico filtrado para una sola version activa.
* Trigger o procedimiento almacenado queda como mejora futura.
* Se aprueba estructura fisica `v1`, `v2`, `v3`.

### Documentado

* Separacion entre `scripts` como script logico y `scripts_versiones` como archivos versionados.
* Regla de maximo 3 versiones disponibles por script.
* Regla de una sola version activa por script.
* Ejecuciones con `id_script` e `id_version` para trazabilidad exacta.
* Rutas fisicas versionadas con carpetas `v1`, `v2`, `v3`.
* Flujos de carga, activacion, ejecucion manual/automatica, reemplazo y auditoria de versiones.
* Estrategia recomendada: validacion inicial en capa de servicio, con constraints simples e indice filtrado para una version activa.

### No implementado

* No se creo conexion SQL Server.
* No se ejecutaron scripts SQL.
* No se crearon tablas.
* No se modifico logica funcional Flask.

### Archivos modificados

* `docs/BASE_DATOS.md`
* `docs/ARQUITECTURA.md`
* `docs/MODULOS.md`
* `docs/FLUJOS.md`
* `docs/CHANGELOG.md`
* `log_codex.md`

## 2026-06-12 - Fase 3 parte 1

### Documentado

* Propuesta inicial de modelo relacional SQL Server para `APP_SCHEDULER_QA`.
* Tablas criticas y tablas futuras.
* Campos principales, claves primarias, claves foraneas e indices recomendados.
* Estados propuestos para tareas, ejecuciones y programaciones.
* Reglas para rutas fisicas/relativas de scripts y logs.
* Propuesta de auditoria y logs de sistema.

### No implementado

* No se creo conexion SQL Server.
* No se ejecutaron scripts SQL.
* No se crearon tablas.
* No se modifico CRUD ni logica funcional.

### Archivos modificados

* `docs/BASE_DATOS.md`
* `docs/ARQUITECTURA.md`
* `docs/MODULOS.md`
* `docs/CHANGELOG.md`
* `log_codex.md`

## 2026-06-12 - Fase 2

### Mejorado

* Layout base responsive con sidebar, topbar, usuario logueado y panel lateral visual para logs.
* Pantalla de login con diseno corporativo moderno, fondo tecnico sutil y formulario refinado.
* Panel principal con cards de resumen, placeholders claros y secciones preparadas para ejecuciones, errores y scheduler.
* Componentes visuales reutilizables: botones, cards, badges, alertas, contenedores, tabla base y estados visuales.
* CSS reorganizado con variables de color, espaciado, sombras, bordes y transiciones.
* JavaScript base para toggle de sidebar, panel lateral de logs y tratamiento visual de alertas.

### Archivos modificados

* `app/templates/base.html`
* `app/templates/login.html`
* `app/templates/panel.html`
* `app/static/css/estilos.css`
* `app/static/js/app.js`
* `README.md`
* `docs/UI_UX.md`
* `docs/ARQUITECTURA.md`
* `log_codex.md`

### Pendientes visuales

* Validar en navegador con datos reales de usuario.
* Refinar iconografia cuando se incorpore libreria de iconos o componentes finales.
* Conectar estados visuales a datos reales en fases posteriores.

## 2026-06-12 - Fase 1

### Agregado

* Estructura inicial Flask.
* Login inicial desde `.env`.
* Panel principal base.
* Layout visual inicial.
* Documentacion tecnica inicial.
* `.gitignore` profesional.
* `.env.example`.
* Bitacora `log_codex.md`.
