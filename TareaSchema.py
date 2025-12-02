from pydantic import BaseModel, Field, validator
from datetime import date
from enum import Enum


class StatusEnum(str, Enum):
    pendiente = "pendiente"
    en_progreso = "en_progreso"
    completado = "completado"


class TareaSchema(BaseModel):
    titulo: str = Field(..., min_length=1)
    descripcion: str = Field(..., min_length=1)
    status: StatusEnum = Field(default=StatusEnum.pendiente)
    fecha: date
    id: int | None = None   #

    @validator("fecha")
    def fecha_no_pasada(cls, v):
        if v < date.today():
            raise ValueError("La fecha no puede ser menor a la fecha actual.")
        return v
