from app.repositorios.repositorio_roles import listar_roles_activos


def obtener_roles_para_formulario():
    return listar_roles_activos()
