import random
from fastapi import APIRouter, HTTPException, Form
from pydantic import BaseModel
from sqlalchemy.orm import aliased
from datetime import date, datetime, time, timedelta
from backend.modelos.Equipos import Equipo
from backend.modelos.Partidos import Partido, PartidoCrear, PartidoDTO
from backend.modelos.Formaciones import Formacion, FormacionJugador
from backend.modelos.Estadisticas_Equipos import Estadisticas_E
from backend.modelos.Estadisticas_Jugadores import Estadisticas_J
from backend.modelos.Eventos import Evento
from backend.modelos.Temporada import Temporada
from backend.utils.enumeraciones import EstadoPartidos, PartePartido, TipoEvento
from backend.db import SessionDep

router = APIRouter(prefix="/partidos", tags=["partidos"])


def _actualizar_partidos_jugados_jugadores(session, partido: Partido):
    """
    Incrementa partidos_jugados para:
    1. Todos los jugadores titulares (de ambas formaciones)
    2. Todos los jugadores que entraron como sustitución
    """
    jugadores_participantes = set()
    
    # 1. Obtener titulares de la formación local
    if partido.formacion_local_id:
        titulares_local = session.query(FormacionJugador).filter_by(
            formacion_id=partido.formacion_local_id,
            titular=True
        ).all()
        for fj in titulares_local:
            jugadores_participantes.add(fj.jugador_id)
    
    # 2. Obtener titulares de la formación visitante
    if partido.formacion_visitante_id:
        titulares_visitante = session.query(FormacionJugador).filter_by(
            formacion_id=partido.formacion_visitante_id,
            titular=True
        ).all()
        for fj in titulares_visitante:
            jugadores_participantes.add(fj.jugador_id)
    
    # 3. Obtener jugadores que entraron por sustitución (jugador_asociado_id en eventos SUSTITUCION)
    sustituciones = session.query(Evento).filter_by(
        partido_id=partido.partido_id,
        tipo=TipoEvento.SUSTITUCION
    ).all()
    
    for sust in sustituciones:
        if sust.jugador_asociado_id:  # El que entra
            jugadores_participantes.add(sust.jugador_asociado_id)
    
    # 4. Actualizar estadísticas de todos los jugadores participantes
    for jugador_id in jugadores_participantes:
        estadistica_jugador = session.query(Estadisticas_J).filter_by(
            jugador_id=jugador_id,
            temporada=partido.temporada_id
        ).first()
        
        if estadistica_jugador:
            estadistica_jugador.partidos_jugados = (estadistica_jugador.partidos_jugados or 0) + 1
            session.add(estadistica_jugador)


def _actualizar_minutos_jugados(session, partido: Partido):
    """Calcula y persiste minutos jugados por jugador en Estadisticas_J para el partido y su temporada."""
    from backend.modelos.Formaciones import FormacionJugador
    from backend.modelos.Eventos import Evento

    # Utiliza la misma lógica del endpoint de minutos
    def cargar_ids(formacion_id: int | None, titulares: bool) -> set[int]:
        if not formacion_id:
            return set()
        rows = session.query(FormacionJugador).filter(
            FormacionJugador.formacion_id == formacion_id,
            FormacionJugador.titular == titulares
        ).all()
        return {r.jugador_id for r in rows}

    titulares_local = cargar_ids(partido.formacion_local_id, True)
    titulares_visitante = cargar_ids(partido.formacion_visitante_id, True)

    eventos = session.query(Evento).filter(Evento.partido_id == partido.partido_id).order_by(Evento.minuto.asc(), Evento.id_evento.asc()).all()

    entradas: dict[int, list[int]] = {}
    salidas: dict[int, list[int]] = {}
    expulsado_en: dict[int, int] = {}
    amarillas_count: dict[int, int] = {}

    for jid in titulares_local | titulares_visitante:
        entradas.setdefault(jid, []).append(0)

    for e in eventos:
        tipo_val = e.tipo.value if hasattr(e.tipo, 'value') else str(e.tipo)
        try:
            tipo_enum = e.tipo if isinstance(e.tipo, TipoEvento) else TipoEvento(tipo_val)
        except Exception:
            continue

        if tipo_enum == TipoEvento.SUSTITUCION:
            if e.jugador_id:
                salidas.setdefault(e.jugador_id, []).append(e.minuto or 0)
            if e.jugador_asociado_id:
                entradas.setdefault(e.jugador_asociado_id, []).append(e.minuto or 0)
        elif tipo_enum == TipoEvento.TARJETA_ROJA:
            if e.jugador_id and e.minuto is not None:
                expulsado_en[e.jugador_id] = e.minuto
                salidas.setdefault(e.jugador_id, []).append(e.minuto)
        elif tipo_enum == TipoEvento.TARJETA_AMARILLA:
            if e.jugador_id:
                amarillas_count[e.jugador_id] = amarillas_count.get(e.jugador_id, 0) + 1
                if amarillas_count[e.jugador_id] >= 2 and e.minuto is not None:
                    expulsado_en[e.jugador_id] = e.minuto
                    salidas.setdefault(e.jugador_id, []).append(e.minuto)

    ultimo_minuto_evento = max([ev.minuto or 0 for ev in eventos], default=0)
    minuto_final = max(ultimo_minuto_evento, 90)

    minutos_por_jugador: dict[int, int] = {}
    for jid, entradas_list in entradas.items():
        salidas_list = salidas.get(jid, [])
        for idx, min_in in enumerate(entradas_list):
            if idx < len(salidas_list):
                min_out = salidas_list[idx]
            else:
                min_out = expulsado_en.get(jid, minuto_final)
            delta = max((min_out or 0) - (min_in or 0), 0)
            minutos_por_jugador[jid] = minutos_por_jugador.get(jid, 0) + delta

    # Persistir en Estadisticas_J
    for jugador_id, minutos in minutos_por_jugador.items():
        estadistica_jugador = session.query(Estadisticas_J).filter_by(
            jugador_id=jugador_id,
            temporada=partido.temporada_id
        ).first()
        if estadistica_jugador:
            estadistica_jugador.minutos_jugados = (estadistica_jugador.minutos_jugados or 0) + minutos
            session.add(estadistica_jugador)


@router.post("/", response_model=Partido)
async def crear_partido(
        session: SessionDep,
        fecha: date = Form(...),
        hora: time = Form(...),
        jornada: int = Form(...),
        temporada_id: int = Form(...),
        estadio: str = Form(...),
        equipo_local_id: int = Form(...),
        equipo_visitante_id: int = Form(...)
        ):
    new_partido = PartidoCrear(
        fecha=fecha,
        hora=hora,
        jornada=jornada,
        estadio=estadio,
        equipo_local_id=equipo_local_id,
        equipo_visitante_id=equipo_visitante_id,
        temporada_id=temporada_id,
    )
    partido = Partido.model_validate(new_partido)
    temporada= session.get(Temporada, partido.temporada_id)

    if not temporada:
        raise HTTPException(status_code=404, detail="La temporada no existe")

    equipo_local = session.get(Equipo, partido.equipo_local_id)
    if not equipo_local:
        raise HTTPException(status_code=404, detail="El equipo local no existe")

    equipo_visitante = session.get(Equipo, partido.equipo_visitante_id)
    if not equipo_visitante:
        raise HTTPException(status_code=404, detail="El equipo visitante no existe")

    if partido.equipo_local_id == partido.equipo_visitante_id:
        raise HTTPException(status_code=400, detail="Un equipo no puede jugar contra sí mismo")

    session.add(partido)
    session.commit()
    session.refresh(partido)

    return partido

class GenerarFixtureRequest(BaseModel):
    temporada_id: int
    dias_semana: list[int]          # 0=lunes … 6=domingo
    max_simultaneos: int = 1        # partidos jugándose al mismo tiempo en un horario
    horas: list[str] = ["15:00"]    # formato HH:MM


class GenerarFixtureResponse(BaseModel):
    partidos_creados: int
    jornadas: int
    fecha_inicio: date
    fecha_fin: date


@router.post("/generar/", response_model=GenerarFixtureResponse)
async def generar_fixture(body: GenerarFixtureRequest, session: SessionDep):
    temporada = session.get(Temporada, body.temporada_id)
    if not temporada:
        raise HTTPException(status_code=404, detail="La temporada no existe")

    if not body.dias_semana:
        raise HTTPException(status_code=400, detail="Seleccione al menos un día de la semana")
    for d in body.dias_semana:
        if d < 0 or d > 6:
            raise HTTPException(status_code=400, detail=f"Día inválido: {d}. Use 0=lunes … 6=domingo")

    if body.max_simultaneos < 1:
        raise HTTPException(status_code=400, detail="El máximo de partidos simultáneos debe ser al menos 1")

    if not body.horas:
        raise HTTPException(status_code=400, detail="Especifique al menos una hora")
    try:
        horas_time = [time.fromisoformat(h) for h in body.horas]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Hora inválida: {exc}")

    existing = session.query(Partido).filter(Partido.temporada_id == body.temporada_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ya existen partidos para esta temporada. Elimínalos antes de generar el fixture.")

    equipos = session.query(Equipo).filter(Equipo.activo == True).all()
    if len(equipos) < 2:
        raise HTTPException(status_code=400, detail="Se necesitan al menos 2 equipos activos")

    team_estadio = {e.equipo_id: e.estadio for e in equipos}
    ids = [e.equipo_id for e in equipos]
    random.shuffle(ids)

    n = len(ids)
    if n % 2 == 1:
        ids.append(None)
        n += 1

    def siguiente_valida(d: date) -> date:
        while d.weekday() not in body.dias_semana:
            d += timedelta(days=1)
        return d

    fecha_actual = siguiente_valida(temporada.fecha_inicio)
    hora_idx = 0          # índice en horas_time para el slot actual
    slot_count = 0        # partidos asignados al slot actual
    partidos_a_crear: list[Partido] = []
    teams = list(ids)

    for jornada in range(n - 1):
        for i in range(n // 2):
            a, b = teams[i], teams[n - 1 - i]
            if a is None or b is None:
                continue
            home, away = (a, b) if jornada % 2 == 0 else (b, a)

            # Si el slot actual ya está lleno, avanzar al siguiente horario del día
            if slot_count >= body.max_simultaneos:
                hora_idx += 1
                slot_count = 0
                # Si se agotaron todos los horarios del día, pasar al siguiente día válido
                if hora_idx >= len(horas_time):
                    hora_idx = 0
                    fecha_actual += timedelta(days=1)
                    fecha_actual = siguiente_valida(fecha_actual)

            hora = horas_time[hora_idx]
            partidos_a_crear.append(Partido(
                fecha=fecha_actual,
                hora=hora,
                jornada=jornada + 1,
                estadio=team_estadio.get(home, ""),
                equipo_local_id=home,
                equipo_visitante_id=away,
                temporada_id=body.temporada_id,
            ))
            slot_count += 1

        teams = [teams[0]] + [teams[-1]] + teams[1:-1]

    if not partidos_a_crear:
        raise HTTPException(status_code=400, detail="No se generaron partidos")

    session.add_all(partidos_a_crear)
    session.commit()

    return GenerarFixtureResponse(
        partidos_creados=len(partidos_a_crear),
        jornadas=n - 1,
        fecha_inicio=temporada.fecha_inicio,
        fecha_fin=max(p.fecha for p in partidos_a_crear),
    )


@router.get("/", response_model=list[PartidoDTO])
async def obtener_partidos(session: SessionDep):
    equipo_local = aliased(Equipo)
    equipo_visitante = aliased(Equipo)

    rows = (
        session.query(Partido, equipo_local, equipo_visitante)
        .join(equipo_local, Partido.equipo_local_id == equipo_local.equipo_id)
        .join(equipo_visitante, Partido.equipo_visitante_id == equipo_visitante.equipo_id)
        .order_by(Partido.fecha.desc())
        .all()
    )

    dto_list: list[PartidoDTO] = []
    for partido, el, ev in rows:
        dto = PartidoDTO(
            partido_id=partido.partido_id,
            equipo_local_id=partido.equipo_local_id,
            equipo_local_nombre=getattr(el, "nombre", "") if el else "",
            equipo_local_logo=getattr(el, "logo", None) if el else None,
            equipo_visitante_id=partido.equipo_visitante_id,
            equipo_visitante_nombre=getattr(ev, "nombre", "") if ev else "",
            equipo_visitante_logo=getattr(ev, "logo", None) if ev else None,
            fecha=partido.fecha,
            hora=partido.hora.strftime("%H:%M") if partido.hora else None,
            lugar=partido.estadio,
            estado=partido.estado.name if hasattr(partido.estado, 'name') else str(partido.estado),
            goles_local=partido.goles_local,
            goles_visitante=partido.goles_visitante,
        )
        dto_list.append(dto)

    return dto_list

@router.get("/{estado}/", response_model=list[PartidoDTO])
async def obtener_partidos_por_estado(estado: EstadoPartidos, session: SessionDep):
    from backend.modelos.Equipos import Equipo
    from backend.modelos.Partidos import PartidoDTO
    from sqlalchemy.orm import aliased
    equipo_local = aliased(Equipo)
    equipo_visitante = aliased(Equipo)

    rows = (
        session.query(Partido, equipo_local, equipo_visitante)
        .join(equipo_local, Partido.equipo_local_id == equipo_local.equipo_id)
        .join(equipo_visitante, Partido.equipo_visitante_id == equipo_visitante.equipo_id)
        .filter(Partido.estado == estado)
        .order_by(Partido.fecha.desc())
        .all()
    )

    dto_list: list[PartidoDTO] = []
    for partido, el, ev in rows:
        dto = PartidoDTO(
            partido_id=partido.partido_id,
            equipo_local_nombre=getattr(el, "nombre", "") if el else "",
            equipo_local_logo=getattr(el, "logo", None) if el else None,
            equipo_visitante_nombre=getattr(ev, "nombre", "") if ev else "",
            equipo_visitante_logo=getattr(ev, "logo", None) if ev else None,
            fecha=partido.fecha,
            hora=partido.hora.strftime("%H:%M") if partido.hora else None,
            lugar=partido.estadio,
            estado=partido.estado.name if hasattr(partido.estado, 'name') else str(partido.estado),
            goles_local=partido.goles_local,
            goles_visitante=partido.goles_visitante,
        )
        dto_list.append(dto)

    return dto_list


@router.get("/equipo/{equipo_id}", response_model=list[PartidoDTO])
async def obtener_partidos_equipo(equipo_id: int, session: SessionDep):
    equipo_local = aliased(Equipo)
    equipo_visitante = aliased(Equipo)

    rows = (
        session.query(Partido, equipo_local, equipo_visitante)
        .join(equipo_local, Partido.equipo_local_id == equipo_local.equipo_id)
        .join(equipo_visitante, Partido.equipo_visitante_id == equipo_visitante.equipo_id)
        .filter(
            (Partido.equipo_local_id == equipo_id) | (Partido.equipo_visitante_id == equipo_id)
        )
        .order_by(Partido.fecha.desc())
        .all()
    )

    if not rows:
        raise HTTPException(status_code=404, detail="No se encontraron partidos para este equipo")

    dto_list: list[PartidoDTO] = []
    for partido, el, ev in rows:
        # Limpiar URLs de logos corruptas
    
        logo_local = getattr(el, "logo", None) if el else None
        logo_visitante = getattr(ev, "logo", None) if ev else None

        dto = PartidoDTO(
            partido_id=partido.partido_id,
            equipo_local_nombre=getattr(el, "nombre", "") if el else "",
            equipo_local_logo=logo_local,
            equipo_visitante_nombre=getattr(ev, "nombre", "") if ev else "",
            equipo_visitante_logo=logo_visitante,
            fecha=partido.fecha,
            hora=partido.hora.strftime("%H:%M") if partido.hora else None,
            lugar=partido.estadio,
            estado=partido.estado.name if hasattr(partido.estado, 'name') else str(partido.estado),
            goles_local=partido.goles_local,
            goles_visitante=partido.goles_visitante,
        )
        dto_list.append(dto)

    return dto_list


@router.patch("/{partido_id}", response_model=Partido)
async def cambiar_estado_partido(partido_id: int, estado:EstadoPartidos, session: SessionDep):
    partido = session.get(Partido, partido_id)

    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    # Validar requisito de formaciones antes de poner EN CURSO
    if estado == EstadoPartidos.EN_CURSO:
        if not partido.formacion_local_id or not partido.formacion_visitante_id:
            raise HTTPException(status_code=400, detail="Ambos equipos deben tener formación asignada antes de iniciar el partido (EN CURSO)")
        partido.hora_inicio = datetime.now().time()
        # Si no tiene parte asignada, iniciar en primer tiempo (guardar la instancia del enum)
        if not partido.parte:
            partido.parte = PartePartido.PRIMER_TIEMPO
    

    # Solo actualizar estadísticas, PJ y minutos jugados cuando el partido pasa a FINALIZADO
    if estado == EstadoPartidos.FINALIZADO and str(partido.estado).lower() != EstadoPartidos.FINALIZADO.value:
        estadistica = session.query(Estadisticas_E).filter_by(equipo_id=partido.equipo_local_id,temporada=partido.temporada_id).first()
        estadistica_rival = session.query(Estadisticas_E).filter_by(equipo_id=partido.equipo_visitante_id,temporada=partido.temporada_id).first()

        
        # La columna 'parte' en la BDD usa el enum; comparamos con la instancia del enum
        if partido.parte is None or partido.parte == PartePartido.SEGUNDO_TIEMPO:
            partido.hora_fin_segundo_tiempo = datetime.now().time()
        else:
            partido.hora_fin_segundo_tiempo_extra = datetime.now().time()
            

        if estadistica:
            estadistica.partidos_jugados = (estadistica.partidos_jugados or 0) + 1
        if estadistica_rival:
            estadistica_rival.partidos_jugados = (estadistica_rival.partidos_jugados or 0) + 1

        goles_local = partido.goles_local or 0
        goles_visitante = partido.goles_visitante or 0

        if estadistica and estadistica_rival:
            if goles_local > goles_visitante:
                estadistica.victorias += 1
                estadistica_rival.derrotas += 1
                estadistica.puntos += 3
            elif goles_local < goles_visitante:
                estadistica.derrotas += 1
                estadistica_rival.victorias += 1
                estadistica_rival.puntos += 3
            else:
                estadistica.empates += 1
                estadistica_rival.empates += 1
                estadistica.puntos += 1
                estadistica_rival.puntos += 1

            session.add_all([estadistica, estadistica_rival])
        
        # Actualizar partidos_jugados para los jugadores que participaron
        _actualizar_partidos_jugados_jugadores(session, partido)

        # Calcular y persistir minutos jugados por jugador
        _actualizar_minutos_jugados(session, partido)


    partido.estado = estado.value
    session.add(partido)
    session.commit()
    session.refresh(partido)
    return partido

@router.get("/{partido_id}/jugadores_en_cancha")
async def jugadores_en_cancha(partido_id: int, session: SessionDep):
    """Devuelve los jugadores actualmente en cancha para cada equipo del partido.

    Lógica dinámica (sin persistencia adicional):
    1. Se parte de los titulares de las formaciones asignadas al partido.
    2. Se recorren los eventos cronológicamente aplicando sustituciones y expulsiones.
       - Evento SUSTITUCION: jugador_id sale, jugador_asociado_id entra.
       - Evento TARJETA_ROJA: jugador_id sale.

    Respuesta incluye jugadores con nombre y posición.
    """
    partido = session.get(Partido, partido_id)
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    # Cargar formaciones (pueden ser None si no asignadas aún)
    from backend.modelos.Formaciones import FormacionJugador
    from backend.modelos.Jugadores import Jugador

    def cargar_titulares(formacion_id: int | None) -> set[int]:
        if not formacion_id:
            return set()
        rows = session.query(FormacionJugador).filter(
            FormacionJugador.formacion_id == formacion_id,
            FormacionJugador.titular == True
        ).all()
        return {r.jugador_id for r in rows}

    activos_local = cargar_titulares(partido.formacion_local_id)
    activos_visitante = cargar_titulares(partido.formacion_visitante_id)

    # Aplicar eventos ordenados
    eventos = session.query(Evento).filter(Evento.partido_id == partido_id).order_by(Evento.minuto.asc(), Evento.id_evento.asc()).all()
    amarillas_por_jugador: dict[int, int] = {}
    for e in eventos:
        tipo_val = e.tipo.value if hasattr(e.tipo, 'value') else str(e.tipo)
        # normalizar a enum para comparación robusta
        try:
            tipo_enum = e.tipo if isinstance(e.tipo, TipoEvento) else TipoEvento(tipo_val)
        except Exception:
            continue  # ignorar tipos desconocidos

        if tipo_enum == TipoEvento.SUSTITUCION:
            # jugador_id sale, jugador_asociado_id entra
            if e.jugador_id in activos_local:
                activos_local.discard(e.jugador_id)
                if e.jugador_asociado_id:
                    activos_local.add(e.jugador_asociado_id)
            elif e.jugador_id in activos_visitante:
                activos_visitante.discard(e.jugador_id)
                if e.jugador_asociado_id:
                    activos_visitante.add(e.jugador_asociado_id)
        elif tipo_enum == TipoEvento.TARJETA_ROJA:
            # expulsión: jugador sale
            if e.jugador_id in activos_local:
                activos_local.discard(e.jugador_id)
            elif e.jugador_id in activos_visitante:
                activos_visitante.discard(e.jugador_id)
        elif tipo_enum == TipoEvento.TARJETA_AMARILLA:
            # contar amarillas y aplicar expulsión por doble amarilla
            if e.jugador_id:
                amarillas_por_jugador[e.jugador_id] = amarillas_por_jugador.get(e.jugador_id, 0) + 1
                if amarillas_por_jugador[e.jugador_id] >= 2:
                    # remover de la cancha por doble amarilla
                    activos_local.discard(e.jugador_id)
                    activos_visitante.discard(e.jugador_id)
        # Otros tipos no modifican quién está en cancha
        

    # Cargar datos de jugadores activos
    todos_ids = list(activos_local | activos_visitante)
    if todos_ids:
        jugadores_rows = session.query(Jugador).filter(Jugador.jugador_id.in_(todos_ids)).all()
        jugadores_map = {j.jugador_id: j for j in jugadores_rows}
    else:
        jugadores_map = {}

    def serializar(ids: set[int]):
        datos = []
        for jid in ids:
            j = jugadores_map.get(jid)
            if not j:
                continue
            posicion_val = j.posicion.value if hasattr(j.posicion, 'value') else str(j.posicion)
            datos.append({
                "jugador_id": j.jugador_id,
                "nombre": f"{j.nombre} {j.apellido}",
                "posicion": posicion_val
            })
        return datos

    return {
        "partido_id": partido.partido_id,
        "estado": partido.estado,
        "local": serializar(activos_local),
        "visitante": serializar(activos_visitante),
        "total_local": len(activos_local),
        "total_visitante": len(activos_visitante)
    }

@router.get("/{partido_id}/minutos_en_cancha")
async def minutos_en_cancha(partido_id: int, session: SessionDep):
    """Calcula los minutos jugados por cada jugador en el partido.

    Reglas:
    - Titulares: desde minuto 0 hasta que salen por sustitución o expulsión/doble amarilla.
    - Suplentes que entran: desde su minuto de entrada hasta que salen o expulsión/doble amarilla.
    - Si el jugador nunca sale ni es expulsado, se cuenta hasta el último minuto registrado del partido (90 por defecto).
    """
    partido = session.get(Partido, partido_id)
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    from backend.modelos.Formaciones import FormacionJugador
    from backend.modelos.Jugadores import Jugador

    # Obtener titulares iniciales por equipo
    def cargar_ids(formacion_id: int | None, titulares: bool) -> set[int]:
        if not formacion_id:
            return set()
        rows = session.query(FormacionJugador).filter(
            FormacionJugador.formacion_id == formacion_id,
            FormacionJugador.titular == titulares
        ).all()
        return {r.jugador_id for r in rows}

    titulares_local = cargar_ids(partido.formacion_local_id, True)
    titulares_visitante = cargar_ids(partido.formacion_visitante_id, True)
    suplentes_local = cargar_ids(partido.formacion_local_id, False)
    suplentes_visitante = cargar_ids(partido.formacion_visitante_id, False)

    # Eventos ordenados
    eventos = session.query(Evento).filter(Evento.partido_id == partido_id).order_by(Evento.minuto.asc(), Evento.id_evento.asc()).all()

    # Mapas para calcular intervalos de juego
    entradas: dict[int, list[int]] = {}  # jugador -> lista de minutos de entrada
    salidas: dict[int, list[int]] = {}   # jugador -> lista de minutos de salida
    expulsado_en: dict[int, int] = {}    # jugador -> minuto de expulsión
    amarillas_count: dict[int, int] = {}

    # Inicializar titulares: entran en minuto 0
    for jid in titulares_local | titulares_visitante:
        entradas.setdefault(jid, []).append(0)

    # Recorrer eventos para armar entradas/salidas/expulsiones
    for e in eventos:
        tipo_val = e.tipo.value if hasattr(e.tipo, 'value') else str(e.tipo)
        try:
            tipo_enum = e.tipo if isinstance(e.tipo, TipoEvento) else TipoEvento(tipo_val)
        except Exception:
            continue

        if tipo_enum == TipoEvento.SUSTITUCION:
            # sale
            if e.jugador_id:
                salidas.setdefault(e.jugador_id, []).append(e.minuto or 0)
            # entra
            if e.jugador_asociado_id:
                entradas.setdefault(e.jugador_asociado_id, []).append(e.minuto or 0)

        elif tipo_enum == TipoEvento.TARJETA_ROJA:
            if e.jugador_id and e.minuto is not None:
                expulsado_en[e.jugador_id] = e.minuto
                # salida inmediata por expulsión
                salidas.setdefault(e.jugador_id, []).append(e.minuto)

        elif tipo_enum == TipoEvento.TARJETA_AMARILLA:
            if e.jugador_id:
                amarillas_count[e.jugador_id] = amarillas_count.get(e.jugador_id, 0) + 1
                if amarillas_count[e.jugador_id] >= 2 and e.minuto is not None:
                    expulsado_en[e.jugador_id] = e.minuto
                    salidas.setdefault(e.jugador_id, []).append(e.minuto)

    # Determinar minuto final (máximo de eventos, o 90 por defecto)
    ultimo_minuto_evento = max([ev.minuto or 0 for ev in eventos], default=0)
    minuto_final = max(ultimo_minuto_evento, 90)

    # Calcular minutos por jugador
    minutos_por_jugador: dict[int, int] = {}
    for jid, entradas_list in entradas.items():
        salidas_list = salidas.get(jid, [])
        # Emparejar entradas con salidas por orden
        for idx, min_in in enumerate(entradas_list):
            if idx < len(salidas_list):
                min_out = salidas_list[idx]
            else:
                # si no hay salida, usar minuto de expulsión si existe; si no, usar minuto_final
                min_out = expulsado_en.get(jid, minuto_final)
            delta = max((min_out or 0) - (min_in or 0), 0)
            minutos_por_jugador[jid] = minutos_por_jugador.get(jid, 0) + delta

    # Preparar respuesta con datos básicos del jugador
    jugadores_ids = list(minutos_por_jugador.keys())
    if jugadores_ids:
        jugadores_rows = session.query(Jugador).filter(Jugador.jugador_id.in_(jugadores_ids)).all()
        jugadores_map = {j.jugador_id: j for j in jugadores_rows}
    else:
        jugadores_map = {}

    resultado_local = []
    resultado_visitante = []
    for jid, minutos in minutos_por_jugador.items():
        j = jugadores_map.get(jid)
        if not j:
            continue
        posicion_val = j.posicion.value if hasattr(j.posicion, 'value') else str(j.posicion)
        item = {
            "jugador_id": j.jugador_id,
            "nombre": f"{j.nombre} {j.apellido}",
            "posicion": posicion_val,
            "minutos_jugados": minutos
        }
        # Clasificar por equipo usando formación/banca
        if jid in titulares_local or jid in suplentes_local:
            resultado_local.append(item)
        elif jid in titulares_visitante or jid in suplentes_visitante:
            resultado_visitante.append(item)

    return {
        "partido_id": partido.partido_id,
        "minuto_final": minuto_final,
        "local": resultado_local,
        "visitante": resultado_visitante,
        "total_local": len(resultado_local),
        "total_visitante": len(resultado_visitante)
    }

@router.get("/{partido_id}/suplentes_en_cancha")
async def suplentes_en_cancha(partido_id: int, session: SessionDep):
    """Devuelve los jugadores suplentes actualmente en banca para cada equipo del partido."""
    partido = session.get(Partido, partido_id)
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    from backend.modelos.Formaciones import FormacionJugador
    from backend.modelos.Jugadores import Jugador

    def cargar_suplentes(formacion_id: int | None) -> set[int]:
        if not formacion_id:
            return set()
        rows = session.query(FormacionJugador).filter(
            FormacionJugador.formacion_id == formacion_id,
            FormacionJugador.titular == False
        ).all()
        return {r.jugador_id for r in rows}

    # Suplentes iniciales por formación (banca inicial)
    suplentes_local = cargar_suplentes(partido.formacion_local_id)
    suplentes_visitante = cargar_suplentes(partido.formacion_visitante_id)

    # Construir mapa jugador -> lado (local/visitante) a partir de ambas formaciones
    jugador_a_lado: dict[int, str] = {}
    if partido.formacion_local_id:
        filas_local = session.query(FormacionJugador).filter(
            FormacionJugador.formacion_id == partido.formacion_local_id
        ).all()
        for fj in filas_local:
            jugador_a_lado[fj.jugador_id] = "local"
    if partido.formacion_visitante_id:
        filas_visit = session.query(FormacionJugador).filter(
            FormacionJugador.formacion_id == partido.formacion_visitante_id
        ).all()
        for fj in filas_visit:
            jugador_a_lado[fj.jugador_id] = "visitante"

    # Aplicar eventos para actualizar la banca:
    # - En SUSTITUCION: el que entra deja de ser suplente; el que sale pasa a la banca
    # - En TARJETA_ROJA: no se agrega a la banca (queda expulsado)
    eventos = (
        session
        .query(Evento)
        .filter(Evento.partido_id == partido_id)
        .order_by(Evento.minuto.asc(), Evento.id_evento.asc())
        .all()
    )

    for e in eventos:
        tipo_val = e.tipo.value if hasattr(e.tipo, 'value') else str(e.tipo)
        try:
            tipo_enum = e.tipo if isinstance(e.tipo, TipoEvento) else TipoEvento(tipo_val)
        except Exception:
            continue

        if tipo_enum == TipoEvento.SUSTITUCION:
            # Entrante: siempre debe salir de la banca si estuviera
            if e.jugador_asociado_id:
                suplentes_local.discard(e.jugador_asociado_id)
                suplentes_visitante.discard(e.jugador_asociado_id)

    # Cargar datos de jugadores suplentes
    todos_ids = list(suplentes_local | suplentes_visitante)
    if todos_ids:
        jugadores_rows = session.query(Jugador).filter(Jugador.jugador_id.in_(todos_ids)).all()
        jugadores_map = {j.jugador_id: j for j in jugadores_rows}
    else:
        jugadores_map = {}

    def serializar(ids: set[int]):
        datos = []
        for jid in ids:
            j = jugadores_map.get(jid)
            if not j:
                continue
            posicion_val = j.posicion.value if hasattr(j.posicion, 'value') else str(j.posicion)
            datos.append({
                "jugador_id": j.jugador_id,
                "nombre": f"{j.nombre} {j.apellido}",
                "posicion": posicion_val
            })
        return datos

    return {
        "partido_id": partido.partido_id,
        "estado": partido.estado,
        "local": serializar(suplentes_local),
        "visitante": serializar(suplentes_visitante),
        "total_local": len(suplentes_local),
        "total_visitante": len(suplentes_visitante)
    }

@router.patch("/iniciar_tiempo/{partido_id}", response_model=Partido)
async def iniciar_tiempo_partido(partido_id: int, session: SessionDep):
    """Registra únicamente las marcas de inicio correspondientes a la parte actual.
    No cambia la 'parte' del partido; solo escribe la hora de inicio si aún no existe.
    """
    partido = session.get(Partido, partido_id)
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    if str(partido.estado).replace(' ', '_').upper() != EstadoPartidos.EN_CURSO.name:
        raise HTTPException(status_code=400, detail="Solo se pueden iniciar tiempos cuando el partido está EN_CURSO")

    now_time = datetime.now().time()

    # Determinar qué campo de inicio corresponde según la parte actual
    if partido.parte is None:
        if partido.hora_inicio:
            raise HTTPException(status_code=400, detail="La hora de inicio del partido ya está registrada")
        partido.hora_inicio = now_time
    elif partido.parte == PartePartido.SEGUNDO_TIEMPO:
        if partido.hora_inicio_segundo_tiempo:
            raise HTTPException(status_code=400, detail="La hora de inicio del segundo tiempo ya está registrada")
        partido.hora_inicio_segundo_tiempo = now_time
    elif partido.parte == PartePartido.PRIMER_TIEMPO_EXTRA:
        if partido.hora_inicio_primer_tiempo_extra:
            raise HTTPException(status_code=400, detail="La hora de inicio del primer tiempo extra ya está registrada")
        partido.hora_inicio_primer_tiempo_extra = now_time
    elif partido.parte == PartePartido.SEGUNDO_TIEMPO_EXTRA:
        if partido.hora_inicio_segundo_tiempo_extra:
            raise HTTPException(status_code=400, detail="La hora de inicio del segundo tiempo extra ya está registrada")
        partido.hora_inicio_segundo_tiempo_extra = now_time
    else:
        raise HTTPException(status_code=400, detail="No corresponde iniciar un tiempo para la parte actual")

    session.add(partido)
    session.commit()
    session.refresh(partido)
    return partido


@router.patch("/finalizar_tiempo/{partido_id}", response_model=Partido)
async def finalizar_tiempo_partido(partido_id: int, session: SessionDep):
    """Registra únicamente las marcas de fin correspondientes a la parte actual.
    No cambia la 'parte' del partido; solo escribe la hora de finalización si aún no existe.
    """
    partido = session.get(Partido, partido_id)
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    if str(partido.estado).replace(' ', '_').upper() != EstadoPartidos.EN_CURSO.name:
        raise HTTPException(status_code=400, detail="Solo se pueden finalizar tiempos cuando el partido está EN_CURSO")

    now_time = datetime.now().time()

    # Mapear la parte actual a la marca de fin correspondiente
    if partido.parte is None:
        # Si no hay parte definida, considerar que debemos finalizar el primer tiempo
        if partido.hora_fin_primer_tiempo:
            raise HTTPException(status_code=400, detail="La hora de fin del primer tiempo ya está registrada")
        partido.hora_fin_primer_tiempo = now_time
    elif partido.parte == PartePartido.PRIMER_TIEMPO:
        if partido.hora_fin_primer_tiempo:
            raise HTTPException(status_code=400, detail="La hora de fin del primer tiempo ya está registrada")
        partido.hora_fin_primer_tiempo = now_time
    elif partido.parte == PartePartido.SEGUNDO_TIEMPO:
        if partido.hora_fin_segundo_tiempo:
            raise HTTPException(status_code=400, detail="La hora de fin del segundo tiempo ya está registrada")
        partido.hora_fin_segundo_tiempo = now_time
    elif partido.parte == PartePartido.PRIMER_TIEMPO_EXTRA:
        if partido.hora_fin_primer_tiempo_extra:
            raise HTTPException(status_code=400, detail="La hora de fin del primer tiempo extra ya está registrada")
        partido.hora_fin_primer_tiempo_extra = now_time
    elif partido.parte == PartePartido.SEGUNDO_TIEMPO_EXTRA:
        if partido.hora_fin_segundo_tiempo_extra:
            raise HTTPException(status_code=400, detail="La hora de fin del segundo tiempo extra ya está registrada")
        partido.hora_fin_segundo_tiempo_extra = now_time
    else:
        raise HTTPException(status_code=400, detail="No corresponde finalizar un tiempo para la parte actual")

    session.add(partido)
    session.commit()
    session.refresh(partido)
    return partido


@router.patch("/actualizar_parte/{partido_id}", response_model=Partido)
async def actualizar_parte_partido(partido_id: int, session: SessionDep):
    partido = session.get(Partido, partido_id)
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")
    # Aceptar distintos formatos de representación en DB (p.ej. 'EN_CURSO' o 'en curso').
    # Normalizamos a mayúsculas y comparamos con el nombre del enum.
    if str(partido.estado).replace(' ', '_').upper() != EstadoPartidos.EN_CURSO.name:
        raise HTTPException(status_code=400, detail="Solo se puede actualizar la parte de un partido que está EN_CURSO")
    # Asignar el siguiente valor usando el nombre del enum (coincide con el tipo enum en Postgres)
    if partido.parte is None:
        partido.parte = PartePartido.PRIMER_TIEMPO
        partido.hora_inicio = datetime.now().time()
    elif partido.parte == PartePartido.PRIMER_TIEMPO:
        partido.parte = PartePartido.SEGUNDO_TIEMPO
        partido.hora_fin_primer_tiempo = datetime.now().time()
    elif partido.parte == PartePartido.SEGUNDO_TIEMPO:
        partido.parte = PartePartido.PRIMER_TIEMPO_EXTRA
        partido.hora_inicio_primer_tiempo_extra = datetime.now().time()
    elif partido.parte == PartePartido.PRIMER_TIEMPO_EXTRA:
        partido.parte = PartePartido.SEGUNDO_TIEMPO_EXTRA
        partido.hora_fin_primer_tiempo_extra = datetime.now().time()
    elif partido.parte == PartePartido.SEGUNDO_TIEMPO_EXTRA:
        partido.parte = PartePartido.PENALTIS
        partido.hora_inicio_segundo_tiempo_extra = datetime.now().time()

    session.add(partido)
    session.commit()
    session.refresh(partido)
    return partido

@router.post("/{partido_id}/formacion/{formacion_id}", response_model=Partido)
async def asignar_formacion_partido(partido_id: int, formacion_id: int, session: SessionDep):
    """Asignar una formación (alineación) al partido, detectando si pertenece al local o visitante.

    Reglas:
    - La formación debe existir.
    - El partido debe existir.
    - El equipo dueño de la formación debe ser el equipo local o visitante del partido.
    - Se asigna automáticamente al campo correspondiente (local/visitante).
    """
    partido = session.get(Partido, partido_id)
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    formacion = session.get(Formacion, formacion_id)
    if not formacion:
        raise HTTPException(status_code=404, detail="Formación no encontrada")

    # Determinar si la formación pertenece al local o al visitante
    if formacion.equipo_id == partido.equipo_local_id:
        partido.formacion_local_id = formacion.formacion_id
    elif formacion.equipo_id == partido.equipo_visitante_id:
        partido.formacion_visitante_id = formacion.formacion_id
    else:
        raise HTTPException(status_code=400, detail="La formación no pertenece a ninguno de los dos equipos del partido")

    session.add(partido)
    session.commit()
    session.refresh(partido)
    return partido


@router.get("/id/{partido_id}", response_model=PartidoDTO)
async def obtener_partido_por_id(partido_id: int, session: SessionDep):
    from backend.modelos.Equipos import Equipo
    equipo_local = aliased(Equipo)
    equipo_visitante = aliased(Equipo)

    row = (
        session.query(Partido, equipo_local, equipo_visitante)
        .join(equipo_local, Partido.equipo_local_id == equipo_local.equipo_id)
        .join(equipo_visitante, Partido.equipo_visitante_id == equipo_visitante.equipo_id)
        .filter(Partido.partido_id == partido_id)
        .first()
    )

    if not row:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    partido, el, ev = row
    dto = PartidoDTO(
        partido_id=partido.partido_id,
        equipo_local_id=partido.equipo_local_id,
        equipo_local_nombre=getattr(el, "nombre", "") if el else "",
        equipo_local_logo=getattr(el, "logo", None) if el else None,
        equipo_visitante_id=partido.equipo_visitante_id,
        equipo_visitante_nombre=getattr(ev, "nombre", "") if ev else "",
        equipo_visitante_logo=getattr(ev, "logo", None) if ev else None,
        fecha=partido.fecha,
        hora=partido.hora.strftime("%H:%M") if partido.hora else None,
        hora_inicio=partido.hora_inicio.strftime("%H:%M:%S") if partido.hora_inicio else None,
        hora_fin_primer_tiempo=partido.hora_fin_primer_tiempo.strftime("%H:%M:%S") if partido.hora_fin_primer_tiempo else None,
        hora_inicio_segundo_tiempo=partido.hora_inicio_segundo_tiempo.strftime("%H:%M:%S") if partido.hora_inicio_segundo_tiempo else None,
        hora_fin_segundo_tiempo=partido.hora_fin_segundo_tiempo.strftime("%H:%M:%S") if partido.hora_fin_segundo_tiempo else None,
        parte=partido.parte.name if partido.parte else None,
        lugar=partido.estadio,
        estado=partido.estado.name if hasattr(partido.estado, 'name') else str(partido.estado),
        goles_local=partido.goles_local,
        goles_visitante=partido.goles_visitante,
    )

    return dto

@router.delete("/{partido_id}", response_model=Partido)
async def eliminar_partido(partido_id: int, session: SessionDep):
    partido = session.get(Partido, partido_id)
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    partido.estado = "CANCELADO"
    session.add(partido)
    session.commit()
    session.refresh(partido)