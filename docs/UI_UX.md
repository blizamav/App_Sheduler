# UI/UX

## Lineamientos visuales

Estilo moderno, sobrio, corporativo y futurista moderado. La interfaz debe sentirse como una herramienta interna de control TI: clara, rapida de escanear, con jerarquia visual y sin efectos que reduzcan legibilidad.

## Paleta de colores

Variables CSS principales definidas en `app/static/css/estilos.css`:

* `--color-fondo: #f4f7fb`: fondo general claro.
* `--color-superficie: #ffffff`: tarjetas, paneles y formularios.
* `--color-azul: #0f4cbd`: acciones primarias e informacion relevante.
* `--color-azul-oscuro: #071b35`: sidebar y paneles de alto contraste.
* `--color-cyan: #18a8d8`: acentos futuristas moderados.
* `--color-verde: #138a4b`: estados activos/exitosos.
* `--color-rojo: #c53a3a`: errores o estados criticos.
* `--color-amarillo: #b87503`: advertencias o pendientes.
* `--color-gris: #7b8798`: estados inactivos o secundarios.
* `--color-borde: #d9e2ef`: separadores suaves.

## Tipografias sugeridas

`Segoe UI`, Arial o sans-serif del sistema para mantener rendimiento y compatibilidad en Windows y Linux.

## Componentes creados

* Login corporativo centrado con fondo tecnico sutil.
* Sidebar responsive con navegacion principal.
* Topbar con usuario logueado, avatar textual y salida.
* Botones primarios y secundarios.
* Botones iconicos para menu y cierre.
* Cards de metricas.
* Badges de estado: activo, inactivo, error, advertencia e informativo.
* Alertas visuales para mensajes Flask.
* Contenedores base.
* Formularios con foco visible.
* Tabla base preparada para listados futuros.
* Panel lateral visual preparado para logs.

## Layout

Aplicacion con sidebar fijo en escritorio, topbar persistente y contenido en grillas responsivas. En pantallas menores el sidebar queda oculto y se abre con toggle. El panel lateral de logs se despliega desde la derecha como preparacion visual para Fase 9.

## Estados visuales

* Activo/exitoso: verde.
* Inactivo/pendiente: gris.
* Error: rojo.
* Advertencia: amarillo/naranjo.
* Informativo/en preparacion: azul.

Los estados son visuales en Fase 2; su alimentacion real vendra desde tareas, ejecuciones y logs en fases posteriores.

## Reglas de experiencia

* Acciones criticas deben confirmar en fases posteriores.
* Errores deben ser claros y accionables.
* Los paneles deben permitir escaneo rapido.
* Los datos no implementados se muestran como placeholders explicitos para evitar confusion.
* La interfaz debe ser responsive sin ocultar acciones principales.
* Los efectos visuales deben ser suaves y no deben competir con la lectura.

## Decisiones visuales tomadas en Fase 2

* Se mantuvo una paleta clara con sidebar oscuro para dar jerarquia corporativa.
* Se agrego un fondo tecnico sutil al login sin imagenes pesadas ni dependencias externas.
* Se preparo un panel lateral de logs solo visual, sin lectura real de archivos.
* Se agregaron componentes reutilizables antes de crear modulos funcionales.
* No se implementaron tareas, base de datos, usuarios avanzados ni scheduler.
