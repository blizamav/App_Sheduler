"""DTO inmutables de persistencia para los modulos fundacionales."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import Generic, TypeVar

from app_scheduler.compartido.errores import ErrorValidacion


T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class Paginacion:
    pagina: int = 1
    por_pagina: int = 50

    def __post_init__(self) -> None:
        if self.pagina < 1:
            raise ErrorValidacion("La pagina debe ser mayor o igual a 1.")
        if not 1 <= self.por_pagina <= 200:
            raise ErrorValidacion("El tamano de pagina debe estar entre 1 y 200.")

    @property
    def desplazamiento(self) -> int:
        return (self.pagina - 1) * self.por_pagina


@dataclass(frozen=True, slots=True)
class Pagina(Generic[T]):
    elementos: tuple[T, ...]
    total: int
    pagina: int
    por_pagina: int

    @property
    def total_paginas(self) -> int:
        if self.total == 0:
            return 0
        return (self.total + self.por_pagina - 1) // self.por_pagina


@dataclass(frozen=True, slots=True)
class Usuario:
    id_usuario: int
    usuario: str
    nombre_completo: str
    email: str | None
    debe_cambiar_password: bool
    ultimo_login: datetime | None
    intentos_fallidos: int
    bloqueado: bool
    eliminado_operativo: bool
    fecha_eliminado_operativo: datetime | None
    fecha_creacion: datetime
    fecha_actualizacion: datetime | None
    activo: bool


@dataclass(frozen=True, slots=True)
class CredencialUsuario:
    usuario: Usuario
    password_hash: str = field(repr=False)


@dataclass(frozen=True, slots=True)
class Rol:
    id_rol: int
    codigo_rol: str
    nombre_rol: str
    descripcion: str | None
    es_sistema: bool
    activo: bool


@dataclass(frozen=True, slots=True)
class Permiso:
    id_permiso: int
    codigo_permiso: str
    modulo: str
    accion: str
    descripcion: str | None
    activo: bool


@dataclass(frozen=True, slots=True)
class EventoAuditoria:
    usuario: str
    accion: str
    entidad: str
    id_usuario: int | None = None
    id_entidad: str | None = None
    nombre_entidad: str | None = None
    descripcion: str | None = None
    valores_antes: str | None = None
    valores_despues: str | None = None
    ip_origen: str | None = None
    user_agent: str | None = None
    resultado: str = "OK"
    modulo: str = "SEGURIDAD"
    ruta: str | None = None
    metodo_http: str | None = None


@dataclass(frozen=True, slots=True)
class RegistroAuditoria:
    id_auditoria: int
    fecha_evento: datetime
    usuario: str
    id_usuario: int | None
    accion: str
    entidad: str
    id_entidad: str | None
    nombre_entidad: str | None
    descripcion: str | None
    valores_antes: str | None
    valores_despues: str | None
    ip_origen: str | None
    user_agent: str | None
    resultado: str | None
    modulo: str | None
    ruta: str | None
    metodo_http: str | None


@dataclass(frozen=True, slots=True)
class ElementoPapelera:
    entidad: str
    id_registro: int
    nombre: str
    descripcion: str | None
    contexto: str | None
    activo_anterior: bool
    fecha_retiro: datetime | None
    usuario_retiro: str | None
    motivo_retiro: str | None


@dataclass(frozen=True, slots=True)
class Cliente:
    id_cliente: int
    nombre: str
    nombre_normalizado: str
    descripcion: str | None
    eliminado_operativo: bool
    fecha_creacion: datetime
    fecha_actualizacion: datetime | None
    activo: bool


@dataclass(frozen=True, slots=True)
class Categoria:
    id_categoria: int
    nombre: str
    nombre_normalizado: str
    descripcion: str | None
    eliminado_operativo: bool
    fecha_creacion: datetime
    fecha_actualizacion: datetime | None
    activo: bool


@dataclass(frozen=True, slots=True)
class Tipo:
    id_tipo: int
    nombre: str
    nombre_normalizado: str
    descripcion: str | None
    eliminado_operativo: bool
    fecha_creacion: datetime
    fecha_actualizacion: datetime | None
    activo: bool


@dataclass(frozen=True, slots=True)
class Tarea:
    id_tarea: int
    nombre_tarea: str
    descripcion: str | None
    observacion_tecnica: str | None
    id_cliente: int
    cliente: str
    id_categoria: int
    categoria: str
    id_tipo: int
    tipo: str
    tipo_tarea: str
    estado_tarea: str
    permite_ejecucion_manual: bool
    fecha_creacion: datetime
    fecha_actualizacion: datetime | None
    activo: bool


@dataclass(frozen=True, slots=True)
class Script:
    id_script: int
    id_tarea: int
    nombre_script: str
    descripcion: str | None
    id_version_activa: int | None
    fecha_creacion: datetime
    fecha_actualizacion: datetime | None
    activo: bool


@dataclass(frozen=True, slots=True)
class ResumenScript:
    id_script: int
    id_tarea: int
    nombre_script: str
    nombre_tarea: str
    cliente: str
    activo: bool
    numero_version_activa: int | None
    nombre_archivo_activo: str | None
    slots_ocupados: int
    env_configurados: int
    ultima_modificacion: datetime


@dataclass(frozen=True, slots=True)
class VersionScript:
    id_version: int
    id_script: int
    numero_version: int
    nombre_archivo: str
    ruta_fisica: str
    ruta_relativa: str
    hash_archivo: str
    estado_version: str
    es_activa: bool
    requiere_env: bool
    ruta_env_fisica: str | None
    ruta_env_relativa: str | None
    usuario_carga: str
    fecha_carga: datetime
    observacion: str | None
    fecha_creacion: datetime
    fecha_actualizacion: datetime | None


@dataclass(frozen=True, slots=True)
class Programacion:
    id_programacion: int
    id_tarea: int
    nombre_tarea: str
    estado_tarea: str
    tipo_programacion: str
    modo_ejecucion_dia: str | None
    hora_inicio: time | None
    hora_termino: time | None
    hora_ejecucion: time | None
    intervalo_minutos: int | None
    dias_semana: str | None
    dia_mes: int | None
    fecha_especifica: date | None
    fechas_especificas: str | None
    ejecutar_en_feriados: bool
    zona_horaria: str
    fecha_inicio_vigencia: date | None
    fecha_fin_vigencia: date | None
    fecha_creacion: datetime
    fecha_actualizacion: datetime | None
    activo: bool
    proxima_ejecucion: datetime | None = None


@dataclass(frozen=True, slots=True)
class CandidatoProgramacion:
    programacion: Programacion
    id_script: int | None
    id_version: int | None
    estado_version: str | None
    script_activo: bool
    version_activa: bool
    proxima_ejecucion: datetime | None


@dataclass(frozen=True, slots=True)
class ConfiguracionScheduler:
    scheduler_activo: bool
    intervalo_revision_segundos: int
    max_ejecuciones_concurrentes: int
    permitir_ejecucion_automatica: bool
    modo_mantenimiento: bool
    nombre_worker_principal: str | None


@dataclass(frozen=True, slots=True)
class ConfiguracionSchedulerOperativa:
    id_configuracion: int
    scheduler_activo: bool
    intervalo_revision_segundos: int
    max_ejecuciones_concurrentes: int
    permitir_ejecucion_automatica: bool
    modo_mantenimiento: bool
    nombre_worker_principal: str | None
    descripcion: str | None
    fecha_actualizacion: datetime | None
    usuario_actualizacion: str | None


@dataclass(frozen=True, slots=True)
class HeartbeatWorker:
    id_worker: int
    nombre_worker: str
    estado: str
    fecha_inicio: datetime | None
    fecha_ultimo_heartbeat: datetime | None
    fecha_ultimo_ciclo: datetime | None
    resultado_ultimo_ciclo: str | None
    ultimo_error: str | None
    ciclos_ejecutados: int
    tareas_evaluadas_ultimo_ciclo: int
    tareas_ejecutadas_ultimo_ciclo: int
    tareas_omitidas_ultimo_ciclo: int
    pid_proceso: int | None
    host: str | None
    version_app: str | None


@dataclass(frozen=True, slots=True)
class LogSistema:
    id: int
    usuario: str | None
    accion: str
    modulo: str
    descripcion: str
    valor_anterior: str | None
    valor_nuevo: str | None
    ip: str | None
    user_agent: str | None
    fecha_hora: datetime
    nivel: str


@dataclass(frozen=True, slots=True)
class ConfiguracionSistema:
    id_configuracion: int
    clave: str
    valor: str
    tipo_dato: str
    descripcion: str | None
    es_sensible: bool
    fecha_actualizacion: datetime | None
    usuario_actualizacion: str | None
    activo: bool


@dataclass(frozen=True, slots=True)
class ConfiguracionEvidenciaTarea:
    id_config_notificacion: int | None
    id_tarea: int
    enviar_evidencia: bool
    plantilla_evidencia: str
    adjuntar_archivos_declarados: bool
    adjuntar_log_tecnico: bool


@dataclass(frozen=True, slots=True)
class DestinatarioNotificacion:
    id_destinatario: int | None
    tipo_destinatario: str
    canal: str
    email: str
    nombre: str | None


@dataclass(frozen=True, slots=True)
class ConfiguracionNotificacionTarea:
    id_config_notificacion: int | None
    id_tarea: int
    enviar_evidencia: bool
    notificar_exito_activa: bool
    plantilla_evidencia: str
    asunto_personalizado: str | None
    usar_asunto_sugerido_script: bool
    adjuntar_archivos_declarados: bool
    adjuntar_log_tecnico: bool
    alerta_error_activa: bool
    usar_alerta_global: bool
    destinatarios: tuple[DestinatarioNotificacion, ...] = ()


@dataclass(frozen=True, slots=True)
class Feriado:
    id_feriado: int
    fecha: date
    nombre: str
    tipo: str | None
    pais: str
    irrenunciable: bool
    activo: bool
    origen: str
    observacion: str | None
    fecha_creacion: datetime
    fecha_actualizacion: datetime | None
    usuario_creacion: str | None
    usuario_actualizacion: str | None


@dataclass(frozen=True, slots=True)
class ConfiguracionMailGraph:
    id_config_mail: int
    activo: bool
    tenant_id: str | None
    client_id: str | None
    graph_scope: str
    send_mail_user: str | None
    save_to_sent_items: bool
    alertas_destinatarios_default: str | None
    client_secret_origen: str
    fecha_actualizacion: datetime | None
    usuario_actualizacion: str | None


@dataclass(frozen=True, slots=True)
class ContextoEjecucion:
    id_ejecucion: int
    id_tarea: int | None
    id_script: int
    id_version: int
    origen_ejecucion: str
    estado_ejecucion: str
    usuario_ejecucion: str | None
    nombre_worker: str | None
    nombre_tarea: str
    nombre_script: str
    nombre_archivo: str
    numero_version: int
    ruta_script_fisica: str
    ruta_script_relativa: str
    requiere_env: bool
    ruta_env_fisica: str | None
    ruta_env_relativa: str | None
    enviar_evidencia: bool


@dataclass(frozen=True, slots=True)
class EjecucionResumen:
    id_ejecucion: int
    id_tarea: int | None
    origen_ejecucion: str
    estado_ejecucion: str
    fecha_hora_inicio: datetime
    fecha_hora_termino: datetime | None
    duracion_segundos: int | None
    codigo_salida: int | None
    usuario_ejecucion: str | None
    nombre_worker: str | None
    nombre_tarea: str
    nombre_script: str
    nombre_archivo: str
    version_script: str


@dataclass(frozen=True, slots=True)
class DetalleEjecucion(EjecucionResumen):
    id_script: int | None
    id_version: int | None
    mensaje_error: str | None
    pid_proceso: int | None
    fecha_programada: datetime | None
    clave_programacion: str | None
    usuario_detencion: str | None
    fecha_hora_detencion: datetime | None
    motivo_detencion: str | None
    fue_detencion_forzada: bool
    ruta_fisica_log: str | None
    ruta_relativa_log: str | None
    estado_evidencia: str | None
