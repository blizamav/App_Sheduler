from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

import pytest

from app_scheduler import crear_aplicacion

from app_scheduler.compartido.auditoria import ContextoAuditoria
from app_scheduler.compartido.autorizacion import CLAVE_IDENTIDAD, IdentidadSesion, TIPO_BASE_DATOS
from app_scheduler.compartido.errores import ErrorValidacion
from app_scheduler.compartido.filesystem import AlmacenArchivosProcesos, validar_env, validar_script
from app_scheduler.modulos.scripts.casos_uso import ServicioScripts
from app_scheduler.modulos.tareas.casos_uso import ServicioTareas
from app_scheduler.persistencia.modelos import Pagina, Script, Tarea, VersionScript
from app_scheduler.persistencia.modelos import Paginacion
from app_scheduler.persistencia.repositorio_scripts import RepositorioScripts
from app_scheduler.persistencia.repositorio_tareas import RepositorioTareas
from tests.reconstruccion.fakes_sql import ConexionProgramada, ResultadoSQL


FECHA = datetime(2026, 8, 18, 12, 0)


def tarea():
    return Tarea(1, "Proceso diario", None, None, 2, "Cliente", 3, "Categoria", 4,
                 "Tipo", "MANUAL", "ACTIVA", True, FECHA, None, True)


def version(numero=1, *, activa=False, estado="DISPONIBLE", ruta=""):
    return VersionScript(numero, 8, numero, f"proceso_{numero}.py", ruta, ruta,
                         "a" * 64, "ACTIVA" if activa else estado, activa, False,
                         None, None, "actor", FECHA, None, FECHA, None)


class Estado:
    def __init__(self):
        self.tarea = tarea(); self.script = None; self.versiones = []
        self.referencias = {}; self.eventos = []; self.confirmaciones = 0
        self.fallar_commit = False; self.ultima_creacion_tarea = None
        self.fallar_auditoria = False
        self.catalogos_validos = True

    @contextmanager
    def conexion_lectura(self): yield self


class Uow:
    def __init__(self, estado): self.e = estado
    def __enter__(self):
        self._versiones_antes = list(self.e.versiones)
        return self
    def __exit__(self, tipo_error, *_):
        if tipo_error is not None:
            self.e.versiones = self._versiones_antes
        return False
    def obtener_conexion(self): return self.e
    def confirmar(self):
        if self.e.fallar_commit: raise RuntimeError("commit controlado")
        self.e.confirmaciones += 1


class RepoTareas:
    def __init__(self, e): self.e = e
    def obtener_por_id(self, identificador): return self.e.tarea if identificador == 1 else None
    def existe_clave(self, *_args, **_kwargs): return False
    def catalogos_validos(self, *_): return self.e.catalogos_validos
    def crear(self, datos, actor): self.e.ultima_creacion_tarea = (datos, actor); return 11
    def actualizar(self, *_): return True
    def cambiar_estado(self, *_): return True


class RepoScripts:
    def __init__(self, e): self.e = e
    def obtener_por_tarea(self, _): return self.e.script
    def obtener(self, _): return self.e.script
    def listar_versiones(self, _): return tuple(self.e.versiones)
    def obtener_version(self, identificador): return next((v for v in self.e.versiones if v.id_version == identificador), None)
    def contar_referencias_version(self, identificador): return self.e.referencias.get(identificador, 0)
    def contar_referencias_version_para_reemplazo(self, identificador): return self.e.referencias.get(identificador, 0)
    def crear_script(self, id_tarea, nombre, descripcion, actor):
        self.e.script = Script(8, id_tarea, nombre, descripcion, None, FECHA, None, True); return 8
    def crear_version(self, id_script, numero, nombre, fisica, relativa, hash_archivo, activa, observacion, actor):
        nueva = VersionScript(numero, id_script, numero, nombre, fisica, relativa, hash_archivo,
                              "ACTIVA" if activa else "DISPONIBLE", activa, False, None, None,
                              actor, FECHA, observacion, FECHA, None)
        self.e.versiones.append(nueva); return nueva.id_version
    def establecer_version_activa(self, id_script, id_version, actor):
        self.e.versiones = [VersionScript(v.id_version, v.id_script, v.numero_version,
            v.nombre_archivo, v.ruta_fisica, v.ruta_relativa, v.hash_archivo,
            "ACTIVA" if v.id_version == id_version else ("DISPONIBLE" if v.es_activa else v.estado_version),
            v.id_version == id_version, v.requiere_env, v.ruta_env_fisica, v.ruta_env_relativa,
            v.usuario_carga, v.fecha_carga, v.observacion, v.fecha_creacion, v.fecha_actualizacion)
            for v in self.e.versiones]
    def reemplazar_version(self, id_version, nombre, fisica, relativa, hash_archivo, observacion, actor): return True
    def desactivar_version(self, _): return True
    def actualizar_env(self, *_): return True


class Auditoria:
    def __init__(self, e): self.e = e
    def registrar(self, evento):
        if self.e.fallar_auditoria: raise RuntimeError("auditoria controlada")
        self.e.eventos.append(evento)


def actor(permisos=frozenset()):
    return IdentidadSesion(1, "actor", "Actor", TIPO_BASE_DATOS, frozenset({"ADMIN"}), permisos)


def servicio_scripts(estado, tmp_path):
    config = SimpleNamespace(ruta_base_scripts=tmp_path / "scripts",
        ruta_base_env_scripts=tmp_path / "env_scripts", max_script_size_mb=1, max_env_size_kb=1)
    return ServicioScripts(estado, config, fabrica_uow=Uow, repositorio=RepoScripts,
        repositorio_tareas=RepoTareas, repositorio_auditoria=Auditoria)


def test_tarea_no_persiste_usuario_ejecutor():
    estado = Estado()
    servicio = ServicioTareas(estado, fabrica_uow=Uow, repositorio=RepoTareas,
                              repositorio_auditoria=Auditoria)
    identificador = servicio.crear({"nombre_tarea": "Proceso", "id_cliente": "2",
        "id_categoria": "3", "id_tipo": "4", "estado_tarea": "ACTIVA",
        "usuario_ejecutor": "no-persistir"}, actor(), ContextoAuditoria())
    assert identificador == 11
    assert "usuario_ejecutor" not in estado.ultima_creacion_tarea[0]
    assert estado.eventos[0].accion == "TAREA_CREADA"


def test_tarea_rechaza_catalogo_inactivo():
    estado = Estado(); estado.catalogos_validos = False
    servicio = ServicioTareas(estado, fabrica_uow=Uow, repositorio=RepoTareas,
                              repositorio_auditoria=Auditoria)
    with pytest.raises(ErrorValidacion, match="estar activos"):
        servicio.crear({"nombre_tarea": "Proceso", "id_cliente": "2",
            "id_categoria": "3", "id_tipo": "4", "estado_tarea": "ACTIVA"},
            actor(), ContextoAuditoria())
    assert estado.ultima_creacion_tarea is None


@pytest.mark.parametrize("nombre", ("../malo.py", "malo.txt", "carpeta/malo.py"))
def test_script_rechaza_nombre_inseguro(nombre):
    with pytest.raises(ErrorValidacion): validar_script(nombre, b"print('ok')\n", 100)


def test_script_rechaza_sintaxis_y_tamano():
    with pytest.raises(ErrorValidacion, match="sintaxis"): validar_script("x.py", b"if :", 100)
    with pytest.raises(ErrorValidacion, match="tamano"): validar_script("x.py", b"print(1)", 2)


def test_primera_version_crea_v1_activa_y_archivo(tmp_path):
    estado = Estado(); servicio = servicio_scripts(estado, tmp_path)
    identificador = servicio.subir_version(1, "proceso.py", b"print('ok')\n", None,
                                           actor(), ContextoAuditoria())
    assert identificador == 1 and estado.versiones[0].es_activa
    assert Path(estado.versiones[0].ruta_fisica).read_bytes() == b"print('ok')\n"
    assert estado.eventos[0].accion == "SCRIPT_VERSION_CARGADA"


def test_no_crea_cuarta_version(tmp_path):
    estado = Estado(); estado.script = Script(8, 1, "Script", None, 1, FECHA, None, True)
    estado.versiones = [version(n, activa=n == 1) for n in (1, 2, 3)]
    with pytest.raises(ErrorValidacion, match="tres slots"):
        servicio_scripts(estado, tmp_path).subir_version(1, "cuarta.py", b"print(4)\n", None, actor(), ContextoAuditoria())


def test_activar_v2_deja_una_unica_version_activa(tmp_path):
    estado = Estado(); estado.script = Script(8, 1, "Script", None, 1, FECHA, None, True)
    estado.versiones = [version(1, activa=True), version(2)]

    servicio_scripts(estado, tmp_path).activar(1, 2, actor(), ContextoAuditoria())

    activas = [item for item in estado.versiones if item.es_activa]
    assert len(activas) == 1 and activas[0].id_version == 2
    assert next(item for item in estado.versiones if item.id_version == 1).estado_version == "DISPONIBLE"
    assert estado.eventos[0].accion == "SCRIPT_VERSION_ACTIVADA"


def test_activar_rechaza_version_inexistente_y_transicion_invalida(tmp_path):
    estado = Estado(); estado.script = Script(8, 1, "Script", None, 1, FECHA, None, True)
    estado.versiones = [version(1, activa=True), version(2, estado="REEMPLAZADA")]
    servicio = servicio_scripts(estado, tmp_path)

    with pytest.raises(ErrorValidacion, match="no encontrada"):
        servicio.activar(1, 99, actor(), ContextoAuditoria())
    with pytest.raises(ErrorValidacion, match="no permite"):
        servicio.activar(1, 2, actor(), ContextoAuditoria())


def test_activar_revierte_cambio_si_falla_commit(tmp_path):
    estado = Estado(); estado.script = Script(8, 1, "Script", None, 1, FECHA, None, True)
    estado.versiones = [version(1, activa=True), version(2)]
    estado.fallar_commit = True

    with pytest.raises(RuntimeError, match="commit"):
        servicio_scripts(estado, tmp_path).activar(1, 2, actor(), ContextoAuditoria())

    activas = [item for item in estado.versiones if item.es_activa]
    assert len(activas) == 1 and activas[0].id_version == 1


def test_reemplazo_bloquea_activa_e_historial(tmp_path):
    estado = Estado(); estado.script = Script(8, 1, "Script", None, 1, FECHA, None, True)
    estado.versiones = [version(1, activa=True), version(2)]
    servicio = servicio_scripts(estado, tmp_path)
    with pytest.raises(ErrorValidacion, match="activa"):
        servicio.reemplazar(1, 1, "nueva.py", b"print(1)\n", None, actor(), ContextoAuditoria())
    estado.referencias[2] = 1
    with pytest.raises(ErrorValidacion, match="historial"):
        servicio.reemplazar(1, 2, "nueva.py", b"print(2)\n", None, actor(), ContextoAuditoria())


def test_fallo_commit_compensa_archivo_nuevo(tmp_path):
    estado = Estado(); estado.fallar_commit = True
    with pytest.raises(RuntimeError, match="commit"):
        servicio_scripts(estado, tmp_path).subir_version(1, "proceso.py", b"print(1)\n", None, actor(), ContextoAuditoria())
    assert not list(tmp_path.rglob("*.py"))
    assert not list(tmp_path.rglob("*.tmp"))


def test_fallo_auditoria_compensa_archivo_nuevo(tmp_path):
    estado = Estado(); estado.fallar_auditoria = True
    with pytest.raises(RuntimeError, match="auditoria"):
        servicio_scripts(estado, tmp_path).subir_version(1, "proceso.py", b"print(1)\n", None, actor(), ContextoAuditoria())
    assert not list(tmp_path.rglob("*.py")) and not list(tmp_path.rglob("*.tmp"))


def test_reemplazo_fallido_restaura_archivo_y_env(tmp_path):
    estado = Estado(); servicio = servicio_scripts(estado, tmp_path)
    destino = servicio.almacen.ruta_script(("Categoria", "Tipo", "Cliente", "Proceso diario"), 2, "viejo.py")
    destino.parent.mkdir(parents=True); destino.write_bytes(b"print('viejo')\n")
    env = servicio.almacen.ruta_env(("Categoria", "Tipo", "Cliente", "Proceso diario"), 2)
    env.parent.mkdir(parents=True, exist_ok=True); env.write_bytes(b"CLAVE=valor\n")
    estado.script = Script(8, 1, "Script", None, 1, FECHA, None, True)
    v = version(2, ruta=str(destino))
    v = VersionScript(v.id_version, v.id_script, v.numero_version, v.nombre_archivo,
        v.ruta_fisica, v.ruta_relativa, v.hash_archivo, v.estado_version, v.es_activa,
        True, str(env), "env", v.usuario_carga, v.fecha_carga, v.observacion,
        v.fecha_creacion, v.fecha_actualizacion)
    estado.versiones = [v]; estado.fallar_commit = True
    with pytest.raises(RuntimeError):
        servicio.reemplazar(1, 2, "nuevo.py", b"print('nuevo')\n", "motivo", actor(), ContextoAuditoria())
    assert destino.read_bytes() == b"print('viejo')\n" and env.read_bytes() == b"CLAVE=valor\n"
    assert not (destino.parent / "nuevo.py").exists()


def test_reemplazo_exitoso_retira_archivos_y_audita_hashes(tmp_path):
    estado = Estado(); servicio = servicio_scripts(estado, tmp_path)
    viejo = servicio.almacen.ruta_script(("Categoria", "Tipo", "Cliente", "Proceso diario"), 2, "viejo.py")
    viejo.parent.mkdir(parents=True); viejo.write_bytes(b"print('viejo')\n")
    env = servicio.almacen.ruta_env(("Categoria", "Tipo", "Cliente", "Proceso diario"), 2)
    env.parent.mkdir(parents=True, exist_ok=True); env.write_bytes(b"CLAVE=valor\n")
    estado.script = Script(8, 1, "Script", None, 1, FECHA, None, True)
    v = version(2, ruta=str(viejo))
    estado.versiones = [VersionScript(v.id_version, v.id_script, v.numero_version,
        v.nombre_archivo, v.ruta_fisica, v.ruta_relativa, v.hash_archivo,
        v.estado_version, v.es_activa, True, str(env), "env", v.usuario_carga,
        v.fecha_carga, v.observacion, v.fecha_creacion, v.fecha_actualizacion)]
    servicio.reemplazar(1, 2, "nuevo.py", b"print('nuevo')\n", "motivo", actor(), ContextoAuditoria())
    assert not viejo.exists() and not env.exists()
    assert (viejo.parent / "nuevo.py").read_bytes() == b"print('nuevo')\n"
    auditoria = estado.eventos[0].valores_despues or ""
    assert "sha256_anterior" in auditoria and "sha256_nuevo" in auditoria
    assert "PROTEGIDO" not in auditoria


@pytest.mark.parametrize("contenido", (b"SIN_IGUAL", b"1MALA=valor", b"\xff"))
def test_env_rechaza_formato_inseguro(contenido):
    with pytest.raises(ErrorValidacion): validar_env(contenido, 100)


def test_env_no_expone_secretos_en_auditoria(tmp_path):
    estado = Estado(); servicio = servicio_scripts(estado, tmp_path)
    estado.script = Script(8, 1, "Script", None, 2, FECHA, None, True)
    estado.versiones = [version(2)]
    servicio.guardar_env(1, 2, b"TOKEN=ultrasecreto\n", actor(), ContextoAuditoria())
    evento = estado.eventos[0]
    assert "ultrasecreto" not in (evento.valores_despues or "")
    assert "PROTEGIDO" in (evento.valores_despues or "")


def test_descarga_rechaza_env_y_ruta_externa(tmp_path):
    estado = Estado(); servicio = servicio_scripts(estado, tmp_path)
    estado.script = Script(8, 1, "Script", None, 2, FECHA, None, True)
    env_externo = tmp_path / "externo.env"; env_externo.write_text("CLAVE=valor", encoding="utf-8")
    estado.versiones = [version(2, ruta=str(env_externo))]
    with pytest.raises(ErrorValidacion, match="fuera"):
        servicio.obtener_descarga(1, 2)

    env_interno = servicio.almacen.ruta_env(("Categoria", "Tipo", "Cliente", "Proceso diario"), 2)
    env_interno.parent.mkdir(parents=True); env_interno.write_text("CLAVE=valor", encoding="utf-8")
    estado.versiones = [version(2, ruta=str(env_interno))]
    with pytest.raises(ErrorValidacion, match="no esta disponible"):
        servicio.obtener_descarga(1, 2)


def test_almacen_confina_destinos(tmp_path):
    almacen = AlmacenArchivosProcesos(tmp_path / "scripts", tmp_path / "env")
    with pytest.raises(ErrorValidacion, match="fuera"):
        almacen.preparar(tmp_path / "afuera.py", b"x")


def test_almacen_rechaza_symlink_que_escapa(tmp_path):
    almacen = AlmacenArchivosProcesos(tmp_path / "scripts", tmp_path / "env")
    almacen.raiz_scripts.mkdir(); afuera = tmp_path / "afuera"; afuera.mkdir()
    enlace = almacen.raiz_scripts / "enlace"
    try: enlace.symlink_to(afuera, target_is_directory=True)
    except OSError: pytest.skip("El host no permite crear symlinks de prueba.")
    with pytest.raises(ErrorValidacion, match="fuera"):
        almacen.validar_ruta_persistida(enlace / "x.py")


def test_nueva_version_no_sobrescribe_colision_fisica(tmp_path):
    estado = Estado(); servicio = servicio_scripts(estado, tmp_path)
    destino = servicio.almacen.ruta_script(
        ("Categoria", "Tipo", "Cliente", "Proceso diario"), 1, "proceso.py"
    )
    destino.parent.mkdir(parents=True); destino.write_bytes(b"archivo-ajeno")
    with pytest.raises(ErrorValidacion, match="destino"):
        servicio.subir_version(1, "proceso.py", b"print(1)\n", None, actor(), ContextoAuditoria())
    assert destino.read_bytes() == b"archivo-ajeno"


def test_retiro_env_fallido_restaura_archivo(tmp_path):
    estado = Estado(); servicio = servicio_scripts(estado, tmp_path)
    env = servicio.almacen.ruta_env(("Categoria", "Tipo", "Cliente", "Proceso diario"), 2)
    env.parent.mkdir(parents=True); env.write_bytes(b"SECRETO=valor\n")
    estado.script = Script(8, 1, "Script", None, 2, FECHA, None, True)
    v = version(2)
    estado.versiones = [VersionScript(v.id_version, v.id_script, v.numero_version,
        v.nombre_archivo, v.ruta_fisica, v.ruta_relativa, v.hash_archivo,
        v.estado_version, v.es_activa, True, str(env), "env", v.usuario_carga,
        v.fecha_carga, v.observacion, v.fecha_creacion, v.fecha_actualizacion)]
    estado.fallar_commit = True
    with pytest.raises(RuntimeError):
        servicio.quitar_env(1, 2, actor(), ContextoAuditoria())
    assert env.read_bytes() == b"SECRETO=valor\n"


class AuthWeb:
    def __init__(self, identidad): self.identidad = identidad
    def cargar_identidad(self, _): return self.identidad


class TareasWeb:
    def __init__(self): self.creaciones = []
    def listar(self, **_): return Pagina((tarea(),), 1, 1, 25)
    def catalogos(self): return {"clientes": ((2, "Cliente"),), "categorias": ((3, "Categoria"),), "tipos": ((4, "Tipo"),)}
    def obtener(self, identificador): return tarea() if identificador == 1 else None
    def crear(self, datos, actor_actual, _contexto): self.creaciones.append((datos, actor_actual.usuario)); return 1


class ScriptsWeb:
    def __init__(self): self.cargas = []
    def detalle(self, _):
        versiones = (version(1, activa=True), version(2), version(3))
        return {"tarea": tarea(), "script": Script(8, 1, "Script", None, 1, FECHA, None, True),
                "versiones": versiones, "referencias": {1: 0, 2: 1, 3: 0}, "slots_libres": ()}
    def subir_version(self, id_tarea, nombre, contenido, observacion, actor_actual, _contexto):
        self.cargas.append((id_tarea, nombre, contenido, observacion, actor_actual.usuario)); return 1


def app_web(configuracion, identidad):
    app = crear_aplicacion(configuracion, ajustes={"TESTING": True, "PROPAGATE_EXCEPTIONS": False})
    auth = AuthWeb(identidad); app.extensions["cargador_identidad"] = auth.cargar_identidad
    tareas = TareasWeb(); scripts = ScriptsWeb()
    app.extensions["servicio_tareas"] = tareas; app.extensions["servicio_scripts"] = scripts
    return app, tareas, scripts


def iniciar_sesion(cliente, identidad):
    with cliente.session_transaction() as sesion:
        sesion[CLAVE_IDENTIDAD] = {"tipo": identidad.tipo_identidad,
            "id_usuario": identidad.id_usuario, "usuario": identidad.usuario}


def token_csrf(cliente):
    cliente.get("/")
    with cliente.session_transaction() as sesion: return sesion["_csrf"]["token"]


def test_rutas_tareas_exigen_permiso_y_csrf(configuracion):
    sin_permiso = actor(frozenset({"PANEL_VER"})); app, _, _ = app_web(configuracion, sin_permiso)
    cliente = app.test_client()
    assert cliente.get("/tareas/").status_code == 302
    iniciar_sesion(cliente, sin_permiso)
    assert cliente.get("/tareas/").status_code == 403
    assert cliente.post("/tareas/1/estado").status_code == 403


def test_formulario_tarea_solo_mapea_allowlist(configuracion):
    identidad = actor(frozenset({"PANEL_VER", "TAREAS_VER", "TAREAS_CREAR"}))
    app, tareas, _ = app_web(configuracion, identidad); cliente = app.test_client(); iniciar_sesion(cliente, identidad)
    token = token_csrf(cliente)
    respuesta = cliente.post("/tareas/nueva", data={"csrf_token": token,
        "nombre_tarea": "Proceso", "descripcion": "Base", "observacion_tecnica": "TI",
        "id_cliente": "2", "id_categoria": "3", "id_tipo": "4", "estado_tarea": "ACTIVA",
        "usuario_ejecutor": "inyeccion", "eliminado_operativo": "1"})
    assert respuesta.status_code == 302
    assert set(tareas.creaciones[0][0]) == {"nombre_tarea", "descripcion", "observacion_tecnica",
        "id_cliente", "id_categoria", "id_tipo", "estado_tarea"}


def test_panel_versiones_explica_maximo_y_bloqueo(configuracion):
    identidad = actor(frozenset({"PANEL_VER", "TAREAS_VER", "SCRIPTS_VER", "SCRIPTS_REEMPLAZAR"}))
    app, _, _ = app_web(configuracion, identidad); cliente = app.test_client(); iniciar_sesion(cliente, identidad)
    respuesta = cliente.get("/tareas/1/scripts")
    assert respuesta.status_code == 200
    assert b"Maximo de tres slots alcanzado" in respuesta.data
    assert b"Bloqueado: la version tiene historia" in respuesta.data
    assert b"v4" in respuesta.data  # Solo aparece en la explicacion de que nunca se crea.


def test_upload_script_exige_csrf_y_transfiere_bytes(configuracion):
    identidad = actor(frozenset({"PANEL_VER", "TAREAS_VER", "SCRIPTS_VER", "SCRIPTS_VERSIONAR"}))
    app, _, scripts = app_web(configuracion, identidad); cliente = app.test_client(); iniciar_sesion(cliente, identidad)
    assert cliente.post("/tareas/1/scripts/versiones", data={}).status_code == 403
    token = token_csrf(cliente)
    respuesta = cliente.post("/tareas/1/scripts/versiones", data={"csrf_token": token,
        "observacion": "Inicial", "archivo_script": (BytesIO(b"print('ok')\n"), "proceso.py")},
        content_type="multipart/form-data")
    assert respuesta.status_code == 302
    assert scripts.cargas == [(1, "proceso.py", b"print('ok')\n", "Inicial", "actor")]


def test_repositorio_tareas_pagina_parametrizada_sin_commit():
    fila = (1, "Proceso", None, None, 2, "Cliente", 3, "Categoria", 4, "Tipo",
            "MANUAL", "ACTIVA", 1, FECHA, None, 1)
    conexion = ConexionProgramada(ResultadoSQL(fila=(1,)), ResultadoSQL(filas=[fila]))
    pagina = RepositorioTareas(conexion).listar_paginado(Paginacion(1, 25), busqueda="100%")
    assert pagina.elementos[0].nombre_tarea == "Proceso"
    assert conexion.commits == 0
    assert "LIKE ? ESCAPE '~'" in conexion.ejecuciones[0][0]
    assert conexion.ejecuciones[0][1] == ("%100~%%", "%100~%%")


def test_repositorio_version_protege_referencias_reales():
    conexion = ConexionProgramada(ResultadoSQL(fila=(3,)))
    assert RepositorioScripts(conexion).contar_referencias_version_para_reemplazo(9) == 3
    sql, parametros = conexion.ejecuciones[0]
    assert "dbo.ejecuciones" in sql and "id_version = ?" in sql
    assert "UPDLOCK, HOLDLOCK" in sql
    assert parametros == (9,) and conexion.commits == 0


def test_schema_no_contiene_usuario_ejecutor_y_conserva_tres_slots():
    esquema = Path("database/release/002_schema_final.sql").read_text(encoding="utf-8")
    bloque_tareas = esquema.split("CREATE TABLE dbo.tareas", 1)[1].split("END;", 1)[0]
    assert "id_usuario_ejecutor" not in bloque_tareas
    assert "numero_version BETWEEN 1 AND 3" in esquema
    assert "UNIQUE (id_script, numero_version)" in esquema
