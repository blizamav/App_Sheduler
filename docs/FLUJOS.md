# Flujos

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

Pendiente para Fase 6.

## Flujo de ejecucion automatica

Pendiente para Fase 8.

## Flujo de ejecucion manual

Pendiente para Fase 8.

## Flujo de ejecucion con env por script

1. Servicio resuelve tarea, script logico y version exacta.
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
11. La consola lateral muestra estado detenido y mensaje amigable.

## Flujo de reemplazo de script

Propuesta documental Fase 3A; implementacion pendiente para Fase 7.

## Flujo de carga de primera version

1. Usuario crea o edita una tarea.
2. El sistema crea el script logico en `scripts`.
3. Usuario carga archivo `.py`.
4. Servicio valida extension, nombre seguro, ruta permitida y hash.
5. Se crea `scripts_versiones` con `numero_version = 1`, `estado_version = ACTIVA`, `es_activa = 1`.
6. `scripts.id_version_activa` queda apuntando a la version 1.
7. Se registra evento en `logs_sistema` y `auditoria_cambios`.

## Flujo de carga de segunda o tercera version

1. Usuario selecciona script logico existente.
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
