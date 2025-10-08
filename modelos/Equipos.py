from typing import Optional
from sqlmodel import SQLModel, Field, Relationship

class EquipoBase(SQLModel):
    nombre: str = Field(nullable=False, description="nombre del equipo")
    ciudad: str = Field(nullable=False, description="ciudad del equipo")
    estadio: str = Field(nullable=False, description="estadio del equipo")
    anio_fundacion: int = Field(nullable=False, description="año de fundación del equipo")


class Equipo(EquipoBase, table=True):
    id_equipo: int | None = Field(default=None, primary_key=True)

class EquipoCrear(EquipoBase):
    pass

class EquipoActualizar(SQLModel):
    nombre: Optional[str] = None
    ciudad: Optional[str] = None
    estadio: Optional[str] = None
    anio_fundacion: Optional[int] = None
