from pydantic import BaseModel
from typing import List, Optional

class SignalResponse(BaseModel):
    status: str
    terminal: Optional[int] = None
    gale: int = 0
    numeros: List[int] = []
    forca: float = 0.0
    mensagem: str
