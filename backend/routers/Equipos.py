from typing import List
from fastapi import APIRouter, HTTPException, Form, UploadFile, File
from backend.modelos.Equipos import Equipo, EquipoCrear, EquipoActualizar
from backend.db import SessionDep
from backend.utils.bucket import upload_file

router = APIRouter(prefix="/equipos", tags=["equipos"])

@router.post("/", response_model=Equipo)
async def crear_equipo(session: SessionDep,
                       nombre: str = Form(...),
                       ciudad: str = Form(...),
                       estadio: str = Form(...),
                       anio_fundacion: int = Form(...),
                       titulos: int = Form(0),
                       file: UploadFile = File(None)
                       ):
    if file:
        logo = await upload_file(file)
    else:
        logo = {"file_name": None}

    new_equipo = EquipoCrear(
        nombre=nombre,
        ciudad=ciudad,
        estadio=estadio,
        anio_fundacion=anio_fundacion,
        titulos=titulos or 0,
        logo=logo["file_name"]
    )
    equipo = Equipo.model_validate(new_equipo)

    session.add(equipo)
    session.commit()
    session.refresh(equipo)

    return equipo

@router.get("/", response_model=List[Equipo])
async def obtener_equipos(session: SessionDep):
    return session.query(Equipo).filter(Equipo.activo == True).all()

@router.get("/{equipo_id}", response_model=Equipo)
async def obtener_equipo(equipo_id: int, session: SessionDep):
    equipo = session.get(Equipo, equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="El equipo no existe")
    return equipo

@router.delete("/{equipo_id}", response_model=Equipo)
async def eliminar_equipo(equipo_id: int, session: SessionDep):
    equipo = session.get(Equipo, equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="El equipo no existe")

    equipo.activo = False
    session.commit()
    return equipo

@router.patch("/{equipo_id}", response_model=Equipo)
async def actualizar_equipo(equipo_id: int,
                            session: SessionDep,
                            nombre: str = Form(None),
                            ciudad: str = Form(None),
                            estadio: str = Form(None),
                            anio_fundacion: int = Form(None),
                            titulos: int = Form(None),
                            file: UploadFile = File(None)
                            ):
    equipo = session.get(Equipo, equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="El equipo no existe")

    if file:
        logo = await upload_file(file)
        equipo.logo = logo["file_name"]

    if nombre is not None:
        equipo.nombre = nombre
    if ciudad is not None:
        equipo.ciudad = ciudad
    if estadio is not None:
        equipo.estadio = estadio
    if anio_fundacion is not None:
        equipo.anio_fundacion = anio_fundacion
    if titulos is not None:
        equipo.titulos = titulos
    session.commit()
    session.refresh(equipo)
    return equipo