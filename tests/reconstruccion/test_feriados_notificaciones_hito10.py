from __future__ import annotations

import json
from contextlib import contextmanager
from dataclasses import replace
from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
import requests

from app_scheduler import crear_aplicacion
from app_scheduler.compartido.auditoria import ContextoAuditoria
from app_scheduler.compartido.autorizacion import CLAVE_IDENTIDAD, IdentidadSesion, TIPO_BASE_DATOS
from app_scheduler.compartido.errores import ErrorPersistencia, ErrorValidacion
from app_scheduler.compartido.unidad_trabajo import UnidadTrabajoSQL
from app_scheduler.modulos.feriados.casos_uso import ServicioFeriados
from app_scheduler.modulos.feriados.cliente_nager import ClienteNagerDate, ErrorNagerDate
from app_scheduler.modulos.notificaciones.casos_uso import ServicioConfiguracionGraph, ServicioNotificacionesTarea
from app_scheduler.modulos.notificaciones.cliente_graph import ClienteMicrosoftGraph, ErrorGraph
from app_scheduler.modulos.notificaciones.despacho import (
    ErrorAdjunto,
    ServicioDespachoNotificaciones,
    construir_mensaje_graph,
    preparar_adjuntos,
)
from app_scheduler.modulos.notificaciones.seguridad import normalizar_email, sanitizar_texto_externo
from app_scheduler.persistencia.modelos import (
    ConfiguracionMailGraph,
    ConfiguracionNotificacionTarea,
    DestinatarioNotificacion,
    Feriado,
    Pagina,
)
from app_scheduler.persistencia.repositorio_notificaciones import RepositorioNotificaciones
from tests.reconstruccion.fakes_sql import (
    ConexionProgramada,
    ProveedorProgramado,
    ResultadoSQL,
)


AHORA = datetime(2026, 8, 25, 10, 0)


class RespuestaHTTP:
    def __init__(self, estado=200, datos=None, texto="", headers=None, json_error=False):
        self.status_code = estado
        self._datos = datos
        self.text = texto
        self.headers = headers or {}
        self.json_error = json_error
    def json(self):
        if self.json_error: raise ValueError("json")
        return self._datos


class SesionHTTP:
    def __init__(self, *respuestas): self.respuestas = list(respuestas); self.llamadas = []
    def get(self, url, **kwargs):
        self.llamadas.append(("GET", url, kwargs)); return self._siguiente()
    def post(self, url, **kwargs):
        self.llamadas.append(("POST", url, kwargs)); return self._siguiente()
    def _siguiente(self):
        valor = self.respuestas.pop(0)
        if isinstance(valor, Exception): raise valor
        return valor


def test_nager_usa_endpoint_fijo_timeout_y_tls_por_defecto():
    sesion = SesionHTTP(RespuestaHTTP(datos=[{"date": "2026-01-01"}]))
    assert ClienteNagerDate(sesion=sesion, timeout_segundos=7).consultar(2026, "CL")
    _, url, opciones = sesion.llamadas[0]
    assert url == "https://date.nager.at/api/v3/PublicHolidays/2026/CL"
    assert opciones["timeout"] == 7 and "verify" not in opciones


@pytest.mark.parametrize("respuesta,mensaje", [
    (requests.Timeout(), "tiempo"),
    (requests.ConnectionError(), "conectar"),
    (RespuestaHTTP(503), "HTTP 503"),
    (RespuestaHTTP(datos={}, estado=200), "estructura"),
    (RespuestaHTTP(datos=[], json_error=True), "JSON"),
])
def test_nager_traduce_fallos_sin_borrar_calendario(respuesta, mensaje):
    with pytest.raises(ErrorNagerDate, match=mensaje):
        ClienteNagerDate(sesion=SesionHTTP(respuesta)).consultar(2026, "CL")


def item_nager(fecha="2026-01-01", nombre="Ano Nuevo"):
    return {"date": fecha, "localName": nombre, "name": "New Year's Day",
            "countryCode": "CL", "types": ["Public"], "global": True, "fixed": True}


def test_normalizacion_nager_rechaza_duplicados_y_payload_invalido():
    with pytest.raises(ErrorValidacion, match="duplicadas"):
        ServicioFeriados._normalizar_respuesta([item_nager(), item_nager()], "CL")
    with pytest.raises(ErrorValidacion, match="fecha"):
        ServicioFeriados._normalizar_respuesta([item_nager("no-fecha")], "CL")
    with pytest.raises(ErrorValidacion, match="incompatibles"):
        ServicioFeriados._normalizar_respuesta([item_nager() | {"countryCode": "AR"}], "CL")


def feriado(origen="MANUAL", activo=True, nombre="Local"):
    return Feriado(1, date(2026, 1, 1), nombre, "Public", "CL", False, activo,
                   origen, "obs", AHORA, None, "actor", None)


def test_clasificacion_nager_preserva_manual_e_inactivo_y_es_idempotente():
    item = {"fecha": date(2026, 1, 1), "nombre": "API", "tipo": "Public",
            "pais": "CL", "irrenunciable": False, "observacion": "api"}
    assert ServicioFeriados._accion(item, None) == "INSERTAR"
    assert ServicioFeriados._accion(item, feriado("MANUAL")) == "MANUAL"
    assert ServicioFeriados._accion(item, feriado("API_NAGER", False)) == "INACTIVO"
    igual = feriado("API_NAGER", True, "API")
    igual = replace(igual, observacion="api")
    assert ServicioFeriados._accion(item, igual) == "SIN_CAMBIOS"


def test_datos_feriado_validan_fecha_pais_y_limites():
    datos = ServicioFeriados._validar({"fecha": "2026-09-18", "nombre": "Fiestas Patrias",
                                      "pais": "cl", "irrenunciable": "1"})
    assert datos["pais"] == "CL" and datos["irrenunciable"] is True
    with pytest.raises(ErrorValidacion, match="fecha"):
        ServicioFeriados._validar({"fecha": "x", "nombre": "F", "pais": "CL"})
    with pytest.raises(ErrorValidacion, match="ISO"):
        ServicioFeriados._validar({"fecha": "2026-01-01", "nombre": "F", "pais": "CHL"})


class EstadoFeriados:
    def __init__(self):
        self.items = {}; self.siguiente = 1; self.logs = []; self.auditorias = []; self.commits = 0


class ProveedorEstado:
    def __init__(self, estado): self.estado = estado
    @contextmanager
    def conexion_lectura(self): yield self.estado


class UowEstado:
    def __init__(self, proveedor): self.estado = proveedor.estado
    def __enter__(self): return self
    def __exit__(self, *_): return False
    def obtener_conexion(self): return self.estado
    def confirmar(self): self.estado.commits += 1


class RepoFeriadosEstado:
    def __init__(self, estado): self.estado = estado
    def obtener(self, identificador): return self.estado.items.get(identificador)
    def obtener_por_fecha_pais(self, fecha, pais):
        candidatos = [i for i in self.estado.items.values() if i.fecha == fecha and i.pais == pais]
        return sorted(candidatos, key=lambda i: (i.activo, i.id_feriado), reverse=True)[0] if candidatos else None
    def obtener_regla_irrenunciable(self, pais, mes, dia): return pais == "CL" and (mes, dia) == (9, 18)
    def crear_manual(self, datos, actor): return self._crear(datos, actor, "MANUAL")
    def crear_api_nager(self, datos, actor): return self._crear(datos, actor, "API_NAGER")
    def _crear(self, datos, actor, origen):
        identificador = self.estado.siguiente; self.estado.siguiente += 1
        self.estado.items[identificador] = Feriado(
            identificador, datos["fecha"], datos["nombre"], datos.get("tipo"), datos["pais"],
            bool(datos["irrenunciable"]), True, origen, datos.get("observacion"), AHORA, None,
            actor, actor,
        )
        return identificador
    def actualizar_manual(self, identificador, datos, actor):
        actual = self.estado.items[identificador]
        self.estado.items[identificador] = replace(actual, **datos, usuario_actualizacion=actor)
        return True
    def actualizar_api_nager(self, identificador, datos, actor):
        actual = self.estado.items[identificador]
        self.estado.items[identificador] = replace(
            actual, nombre=datos["nombre"], tipo=datos["tipo"],
            irrenunciable=datos["irrenunciable"], observacion=datos["observacion"],
            usuario_actualizacion=actor,
        )
        return True
    def cambiar_estado(self, identificador, activo, actor):
        self.estado.items[identificador] = replace(self.estado.items[identificador], activo=activo,
                                                   usuario_actualizacion=actor)
        return True
    def eliminar_manual(self, identificador):
        if self.estado.items[identificador].origen != "MANUAL": return False
        del self.estado.items[identificador]; return True


class RepoAuditoriaEstado:
    def __init__(self, estado): self.estado = estado
    def registrar(self, evento): self.estado.auditorias.append(evento); return len(self.estado.auditorias)


class RepoLogsEstado:
    def __init__(self, estado): self.estado = estado
    def registrar(self, **datos): self.estado.logs.append(datos); return len(self.estado.logs)


class NagerFake:
    def __init__(self, datos): self.datos = datos; self.llamadas = 0
    def consultar(self, *_): self.llamadas += 1; return self.datos


def servicio_feriados_estado(estado, datos):
    return ServicioFeriados(
        ProveedorEstado(estado), fabrica_uow=UowEstado, repositorio=RepoFeriadosEstado,
        repositorio_auditoria=RepoAuditoriaEstado, repositorio_logs=RepoLogsEstado,
        cliente_nager=NagerFake(datos),
    )


def test_crud_feriado_manual_audita_y_eliminacion_no_aplica_a_api():
    estado = EstadoFeriados(); servicio = servicio_feriados_estado(estado, [])
    actor = identidad({"FERIADOS_CREAR"})
    identificador = servicio.crear({"fecha": "2026-09-18", "nombre": "Fiestas Patrias",
                                    "pais": "CL", "irrenunciable": "1"}, actor,
                                   ContextoAuditoria(ruta="/feriados/nuevo"))
    assert estado.items[identificador].origen == "MANUAL"
    assert estado.auditorias[-1].accion == "FERIADO_CREADO" and estado.commits == 1
    servicio.cambiar_estado(identificador, False, actor, ContextoAuditoria())
    assert not estado.items[identificador].activo
    servicio.eliminar(identificador, actor, ContextoAuditoria())
    assert identificador not in estado.items and estado.auditorias[-1].accion == "FERIADO_ELIMINADO"
    api_id = RepoFeriadosEstado(estado)._crear({"fecha": date(2026, 1, 1), "nombre": "API",
        "tipo": None, "pais": "CL", "irrenunciable": False, "observacion": None}, "sistema", "API_NAGER")
    with pytest.raises(ErrorValidacion, match="Solo los feriados manuales"):
        servicio.eliminar(api_id, actor, ContextoAuditoria())


def test_sincronizacion_nager_es_idempotente_preserva_manual_y_audita():
    estado = EstadoFeriados()
    repo = RepoFeriadosEstado(estado)
    repo._crear({"fecha": date(2026, 1, 1), "nombre": "Manual prioritario", "tipo": None,
                 "pais": "CL", "irrenunciable": False, "observacion": None}, "ti", "MANUAL")
    servicio = servicio_feriados_estado(estado, [item_nager(), item_nager("2026-09-18", "Fiestas Patrias")])
    actor = identidad({"FERIADOS_SINCRONIZAR"})
    primero = servicio.sincronizar(2026, "CL", actor, ContextoAuditoria())
    segundo = servicio.sincronizar(2026, "CL", actor, ContextoAuditoria())
    assert primero["insertados"] == 1 and primero["manuales_preservados"] == 1
    assert segundo["insertados"] == 0 and segundo["sin_cambios"] == 1
    assert len(estado.items) == 2 and estado.items[1].nombre == "Manual prioritario"
    assert estado.items[2].irrenunciable is True
    assert [e.accion for e in estado.auditorias] == ["FERIADOS_SINCRONIZADOS"] * 2
    assert any(log["accion"] == "NAGER_SYNC_OK" for log in estado.logs)


def test_email_normaliza_rechaza_inyeccion_y_sanitiza_secretos():
    assert normalizar_email(" Usuario@Ejemplo.CL ") == "usuario@ejemplo.cl"
    for valor in ("sin-arroba", "a@b.cl\r\nBcc:x@y.cl", "a b@c.cl"):
        with pytest.raises(ValueError): normalizar_email(valor)
    texto = sanitizar_texto_externo("password=secreto token:abc Authorization: Bearer xyz")
    assert "secreto" not in texto and "abc" not in texto and "xyz" not in texto
    assert "[PROTEGIDO]" in texto


def test_destinatarios_to_cc_bcc_normalizan_y_rechazan_duplicados():
    formulario = {"evidencia_to": "A@EXAMPLE.CL\nb@example.cl", "evidencia_cc": "c@example.cl"}
    items = ServicioNotificacionesTarea._destinatarios(formulario)
    assert [(i.canal, i.email) for i in items] == [
        ("TO", "a@example.cl"), ("TO", "b@example.cl"), ("CC", "c@example.cl")]
    with pytest.raises(ErrorValidacion, match="repetido"):
        ServicioNotificacionesTarea._destinatarios(
            {"evidencia_to": "a@example.cl", "evidencia_cc": "A@example.cl"}
        )


def test_adjuntos_solo_dentro_de_version_y_bloquea_env_script_y_tamano(tmp_path):
    raiz = tmp_path / "v1"; raiz.mkdir()
    reporte = raiz / "salida.csv"; reporte.write_text("a,b\n1,2", encoding="utf-8")
    adjuntos = preparar_adjuntos({"adjuntos": [{"ruta": "salida.csv", "obligatorio": True}]}, raiz)
    assert adjuntos[0]["name"] == "salida.csv" and "contentBytes" in adjuntos[0]
    secreto = raiz / ".env"; secreto.write_text("TOKEN=x", encoding="utf-8")
    with pytest.raises(ErrorAdjunto, match="tipo"):
        preparar_adjuntos({"adjuntos": [{"ruta": ".env"}]}, raiz)
    fuera = tmp_path / "fuera.txt"; fuera.write_text("x", encoding="utf-8")
    with pytest.raises(ErrorAdjunto, match="fuera"):
        preparar_adjuntos({"adjuntos": [{"ruta": "../fuera.txt"}]}, raiz)
    grande = raiz / "grande.bin"; grande.write_bytes(b"x" * (2 * 1024 * 1024 + 1))
    with pytest.raises(ErrorAdjunto, match="limite"):
        preparar_adjuntos({"adjuntos": [{"ruta": "grande.bin"}]}, raiz)


def test_adjunto_opcional_ausente_se_omite_y_obligatorio_falla(tmp_path):
    assert preparar_adjuntos({"adjuntos": [{"ruta": "no.csv", "obligatorio": False}]}, tmp_path) == []
    with pytest.raises(ErrorAdjunto, match="obligatorio"):
        preparar_adjuntos({"adjuntos": [{"ruta": "no.csv", "obligatorio": True}]}, tmp_path)


def test_payload_graph_backend_construye_canales_sin_headers_arbitrarios():
    mensaje = construir_mensaje_graph("Asunto", "<p>Seguro</p>",
        {"TO": ["a@example.cl"], "CC": ["b@example.cl"], "BCC": []}, [])
    assert mensaje["toRecipients"][0]["emailAddress"]["address"] == "a@example.cl"
    assert mensaje["body"]["contentType"] == "HTML" and "headers" not in mensaje


def test_graph_token_y_sendmail_ok_sin_secret_en_url_o_json():
    sesion = SesionHTTP(
        RespuestaHTTP(200, {"access_token": "token-super-secreto"}),
        RespuestaHTTP(202, None, headers={"request-id": "req-1"}),
    )
    resultado = ClienteMicrosoftGraph(sesion=sesion).enviar(
        {"tenant_id": "tenant", "client_id": "client", "client_secret": "secret-real",
         "graph_scope": "https://graph.microsoft.com/.default",
         "send_mail_user": "bpm@example.cl", "save_to_sent_items": True},
        {"subject": "Prueba", "body": {"contentType": "HTML", "content": "ok"},
         "toRecipients": []},
    )
    assert resultado.status_code == 202 and resultado.request_id == "req-1"
    _, send_url, send_kwargs = sesion.llamadas[1]
    assert "secret-real" not in send_url and "secret-real" not in json.dumps(send_kwargs["json"])


@pytest.mark.parametrize("respuestas,mensaje", [
    ((RespuestaHTTP(401, {}),), "autenticacion"),
    ((requests.Timeout(),), "token"),
    ((RespuestaHTTP(200, {"access_token": "t"}), RespuestaHTTP(500, texto="password=valor")), "HTTP 500"),
    ((RespuestaHTTP(200, {}),), "token utilizable"),
])
def test_graph_traduce_token_timeout_y_http_sin_exponer_secreto(respuestas, mensaje):
    cliente = ClienteMicrosoftGraph(sesion=SesionHTTP(*respuestas))
    with pytest.raises(ErrorGraph, match=mensaje) as capturado:
        cliente.enviar({"tenant_id": "t", "client_id": "c", "client_secret": "NO_EXPOSICION",
                        "graph_scope": "https://graph.microsoft.com/.default",
                        "send_mail_user": "a@example.cl", "save_to_sent_items": True}, {})
    assert "NO_EXPOSICION" not in str(capturado.value)
    assert "valor" not in str(capturado.value)


def test_template_correo_escapa_html_y_sanitiza_stdout():
    servicio = ServicioDespachoNotificaciones(None, None)
    html = servicio._cuerpo("EVIDENCIA_CLIENTE", {"id_ejecucion": 1, "nombre_tarea": "<script>x</script>"},
                            {"titulo": "<img src=x onerror=1>", "resumen": ["password=secreto"]})
    assert "<script>" not in html and "<img src=x" not in html
    assert "&lt;script&gt;" in html and "secreto" not in html


def test_repositorio_reserva_idempotente_usa_applock_y_estado_pendiente():
    conexion = ConexionProgramada(ResultadoSQL(fila=(91,)))
    repo = RepositorioNotificaciones(conexion)
    assert repo.reservar_envio(7, 8, "EVIDENCIA_CLIENTE", "Asunto",
                               {"TO": "a@example.cl", "CC": None, "BCC": None}) == 91
    sql, parametros = conexion.ejecuciones[0]
    assert sql.lstrip().startswith("SET NOCOUNT ON;")
    assert "sp_getapplock" in sql and "NOT EXISTS" in sql
    assert "estado_envio IN" not in sql
    assert "APP_SCHEDULER_MAIL_7_EVIDENCIA_CLIENTE" in parametros


class CursorPyodbcNotificacionSimulado:
    """Simula los DONE/rowcount previos al SELECT final del batch."""

    def __init__(self, fila=(91,), *, resultado_final=True):
        self.fila = fila
        self.resultado_final = resultado_final
        self.description = None
        self.rowcount = -1
        self.cerrado = False

    def execute(self, sql, parametros=()):
        self.sql = sql
        self.parametros = tuple(parametros)
        if sql.lstrip().startswith("SET NOCOUNT ON;") and self.resultado_final:
            self.description = (("id_envio",),)
        else:
            self.description = None
            self.rowcount = 1
        return self

    def fetchone(self):
        if self.description is None:
            raise RuntimeError("No results. Previous SQL was not a query.")
        return self.fila

    def close(self):
        self.cerrado = True


class ConexionPyodbcNotificacionSimulada:
    def __init__(self, fila=(91,), *, resultado_final=True):
        self.cursor_notificacion = CursorPyodbcNotificacionSimulado(
            fila, resultado_final=resultado_final,
        )
        self.commits = 0
        self.rollbacks = 0
        self.cerrada = False

    def cursor(self):
        return self.cursor_notificacion

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.cerrada = True


def _reservar_notificacion(repo):
    return repo.reservar_envio(
        7, None, "NOTIFICACION_EXITOSA", "Ejecucion exitosa",
        {"TO": "cliente@example.cl", "CC": None, "BCC": None},
    )


def test_reserva_notificacion_nocount_evita_resultados_intermedios_pyodbc():
    conexion = ConexionPyodbcNotificacionSimulada((91,))

    assert _reservar_notificacion(RepositorioNotificaciones(conexion)) == 91
    cursor = conexion.cursor_notificacion
    assert cursor.description[0][0] == "id_envio" and cursor.cerrado

    sin_nocount = CursorPyodbcNotificacionSimulado((91,))
    sin_nocount.execute(cursor.sql.replace("SET NOCOUNT ON;", "", 1), cursor.parametros)
    with pytest.raises(RuntimeError, match="Previous SQL was not a query"):
        sin_nocount.fetchone()


def test_reserva_notificacion_duplicada_retorna_none_sin_error_driver():
    conexion = ConexionPyodbcNotificacionSimulada(None)

    assert _reservar_notificacion(RepositorioNotificaciones(conexion)) is None


def test_reserva_notificacion_sin_resultset_final_revierte_uow():
    conexion = ConexionPyodbcNotificacionSimulada(resultado_final=False)
    proveedor = ProveedorProgramado(conexion)

    with pytest.raises(ErrorPersistencia, match="reservar_envio_notificacion"):
        with UnidadTrabajoSQL(proveedor) as uow:
            _reservar_notificacion(
                RepositorioNotificaciones(uow.obtener_conexion())
            )
            uow.confirmar()

    assert conexion.commits == 0 and conexion.rollbacks == 1 and conexion.cerrada


def test_config_graph_falla_cerrado_y_secret_nunca_es_publico(configuracion):
    sql = ConfiguracionMailGraph(1, True, "tenant", "client",
        "https://graph.microsoft.com/.default", "bpm@example.cl", True,
        "alertas@example.cl", "ENV", None, None)
    class Repo:
        def __init__(self, _): pass
        def obtener_configuracion_graph(self): return sql
    class Proveedor:
        @contextmanager
        def conexion_lectura(self): yield object()
    servicio = ServicioConfiguracionGraph(Proveedor(), configuracion, repositorio=Repo)
    estado = servicio.obtener()
    assert estado["estado"] == "DESHABILITADO" and not estado["disponible_envio"]
    assert "client_secret" not in estado and "graph_client_secret" not in json.dumps(estado, default=str)


def test_config_graph_preserva_identificadores_ocultos_si_no_se_reemplazan(configuracion):
    actual = ConfiguracionMailGraph(1, False, "tenant-vigente", "client-vigente",
        "https://graph.microsoft.com/.default", "bpm@example.cl", True,
        "alertas@example.cl", "ENV", None, None)
    servicio = ServicioConfiguracionGraph(None, configuracion)
    datos = servicio._validar({"send_mail_user": "bpm@example.cl",
        "graph_scope": "https://graph.microsoft.com/.default"}, actual)
    assert datos["tenant_id"] == "tenant-vigente"
    assert datos["client_id"] == "client-vigente"


class EstadoNotificaciones:
    def __init__(self, config=None):
        self.config = config or ConfiguracionNotificacionTarea(
            None, 1, False, False, "STDOUT_V1", None, True, True, False, True, True, ()
        )
        self.auditorias = []; self.commits = 0; self.destinatarios = (); self.reservas = []
        self.finalizaciones = []; self.logs = []; self.envios = set()


class RepoNotificacionesEstado:
    def __init__(self, estado): self.estado = estado
    def obtener_configuracion_tarea(self, _):
        return replace(self.estado.config, destinatarios=self.estado.destinatarios)
    def guardar_configuracion_tarea(self, config):
        self.estado.config = replace(config, id_config_notificacion=3); return 3
    def reemplazar_destinatarios(self, _, destinatarios): self.estado.destinatarios = destinatarios
    def obtener_contexto_envio(self, _): return self.estado.contexto
    def reservar_envio(self, id_ejecucion, _id_evidencia, tipo, asunto, destinatarios):
        clave = (id_ejecucion, tipo)
        if clave in self.estado.envios: return None
        self.estado.envios.add(clave); self.estado.reservas.append((tipo, asunto, destinatarios)); return 55
    def finalizar_envio(self, identificador, estado, **datos):
        self.estado.finalizaciones.append((identificador, estado, datos)); return True


class RepoTareaEstado:
    def __init__(self, _): pass
    def obtener_por_id(self, identificador):
        return SimpleNamespace(id_tarea=identificador, nombre_tarea="Proceso")


class EvidenciasCompatibles:
    def obtener_para_tarea(self, _): return {"soporte": {"compatible": True, "errores": []}}


class EvidenciasNoImplementadas:
    def obtener_para_tarea(self, _):
        return {"soporte": {"compatible": False, "errores": ["No implementada."]}}


def test_configuracion_notificaciones_guarda_destinatarios_y_audita_atomico():
    estado = EstadoNotificaciones(); actor = identidad({"TAREAS_EDITAR"})
    servicio = ServicioNotificacionesTarea(
        ProveedorEstado(estado), EvidenciasCompatibles(), fabrica_uow=UowEstado,
        repositorio=RepoNotificacionesEstado, repositorio_tareas=RepoTareaEstado,
        repositorio_auditoria=RepoAuditoriaEstado,
    )
    servicio.guardar(1, {"notificar_exito_activa": "1", "enviar_evidencia": "1", "alerta_error_activa": "1",
        "usar_alerta_global": "1", "usar_asunto_sugerido_script": "1",
        "adjuntar_archivos_declarados": "1", "evidencia_to": "cliente@example.cl",
        "alerta_cc": "ti@example.cl"}, actor, ContextoAuditoria())
    assert estado.config.enviar_evidencia and estado.destinatarios[0].email == "cliente@example.cl"
    assert estado.auditorias[0].accion == "NOTIFICACIONES_TAREA_EDITADAS"
    assert estado.commits == 1


def test_configuracion_notificaciones_exige_to_y_script_compatible():
    estado = EstadoNotificaciones(); actor = identidad({"TAREAS_EDITAR"})
    servicio = ServicioNotificacionesTarea(
        ProveedorEstado(estado), EvidenciasCompatibles(), fabrica_uow=UowEstado,
        repositorio=RepoNotificacionesEstado, repositorio_tareas=RepoTareaEstado,
        repositorio_auditoria=RepoAuditoriaEstado,
    )
    with pytest.raises(ErrorValidacion, match="destinatario TO"):
        servicio.guardar(1, {"notificar_exito_activa": "1", "enviar_evidencia": "1"}, actor, ContextoAuditoria())


def test_configuracion_exito_sin_evidencia_no_exige_script_compatible():
    estado = EstadoNotificaciones(); actor = identidad({"TAREAS_EDITAR"})
    servicio = ServicioNotificacionesTarea(
        ProveedorEstado(estado), EvidenciasNoImplementadas(), fabrica_uow=UowEstado,
        repositorio=RepoNotificacionesEstado, repositorio_tareas=RepoTareaEstado,
        repositorio_auditoria=RepoAuditoriaEstado,
    )
    servicio.guardar(1, {"notificar_exito_activa": "1",
        "evidencia_to": "cliente@example.cl"}, actor, ContextoAuditoria())
    assert estado.config.notificar_exito_activa
    assert not estado.config.enviar_evidencia


class GraphConfigFake:
    def __init__(self, disponible=True): self.disponible = disponible
    def efectiva(self):
        return ({"tenant_id": "t", "client_id": "c", "client_secret": "s",
                 "graph_scope": "https://graph.microsoft.com/.default",
                 "send_mail_user": "bpm@example.cl", "save_to_sent_items": True}
                if self.disponible else None)
    def obtener(self):
        return {"efectiva": {"alertas_destinatarios_default": "alertas@example.cl"}}


class GraphEnvioFake:
    def __init__(self, error=None): self.error = error; self.mensajes = []
    def enviar(self, _config, mensaje):
        self.mensajes.append(mensaje)
        if self.error: raise self.error
        return SimpleNamespace(status_code=202, request_id="req")


class LogsNotificacionesEstado:
    def __init__(self, estado): self.estado = estado
    def registrar(self, **datos): self.estado.logs.append(datos); return len(self.estado.logs)


def estado_despacho(estado_ejecucion="EXITOSA", estado_evidencia="VALIDADA"):
    destinatario = DestinatarioNotificacion(1, "EVIDENCIA", "TO", "cliente@example.cl", None)
    alerta = DestinatarioNotificacion(2, "ALERTA", "TO", "ti@example.cl", None)
    estado = EstadoNotificaciones(ConfiguracionNotificacionTarea(
        3, 1, True, True, "STDOUT_V1", None, True, True, False, True, True,
        (destinatario, alerta),
    ))
    estado.destinatarios = (destinatario, alerta)
    estado.contexto = {"id_ejecucion": 9, "id_tarea": 1,
        "estado_ejecucion": estado_ejecucion, "codigo_salida": 0,
        "fecha_inicio": AHORA, "fecha_termino": AHORA, "duracion_segundos": 1,
        "nombre_tarea": "Proceso", "mensaje_error": "password=interno" if estado_ejecucion == "ERROR" else None,
        "ruta_script_fisica": str(Path.cwd() / "script.py"), "id_evidencia": 4,
        "estado_evidencia": estado_evidencia, "titulo_evidencia": "OK",
        "asunto_sugerido": "Resultado", "tipo_evidencia": "QA", "error_evidencia": None}
    return estado


def servicio_despacho_estado(estado, graph):
    return ServicioDespachoNotificaciones(
        ProveedorEstado(estado), GraphConfigFake(), cliente_graph=graph,
        fabrica_uow=UowEstado, repositorio=RepoNotificacionesEstado,
        repositorio_logs=LogsNotificacionesEstado,
    )


def test_despacho_evidencia_exitoso_es_idempotente_y_trazable():
    estado = estado_despacho(); graph = GraphEnvioFake()
    servicio = servicio_despacho_estado(estado, graph)
    evidencia = {"titulo": "Resultado", "resumen": [{"nombre": "Filas", "valor": 10}],
                 "adjuntos": []}
    assert servicio.procesar(9, evidencia) == "ENVIADO"
    assert servicio.procesar(9, evidencia) == "OMITIDO"
    assert len(graph.mensajes) == 1 and estado.finalizaciones[0][1] == "ENVIADO"
    assert estado.reservas[0][0] == "NOTIFICACION_EXITOSA"
    assert any(log["accion"] == "GRAPH_ENVIO_OK" for log in estado.logs)


def test_despacho_exito_sin_evidencia_envia_notificacion_estandar():
    estado = estado_despacho(estado_evidencia=None)
    estado.config = replace(estado.config, enviar_evidencia=False)
    graph = GraphEnvioFake()
    assert servicio_despacho_estado(estado, graph).procesar(9, None) == "ENVIADO"
    assert estado.reservas[0][0] == "NOTIFICACION_EXITOSA"
    assert estado.reservas[0][1] == "Ejecucion exitosa | Proceso"
    assert "Evidencia del proceso" not in graph.mensajes[0]["body"]["content"]


def test_despacho_exito_graph_off_reserva_una_vez_y_finaliza_omitido():
    estado = estado_despacho(estado_evidencia=None)
    estado.config = replace(estado.config, enviar_evidencia=False)
    graph = GraphEnvioFake()
    servicio = ServicioDespachoNotificaciones(
        ProveedorEstado(estado), GraphConfigFake(disponible=False),
        cliente_graph=graph, fabrica_uow=UowEstado,
        repositorio=RepoNotificacionesEstado,
        repositorio_logs=LogsNotificacionesEstado,
    )

    assert servicio.procesar(9, None) == "OMITIDO"
    assert servicio.procesar(9, None) == "OMITIDO"
    assert estado.reservas[0][0] == "NOTIFICACION_EXITOSA"
    assert len(estado.reservas) == 1
    assert estado.finalizaciones[0][1] == "OMITIDO"
    assert len(estado.finalizaciones) == 1 and graph.mensajes == []
    assert estado.contexto["estado_ejecucion"] == "EXITOSA"


def test_despacho_evidencia_solicitada_no_emitida_no_bloquea_exito():
    estado = estado_despacho(estado_evidencia="NO_EMITIDA")
    graph = GraphEnvioFake()
    assert servicio_despacho_estado(estado, graph).procesar(9, None) == "ENVIADO"
    assert estado.reservas[0][0] == "NOTIFICACION_EXITOSA"
    assert any(log["accion"] == "EVIDENCIA_OMITIDA" for log in estado.logs)
    assert estado.finalizaciones[0][1] == "ENVIADO"


def test_despacho_graph_fallido_no_cambia_estado_ejecucion_y_no_reintenta():
    estado = estado_despacho(); graph = GraphEnvioFake(ErrorGraph("HTTP 503", status_code=503))
    servicio = servicio_despacho_estado(estado, graph)
    assert servicio.procesar(9, {"titulo": "OK", "resumen": [], "adjuntos": []}) == "FALLIDO"
    assert servicio.procesar(9, {"titulo": "OK", "resumen": [], "adjuntos": []}) == "OMITIDO"
    assert estado.contexto["estado_ejecucion"] == "EXITOSA"
    assert estado.finalizaciones[0][1] == "FALLIDO" and len(graph.mensajes) == 1


def test_error_ejecucion_dispara_alerta_interna_no_evidencia_cliente():
    estado = estado_despacho("ERROR", None); graph = GraphEnvioFake()
    assert servicio_despacho_estado(estado, graph).procesar(9, None) == "ENVIADO"
    assert estado.reservas[0][0] == "ALERTA_INTERNA"
    assert "cliente@example.cl" not in json.dumps(graph.mensajes)
    assert "interno" not in json.dumps(graph.mensajes)


def identidad(permisos):
    return IdentidadSesion(1, "operador", "Operador", TIPO_BASE_DATOS,
                           frozenset({"OPERADOR"}), frozenset(permisos))


def sesion(cliente, actor):
    cliente.get("/login")
    with cliente.session_transaction() as datos:
        datos[CLAVE_IDENTIDAD] = {"tipo": actor.tipo_identidad, "id_usuario": 1,
                                 "usuario": actor.usuario}
        return datos["_csrf"]["token"]


class ServicioFeriadosWeb:
    def listar(self, **_): return Pagina((), 0, 1, 25)
    def previsualizar(self, *_): return {"feriados_preview": (), "resumen": {}, "anio": 2026, "pais": "CL"}


def test_rutas_feriados_exigen_permiso_y_post_exige_csrf(configuracion):
    actor = identidad({"FERIADOS_VER", "FERIADOS_SINCRONIZAR"})
    app = crear_aplicacion(configuracion, ajustes={"TESTING": True})
    app.extensions["cargador_identidad"] = lambda _: actor
    app.extensions["servicio_feriados"] = ServicioFeriadosWeb()
    cliente = app.test_client(); token = sesion(cliente, actor)
    assert cliente.get("/feriados/").status_code == 200
    assert cliente.post("/feriados/sincronizar/preview", data={"anio": "2026", "pais": "CL"}).status_code == 403
    assert cliente.post("/feriados/sincronizar/preview",
                        data={"csrf_token": token, "anio": "2026", "pais": "CL"}).status_code == 200
    sin_permiso = identidad({"TAREAS_VER"}); app.extensions["cargador_identidad"] = lambda _: sin_permiso
    with cliente.session_transaction() as datos:
        datos[CLAVE_IDENTIDAD] = {"tipo": sin_permiso.tipo_identidad, "id_usuario": 1,
                                 "usuario": sin_permiso.usuario}
    assert cliente.get("/feriados/").status_code == 403


def test_ruta_graph_requiere_configuracion_admin(configuracion):
    actor = identidad({"SCHEDULER_CONFIG_VER"})
    app = crear_aplicacion(configuracion, ajustes={"TESTING": True})
    app.extensions["cargador_identidad"] = lambda _: actor
    cliente = app.test_client(); sesion(cliente, actor)
    assert cliente.get("/configuracion/mail-graph").status_code == 403


def test_ruta_graph_no_envia_identificadores_vigentes_al_html(configuracion):
    actor = identidad({"CONFIGURACION_ADMIN"})
    sql = ConfiguracionMailGraph(1, False, "tenant-no-html", "client-no-html",
        "https://graph.microsoft.com/.default", "bpm@example.cl", True,
        "alertas@example.cl", "ENV", None, None)
    efectiva = SimpleNamespace(tenant_id=sql.tenant_id, client_id=sql.client_id,
        graph_scope=sql.graph_scope, send_mail_user=sql.send_mail_user,
        alertas_destinatarios_default=sql.alertas_destinatarios_default)
    servicio = SimpleNamespace(obtener=lambda: SimpleNamespace(
        estado="DESHABILITADO", disponible_envio=False, mail_enabled_env=False,
        secret_configurado=False, sql=sql, efectiva=efectiva,
    ))
    app = crear_aplicacion(configuracion, ajustes={"TESTING": True})
    app.extensions["cargador_identidad"] = lambda _: actor
    app.extensions["servicio_configuracion_graph"] = servicio
    cliente = app.test_client(); sesion(cliente, actor)
    respuesta = cliente.get("/configuracion/mail-graph")
    assert respuesta.status_code == 200
    assert b"tenant-no-html" not in respuesta.data
    assert b"client-no-html" not in respuesta.data
    assert b"bpm@example.cl" in respuesta.data
