from fastapi import APIRouter, HTTPException, Form, UploadFile, File
from datetime import date
from backend.modelos.Equipos import Equipo
from backend.modelos.Jugadores import Jugador, JugadorCrear, JugadorActualizar
from backend.utils.enumeraciones import PosicionJugador
from backend.utils.bucket import upload_file
from backend.db import SessionDep


router = APIRouter(prefix="/jugadores", tags=["jugadores"])

@router.post("/", response_model=Jugador)
async def crear_jugador(session: SessionDep,
                        nombre: str = Form(...),
                        apellido: str = Form(...),
                        fecha_nacimiento: date = Form(...),
                        posicion: PosicionJugador = Form(...),
                        nacionalidad: str = Form(...),
                        numero_camiseta: int = Form(...),
                        equipo_id: int = Form(...),
                        foto: UploadFile = File(None)
                        ):
    foto_name = None
    if foto:
        foto_name = await upload_file(foto)

    nombremayuscula = nombre.title() 
    apellidomayuscula = apellido.title()


    existing_jugador = session.query(Jugador).filter_by(nombre=nombremayuscula, apellido=apellidomayuscula, equipo_id=equipo_id).first()
    if existing_jugador:
        raise HTTPException(status_code=400, detail="El jugador ya existe")

    new_jugador = JugadorCrear(
        nombre=nombremayuscula,
        apellido=apellidomayuscula,
        fecha_nacimiento=fecha_nacimiento,
        posicion=posicion,
        nacionalidad=nacionalidad,
        numero_camiseta=numero_camiseta,
        equipo_id=equipo_id,
        foto=foto_name
    )
    jugador = Jugador.model_validate(new_jugador)

    if jugador.equipo_id:
        equipo = session.get(Equipo, jugador.equipo_id)
        if not equipo:
            raise HTTPException(status_code=404, detail="El equipo no existe")

    session.add(jugador)
    session.commit()
    session.refresh(jugador)

    return jugador

@router.get("/", response_model=list[Jugador])
async def obtener_jugadores(session: SessionDep):
    jugadores = session.query(Jugador).all()
    if not jugadores:
        raise HTTPException(status_code=404, detail="No se encontraron jugadores")
    return jugadores

@router.get("/{jugador_id}", response_model=Jugador)
async def obtener_jugador(jugador_id: int, session: SessionDep):
    jugador = session.get(Jugador, jugador_id)
    if not jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    return jugador

@router.get("/equipo/{equipo_id}")
async def obtener_jugadores_equipo(equipo_id: int, session: SessionDep):
    jugadores = session.query(Jugador).filter(Jugador.equipo_id == equipo_id).all()
    if not jugadores:
        return []
    
    # Normalizar URLs de fotos para evitar problemas con rutas
    result = []
    for j in jugadores:
        # Limpiar URL de foto si está corrupta
        foto = str(j.foto) if j.foto else None
        if foto and '/static/img/http' in foto:
            foto = foto.replace('/static/img/', '')
        
        jugador_dict = {
            "jugador_id": j.jugador_id,
            "nombre": j.nombre,
            "apellido": j.apellido,
            "fecha_nacimiento": j.fecha_nacimiento,
            "posicion": j.posicion,
            "nacionalidad": j.nacionalidad,
            "numero_camiseta": j.numero_camiseta,
            "equipo_id": j.equipo_id,
            "foto": foto
        }
        result.append(jugador_dict)
    
    return result

@router.get("/{Posicion}/", response_model=list[Jugador])
async def obtener_jugador_posicion(Posicion: PosicionJugador , session: SessionDep):
    jugador = session.query(Jugador).filter(Jugador.posicion == Posicion).all()
    if not jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    return jugador

@router.patch("/{jugador_id}", response_model=Jugador)
async def actualizar_jugador(jugador_id: int,
                            session: SessionDep,
                            nombre: str = Form(None),
                            apellido: str = Form(None),
                            fecha_nacimiento: date = Form(None),
                            posicion: PosicionJugador = Form(None),
                            nacionalidad: str = Form(None),
                            numero_camiseta: int = Form(None),
                            equipo_id: int = Form(None),
                            foto: UploadFile = File(None)
                            ):
    jugador = session.get(Jugador, jugador_id)
    if not jugador:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    if foto:
        jugador.foto = await upload_file(foto)

    nombremayuscula = nombre.title() 
    apellidomayuscula = apellido.title()

    if nombre is not None:
        jugador.nombre = nombremayuscula
    if apellido is not None:
        jugador.apellido = apellidomayuscula
    if fecha_nacimiento is not None:
        jugador.fecha_nacimiento = fecha_nacimiento
    if posicion is not None:
        jugador.posicion = posicion
    if nacionalidad is not None:
        jugador.nacionalidad = nacionalidad
    if numero_camiseta is not None:
        jugador.numero_camiseta = numero_camiseta
    if equipo_id is not None:
        equipo = session.get(Equipo, equipo_id)
        if not equipo:
            raise HTTPException(status_code=404, detail="El equipo no existe")
        jugador.equipo_id = equipo_id

    session.add(jugador)
    session.commit()
    session.refresh(jugador)
    return jugador
