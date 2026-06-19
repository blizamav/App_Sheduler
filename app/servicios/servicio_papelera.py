from math import ceil

from app.repositorios.repositorio_papelera import (
    ENTIDADES,
    MENSAJE_BLOQUEO_PERMANENTE,
    MENSAJE_MIGRACION_DESACOPLE,
    MENSAJE_SNAPSHOTS_INSUFICIENTES,
    dependencias,
    eliminar_permanente,
    listar_eliminados,
    obtener_eliminado,
    restaurar,
)
from app.repositorios.repositorio_usuarios import contar_administradores_activos
from app.servicios.servicio_auditoria import registrar_auditoria
from app.servicios.servicio_logs_sistema import registrar_log_sistema


ENTIDADES_FILTRO = [
    ("usuarios", "Usuarios"),
    ("clientes", "Clientes"),
    ("categorias", "Categorias"),
    ("tipos", "Tipos"),
    ("tareas", "Tareas"),
    ("scripts", "Scripts"),
    ("scripts_versiones", "Versiones de scripts"),
]


def listar_papelera(filtros=None):
    filtros = filtros or {}
    pagina = _entero(filtros.get("page"), 1, minimo=1)
    por_pagina = _entero(filtros.get("per_page"), 25, minimo=10, maximo=100)
    registros = listar_eliminados()
    registros = [_enriquecer(registro) for registro in registros]
    registros = _filtrar(registros, filtros)
    registros.sort(key=lambda item: item.get("fecha_eliminado_operativo") or "", reverse=True)

    total = len(registros)
    total_paginas = max(ceil(total / por_pagina), 1)
    if pagina > total_paginas:
        pagina = total_paginas
    inicio = (pagina - 1) * por_pagina
    fin = inicio + por_pagina

    return {
        "registros": registros[inicio:fin],
        "total": total,
        "page": pagina,
        "per_page": por_pagina,
        "total_pages": total_paginas,
        "entidades": ENTIDADES_FILTRO,
    }


def restaurar_registro(entidad, id_registro, usuario):
    if entidad not in ENTIDADES:
        return False, "Entidad no soportada por la papelera."

    registro = obtener_eliminado(entidad, id_registro)
    if not registro:
        return False, "Registro no encontrado en papelera."

    ok, motivo = _validar_restauracion(entidad, id_registro)
    if not ok:
        registrar_auditoria(
            "RESTAURAR",
            entidad,
            id_entidad=id_registro,
            nombre_entidad=registro.get("nombre"),
            descripcion=f"Restauracion bloqueada: {motivo}",
            valores_antes=registro,
            valores_despues={"motivo_bloqueo": motivo},
            resultado="BLOQUEADO",
            modulo="PAPELERA",
            usuario=usuario,
        )
        return False, motivo

    restaurar(entidad, id_registro, usuario)
    registrar_log_sistema(
        "PAPELERA_RESTAURACION",
        "PAPELERA",
        f"Registro restaurado como inactivo desde papelera: {registro['entidad_label']} #{id_registro}.",
        usuario=usuario,
        valor_anterior=str(registro),
    )
    registrar_auditoria(
        "RESTAURAR",
        entidad,
        id_entidad=id_registro,
        nombre_entidad=registro.get("nombre"),
        descripcion=f"Registro restaurado como inactivo desde papelera: {registro['entidad_label']} #{id_registro}.",
        valores_antes=registro,
        valores_despues={"eliminado_operativo": 0, "activo": 0},
        modulo="PAPELERA",
        usuario=usuario,
    )
    return True, "Registro restaurado como inactivo. Puedes activarlo manualmente desde su mantenedor si corresponde."


def eliminar_registro_permanente(entidad, id_registro, usuario, id_usuario_sesion=None):
    if entidad not in ENTIDADES:
        return False, "Entidad no soportada por la papelera."

    registro = obtener_eliminado(entidad, id_registro)
    if not registro:
        return False, "Registro no encontrado en papelera."

    ok, motivo = _validar_eliminacion_permanente(entidad, id_registro, id_usuario_sesion)
    if not ok:
        registrar_log_sistema(
            "PAPELERA_ELIMINACION_PERMANENTE_BLOQUEADA",
            "PAPELERA",
            f"Eliminacion permanente bloqueada: {registro['entidad_label']} #{id_registro}. {motivo}",
            usuario=usuario,
            nivel="WARNING",
        )
        _auditar_eliminacion_permanente_bloqueada(entidad, id_registro, registro, motivo, usuario)
        return False, motivo

    try:
        eliminar_permanente(entidad, id_registro)
    except RuntimeError as error:
        registrar_log_sistema(
            "PAPELERA_ELIMINACION_PERMANENTE_BLOQUEADA",
            "PAPELERA",
            f"Eliminacion permanente bloqueada: {registro['entidad_label']} #{id_registro}. {error}",
            usuario=usuario,
            nivel="WARNING",
        )
        _auditar_eliminacion_permanente_bloqueada(entidad, id_registro, registro, str(error), usuario)
        return False, str(error)
    except Exception:
        registrar_log_sistema(
            "PAPELERA_ELIMINACION_PERMANENTE_BLOQUEADA_FK",
            "PAPELERA",
            f"Eliminacion permanente bloqueada por integridad: {registro['entidad_label']} #{id_registro}.",
            usuario=usuario,
            nivel="WARNING",
        )
        _auditar_eliminacion_permanente_bloqueada(entidad, id_registro, registro, MENSAJE_BLOQUEO_PERMANENTE, usuario)
        return False, MENSAJE_BLOQUEO_PERMANENTE

    registrar_log_sistema(
        "PAPELERA_ELIMINACION_PERMANENTE",
        "PAPELERA",
        f"Registro eliminado permanentemente desde tablas operativas: {registro['entidad_label']} #{id_registro}.",
        usuario=usuario,
        valor_anterior=str(registro),
    )
    registrar_auditoria(
        "ELIMINAR_PERMANENTE",
        entidad,
        id_entidad=id_registro,
        nombre_entidad=registro.get("nombre"),
        descripcion=f"Registro eliminado permanentemente desde tablas operativas: {registro['entidad_label']} #{id_registro}.",
        valores_antes=registro,
        resultado="OK",
        modulo="PAPELERA",
        usuario=usuario,
    )
    return True, "Registro eliminado permanentemente de las tablas operativas. El historial se conserva."


def _auditar_eliminacion_permanente_bloqueada(entidad, id_registro, registro, motivo, usuario):
    registrar_auditoria(
        "ELIMINAR_PERMANENTE",
        entidad,
        id_entidad=id_registro,
        nombre_entidad=registro.get("nombre"),
        descripcion=f"Eliminacion permanente bloqueada: {motivo}",
        valores_antes=registro,
        valores_despues={"motivo_bloqueo": motivo},
        resultado="BLOQUEADO",
        modulo="PAPELERA",
        usuario=usuario,
    )


def _enriquecer(registro):
    deps = dependencias(registro["entidad"], registro["id_registro"])
    puede_eliminar, motivo = _evaluar_eliminacion(registro["entidad"], deps)
    registro["dependencias"] = deps
    registro["puede_restaurar"] = True
    registro["puede_eliminar_permanente"] = puede_eliminar
    registro["motivo_bloqueo"] = motivo
    registro["dependencias_resumen"] = _resumir_dependencias(registro["entidad"], deps, motivo)
    return registro


def _validar_restauracion(entidad, id_registro):
    deps = dependencias(entidad, id_registro)
    if entidad == "tareas":
        if deps.get("maestros_eliminados", 0) > 0:
            return False, "No puedes restaurar la tarea mientras cliente, categoria o tipo asociado siga en papelera."
        return True, ""
    if entidad == "scripts":
        if deps.get("tarea_eliminada", 0) > 0:
            return False, "No puedes restaurar el script mientras su tarea asociada siga en papelera."
        return True, ""
    if entidad == "scripts_versiones":
        if deps.get("script_eliminado", 0) > 0:
            return False, "No puedes restaurar la version mientras su script asociado siga en papelera."
        return True, ""
    return True, ""


def _validar_eliminacion_permanente(entidad, id_registro, id_usuario_sesion=None):
    if entidad == "usuarios" and id_usuario_sesion and int(id_usuario_sesion) == int(id_registro):
        return False, "No puedes eliminar permanentemente el usuario con el que estas conectado."

    deps = dependencias(entidad, id_registro)
    if entidad == "usuarios" and deps.get("codigo_rol") == "ADMIN" and contar_administradores_activos(excluir_id=id_registro) == 0:
        return False, "No puedes eliminar permanentemente el ultimo administrador."

    puede, motivo = _evaluar_eliminacion(entidad, deps)
    return puede, motivo


def _evaluar_eliminacion(entidad, deps):
    if deps.get("migracion_desacople_pendiente", 0) > 0:
        return False, MENSAJE_MIGRACION_DESACOPLE
    if deps.get("snapshots_incompletos", 0) > 0:
        return False, MENSAJE_SNAPSHOTS_INSUFICIENTES
    if entidad in ("clientes", "categorias", "tipos") and deps.get("tareas_activas", 0) > 0:
        return False, MENSAJE_BLOQUEO_PERMANENTE
    if entidad == "tareas" and deps.get("ejecuciones_en_curso", 0) > 0:
        return False, "No puedes eliminar permanentemente una tarea con ejecucion en curso."
    if entidad == "tareas" and deps.get("scripts_operativos", 0) > 0:
        return False, MENSAJE_BLOQUEO_PERMANENTE
    if entidad == "scripts" and deps.get("tareas_vigentes", 0) > 0:
        return False, MENSAJE_BLOQUEO_PERMANENTE
    if entidad == "scripts" and deps.get("versiones_operativas", 0) > 0:
        return False, MENSAJE_BLOQUEO_PERMANENTE
    if entidad == "scripts_versiones" and deps.get("version_activa", 0) > 0:
        return False, MENSAJE_BLOQUEO_PERMANENTE
    return True, ""


def _resumir_dependencias(entidad, deps, motivo):
    if motivo:
        return motivo
    if entidad in ("clientes", "categorias", "tipos"):
        return f"Tareas asociadas: {deps.get('tareas_total', 0)}. Tareas activas: {deps.get('tareas_activas', 0)}."
    if entidad == "usuarios":
        return f"Historial asociado: {deps.get('historial', 0)} eventos."
    if entidad == "tareas":
        return f"Ejecuciones en curso: {deps.get('ejecuciones_en_curso', 0)}. Scripts operativos: {deps.get('scripts_operativos', 0)}."
    if entidad == "scripts":
        return f"Tareas vigentes: {deps.get('tareas_vigentes', 0)}. Versiones operativas: {deps.get('versiones_operativas', 0)}."
    if entidad == "scripts_versiones":
        return f"Version activa vigente: {deps.get('version_activa', 0)}."
    return "Sin bloqueos operativos detectados."


def _filtrar(registros, filtros):
    entidad = filtros.get("entidad")
    buscar = (filtros.get("buscar") or "").strip().lower()
    usuario = (filtros.get("usuario") or "").strip().lower()
    fecha_desde = (filtros.get("fecha_desde") or "").strip()
    fecha_hasta = (filtros.get("fecha_hasta") or "").strip()

    filtrados = []
    for registro in registros:
        if entidad and registro["entidad"] != entidad:
            continue
        texto = " ".join(
            str(registro.get(clave) or "")
            for clave in ("entidad_label", "id_registro", "nombre", "descripcion", "motivo_eliminado_operativo")
        ).lower()
        if buscar and buscar not in texto:
            continue
        if usuario and usuario not in str(registro.get("usuario_eliminado_operativo") or "").lower():
            continue
        fecha = str(registro.get("fecha_eliminado_operativo") or "")[:10]
        if fecha_desde and fecha < fecha_desde:
            continue
        if fecha_hasta and fecha > fecha_hasta:
            continue
        filtrados.append(registro)
    return filtrados


def _entero(valor, defecto, minimo=None, maximo=None):
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        numero = defecto
    if minimo is not None:
        numero = max(numero, minimo)
    if maximo is not None:
        numero = min(numero, maximo)
    return numero
