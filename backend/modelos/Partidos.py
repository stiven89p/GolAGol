from typing import Optional
from datetime import date, time
from sqlmodel import SQLModel, Field
from backend.utils.enumeraciones import PartePartido

class PartidoBase(SQLModel):
    fecha: date = Field(nullable=False, description="Fecha del partido")
    hora: time = Field(nullable=False, description="Hora del partido (e.g., 18:30:00)")
    jornada: int = Field(nullable=False, description="Jornada del partido")
    estadio: str = Field(nullable=False, description="Estadio del partido")
    temporada_id: int = Field(foreign_key="temporada.temporada_id", nullable=False, description="ID de la temporada")
    equipo_local_id: int = Field(foreign_key="equipo.equipo_id", nullable=False, description="ID del equipo local")
    equipo_visitante_id: int = Field(foreign_key="equipo.equipo_id", nullable=False, description="ID del equipo visitante")
    parte: Optional[PartePartido] = Field(default=None, description="en que secion del partido esta primer segundo tiempo")
    hora_inicio: Optional[time] = Field(default=None, description="Hora de inicio del partido")
    hora_fin_primer_tiempo: Optional[time] = Field(default=None, description="Hora de finalización del primer tiempo")
    hora_inicio_segundo_tiempo: Optional[time] = Field(default=None, description="Hora de inicio del segundo tiempo")
    hora_fin_segundo_tiempo: Optional[time] = Field(default=None, description="Hora de finalización del segundo tiempo")
    hora_inicio_primer_tiempo_extra: Optional[time] = Field(default=None, description="Hora de inicio del primer tiempo extra")
    hora_fin_primer_tiempo_extra: Optional[time] = Field(default=None, description="Hora de finalización del primer tiempo extra")
    hora_inicio_segundo_tiempo_extra: Optional[time] = Field(default=None, description="Hora de inicio del segundo tiempo extra")
    hora_fin_segundo_tiempo_extra: Optional[time] = Field(default=None, description="Hora de finalización del segundo tiempo extra")



class Partido(PartidoBase, table=True):
    partido_id: Optional[int] = Field(default=None, primary_key=True)
    goles_local: Optional[int] = Field(default=0, nullable=False, description="Goles del equipo local")
    goles_visitante: Optional[int] = Field(default=0, nullable=False, description="Goles del equipo visitante")
    estado: str = Field(default="PROGRAMADO", nullable=False, description="Estado del partido (pendiente, en curso, finalizado)")
    formacion_local_id: Optional[int] = Field(default=None, foreign_key="formacion.formacion_id", description="Formación asignada al equipo local")
    formacion_visitante_id: Optional[int] = Field(default=None, foreign_key="formacion.formacion_id", description="Formación asignada al equipo visitante")


class PartidoCrear(PartidoBase):
    pass


class PartidoActualizar(SQLModel):
    fecha: Optional[date] = None
    jornada: Optional[int] = None
    estadio: Optional[str] = None
    equipo_local_id: Optional[int] = None
    equipo_visitante_id: Optional[int] = None

class PartidoDTO(SQLModel):
    partido_id: int = Field(..., description="ID del partido")
    equipo_local_nombre: str = Field(..., description="Nombre del equipo local")
    equipo_local_logo: Optional[str] = Field(None, description="URL o ruta del logo del equipo local")
    equipo_visitante_nombre: str = Field(..., description="Nombre del equipo visitante")
    equipo_visitante_logo: Optional[str] = Field(None, description="URL o ruta del logo del equipo visitante")
    fecha: date = Field(..., description="Fecha del partido (YYYY-MM-DD)")
    hora: Optional[str] = Field(None, description="Hora del partido (HH:MM)")
    hora_inicio: Optional[str] = Field(None, description="Hora de inicio del partido (HH:MM:SS)")
    hora_fin_primer_tiempo: Optional[str] = Field(None, description="Hora de fin del primer tiempo (HH:MM:SS)")
    hora_inicio_segundo_tiempo: Optional[str] = Field(None, description="Hora de inicio del segundo tiempo (HH:MM:SS)")
    hora_fin_segundo_tiempo: Optional[str] = Field(None, description="Hora de fin del segundo tiempo (HH:MM:SS)")
    parte: Optional[str] = Field(None, description="Parte actual del partido (PRIMER_TIEMPO, SEGUNDO_TIEMPO, ...)")
    lugar: Optional[str] = Field(None, description="Lugar o estadio del partido")
    estado: str = Field(..., description="Estado del partido (PROGRAMADO, EN_CURSO, FINALIZADO, etc.)")
    goles_local: Optional[int] = Field(0, description="Goles del equipo local")
    goles_visitante: Optional[int] = Field(0, description="Goles del equipo visitante")
    formacion_local_id: Optional[int] = Field(None, description="ID de la formación del equipo local si asignada")
    formacion_visitante_id: Optional[int] = Field(None, description="ID de la formación del equipo visitante si asignada")
