from enum import Enum

class TipoEvento(Enum):
    GOL = "gol"
    SUSTITUCION = "sustitucion"
    TARJETA_AMARILLA = "tarjeta_amarilla"
    TARJETA_ROJA = "tarjeta_roja"
    PENAL = "penal"
    PENAL_FALLADO = "penal_fallado"
    TIRO = "tiro"
    TIRO_A_PUERTA = "tiro_a_puerta"
    ENTRADA = "entrada"
    INTERCEPCION = "intercepcion"
    GOL_EN_CONTRA = "gol_en_contra"

class EstadoPartidos(Enum):
    PROGRAMADO = "programado"
    EN_CURSO = "en curso"
    FINALIZADO = "finalizado"
    SUSPENDIDO = "suspendido"
    CANCELADO = "cancelado"

class EstadoTemporada(Enum):
    PROGRAMADO = "programado"
    EN_CURSO = "en curso"
    FINALIZADO = "finalizado"

class PosicionJugador(Enum):
    PORTERO = "portero"
    DEFENSOR = "defensor"
    MEDIOCAMPISTA = "mediocampista"
    DELANTERO = "delantero"


class PartePartido(Enum):
    PRIMER_TIEMPO = "primer tiempo"
    SEGUNDO_TIEMPO = "segundo tiempo"
    PRIMER_TIEMPO_EXTRA = "primer tiempo extra"
    SEGUNDO_TIEMPO_EXTRA = "segundo tiempo extra"
    PENALTIS = "penaltis"