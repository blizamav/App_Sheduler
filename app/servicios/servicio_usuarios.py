import re

from werkzeug.security import check_password_hash, generate_password_hash

from app.repositorios.repositorio_roles import obtener_rol_por_id
from app.repositorios.repositorio_usuarios import (
    actualizar_usuario,
    asegurar_snapshots_usuario,
    cambiar_estado_usuario,
    contar_administradores_activos,
    crear_usuario,
    existe_usuario,
    listar_usuarios,
    marcar_usuario_eliminado_operativo,
    obtener_usuario_por_id,
    obtener_usuario_por_usuario,
    registrar_login_exitoso,
    registrar_login_fallido,
)
from app.servicios.servicio_logs_sistema import registrar_log_sistema
from app.servicios.servicio_permisos import cargar_accesos_usuario


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


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


def _validar_datos_usuario(datos, modo, id_usuario=None):
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
        elif existe_usuario(usuario):
            errores.append("El usuario ya existe.")

    if not nombre:
        errores.append("El nombre completo es obligatorio.")

    if email and not EMAIL_RE.match(email):
        errores.append("El email informado no tiene un formato valido.")

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


def crear_usuario_admin(datos, usuario_accion):
    errores = _validar_datos_usuario(datos, "crear")
    if errores:
        return False, errores, None

    datos_bd = {
        "usuario": datos["usuario"].strip(),
        "nombre_completo": datos["nombre_completo"].strip(),
        "email": datos.get("email", "").strip() or None,
        "password_hash": generate_password_hash(datos["password"]),
        "id_rol": int(datos["id_rol"]),
        "activo": 1 if datos.get("activo") else 0,
        "usuario_accion": usuario_accion,
    }
    id_usuario = crear_usuario(datos_bd)
    registrar_log_sistema(
        "USUARIO_CREADO",
        "USUARIOS",
        f"Usuario creado: {datos_bd['usuario']}.",
        usuario=usuario_accion,
        valor_nuevo=datos_bd["usuario"],
    )
    return True, ["Usuario creado correctamente."], id_usuario


def actualizar_usuario_admin(id_usuario, datos, usuario_accion):
    usuario_actual = obtener_usuario_por_id(id_usuario)
    if not usuario_actual:
        return False, ["Usuario no encontrado."]

    errores = _validar_datos_usuario(datos, "editar", id_usuario)
    if errores:
        return False, errores

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

    actualizar_usuario(id_usuario, datos_bd)
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


def cambiar_estado_usuario_admin(id_usuario, activo, usuario_accion):
    usuario_actual = obtener_usuario_por_id(id_usuario)
    if not usuario_actual:
        return False, "Usuario no encontrado."

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
    if activo:
        return True, "Usuario activado correctamente."
    return True, "Usuario deshabilitado correctamente."


def eliminar_usuario_admin(id_usuario, usuario_accion, id_usuario_sesion=None):
    usuario_actual = obtener_usuario_por_id(id_usuario)
    if not usuario_actual:
        return False, "Usuario no encontrado."

    if id_usuario_sesion and int(id_usuario_sesion) == int(id_usuario):
        registrar_log_sistema(
            "USUARIO_BORRADO_BLOQUEADO_ACTUAL",
            "USUARIOS",
            f"Intento bloqueado de borrar usuario actualmente logueado: {usuario_actual['usuario']}.",
            usuario=usuario_accion,
            nivel="WARNING",
        )
        return False, "No puedes borrar el usuario con el que estas conectado."

    if usuario_actual.get("codigo_rol") == "ADMIN" and contar_administradores_activos(excluir_id=id_usuario) == 0:
        registrar_log_sistema(
            "USUARIO_BORRADO_BLOQUEADO_ULTIMO_ADMIN",
            "USUARIOS",
            f"Intento bloqueado de borrar ultimo administrador activo: {usuario_actual['usuario']}.",
            usuario=usuario_accion,
            nivel="WARNING",
        )
        return False, "No puedes borrar el ultimo administrador activo."

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
    return True, "Usuario borrado de la operacion y enviado a Papelera operativa. No podra iniciar sesion y el historial se conserva."
