"""Estado presentacional del flujo guiado de configuracion de una tarea."""

from __future__ import annotations


def construir_flujo(*, detalle_scripts=None, evidencia=None,
                    notificaciones=None, total_programaciones=0):
    detalle_scripts = detalle_scripts or {}
    soporte = (evidencia or {}).get("soporte", {})
    validaciones = soporte.get("validaciones", {})
    config = (notificaciones or {}).get("configuracion")

    tiene_script = bool(detalle_scripts.get("script"))
    tiene_version_activa = any(
        bool(getattr(version, "es_activa", False))
        for version in detalle_scripts.get("versiones", ())
    )
    if soporte.get("compatible"):
        estado_evidencia, detalle_evidencia = "completo", "Compatible 1.0"
    elif any(bool(valor) for valor in validaciones.values()):
        estado_evidencia, detalle_evidencia = "ajuste", "Requiere ajuste"
    else:
        estado_evidencia, detalle_evidencia = "pendiente", "No implementada"

    notificaciones_configuradas = bool(
        config
        and config.id_config_notificacion is not None
        and (config.notificar_exito_activa or config.alerta_error_activa)
    )
    return (
        {"numero": 1, "nombre": "Datos", "estado": "completo", "detalle": "Guardados"},
        {"numero": 2, "nombre": "Script", "estado": "completo" if tiene_script and tiene_version_activa else "pendiente",
         "detalle": "Ejecutable" if tiene_script and tiene_version_activa else "Pendiente"},
        {"numero": 3, "nombre": "Evidencia", "estado": estado_evidencia, "detalle": detalle_evidencia},
        {"numero": 4, "nombre": "Notificaciones", "estado": "completo" if notificaciones_configuradas else "pendiente",
         "detalle": "Configuradas" if notificaciones_configuradas else "Pendientes"},
        {"numero": 5, "nombre": "Programacion", "estado": "completo" if total_programaciones else "pendiente",
         "detalle": "Configurada" if total_programaciones else "Pendiente"},
    )


def flujo_nueva_tarea():
    return (
        {"numero": 1, "nombre": "Datos", "estado": "actual", "detalle": "En curso"},
        {"numero": 2, "nombre": "Script", "estado": "pendiente", "detalle": "Pendiente"},
        {"numero": 3, "nombre": "Evidencia", "estado": "pendiente", "detalle": "Opcional"},
        {"numero": 4, "nombre": "Notificaciones", "estado": "pendiente", "detalle": "Pendientes"},
        {"numero": 5, "nombre": "Programacion", "estado": "pendiente", "detalle": "Pendiente"},
    )
