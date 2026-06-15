# Flujos

## Flujo de gestion de scripts por tarea

1. Usuario autorizado abre `/tareas`.
2. Selecciona `Scripts` en una tarea.
3. El sistema muestra datos de la tarea, archivo activo real y tabla de versiones.
4. Si no existe contenedor de script, el boton dice `Asociar script` y el modal informa que se creara v1 activa.
5. Si ya existe v1 o v2, el modal informa que se creara v2 o v3.
6. Si ya existen v1, v2 y v3, no se ofrece crear v4; se indica reemplazar una version existente.
7. Usuario carga archivo `.py`.
8. El backend valida extension, tamano, nombre y ruta segura.
9. Si no existe contenedor de script, lo crea con nombre `Script de {nombre_tarea}` y registra v1 activa.
10. Si ya existe, crea la siguiente version disponible hasta v3.
11. Si ya existen v1, v2 y v3, bloquea la carga directa y solicita reemplazar una version.
12. El archivo queda guardado bajo `scripts/CATEGORIA/TIPO/CLIENTE/TAREA/vX/`.
13. Solo se guardan rutas y hash en base de datos; no se ejecuta el archivo.

## Diferencia entre contenedor y archivo activo

1. `scripts.nombre_script` representa un contenedor descriptivo asociado a la tarea.
2. El archivo activo se obtiene desde la version activa en `scripts_versiones`.
3. El bloque superior muestra como protagonista `scripts_versiones.nombre_archivo` de la version activa.
4. El nombre interno del contenedor se conserva en base de datos, pero no se muestra por defecto en la vista principal.
5. Si se reemplaza la version activa, el bloque superior cambia al nuevo archivo de esa version.
6. Si se reemplaza una version no activa, el bloque superior no cambia porque la version activa sigue siendo la misma.
7. La tabla de versiones sigue mostrando el detalle completo de cada version.
8. El nombre del primer archivo cargado no define el nombre del contenedor principal.

## Flujo de version activa

1. Usuario selecciona activar una version disponible.
2. Se muestra modal corporativo.
3. Al confirmar, todas las versiones del script dejan de ser activas.
4. La version seleccionada queda `ACTIVA`.
5. `scripts.id_version_activa` apunta a esa version.
6. Futuras ejecuciones usaran esa version, cuando exista Fase 8.

## Flujo de eliminacion de script completo y version

1. El boton superior `Eliminar script completo` representa la eliminacion del contenedor de script asociado a la tarea.
2. Esa accion afecta a todo el conjunto de versiones solo si el usuario la confirma explicitamente.
3. Si el script completo no tiene historial, se eliminan registros y archivos asociados de todas sus versiones.
4. Si el script completo tiene historial, se bloquea la eliminacion fisica y se sugiere desactivarlo.
5. En la tabla de versiones, `Eliminar version` intenta eliminar solo la version de esa fila.
6. Eliminar una version nunca elimina el script completo ni las demas versiones.
7. Si la version es activa, se bloquea la eliminacion y se pide activar otra version primero.
8. Si es la unica version del script, se bloquea la eliminacion individual y se indica usar `Eliminar script completo`.
9. Si la version tiene historial, se bloquea la eliminacion fisica y se muestra mensaje amigable.
10. Todo bloqueo o eliminacion confirmada se registra en `logs_sistema` sin exponer contenido de `.env`.

## Flujo de env por version

1. Usuario abre panel `.env` de una version.
2. Marca si la version requiere `.env`.
3. Puede subir archivo `.env`.
4. Si no existe `.env`, el modal dice `Asociar archivo .env`.
5. Si ya existe `.env`, el modal dice `Reemplazar archivo .env`.
6. El backend valida tamano, nombre y ruta segura.
7. El archivo queda guardado bajo `env_scripts/CATEGORIA/TIPO/CLIENTE/TAREA/vX/.env`.
8. La base guarda solo rutas, nunca contenido.
9. Si una version requiere `.env` y no lo tiene, se muestra `Pendiente .env`.

## Estandar futuro para scripts

1. El script cargado debe leer variables usando `os.getenv()`.
2. No debe tener credenciales quemadas.
3. No debe ejecutar `load_dotenv()` con ruta fija.
4. En Fase 8 la aplicacion carga el `.env` correspondiente a la version que se ejecute.

## Flujo de login

1. Usuario abre `/login`.
2. Ingresa usuario y contrasena.
3. El backend valida primero contra `.env`.
4. Si coincide, crea sesion `SUPER_ADMIN_ENV` con permisos totales y redirige a `/panel`.
5. Si no coincide, valida contra la tabla `usuarios`.
6. Si el usuario de base de datos esta activo, no bloqueado y la contrasena coincide con el hash, carga roles/permisos y redirige a `/panel`.
7. Si falla, muestra mensaje amigable y registra evento en `logs_sistema` cuando la base de datos esta disponible.

## Flujo de administracion de usuarios

1. Usuario con `USUARIOS_ADMIN` o administrador `.env` abre `/usuarios`.
2. El sistema lista usuarios de base de datos con rol y estado.
3. Puede filtrar por estado, rol o busqueda general por usuario, nombre y correo.
4. Para crear usuario, se exige usuario unico, nombre, rol, contrasena y confirmacion.
5. Para editar usuario, se permite cambiar nombre, email, rol, estado y contrasena opcional.
6. Si cambia el rol, el formulario muestra una advertencia de permisos.
7. Si ingresa nueva contrasena, el formulario advierte que sera actualizada.
8. Para activar o desactivar usuario, se abre un modal corporativo de confirmacion antes de enviar el cambio.
9. Si el administrador cancela la confirmacion, no se ejecuta accion ni se registra log.
10. No existe eliminacion fisica desde la app.
11. Cada creacion, edicion o cambio confirmado registra evento en `logs_sistema`.

## Flujo de mantenedores base

1. Usuario autorizado abre `/clientes`, `/categorias` o `/tipos`.
2. El sistema lista registros con filtros por estado y busqueda por nombre o descripcion.
3. Para crear, el usuario ingresa nombre y descripcion opcional.
4. Antes de guardar, se muestra modal corporativo de confirmacion.
5. El servicio normaliza el nombre y valida duplicados.
6. Para editar, se repite confirmacion y validacion de duplicados excluyendo el registro actual.
7. Para activar o desactivar, se solicita confirmacion por modal.
8. Para eliminar definitivamente, se solicita confirmacion fuerte por modal.
9. El backend valida dependencias contra `tareas`.
10. Si no tiene dependencias, elimina fisicamente y registra `logs_sistema`.
11. Si tiene dependencias, bloquea la eliminacion, muestra mensaje amigable, sugiere desactivar y registra intento bloqueado.
12. Cada cambio confirmado registra evento en `logs_sistema`.

## Flujo de confirmacion critica

1. Usuario presiona un boton marcado como accion critica.
2. El frontend evita el envio inmediato del formulario.
3. Se abre el modal reutilizable del sistema con titulo, mensaje, tipo visual y botones configurados por `data-*`.
4. Si el usuario cancela, se cierra el modal y no se envia el formulario.
5. Si el usuario confirma, el formulario original se envia por POST al backend.
6. El backend mantiene la logica existente y registra logs solo cuando recibe una accion confirmada.

## Flujo de confirmacion al guardar usuario

1. Usuario presiona guardar en creacion o edicion de usuario.
2. El frontend intercepta el submit del formulario.
3. En creacion se muestra modal `Crear usuario`.
4. En edicion sin cambios criticos se muestra modal `Guardar cambios del usuario`.
5. Si el rol cambio, se muestra modal `Confirmar cambio de rol`.
6. Si se ingreso nueva contrasena, se muestra modal `Confirmar cambio de contrasena`.
7. Si cambia rol y contrasena al mismo tiempo, se muestra modal `Confirmar cambios criticos`.
8. Si cancela, no se envia el formulario.
9. Si confirma, se envia el POST normal y el backend guarda cambios.

## Flujo de creacion de tarea

1. Usuario autorizado abre `/tareas/nueva`.
2. Ingresa nombre, descripcion, cliente, categoria, tipo y observacion tecnica opcional.
3. Define tipo de programacion: manual, diaria, semanal, mensual o fecha especifica.
4. Si la programacion no es manual, selecciona modo `UNA_VEZ` o `INTERVALO`.
5. El formulario muestra solo los campos necesarios para el tipo y modo seleccionados.
6. Antes de guardar, el frontend valida los campos requeridos de la programacion.
7. Si la informacion esta completa, se muestra modal corporativo con resumen de la tarea.
8. El resumen muestra nombres visibles de cliente, categoria y tipo, no IDs.
9. Si el usuario cancela, no se envia el formulario.
10. Si confirma, el backend valida campos obligatorios, duplicados y reglas de programacion.
11. Si es valido, crea la tarea y una programacion activa.
12. Registra eventos en `logs_sistema`.

## Flujo de edicion de tarea

1. Usuario autorizado abre `/tareas/<id>/editar`.
2. Modifica datos base o programacion.
3. Al presionar guardar, el frontend compara el estado original contra el estado actual.
4. Si no hay cambios reales, no muestra modal, no envia el formulario y muestra `No hay cambios para guardar.`.
5. Si hay cambios, valida los campos requeridos de la programacion.
6. Se muestra modal corporativo con el resumen final de como quedara la tarea.
7. Si el usuario cancela, no se envia el formulario.
8. Si confirma, el backend valida reglas y duplicados excluyendo la tarea actual.
9. El backend vuelve a comparar datos actuales contra datos enviados.
10. Si no hay cambios, no ejecuta `UPDATE`, no registra logs y muestra `No hay cambios para guardar.`.
11. Si hay cambios, inactiva la programacion activa anterior.
12. Crea una nueva programacion activa con los cambios.
13. Registra eventos en `logs_sistema`.

## Flujo de confirmacion con resumen de tarea

1. El formulario de tarea usa el modal global reutilizable.
2. El JS toma los valores actuales del formulario antes de enviarlo.
3. Para cliente, categoria y tipo lee el texto visible de la opcion seleccionada.
4. Genera un resumen legible de programacion: manual, diaria, semanal, mensual o fecha especifica.
5. Muestra datos generales, programacion, feriados y estado.
6. El contenido del resumen se genera con nodos DOM y texto, no con HTML libre.
7. Cancelar cierra el modal sin guardar.
8. Confirmar envia el formulario y mantiene las validaciones backend existentes.

## Flujo de deteccion de cambios reales en tarea

1. Al cargar formulario de edicion, el frontend guarda una fotografia normalizada del formulario.
2. Antes de guardar compara textos normalizados, selects, checkboxes, tipo de programacion, modo, horarios, intervalo, fecha, dia de mes y dias de semana.
3. Los dias de semana se comparan como conjunto ordenado.
4. Si no hay diferencias, se muestra un mensaje inline y se detiene el envio.
5. Si hay diferencias, continua el modal de resumen de Fase 6.1.
6. El backend aplica una comparacion equivalente antes de actualizar para evitar cambios innecesarios si el JS fue omitido.

## Flujo de estado y eliminacion de tarea

1. Para activar o desactivar, el usuario confirma por modal.
2. El backend actualiza `activo` y `estado_tarea`.
3. Para eliminar definitivamente, el usuario confirma por modal `danger`.
4. El backend valida dependencias en `scripts`, `ejecuciones` y `logs_tareas`.
5. Si no existen dependencias, elimina programaciones y tarea.
6. Si existen dependencias, bloquea la eliminacion y sugiere desactivar.
7. Cada accion confirmada o intento bloqueado se registra en `logs_sistema`.

## Flujo de reglas de programacion

1. `MANUAL`: no exige hora ni calendario.
2. `DIARIA`: exige hora si es `UNA_VEZ`, o intervalo con inicio/fin si es `INTERVALO`.
3. `SEMANAL`: exige al menos un dia de semana.
4. `MENSUAL`: exige dia del mes entre 1 y 31.
5. `FECHA_ESPECIFICA`: exige fecha valida.
6. `INTERVALO`: exige intervalo mayor a 0 y hora inicio menor a hora fin.
7. `ejecutar_en_feriados` queda guardado como dato declarativo; la validacion real queda pendiente.

## Flujo de ejecucion automatica

Pendiente para fase posterior. No se implementa scheduler automatico en Fase 8.

## Flujo de ejecucion manual

Validacion local Fase 8:

* El seed `006_permisos_ejecuciones.sql` fue ejecutado correctamente en SQL Server local.
* Se valido ejecucion manual con script activo, consola, polling, estado `EXITOSA`, detencion `DETENIDA_MANUALMENTE`, PID y archivo de log.
* Se probo ejecucion sin `.env` y con `.env` de prueba cargado mediante `os.getenv()`.
* No se mostraron secretos, no se implemento scheduler automatico y no se conecto API de feriados.

1. Usuario autorizado presiona `Ejecutar ahora` desde `/tareas` o desde la pantalla de scripts.
2. Se muestra modal corporativo indicando tarea, script activo, version activa y que no se usara scheduler.
3. Al confirmar, el servicio valida tarea activa, script activo, version activa y archivo `.py` fisico.
4. Si la version requiere `.env`, valida que exista archivo `.env` asociado.
5. Si ya existe una ejecucion `EN_EJECUCION` para la misma tarea, bloquea la nueva ejecucion.
6. Crea registro en `ejecuciones` con origen `MANUAL` y estado `EN_EJECUCION`.
7. Crea archivo de log en `logs_tareas/AAAA/MM/DD/`.
8. Crea registro en `logs_tareas` con rutas del log.
9. Ejecuta el script con el interprete Python actual y `subprocess` sin `shell=True`.
10. Registra `pid_proceso`.
11. Redirige a `/ejecuciones/<id_ejecucion>`.
12. La consola consulta `/ejecuciones/<id_ejecucion>/log` cada 3 segundos.
13. Si el proceso termina con codigo 0, marca `EXITOSA`.
14. Si termina con codigo distinto de 0 o error controlado, marca `ERROR`.
15. No se muestran secretos ni contenido del `.env`.

## Flujo de ejecucion con env por script

1. Servicio resuelve tarea, contenedor de script y version exacta.
2. Valida que el archivo `.py` exista y pertenezca a rutas permitidas.
3. Revisa `scripts_versiones.requiere_env`.
4. Si no requiere `.env`, continua ejecucion normal.
5. Si requiere `.env`, valida `ruta_env_fisica` y `ruta_env_relativa`.
6. Si falta el `.env`, marca ejecucion como `ERROR` controlado antes de iniciar proceso.
7. Si existe, carga variables en el entorno del proceso sin guardar ni imprimir secretos.
8. Inicia proceso, registra `pid_proceso` y estado `EN_EJECUCION`.
9. Captura salida hacia `logs_tareas`.
10. Al terminar, actualiza estado final, duracion, codigo de salida y logs.

## Flujo de detencion manual de ejecucion

1. Usuario autorizado visualiza una ejecucion `EN_EJECUCION`.
2. Interfaz muestra boton `Detener ejecucion`.
3. Usuario presiona detener y el sistema muestra modal corporativo de confirmacion.
4. Si cancela, no se ejecuta accion ni se registran cambios.
5. Si confirma, el backend valida permisos y estado actual.
6. Servicio intenta detener el proceso de forma controlada usando `pid_proceso`.
7. Si el proceso no responde, se fuerza termino y se marca `fue_detencion_forzada = 1`.
8. Se actualiza `ejecuciones` con usuario, fecha/hora y motivo de detencion.
9. Se registra evento en `logs_tareas`.
10. Se registra evento en `logs_sistema`.
11. La consola muestra estado detenido y mensaje amigable.

## Flujo de reemplazo de script

Propuesta documental Fase 3A; implementacion pendiente para Fase 7.

## Flujo de carga de primera version

1. Usuario crea o edita una tarea.
2. El sistema crea el contenedor en `scripts` con nombre `Script de {nombre_tarea}`.
3. Usuario carga archivo `.py`.
4. Servicio valida extension, nombre seguro, ruta permitida y hash.
5. Se crea `scripts_versiones` con `numero_version = 1`, `estado_version = ACTIVA`, `es_activa = 1`.
6. `scripts.id_version_activa` queda apuntando a la version 1.
7. Se registra evento en `logs_sistema` y `auditoria_cambios`.

## Flujo de carga de segunda o tercera version

1. Usuario selecciona una tarea con contenedor de script existente.
2. Servicio cuenta versiones disponibles del `id_script`.
3. Si existen menos de 3, permite cargar nueva version.
4. Se asigna el siguiente `numero_version` disponible.
5. La nueva version queda `DISPONIBLE` por defecto, salvo que el usuario confirme activarla.
6. Si se activa, la version anterior pasa a `DISPONIBLE`, y solo una queda `ACTIVA`.
7. Se registra auditoria con hash, usuario, fecha y rutas.

## Flujo cuando ya existen 3 versiones

1. Usuario intenta cargar otra version.
2. Servicio detecta 3 versiones disponibles.
3. Sistema impide carga directa.
4. Sistema solicita seleccionar una version existente para reemplazar.
5. Si cancela, no se modifica nada.
6. Si confirma, se ejecuta flujo de reemplazo de version.

## Flujo para seleccionar version activa

1. Usuario visualiza versiones disponibles del script.
2. Selecciona una version como activa.
3. Sistema muestra confirmacion indicando version actual y version nueva.
4. Servicio desmarca `es_activa` en las demas versiones.
5. Servicio marca la version seleccionada como `ACTIVA` y actualiza `scripts.id_version_activa`.
6. Se registra auditoria con valor anterior y valor nuevo.

## Flujo para ejecucion automatica con version activa

1. Scheduler selecciona tareas activas segun programacion.
2. Servicio obtiene `scripts.id_version_activa`.
3. Valida que la version exista, este activa/disponible y el archivo exista.
4. Crea registro en `ejecuciones` con `id_script` e `id_version`.
5. Ejecuta el archivo de `scripts_versiones.ruta_fisica`.
6. Registra resultado y log asociado a `id_ejecucion`.

## Flujo para ejecucion manual seleccionando version

1. Usuario abre tarea.
2. Sistema muestra version activa y versiones disponibles.
3. Usuario elige version activa o una version especifica.
4. Si elige una version distinta a la activa, sistema muestra advertencia y pide confirmacion.
5. Si cancela, no ejecuta.
6. Si confirma, crea `ejecuciones` con `id_script` e `id_version`.
7. Se ejecuta la version elegida y se registra log.

## Flujo de reemplazo de version

1. Usuario selecciona version existente a reemplazar.
2. Sistema muestra advertencia con numero de version, hash actual y fecha de carga.
3. Usuario carga nuevo archivo `.py`.
4. Servicio valida archivo, ruta, nombre seguro y hash.
5. Servicio registra auditoria del valor anterior.
6. Version anterior cambia a `REEMPLAZADA`; no se elimina fisicamente desde la app.
7. Nueva informacion de version queda registrada en `scripts_versiones`.
8. Si la version reemplazada era activa, el sistema debe confirmar si la nueva queda activa.

## Flujo para deshabilitar version

1. Usuario selecciona una version disponible.
2. Sistema muestra confirmacion indicando que no se borrara fisicamente el archivo.
3. Si confirma, servicio cambia `estado_version` a `INACTIVA`.
4. Si la version era activa, el sistema debe exigir seleccionar otra version activa antes de completar la operacion.
5. Se registra evento en `logs_sistema`.
6. Se registra cambio en `auditoria_cambios` con estado anterior y nuevo.
7. El archivo fisico permanece disponible para trazabilidad y revision historica.

## Flujo de auditoria de cambios de version

1. Toda carga, activacion, inactivacion o reemplazo genera registro en `auditoria_cambios`.
2. `tabla_afectada` debe ser `scripts` o `scripts_versiones`.
3. `valor_anterior` debe guardar numero de version, hash, ruta, estado y usuario previo cuando aplique.
4. `valor_nuevo` debe guardar numero de version, hash, ruta, estado y usuario nuevo.
5. Tambien se registra evento operativo en `logs_sistema`.

## Flujo de logs

Pendiente para Fase 9.

## Flujo de auditoria

Pendiente para Fase 10.
