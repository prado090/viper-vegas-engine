# backend/schemas.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class SpinRequest(BaseModel):
    numero: int = Field(ge=0, le=36)
    modo: str = Field(default="conservador")  # conservador | agressivo
    source: str = Field(default="manual")     # manual | auto


class SignalResponse(BaseModel):
    time: str
    source: str
    numero: int
    cor: str
    terminal: int
    status: str
    padroes: List[str] = []
    score_terminal: float = 0.0
    score_padrao: float = 0.0
    score_combinado: float = 0.0
    numeros_analise: List[int] = []  # apenas “conjunto de observação”
    mensagem: Optional[str] = None
    debug: Dict[str, Any] = {}
