from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship


class EquipoBase(SQLModel):
    nombre: str = Field(nullable=False, description="nombre del equipo")
    ciudad: str = Field(nullable=False, description="ciudad del equipo")
    estadio: str = Field(nullable=False, description="estadio del equipo")
    anio_fundacion: int = Field(nullable=False, description="año de fundación del equipo")
    titulos: Optional[int] = Field(default=0, description="titulos del equipo")
    logo: Optional[str] = Field(default=None, description="URL del logo del equipo")

class Equipo(EquipoBase, table=True):
    equipo_id: int | None = Field(default=None, primary_key=True)
    estadisticas: list["Estadisticas_E"] = Relationship(back_populates="equipo")
    activo: bool = Field(default=True, description="Indica si el equipo está activo")

class EquipoCrear(EquipoBase):
    pass

class EquipoActualizar(SQLModel):
    nombre: Optional[str] = None
    ciudad: Optional[str] = None
    estadio: Optional[str] = None
    anio_fundacion: Optional[int] = None
    titulos: Optional[int] = None
    logo: Optional[str] = None

from ..modelos.Estadisticas_Equipos import Estadisticas_E