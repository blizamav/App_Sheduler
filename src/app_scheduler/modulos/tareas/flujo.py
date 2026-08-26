"""Estado presentacional del flujo guiado de configuracion de una tarea."""

from __future__ import annotations


def construir_flujo(*, detalle_scripts=None, evidencia=None,
                    notificaciones=None, total_programaciones=0,
                    paso_actual=None):
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
    estados = (
        ("datos", 1, "Datos", "completo", "Datos guardados"),
        ("script", 2, "Script", "completo" if tiene_script and tiene_version_activa else "pendiente",
         "Script listo" if tiene_script and tiene_version_activa else "Sin version activa"),
        ("evidencia", 3, "Evidencia", estado_evidencia, detalle_evidencia),
        ("notificaciones", 4, "Notificaciones", "completo" if notificaciones_configuradas else "pendiente",
         "Reglas configuradas" if notificaciones_configuradas else "Sin configurar"),
        ("programacion", 5, "Programacion", "completo" if total_programaciones else "pendiente",
         "Programacion configurada" if total_programaciones else "Sin programacion"),
    )
    etiquetas = {"completo": "Completado", "pendiente": "Pendiente", "ajuste": "Requiere ajuste"}
    return tuple({
        "clave": clave,
        "numero": numero,
        "nombre": nombre,
        "estado_funcional": estado,
        "estado": "actual" if clave == paso_actual else estado,
        "detalle": "En curso" if clave == paso_actual else etiquetas[estado],
        "descripcion": descripcion,
    } for clave, numero, nombre, estado, descripcion in estados)


def flujo_nueva_tarea():
    return construir_flujo(paso_actual="datos")
