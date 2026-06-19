import re

from werkzeug.security import check_password_hash, generate_password_hash

from app.repositorios.repositorio_roles import obtener_rol_por_id
from app.repositorios.repositorio_usuarios import (
    actualizar_usuario,
    asegurar_snapshots_usuario,
    cambiar_estado_usuario,
    contar_super_admin_activos,
    contar_usuarios_capacidad_admin_activos,
    buscar_duplicado_usuario,
    crear_usuario,
    listar_usuarios,
    marcar_usuario_eliminado_operativo,
    obtener_usuario_por_id,
    obtener_usuario_por_usuario,
    registrar_login_exitoso,
    registrar_login_fallido,
)
from app.servicios.servicio_logs_sistema import registrar_log_sistema
from app.servicios.servicio_auditoria import registrar_auditoria
from app.servicios.servicio_duplicados import (
    MENSAJE_DUPLICADO_SQL,
    es_error_duplicado_sql,
    registrar_bloqueo_duplicado,
    validar_sin_duplicado,
)
from app.servicios.servicio_permisos import cargar_accesos_usuario


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
ROL_SUPER_ADMIN = "SUPER_ADMIN"
ROL_ADMIN = "ADMIN"


def autenticar_usuario_bd(usuario, password):
    """Valida credenciales contra tabla usuarios."""
    usuario_bd = obtener_usuario_por_usuario(usuario)
    if not usuario_bd:
        registrar_log_sistema(
            "LOGIN_FALLIDO",
            "AUTH",
            "Intento de login con usuario inexistente.",
            usuario=usuario,
            nivel="WARNING",
        )
        return False, "Usuario o contrasena incorrectos.", None

    if not usuario_bd["activo"] or usuario_bd["bloqueado"]:
        registrar_log_sistema(
            "LOGIN_BLOQUEADO",
            "AUTH",
            "Intento de login con usuario inactivo o bloqueado.",
            usuario=usuario,
            nivel="WARNING",
        )
        return False, "Usuario inactivo o bloqueado. Solicita activacion a un administrador.", None

    if not check_password_hash(usuario_bd["password_hash"], password):
        registrar_login_fallido(usuario)
        registrar_log_sistema(
            "LOGIN_FALLIDO",
            "AUTH",
            "Intento de login con contrasena no valida.",
            usuario=usuario,
            nivel="WARNING",
        )
        return False, "Usuario o contrasena incorrectos.", None

    roles, permisos = cargar_accesos_usuario(usuario_bd["id_usuario"])
    registrar_login_exitoso(usuario_bd["id_usuario"])
    registrar_log_sistema(
        "LOGIN_EXITOSO",
        "AUTH",
        "Login correcto con usuario de base de datos.",
        usuario=usuario,
        nivel="INFO",
    )

    return True, "Sesion iniciada correctamente.", {
        "id_usuario": usuario_bd["id_usuario"],
        "usuario": usuario_bd["usuario"],
        "nombre_completo": usuario_bd["nombre_completo"],
        "email": usuario_bd["email"],
        "roles": roles,
        "permisos": permisos,
    }


def listar_usuarios_admin(filtros=None):
    return listar_usuarios(filtros)


def obtener_usuario_admin(id_usuario):
    return obtener_usuario_por_id(id_usuario)


def _validar_datos_usuario(datos, modo, id_usuario=None, usuario_accion=None):
    errores = []
    usuario = datos.get("usuario", "").strip()
    nombre = datos.get("nombre_completo", "").strip()
    email = datos.get("email", "").strip()
    password = datos.get("password", "")
    confirmacion = datos.get("confirmacion_password", "")
    id_rol = datos.get("id_rol")

    if modo == "crear":
        if not usuario:
            errores.append("El usuario es obligatorio.")
        else:
            mensaje = validar_sin_duplicado(
                buscar_duplicado_usuario("usuario", usuario, id_usuario),
                "usuarios",
                usuario_accion,
                valores={"campo": "usuario", "valor": usuario},
                modulo="USUARIOS",
            )
            if mensaje:
                errores.append(mensaje)

    if not nombre:
        errores.append("El nombre completo es obligatorio.")

    if email and not EMAIL_RE.match(email):
        errores.append("El email informado no tiene un formato valido.")
    elif email:
        mensaje = validar_sin_duplicado(
            buscar_duplicado_usuario("email", email, id_usuario),
            "usuarios",
            usuario_accion,
            valores={"campo": "email", "valor": email},
            modulo="USUARIOS",
        )
        if mensaje:
            errores.append(mensaje)

    if not id_rol:
        errores.append("Debes seleccionar un rol.")
    elif not obtener_rol_por_id(id_rol):
        errores.append("El rol seleccionado no es valido.")

    if modo == "crear" and not password:
        errores.append("La contrasena es obligatoria.")

    if password or confirmacion:
        if password != confirmacion:
            errores.append("La confirmacion de contrasena no coincide.")
        elif len(password) < 8:
            errores.append("La contrasena debe tener al menos 8 caracteres.")

    return errores


def crear_usuario_admin(datos, usuario_accion, actor=None):
    errores = _validar_datos_usuario(datos, "crear", usuario_accion=usuario_accion)
    if errores:
        return False, errores, None

    rol_nuevo = obtener_rol_por_id(datos.get("id_rol"))
    if _es_rol_super_admin(rol_nuevo) and not _actor_es_super_admin(actor):
        mensaje = "Solo un SUPER_ADMIN puede asignar el rol SUPER_ADMIN."
        _auditar_bloqueo_rol(
            "CREAR",
            None,
            datos.get("usuario"),
            mensaje,
            usuario_accion,
            valores_despues={"id_rol": datos.get("id_rol"), "codigo_rol": ROL_SUPER_ADMIN},
        )
        return False, [mensaje], None

    datos_bd = {
        "usuario": datos["usuario"].strip(),
        "nombre_completo": datos["nombre_completo"].strip(),
        "email": datos.get("email", "").strip() or None,
        "password_hash": generate_password_hash(datos["password"]),
        "id_rol": int(datos["id_rol"]),
        "activo": 1 if datos.get("activo") else 0,
        "usuario_accion": usuario_accion,
    }
    try:
        id_usuario = crear_usuario(datos_bd)
    except Exception as error:
        if es_error_duplicado_sql(error):
            registrar_bloqueo_duplicado(
                "usuarios",
                usuario_accion,
                MENSAJE_DUPLICADO_SQL,
                nombre_entidad=datos_bd["usuario"],
                valores={"usuario": datos_bd["usuario"], "email": datos_bd.get("email")},
                modulo="USUARIOS",
            )
            return False, [MENSAJE_DUPLICADO_SQL], None
        raise
    registrar_log_sistema(
        "USUARIO_CREADO",
        "USUARIOS",
        f"Usuario creado: {datos_bd['usuario']}.",
        usuario=usuario_accion,
        valor_nuevo=datos_bd["usuario"],
    )
    registrar_auditoria(
        "CREAR",
        "usuarios",
        id_entidad=id_usuario,
        nombre_entidad=datos_bd["usuario"],
        descripcion=f"Usuario creado: {datos_bd['usuario']}.",
        valores_despues=datos_bd,
        modulo="USUARIOS",
        usuario=usuario_accion,
    )
    return True, ["Usuario creado correctamente."], id_usuario


def actualizar_usuario_admin(id_usuario, datos, usuario_accion, actor=None):
    usuario_actual = obtener_usuario_por_id(id_usuario)
    if not usuario_actual:
        return False, ["Usuario no encontrado."]

    errores = _validar_datos_usuario(datos, "editar", id_usuario, usuario_accion)
    if errores:
        return False, errores

    rol_nuevo = obtener_rol_por_id(datos.get("id_rol"))
    ok_seguridad, mensaje_seguridad = _validar_operacion_usuario(
        actor,
        usuario_actual,
        "EDITAR",
        nuevo_rol=rol_nuevo,
        nuevo_activo=1 if datos.get("activo") else 0,
    )
    if not ok_seguridad:
        _auditar_bloqueo_rol(
            "EDITAR",
            id_usuario,
            usuario_actual["usuario"],
            mensaje_seguridad,
            usuario_accion,
            valores_antes=usuario_actual,
            valores_despues={"id_rol": datos.get("id_rol"), "activo": 1 if datos.get("activo") else 0},
        )
        return False, [mensaje_seguridad]

    datos_bd = {
        "nombre_completo": datos["nombre_completo"].strip(),
        "email": datos.get("email", "").strip() or None,
        "id_rol": int(datos["id_rol"]),
        "activo": 1 if datos.get("activo") else 0,
        "usuario_accion": usuario_accion,
    }
    if datos.get("password"):
        datos_bd["password_hash"] = generate_password_hash(datos["password"])
        datos_bd["password_actualizada"] = True

    try:
        actualizar_usuario(id_usuario, datos_bd)
    except Exception as error:
        if es_error_duplicado_sql(error):
            registrar_bloqueo_duplicado(
                "usuarios",
                usuario_accion,
                MENSAJE_DUPLICADO_SQL,
                id_entidad=id_usuario,
                nombre_entidad=usuario_actual["usuario"],
                valores={"email": datos_bd.get("email")},
                modulo="USUARIOS",
            )
            return False, [MENSAJE_DUPLICADO_SQL]
        raise
    rol_anterior = usuario_actual.get("id_rol")
    rol_nuevo = datos_bd["id_rol"]
    mensajes = ["Usuario actualizado correctamente."]

    registrar_log_sistema(
        "USUARIO_EDITADO",
        "USUARIOS",
        f"Usuario editado: {usuario_actual['usuario']}.",
        usuario=usuario_accion,
        valor_anterior=str(usuario_actual),
        valor_nuevo=str({k: v for k, v in datos_bd.items() if k != "password_hash"}),
    )
    registrar_auditoria(
        "EDITAR",
        "usuarios",
        id_entidad=id_usuario,
        nombre_entidad=usuario_actual["usuario"],
        descripcion=f"Usuario editado: {usuario_actual['usuario']}.",
        valores_antes=usuario_actual,
        valores_despues=datos_bd,
        modulo="USUARIOS",
        usuario=usuario_accion,
    )

    if str(rol_anterior) != str(rol_nuevo):
        registrar_log_sistema(
            "ROL_USUARIO_ACTUALIZADO",
            "USUARIOS",
            f"Rol actualizado para usuario: {usuario_actual['usuario']}.",
            usuario=usuario_accion,
            valor_anterior=str(rol_anterior),
            valor_nuevo=str(rol_nuevo),
        )
        mensajes.append("Rol actualizado correctamente.")

    if datos_bd.get("password_actualizada"):
        registrar_log_sistema(
            "PASSWORD_USUARIO_ACTUALIZADA",
            "USUARIOS",
            f"Contrasena actualizada para usuario: {usuario_actual['usuario']}.",
            usuario=usuario_accion,
        )
        mensajes.append("Contrasena actualizada correctamente.")

    return True, mensajes


def cambiar_estado_usuario_admin(id_usuario, activo, usuario_accion, actor=None):
    usuario_actual = obtener_usuario_por_id(id_usuario)
    if not usuario_actual:
        return False, "Usuario no encontrado."

    ok_seguridad, mensaje_seguridad = _validar_operacion_usuario(
        actor,
        usuario_actual,
        "ACTIVAR" if activo else "DESACTIVAR",
        nuevo_activo=1 if activo else 0,
    )
    if not ok_seguridad:
        _auditar_bloqueo_rol(
            "ACTIVAR" if activo else "DESACTIVAR",
            id_usuario,
            usuario_actual["usuario"],
            mensaje_seguridad,
            usuario_accion,
            valores_antes=usuario_actual,
            valores_despues={"activo": 1 if activo else 0},
        )
        return False, mensaje_seguridad

    cambiar_estado_usuario(id_usuario, 1 if activo else 0, usuario_accion)
    accion = "USUARIO_ACTIVADO" if activo else "USUARIO_DESACTIVADO"
    registrar_log_sistema(
        accion,
        "USUARIOS",
        f"Estado actualizado para usuario: {usuario_actual['usuario']}.",
        usuario=usuario_accion,
        valor_anterior=str(usuario_actual["activo"]),
        valor_nuevo=str(1 if activo else 0),
    )
    registrar_auditoria(
        "ACTIVAR" if activo else "DESACTIVAR",
        "usuarios",
        id_entidad=id_usuario,
        nombre_entidad=usuario_actual["usuario"],
        descripcion=f"Estado actualizado para usuario: {usuario_actual['usuario']}.",
        valores_antes={"activo": usuario_actual["activo"]},
        valores_despues={"activo": 1 if activo else 0},
        modulo="USUARIOS",
        usuario=usuario_accion,
    )
    if activo:
        return True, "Usuario activado correctamente."
    return True, "Usuario deshabilitado correctamente."


def eliminar_usuario_admin(id_usuario, usuario_accion, id_usuario_sesion=None, actor=None):
    usuario_actual = obtener_usuario_por_id(id_usuario)
    if not usuario_actual:
        return False, "Usuario no encontrado."

    ok_seguridad, mensaje_seguridad = _validar_operacion_usuario(actor, usuario_actual, "BORRAR_OPERATIVO")
    if not ok_seguridad:
        registrar_log_sistema(
            "USUARIO_BORRADO_BLOQUEADO_ROL",
            "USUARIOS",
            f"Intento bloqueado de borrar usuario protegido: {usuario_actual['usuario']}.",
            usuario=usuario_accion,
            nivel="WARNING",
        )
        registrar_auditoria(
            "BLOQUEO_AUTO_ELIMINACION",
            "usuarios",
            id_entidad=id_usuario,
            nombre_entidad=usuario_actual["usuario"],
            descripcion=mensaje_seguridad,
            valores_antes=usuario_actual,
            resultado="BLOQUEADO",
            modulo="USUARIOS",
            usuario=usuario_accion,
        )
        return False, mensaje_seguridad

    if id_usuario_sesion and int(id_usuario_sesion) == int(id_usuario):
        registrar_log_sistema(
            "USUARIO_BORRADO_BLOQUEADO_ACTUAL",
            "USUARIOS",
            f"Intento bloqueado de borrar usuario actualmente logueado: {usuario_actual['usuario']}.",
            usuario=usuario_accion,
            nivel="WARNING",
        )
        registrar_auditoria(
            "BORRAR_OPERATIVO",
            "usuarios",
            id_entidad=id_usuario,
            nombre_entidad=usuario_actual["usuario"],
            descripcion="Intento bloqueado de borrar el usuario actualmente conectado.",
            valores_antes=usuario_actual,
            resultado="BLOQUEADO",
            modulo="USUARIOS",
            usuario=usuario_accion,
        )
        return False, "No puedes borrar el usuario con el que estas conectado."

    asegurar_snapshots_usuario(usuario_actual["usuario"])
    marcar_usuario_eliminado_operativo(
        id_usuario,
        usuario_accion,
        "Borrado operativo seguro. Eliminacion permanente disponible solo desde Papelera operativa.",
    )
    registrar_log_sistema(
        "USUARIO_BORRADO_OPERATIVO",
        "USUARIOS",
        f"Usuario retirado de operacion conservando historial: {usuario_actual['usuario']}.",
        usuario=usuario_accion,
        valor_anterior=str(usuario_actual),
    )
    registrar_auditoria(
        "BORRAR_OPERATIVO",
        "usuarios",
        id_entidad=id_usuario,
        nombre_entidad=usuario_actual["usuario"],
        descripcion=f"Usuario retirado de operacion conservando historial: {usuario_actual['usuario']}.",
        valores_antes=usuario_actual,
        valores_despues={"eliminado_operativo": 1, "activo": 0},
        modulo="USUARIOS",
        usuario=usuario_accion,
    )
    return True, "Usuario borrado de la operacion y enviado a Papelera operativa. No podra iniciar sesion y el historial se conserva."


def actor_es_super_admin(actor):
    return _actor_es_super_admin(actor)


def accion_usuario_permitida(actor, usuario_objetivo, accion):
    ok, _mensaje = _validar_operacion_usuario(actor, usuario_objetivo, accion)
    return ok


def _validar_operacion_usuario(actor, usuario_objetivo, accion, nuevo_rol=None, nuevo_activo=None):
    actor = actor or {}
    codigo_rol_actual = usuario_objetivo.get("codigo_rol")
    objetivo_es_super = codigo_rol_actual == ROL_SUPER_ADMIN
    actor_super = _actor_es_super_admin(actor)
    mismo_usuario = _mismo_usuario(actor, usuario_objetivo)

    if objetivo_es_super and not actor_super:
        return False, "Solo un SUPER_ADMIN puede modificar, desactivar o eliminar usuarios SUPER_ADMIN."

    if nuevo_rol and _es_rol_super_admin(nuevo_rol) and not actor_super:
        return False, "Solo un SUPER_ADMIN puede asignar el rol SUPER_ADMIN."

    if objetivo_es_super and nuevo_rol and not _es_rol_super_admin(nuevo_rol) and not actor_super:
        return False, "Solo un SUPER_ADMIN puede quitar el rol SUPER_ADMIN."

    if accion in ("DESACTIVAR", "BORRAR_OPERATIVO") and mismo_usuario:
        return False, "No puedes desactivar ni borrar el usuario con el que estas conectado."

    if accion in ("DESACTIVAR", "BORRAR_OPERATIVO") and objetivo_es_super:
        if contar_super_admin_activos(excluir_id=usuario_objetivo["id_usuario"]) == 0:
            return False, "No puedes desactivar ni borrar el ultimo SUPER_ADMIN activo."

    if accion == "EDITAR" and objetivo_es_super:
        deja_de_ser_super = nuevo_rol and not _es_rol_super_admin(nuevo_rol)
        queda_inactivo = nuevo_activo == 0
        if mismo_usuario and queda_inactivo:
            return False, "No puedes desactivar el usuario con el que estas conectado."
        if (deja_de_ser_super or queda_inactivo) and contar_super_admin_activos(excluir_id=usuario_objetivo["id_usuario"]) == 0:
            return False, "No puedes quitar o desactivar el ultimo SUPER_ADMIN activo."

    if accion == "BORRAR_OPERATIVO" and codigo_rol_actual == ROL_ADMIN:
        if contar_usuarios_capacidad_admin_activos(excluir_id=usuario_objetivo["id_usuario"]) == 0:
            return False, "No puedes borrar el ultimo usuario con capacidad administrativa."

    return True, ""


def _actor_es_super_admin(actor):
    roles = actor.get("roles") or []
    permisos = actor.get("permisos") or []
    return bool(actor.get("es_admin_env") or "*" in permisos or ROL_SUPER_ADMIN in roles or "SUPER_ADMIN_ENV" in roles)


def _mismo_usuario(actor, usuario_objetivo):
    id_actor = actor.get("id_usuario")
    return id_actor is not None and str(id_actor) == str(usuario_objetivo.get("id_usuario"))


def _es_rol_super_admin(rol):
    return bool(rol and rol.get("codigo_rol") == ROL_SUPER_ADMIN)


def _auditar_bloqueo_rol(accion, id_usuario, nombre_usuario, mensaje, usuario_accion, valores_antes=None, valores_despues=None):
    registrar_auditoria(
        _accion_bloqueo_usuario(mensaje, accion),
        "usuarios",
        id_entidad=id_usuario,
        nombre_entidad=nombre_usuario,
        descripcion=mensaje,
        valores_antes=valores_antes,
        valores_despues=valores_despues,
        resultado="BLOQUEADO",
        modulo="USUARIOS",
        usuario=usuario_accion,
    )


def _accion_bloqueo_usuario(mensaje, accion_base):
    texto = str(mensaje or "").lower()
    if "super_admin" in texto and ("asignar" in texto or "quitar" in texto):
        return "BLOQUEO_ESCALAMIENTO_PRIVILEGIOS"
    if "super_admin" in texto and ("modificar" in texto or "editar" in texto or "desactivar" in texto or "eliminar" in texto):
        return "BLOQUEO_MODIFICAR_SUPER_ADMIN"
    if "ultimo super_admin" in texto or "ultimo usuario con capacidad administrativa" in texto:
        return "BLOQUEO_ELIMINAR_ULTIMO_SUPER_ADMIN"
    if "con el que estas conectado" in texto:
        return "BLOQUEO_AUTO_ELIMINACION"
    return accion_base
