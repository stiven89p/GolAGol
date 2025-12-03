from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form
from jinja2.bccache import Bucket
from fastapi.staticfiles import StaticFiles
from backend.utils.bucket import upload_file
from sqlalchemy import text
from sqlalchemy.orm import aliased
import backend.routers.Partidos
import backend.routers.Temporadas
import backend.routers.Equipos
import backend.routers.Eventos
import backend.routers.Jugadores
import backend.routers.Formaciones
from backend.modelos.Equipos import Equipo
import backend.routers.Estadisticas_Equipos
import backend.routers.Estadisticas_Jugadores
from backend.db import *
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.modelos.Partidos import Partido
import time

app = FastAPI(lifespan=create_tables, title="Gol a Gol API")

from fastapi.middleware.cors import CORSMiddleware

# Montar archivos estáticos ANTES de las rutas
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# 🔹 Rutas del proyecto
app.include_router(backend.routers.Equipos.router)
app.include_router(backend.routers.Partidos.router)
app.include_router(backend.routers.Eventos.router)
app.include_router(backend.routers.Jugadores.router)
app.include_router(backend.routers.Formaciones.router)
app.include_router(backend.routers.Temporadas.router)
app.include_router(backend.routers.Estadisticas_Equipos.router)
app.include_router(backend.routers.Estadisticas_Jugadores.router)
@app.post("/bucket")
async def create_bucket(file: UploadFile = File(...) ):
    result = await upload_file(file)
    return result

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "cache_bust": int(time.time())})

# ========== RUTAS ADMIN ==========

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, session: SessionDep):
    from backend.modelos.Jugadores import Jugador
    from backend.modelos.Formaciones import Formacion
    from backend.utils.enumeraciones import EstadoPartidos
    from datetime import datetime
    
    # Estadísticas
    stats = {
        "total_equipos": session.query(Equipo).count(),
        "total_jugadores": session.query(Jugador).count(),
        "total_partidos": session.query(Partido).count(),
        "total_formaciones": session.query(Formacion).count()
    }
    
    # Próximos partidos
    el = aliased(Equipo, name="equipo_local")
    ev = aliased(Equipo, name="equipo_visitante")
    
    partidos = (
        session.query(Partido, el, ev)
        .select_from(Partido)
        .join(el, Partido.equipo_local_id == el.equipo_id)
        .join(ev, Partido.equipo_visitante_id == ev.equipo_id)
        .filter(Partido.estado == EstadoPartidos.PROGRAMADO)
        .order_by(Partido.fecha.asc())
        .limit(10)
        .all()
    )
    
    proximos_partidos = []
    for partido, eq_local, eq_visitante in partidos:
        proximos_partidos.append({
            "partido_id": partido.partido_id,
            "fecha": partido.fecha.strftime("%d/%m/%Y"),
            "hora": partido.hora.strftime("%H:%M") if partido.hora else "",
            "equipo_local": eq_local.nombre,
            "equipo_visitante": eq_visitante.nombre,
            "estado": partido.estado
        })
    
    return templates.TemplateResponse("admin/index.html", {
        "request": request,
        "stats": stats,
        "proximos_partidos": proximos_partidos
    })

@app.get("/admin/equipos", response_class=HTMLResponse)
async def admin_equipos(request: Request, session: SessionDep):
    def logo_url(logo_val: str|None):
        if not logo_val:
            return "/static/img/default_logo.png"
        if str(logo_val).startswith("http") or str(logo_val).startswith("/static/"):
            return str(logo_val)
        path = str(logo_val)
        if not path.startswith("img/"):
            path = f"img/{path}"
        return f"/static/{path}"
    
    equipos_raw = session.query(Equipo).all()
    equipos = []
    for eq in equipos_raw:
        equipos.append({
            "equipo_id": eq.equipo_id,
            "nombre": eq.nombre,
            "ciudad": eq.ciudad,
            "estadio": eq.estadio,
            "anio_fundacion": eq.anio_fundacion,
            "titulos": eq.titulos,
            "activo": eq.activo,
            "logo": logo_url(eq.logo)
        })
    
    return templates.TemplateResponse("admin/equipos.html", {
        "request": request,
        "equipos": equipos
    })

@app.get("/admin/jugadores", response_class=HTMLResponse)
async def admin_jugadores(request: Request, session: SessionDep, equipo_id: int = None, posicion: str = None):
    from backend.modelos.Jugadores import Jugador
    from datetime import datetime
    
    query = session.query(Jugador, Equipo).join(Equipo, Jugador.equipo_id == Equipo.equipo_id)
    
    if equipo_id:
        query = query.filter(Jugador.equipo_id == equipo_id)
    if posicion:
        query = query.filter(Jugador.posicion == posicion)
    
    rows = query.all()
    
    jugadores = []
    for jugador, equipo in rows:
        edad = datetime.now().year - jugador.fecha_nacimiento.year
        foto_url = f"/static/img/{jugador.foto}" if jugador.foto else "/static/img/default-player.png"
        posicion_value = jugador.posicion.value if hasattr(jugador.posicion, 'value') else str(jugador.posicion)
        jugadores.append({
            "jugador_id": jugador.jugador_id,
            "nombre": jugador.nombre,
            "apellido": jugador.apellido,
            "numero_camiseta": jugador.numero_camiseta,
            "equipo_nombre": equipo.nombre,
            "posicion": posicion_value,  # raw lowercase enum value
            "edad": edad,
            "nacionalidad": jugador.nacionalidad,
            "foto": foto_url
        })
    
    equipos = session.query(Equipo).all()
    
    return templates.TemplateResponse("admin/jugadores.html", {
        "request": request,
        "jugadores": jugadores,
        "equipos": equipos
    })

@app.get("/admin/partidos", response_class=HTMLResponse)
async def admin_partidos(request: Request, session: SessionDep):
    from backend.modelos.Temporada import Temporada
    
    el = aliased(Equipo, name="equipo_local")
    ev = aliased(Equipo, name="equipo_visitante")
    
    rows = (
        session.query(Partido, el, ev)
        .select_from(Partido)
        .join(el, Partido.equipo_local_id == el.equipo_id)
        .join(ev, Partido.equipo_visitante_id == ev.equipo_id)
        .order_by(Partido.fecha.desc())
        .all()
    )
    
    partidos = []
    for partido, eq_local, eq_visitante in rows:
        partidos.append({
            "partido_id": partido.partido_id,
            "fecha": partido.fecha.strftime("%d/%m/%Y"),
            "hora": partido.hora.strftime("%H:%M") if partido.hora else "",
            "equipo_local": eq_local.nombre,
            "equipo_visitante": eq_visitante.nombre,
            "goles_local": partido.goles_local,
            "goles_visitante": partido.goles_visitante,
            "jornada": partido.jornada,
            "estado": partido.estado
        })
    
    equipos = session.query(Equipo).filter(Equipo.activo == True).all()
    temporadas = session.query(Temporada).all()
    
    return templates.TemplateResponse("admin/partidos.html", {
        "request": request,
        "partidos": partidos,
        "equipos": equipos,
        "temporadas": temporadas
    })

@app.get("/admin/formaciones", response_class=HTMLResponse)
async def admin_formaciones(request: Request, session: SessionDep, equipo_id: int = None):
    from backend.modelos.Formaciones import Formacion, FormacionJugador
    from backend.modelos.Jugadores import Jugador

    query = session.query(Formacion).order_by(Formacion.formacion_id.desc())
    if equipo_id:
        query = query.filter(Formacion.equipo_id == equipo_id)
    formaciones_rows = query.all()

    formaciones = []
    for f in formaciones_rows:
        jugadores_rel = session.query(FormacionJugador).filter(FormacionJugador.formacion_id == f.formacion_id).all()
        titulares_ids = [jr.jugador_id for jr in jugadores_rel if jr.titular]
        suplentes_ids = [jr.jugador_id for jr in jugadores_rel if not jr.titular]
        # cargar nombres
        if titulares_ids:
            titulares_objs = session.query(Jugador).filter(Jugador.jugador_id.in_(titulares_ids)).all()
        else:
            titulares_objs = []
        if suplentes_ids:
            suplentes_objs = session.query(Jugador).filter(Jugador.jugador_id.in_(suplentes_ids)).all()
        else:
            suplentes_objs = []
        formaciones.append({
            "formacion_id": f.formacion_id,
            "equipo_id": f.equipo_id,
            "portero_id": f.portero_id,
            "defensas": f.defensas,
            "mediocampistas": f.mediocampistas,
            "delanteros": f.delanteros,
            "titulares": [f"{j.nombre} {j.apellido}" for j in titulares_objs],
            "suplentes": [f"{j.nombre} {j.apellido}" for j in suplentes_objs],
            "total": 11
        })

    equipos = session.query(Equipo).filter(Equipo.activo == True).all()

    return templates.TemplateResponse("admin/formaciones.html", {
        "request": request,
        "formaciones": formaciones,
        "equipos": equipos
    })

@app.get("/admin/partidos/{partido_id}/eventos", response_class=HTMLResponse)
async def admin_eventos_partido(request: Request, partido_id: int, session: SessionDep):
    # Validar que el partido existe
    partido = session.get(Partido, partido_id)
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")
    return templates.TemplateResponse("admin/eventos.html", {
        "request": request,
        "partido_id": partido_id
    })

@app.get("/partido/{partido_id}", response_class=HTMLResponse)
async def partido_detalle(request: Request, partido_id: int, session: SessionDep):
    from backend.modelos.Formaciones import Formacion, FormacionJugador
    from backend.modelos.Jugadores import Jugador
    
    el = aliased(Equipo, name="equipo_local")
    ev = aliased(Equipo, name="equipo_visitante")

    row = (
        session.query(Partido, el, ev)
        .select_from(Partido)
        .join(el, Partido.equipo_local_id == el.equipo_id)
        .join(ev, Partido.equipo_visitante_id == ev.equipo_id)
        .filter(Partido.partido_id == partido_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    partido, equipo_local, equipo_visitante = row

    def logo_url(logo_val: str|None):
        if not logo_val:
            return "/static/img/default_logo.png"
        # si ya es url absoluta o ruta desde static, dejarla
        if str(logo_val).startswith("http") or str(logo_val).startswith("/static/"):
            return str(logo_val)
        # caso común: almacena 'img/archivo.png' o solo 'archivo.png'
        path = str(logo_val)
        if not path.startswith("img/"):
            path = f"img/{path}"
        return f"/static/{path}"

    # Función para cargar formación con jugadores
    def cargar_formacion(formacion_id: int | None):
        if not formacion_id:
            return None
        
        formacion = session.get(Formacion, formacion_id)
        if not formacion:
            return None
        
        # Obtener jugadores de la formación
        fjs = session.query(FormacionJugador).filter(FormacionJugador.formacion_id == formacion_id).all()
        jugador_ids = [fj.jugador_id for fj in fjs]
        jugadores = session.query(Jugador).filter(Jugador.jugador_id.in_(jugador_ids)).all()
        jugadores_dict = {j.jugador_id: j for j in jugadores}
        
        titulares = []
        suplentes = []
        
        for fj in fjs:
            jugador = jugadores_dict.get(fj.jugador_id)
            if jugador:
                info = {
                    "jugador_id": jugador.jugador_id,
                    "nombre": f"{jugador.nombre} {jugador.apellido}",
                    "posicion": fj.posicion.name if hasattr(fj.posicion, 'name') else str(fj.posicion),
                    "foto": logo_url(jugador.foto)
                }
                if fj.titular:
                    titulares.append(info)
                else:
                    suplentes.append(info)
        
        return {
            "defensas": formacion.defensas,
            "mediocampistas": formacion.mediocampistas,
            "delanteros": formacion.delanteros,
            "portero_id": formacion.portero_id,
            "titulares": titulares,
            "suplentes": suplentes
        }

    detalle = {
        "partido_id": partido.partido_id,
        "estado": partido.estado,
        "fecha": str(partido.fecha),
        "hora": partido.hora.strftime("%H:%M") if partido.hora else None,
        "hora_inicio": partido.hora_inicio.strftime("%H:%M:%S") if partido.hora_inicio else None,
        "hora_fin_primer_tiempo": partido.hora_fin_primer_tiempo.strftime("%H:%M:%S") if partido.hora_fin_primer_tiempo else None,
        "hora_inicio_segundo_tiempo": partido.hora_inicio_segundo_tiempo.strftime("%H:%M:%S") if partido.hora_inicio_segundo_tiempo else None,
        "hora_fin_segundo_tiempo": partido.hora_fin_segundo_tiempo.strftime("%H:%M:%S") if partido.hora_fin_segundo_tiempo else None,
        "parte": partido.parte.name if partido.parte else None,
        "lugar": partido.estadio,
        "goles_local": partido.goles_local,
        "goles_visitante": partido.goles_visitante,
        "equipo_local_id": partido.equipo_local_id,
        "equipo_local_nombre": getattr(equipo_local, "nombre", ""),
        "equipo_local_logo": logo_url(getattr(equipo_local, "logo", None)),
        "equipo_visitante_id": partido.equipo_visitante_id,
        "equipo_visitante_nombre": getattr(equipo_visitante, "nombre", ""),
        "equipo_visitante_logo": logo_url(getattr(equipo_visitante, "logo", None)),
        "formacion_local": cargar_formacion(partido.formacion_local_id),
        "formacion_visitante": cargar_formacion(partido.formacion_visitante_id),
    }

    return templates.TemplateResponse("partido.html", {"request": request, "partido": detalle})

@app.get("/equipo/{equipo_id}")
async def equipo(request: Request, equipo_id: int, session: SessionDep):
    from backend.modelos.Estadisticas_Equipos import Estadisticas_E
    from backend.utils.enumeraciones import EstadoPartidos
    from sqlalchemy import or_
    
    equipo = session.get(Equipo, equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    
    def logo_url(logo_val: str|None):
        if not logo_val:
            return "/static/img/default_logo.png"
        if str(logo_val).startswith("http") or str(logo_val).startswith("/static/"):
            return str(logo_val)
        path = str(logo_val)
        if not path.startswith("img/"):
            path = f"img/{path}"
        return f"/static/{path}"
    
    # Obtener resultados recientes (últimos 5 partidos finalizados)
    el = aliased(Equipo, name="equipo_local")
    ev = aliased(Equipo, name="equipo_visitante")
    
    partidos_finalizados = (
        session.query(Partido, el, ev)
        .select_from(Partido)
        .join(el, Partido.equipo_local_id == el.equipo_id)
        .join(ev, Partido.equipo_visitante_id == ev.equipo_id)
        .filter(
            or_(Partido.equipo_local_id == equipo_id, Partido.equipo_visitante_id == equipo_id),
            Partido.estado == EstadoPartidos.FINALIZADO
        )
        .order_by(Partido.fecha.desc())
        .limit(5)
        .all()
    )
    
    resultados = []
    for partido, eq_local, eq_visitante in partidos_finalizados:
        es_local = partido.equipo_local_id == equipo_id
        if es_local:
            resultado = f"{partido.goles_local} - {partido.goles_visitante}"
            eq_oponente = eq_visitante
        else:
            resultado = f"{partido.goles_visitante} - {partido.goles_local}"
            eq_oponente = eq_local

        resultados.append({
            "resultado": resultado,
            "oponente": eq_oponente.nombre,
            "oponente_logo": logo_url(getattr(eq_oponente, "logo", None)),
            "fecha": partido.fecha.strftime("%d/%m/%Y")
        })
    
    # Obtener próximos partidos (programados)
    partidos_programados = (
        session.query(Partido, el, ev)
        .select_from(Partido)
        .join(el, Partido.equipo_local_id == el.equipo_id)
        .join(ev, Partido.equipo_visitante_id == ev.equipo_id)
        .filter(
            or_(Partido.equipo_local_id == equipo_id, Partido.equipo_visitante_id == equipo_id),
            Partido.estado == EstadoPartidos.PROGRAMADO
        )
        .order_by(Partido.fecha.asc())
        .limit(5)
        .all()
    )
    
    proximos = []
    for partido, eq_local, eq_visitante in partidos_programados:
        es_local = partido.equipo_local_id == equipo_id
        eq_oponente = eq_visitante if es_local else eq_local
        
        proximos.append({
            "oponente": eq_oponente.nombre,
            "oponente_logo": logo_url(eq_oponente.logo),
            "fecha": partido.fecha.strftime("%d/%m/%Y"),
            "hora": partido.hora.strftime("%H:%M") if partido.hora else None,
            "lugar": partido.estadio
        })
    
    # Obtener estadísticas del equipo (todas las temporadas)
    stats = session.query(Estadisticas_E).filter(Estadisticas_E.equipo_id == equipo_id).all()

    estadisticas = []
    for stat in stats:
        estadisticas.append({
            "temporada": f"Temporada {stat.temporada}",
            "partidos_jugados": stat.partidos_jugados,
            "victorias": stat.victorias,
            "empates": stat.empates,
            "derrotas": stat.derrotas,
            "goles_favor": stat.goles_favor,
            "goles_contra": stat.goles_contra,
            "puntos": stat.puntos,
            "tarjetas_amarillas": stat.tarjetas_amarillas,
            "tarjetas_rojas": stat.tarjetas_rojas
        })

    # Seleccionar temporada más reciente para subdivisión equipo/jugadores
    latest_season = max([s.temporada for s in stats], default=None)
    estadisticas_equipo = None
    estadisticas_jugadores = []
    if latest_season is not None:
        # Registro del equipo para la última temporada
        estadisticas_equipo = next((s for s in stats if s.temporada == latest_season), None)
        # Estadísticas de jugadores para la misma temporada
        from backend.modelos.Estadisticas_Jugadores import Estadisticas_J
        estadisticas_jugadores = session.query(Estadisticas_J).filter(
            Estadisticas_J.equipo_id == equipo_id,
            Estadisticas_J.temporada == latest_season
        ).all()

    return templates.TemplateResponse("equipo.html", {
        "request": request,
        "equipo": equipo,
        "resultados": resultados,
        "proximos": proximos,
        "estadisticas": estadisticas,
        "estadisticas_equipo": estadisticas_equipo,
        "estadisticas_jugadores": estadisticas_jugadores
    })


@app.get("/jugadores/{equipo_id}", response_class=HTMLResponse)
async def jugadores_equipo(request: Request, equipo_id: int, session: SessionDep):
    equipo = session.get(Equipo, equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    
    def logo_url(logo_val: str|None):
        if not logo_val:
            return "/static/img/default_logo.png"
        if str(logo_val).startswith("http") or str(logo_val).startswith("/static/"):
            return str(logo_val)
        path = str(logo_val)
        if not path.startswith("img/"):
            path = f"img/{path}"
        return f"/static/{path}"
    
    equipo_data = {
        "equipo_id": equipo.equipo_id,
        "nombre": equipo.nombre,
        "logo": logo_url(equipo.logo)
    }
    
    return templates.TemplateResponse("jugadores.html", {
        "request": request,
        "equipo": equipo_data
    })


@app.get("/jugador/{jugador_id}", response_class=HTMLResponse)
async def jugador_perfil(request: Request, jugador_id: int, session: SessionDep):
    from backend.modelos.Jugadores import Jugador
    from backend.modelos.Estadisticas_Jugadores import Estadisticas_J
    from datetime import date
    
    jugador = session.get(Jugador, jugador_id)
    if not jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    
    # Obtener equipo
    equipo = session.get(Equipo, jugador.equipo_id)
    
    def logo_url(logo_val: str|None):
        if not logo_val:
            return "/static/img/default-player.png"
        if str(logo_val).startswith("http") or str(logo_val).startswith("/static/"):
            return str(logo_val)
        path = str(logo_val)
        if not path.startswith("img/"):
            path = f"img/{path}"
        return f"/static/{path}"
    
    # Calcular edad
    def calcular_edad(fecha_nacimiento):
        hoy = date.today()
        edad = hoy.year - fecha_nacimiento.year
        if hoy.month < fecha_nacimiento.month or (hoy.month == fecha_nacimiento.month and hoy.day < fecha_nacimiento.day):
            edad -= 1
        return edad
    
    # Formatear fecha
    def formatear_fecha(fecha):
        meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 
                 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
        return f"{fecha.day} de {meses[fecha.month-1]} de {fecha.year}"
    
    # Formatear posición
    posiciones = {
        'PORTERO': 'Portero',
        'DEFENSOR': 'Defensa',
        'MEDIOCAMPISTA': 'Mediocampista',
        'DELANTERO': 'Delantero'
    }
    
    jugador_data = {
        "jugador_id": jugador.jugador_id,
        "nombre": jugador.nombre,
        "apellido": jugador.apellido,
        "numero_camiseta": jugador.numero_camiseta,
        "posicion": jugador.posicion.name if hasattr(jugador.posicion, 'name') else str(jugador.posicion),
        "posicion_texto": posiciones.get(jugador.posicion.name if hasattr(jugador.posicion, 'name') else str(jugador.posicion), str(jugador.posicion)),
        "nacionalidad": jugador.nacionalidad,
        "edad": calcular_edad(jugador.fecha_nacimiento),
        "fecha_nacimiento_texto": formatear_fecha(jugador.fecha_nacimiento),
        "foto": logo_url(jugador.foto),
        "equipo_id": jugador.equipo_id,
        "equipo_nombre": equipo.nombre if equipo else "Sin equipo"
    }
    
    # Obtener estadísticas
    estadisticas = session.query(Estadisticas_J).filter(
        Estadisticas_J.jugador_id == jugador_id
    ).all()
    
    estadisticas_data = []
    for est in estadisticas:
        estadisticas_data.append({
            "temporada": est.temporada,
            "temporada_nombre": f"Temporada {est.temporada}",
            "partidos_jugados": est.partidos_jugados or 0,
            "goles": est.goles or 0,
            "asistencias": est.asistencias or 0,
            "tarjetas_amarillas": est.tarjetas_amarillas or 0,
            "tarjetas_rojas": est.tarjetas_rojas or 0,
            "minutos_jugados": getattr(est, 'minutos_jugados', 0) or 0,
            "balones_perdidos": getattr(est, 'balones_perdidos', 0) or 0,
            "penales_cobrados": getattr(est, 'penales_cobrados', 0) or 0,
            "penales_fallados": getattr(est, 'penales_fallados', 0) or 0,
            "tiros_totales": getattr(est, 'tiros_totales', 0) or 0,
            "tiros_a_puerta": getattr(est, 'tiros_a_puerta', 0) or 0,
            "entradas": getattr(est, 'entradas', 0) or 0,
            "intercepciones": getattr(est, 'intercepciones', 0) or 0,
            "goles_contra": getattr(est, 'goles_contra', 0) or 0,
            "goles_concedidos": getattr(est, 'goles_concedidos', 0) or 0,
            "paradas": getattr(est, 'paradas', 0) or 0,
            "penales_tapados": getattr(est, 'penales_tapados', 0) or 0
        })
    
    # Obtener otros jugadores del mismo equipo
    otros_jugadores = session.query(Jugador).filter(
        Jugador.equipo_id == jugador.equipo_id,
        Jugador.jugador_id != jugador_id
    ).order_by(Jugador.posicion, Jugador.apellido).all()
    
    otros_jugadores_data = []
    for j in otros_jugadores:
        otros_jugadores_data.append({
            "jugador_id": j.jugador_id,
            "nombre": j.nombre,
            "apellido": j.apellido,
            "nombre_completo": f"{j.nombre} {j.apellido}",
            "numero_camiseta": j.numero_camiseta,
            "posicion": j.posicion.name if hasattr(j.posicion, 'name') else str(j.posicion),
            "posicion_texto": posiciones.get(j.posicion.name if hasattr(j.posicion, 'name') else str(j.posicion), str(j.posicion)),
            "foto": logo_url(j.foto),
            "edad": calcular_edad(j.fecha_nacimiento)
        })
    
    # Datos del equipo
    equipo_data = {
        "equipo_id": equipo.equipo_id,
        "nombre": equipo.nombre,
        "logo": logo_url(equipo.logo)
    } if equipo else None
    
    return templates.TemplateResponse("jugador.html", {
        "request": request,
        "jugador": jugador_data,
        "estadisticas": estadisticas_data,
        "otros_jugadores": otros_jugadores_data,
        "equipo": equipo_data
    })

@app.get("/equipos_listado", response_class=HTMLResponse)
async def equipos_listado(request: Request, session: SessionDep):
    equipos = session.query(Equipo).all()
    return templates.TemplateResponse("equipos_listado.html", {"request": request, "equipos": equipos})

@app.get("/estadisticas/detalle", response_class=HTMLResponse)
async def estadisticas_detalle(request: Request, session: SessionDep, temporada_id: int = None):
    """Vista detallada de estadísticas por categorías"""
    from backend.modelos.Temporada import Temporada
    
    # Si no se especifica temporada, obtener la activa o la más reciente
    if not temporada_id:
        temporada = session.query(Temporada).filter(
            Temporada.estado == "EN_CURSO"
        ).first()
        if not temporada:
            temporada = session.query(Temporada).order_by(
                Temporada.temporada_id.desc()
            ).first()
        temporada_id = temporada.temporada_id if temporada else 1
    else:
        temporada = session.get(Temporada, temporada_id)
    
    temporada_nombre = f"{temporada.nombre}" if temporada else "Temporada Actual"
    
    return templates.TemplateResponse("estadisticas_detalle.html", {
        "request": request,
        "temporada_id": temporada_id,
        "temporada_nombre": temporada_nombre,
        "cache_bust": int(time.time())
    })

