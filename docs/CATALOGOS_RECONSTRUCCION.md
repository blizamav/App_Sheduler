# Catalogos reconstruidos

## Estado y alcance

Hito 4 esta cerrado en `src/app_scheduler/`. El runtime historico sigue activo, no existe cutover y Hito 5 no fue iniciado.

Incluye listado, filtros, paginacion, alta, edicion, activacion/desactivacion, autorizacion backend, CSRF, auditoria y UI responsive para `clientes`, `categorias` y `tipos`. No incluye tareas ni el modulo global de Papelera.

## Contrato SQL preservado

| Catalogo | PK | Nombre visible | Clave fisica UNIQUE | Otros campos editables | Estado |
| --- | --- | --- | --- | --- | --- |
| Clientes | `id_cliente` | `nombre_cliente nvarchar(150)` | `nombre_normalizado nvarchar(150)` | `descripcion nvarchar(300) NULL` | `activo bit` |
| Categorias | `id_categoria` | `nombre_categoria nvarchar(150)` | `nombre_normalizado nvarchar(150)` | `descripcion nvarchar(300) NULL` | `activo bit` |
| Tipos | `id_tipo` | `nombre_tipo nvarchar(150)` | `nombre_normalizado nvarchar(150)` | `descripcion nvarchar(300) NULL` | `activo bit` |

Las tres tablas conservan campos de creacion/actualizacion y retiro operativo. No se agregaron columnas, constraints, FK ni SQL nuevo.

El nombre visible solo elimina espacios exteriores. La clave fisica aplica la regla historica: NFKD, elimina diacriticos, convierte a mayusculas y colapsa espacios. La validacion de duplicado consulta tambien registros con `eliminado_operativo = 1`, porque el UNIQUE fisico los incluye.

`activo = 0` conserva el registro dentro de la operacion y permite administrarlo o reactivarlo, pero impide seleccionarlo para nuevas tareas. `eliminado_operativo = 1` lo retira de listados y flujos normales para que el futuro Hito 9 lo gestione desde Papelera. Son estados distintos: desactivar no envia a Papelera y retirar operativamente no equivale a un DELETE fisico.

## Persistencia y transacciones

`RepositorioClientes`, `RepositorioCategorias` y `RepositorioTipos` reutilizan una especificacion interna cerrada. No se aceptan tabla, columna u orden desde HTTP. Listados y filtros usan placeholders, `ESCAPE '~'`, orden fijo y paginacion SQL Server.

Cada escritura sigue este limite:

```text
caso de uso -> repositorio de catalogo -> repositorio de auditoria -> UoW.confirmar()
```

Los repositorios no confirman. Si falla el cambio o la auditoria, la UoW revierte y cierra la conexion. Un conflicto SQLSTATE `23000` se traduce a un mensaje de duplicado sin exponer driver, constraint o SQL.

## Matriz de rutas y permisos bootstrap

| Modulo | Operacion | Permiso exacto | Ruta | Metodo | CSRF | Roles bootstrap |
| --- | --- | --- | --- | --- | --- | --- |
| Clientes | Listar/buscar/filtrar | `CLIENTES_VER` | `/clientes/` | GET | No aplica | `SUPER_ADMIN`, `ADMIN`, `TI` |
| Clientes | Mostrar alta | `CLIENTES_CREAR` | `/clientes/nuevo` | GET | No aplica | `SUPER_ADMIN`, `ADMIN` |
| Clientes | Crear | `CLIENTES_CREAR` | `/clientes/nuevo` | POST | Si | `SUPER_ADMIN`, `ADMIN` |
| Clientes | Mostrar edicion | `CLIENTES_EDITAR` | `/clientes/<id>/editar` | GET | No aplica | `SUPER_ADMIN`, `ADMIN` |
| Clientes | Editar | `CLIENTES_EDITAR` | `/clientes/<id>/editar` | POST | Si | `SUPER_ADMIN`, `ADMIN` |
| Clientes | Activar/desactivar | `CLIENTES_ESTADO` | `/clientes/<id>/estado` | POST | Si | `SUPER_ADMIN`, `ADMIN` |
| Categorias | Listar/buscar/filtrar | `CATEGORIAS_VER` | `/categorias/` | GET | No aplica | `SUPER_ADMIN`, `ADMIN`, `TI` |
| Categorias | Mostrar alta | `CATEGORIAS_CREAR` | `/categorias/nuevo` | GET | No aplica | `SUPER_ADMIN`, `ADMIN` |
| Categorias | Crear | `CATEGORIAS_CREAR` | `/categorias/nuevo` | POST | Si | `SUPER_ADMIN`, `ADMIN` |
| Categorias | Mostrar edicion | `CATEGORIAS_EDITAR` | `/categorias/<id>/editar` | GET | No aplica | `SUPER_ADMIN`, `ADMIN` |
| Categorias | Editar | `CATEGORIAS_EDITAR` | `/categorias/<id>/editar` | POST | Si | `SUPER_ADMIN`, `ADMIN` |
| Categorias | Activar/desactivar | `CATEGORIAS_ESTADO` | `/categorias/<id>/estado` | POST | Si | `SUPER_ADMIN`, `ADMIN` |
| Tipos | Listar/buscar/filtrar | `TIPOS_VER` | `/tipos/` | GET | No aplica | `SUPER_ADMIN`, `ADMIN`, `TI` |
| Tipos | Mostrar alta | `TIPOS_CREAR` | `/tipos/nuevo` | GET | No aplica | `SUPER_ADMIN`, `ADMIN` |
| Tipos | Crear | `TIPOS_CREAR` | `/tipos/nuevo` | POST | Si | `SUPER_ADMIN`, `ADMIN` |
| Tipos | Mostrar edicion | `TIPOS_EDITAR` | `/tipos/<id>/editar` | GET | No aplica | `SUPER_ADMIN`, `ADMIN` |
| Tipos | Editar | `TIPOS_EDITAR` | `/tipos/<id>/editar` | POST | Si | `SUPER_ADMIN`, `ADMIN` |
| Tipos | Activar/desactivar | `TIPOS_ESTADO` | `/tipos/<id>/estado` | POST | Si | `SUPER_ADMIN`, `ADMIN` |

`TERCERO` no recibe permisos de catalogos en el bootstrap. `SUPER_ADMIN_ENV` usa el mismo mecanismo `IdentidadSesion.tiene_permiso()` con permisos efectivos totales y no tiene excepciones locales en estas rutas.

## Auditoria

Eventos: `CLIENTE_CREADO`, `CLIENTE_EDITADO`, `CLIENTE_ACTIVADO`, `CLIENTE_DESACTIVADO` y sus equivalentes `CATEGORIA_*` y `TIPO_*`.

Se registran actor, accion, entidad, ID, nombre, antes/despues, contexto HTTP, resultado y modulo mediante las columnas canonicas. No se usan `fecha_hora`, `tabla_afectada`, `id_registro`, `valor_anterior`, `valor_nuevo` ni `ip`.

## UI y seguridad

Los formularios aceptan solamente `nombre` y `descripcion`. El estado tiene un endpoint separado; IDs y metadatos del sistema nunca se asignan desde `request.form`. El sidebar y las acciones se ocultan segun permiso, pero cada ruta vuelve a autorizar en backend.

Los listados tienen busqueda por nombre/descripcion, filtro de estado, 25 registros por pagina, orden estable y tabla con scroll horizontal interno en pantallas compactas.

## Papelera y tareas futuras

Hito 4 no expone borrar ni restaurar. Los listados y las lecturas operativas excluyen filas retiradas. La eliminacion, restauracion y limpieza permanente se reconstruiran en Hito 9 con las dependencias y snapshots correspondientes.

Las FK reales `tareas.id_cliente`, `tareas.id_categoria` y `tareas.id_tipo` permanecen intactas y sin cascada. Activar/desactivar no rompe referencias existentes; una futura tarea debera seleccionar registros activos.

## Pruebas y deuda legitima

Se agregaron 23 pruebas para repositorios, paginacion, filtros, normalizacion, duplicados, alta, edicion, estado, rollback, auditoria, permisos, CSRF, mass assignment y `SUPER_ADMIN_ENV`.

* `python -m pytest -q tests/reconstruccion`: 92 casos del runtime reconstruido.
* `python -m pytest -q`: 118 casos de todo el repositorio; esta es la metrica oficial de cierre.

La diferencia son 26 pruebas historicas que la suite acotada no recopila. Ambas metricas son utiles, pero responden a alcances distintos y no deben sumarse.

Deuda legitima:

* No hubo consulta ni DML sobre QA; la validacion es aislada con fakes y Flask test client.
* Un nombre retirado no puede reutilizarse mientras el UNIQUE fisico incluya Papelera.
* La eliminacion operativa/permanente y restauracion pertenecen al Hito 9.
