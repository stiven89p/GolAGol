from typing import List
from fastapi import APIRouter, HTTPException, Form, UploadFile, File
from backend.modelos.Equipos import Equipo, EquipoCrear, EquipoActualizar
from backend.db import SessionDep
from backend.utils.bucket import upload_file
from sqlmodel import select

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
        logo_url = await upload_file(file)
    else:
        logo_url = None

        
    nombremayuscula = nombre.title() 

    existing_equipo = session.query(Equipo).filter_by(nombre=nombremayuscula).first()
    if existing_equipo:
        raise HTTPException(status_code=400, detail="El equipo ya existe")

    

    new_equipo = EquipoCrear(
        nombre=nombremayuscula,
        ciudad=ciudad,
        estadio=estadio,
        anio_fundacion=anio_fundacion,
        titulos=titulos or 0,
        logo=logo_url
    )
    equipo = Equipo.model_validate(new_equipo)

    session.add(equipo)
    session.commit()
    session.refresh(equipo)

    return equipo

@router.get("/")
async def obtener_equipos(session: SessionDep):
    equipos = session.exec(select(Equipo).where(Equipo.activo == True)).all()
    
    # Normalizar URLs de logos para evitar problemas con rutas
    result = []
    for e in equipos:
        # Limpiar URL corrupta si existe
        logo = str(e.logo) if e.logo else None
        if logo and '/static/img/http' in logo:
            # Remover el prefijo corrupto
            logo = logo.replace('/static/img/', '')
        
        equipo_dict = {
            "equipo_id": e.equipo_id,
            "nombre": e.nombre,
            "ciudad": e.ciudad,
            "estadio": e.estadio,
            "anio_fundacion": e.anio_fundacion,
            "titulos": e.titulos,
            "activo": e.activo,
            "logo": logo
        }
        result.append(equipo_dict)
    
    return result

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
                            activo: bool = Form(None),
                            remove_logo: bool = Form(False),
                            file: UploadFile = File(None)
                            ):
    equipo = session.get(Equipo, equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="El equipo no existe")
    # Solo transformar a título si se proporciona un nombre
    nombremayuscula = nombre.title() if nombre is not None else None
    

    if file:
        logo_url = await upload_file(file)
        equipo.logo = logo_url
    elif remove_logo:
        equipo.logo = None

    if nombre is not None:
        equipo.nombre = nombremayuscula
    if ciudad is not None:
        equipo.ciudad = ciudad
    if estadio is not None:
        equipo.estadio = estadio
    if anio_fundacion is not None:
        equipo.anio_fundacion = anio_fundacion
    if titulos is not None:
        equipo.titulos = titulos
    if activo is not None:
        equipo.activo = activo
    session.commit()
    session.refresh(equipo)
    return equipo