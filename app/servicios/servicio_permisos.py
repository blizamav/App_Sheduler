from app.repositorios.repositorio_permisos import obtener_permisos_usuario, obtener_roles_usuario


def cargar_accesos_usuario(id_usuario):
    """Obtiene roles y permisos funcionales para guardar en sesion."""
    roles = obtener_roles_usuario(id_usuario)
    permisos = obtener_permisos_usuario(id_usuario)

    if "SUPER_ADMIN" in roles:
        permisos = ["*"]

    return roles, permisos
