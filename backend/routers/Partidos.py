from fastapi import APIRouter, HTTPException, Form
from sqlalchemy.orm import aliased
from datetime import date, datetime, time
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

@router.get("/", response_model=list[Partido])
async def obtener_partidos(session: SessionDep):
    partidos = session.query(Partido).all()
    return partidos 

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
            estado=partido.estado,
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
        dto = PartidoDTO(
            partido_id=partido.partido_id,
            equipo_local_nombre=getattr(el, "nombre", "") if el else "",
            equipo_local_logo=getattr(el, "logo", None) if el else None,
            equipo_visitante_nombre=getattr(ev, "nombre", "") if ev else "",
            equipo_visitante_logo=getattr(ev, "logo", None) if ev else None,
            fecha=partido.fecha,
            hora=partido.hora.strftime("%H:%M") if partido.hora else None,
            lugar=partido.estadio,
            estado=partido.estado,
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
    

    # Solo actualizar estadísticas y PJ cuando el partido pasa a FINALIZADO
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

        if partido.goles_local > partido.goles_visitante:
            estadistica.victorias += 1
            estadistica_rival.derrotas += 1
            estadistica.puntos += 3

        elif partido.goles_local < partido.goles_visitante:
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


    partido.estado = estado
    session.add(partido)
    session.commit()
    session.refresh(partido)
    return partido

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
        equipo_local_nombre=getattr(el, "nombre", "") if el else "",
        equipo_local_logo=getattr(el, "logo", None) if el else None,
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
        estado=partido.estado,
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