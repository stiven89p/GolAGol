from typing import Optional
from datetime import date
from sqlmodel import SQLModel, Field
from Backend.utils.enumeraciones import PosicionJugador


class JugadorBase(SQLModel):
    nombre: str = Field(nullable=False, description="Nombre del jugador")
    apellido: str = Field(nullable=False, description="Apellido del jugador")
    fecha_nacimiento: date = Field(nullable=False, description="Fecha de nacimiento del jugador")
    posicion: PosicionJugador = Field(nullable=False, description="Posición del jugador")
    nacionalidad: str = Field(nullable=False, description="Nacionalidad del jugador")
    equipo_id: int = Field(foreign_key="equipo.equipo_id", nullable=False, description="ID del equipo al que pertenece el jugador")

class Jugador(JugadorBase, table=True):
    jugador_id: int | None = Field(default=None, primary_key=True)

class JugadorCrear(JugadorBase):
    pass

class JugadorActualizar(SQLModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    posicion: Optional[str] = None
    nacionalidad: Optional[str] = None
    equipo_id: Optional[int] = None