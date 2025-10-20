from typing import Optional
from datetime import date
from sqlmodel import SQLModel, Field
from Backend.utils.enumeraciones import EstadoTemporada

class TemporadaBase(SQLModel):
    nombre: str = Field(nullable=False, description="Nombre de la temporada (e.g., '2023/2024')")
    fecha_inicio: date = Field(nullable=False, description="Fecha de inicio de la temporada")
    fecha_fin: date = Field(nullable=False, description="Fecha de fin de la temporada")

class Temporada(TemporadaBase , table=True):
    temporada_id: Optional[int] = Field(default=None, primary_key=True)
    estado: EstadoTemporada = Field(default="EN_CURSO", description="Indica si la temporada está activa")

class TemporadaCrear(TemporadaBase):
    pass

class TemporadaActualizar(SQLModel):
    nombre: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None

