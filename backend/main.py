# backend/main.py
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Literal, Optional

from backend.logic import (
    gerar_sinal,
    get_historico,
    get_stats,
    get_score_terminal,
    get_score_padrao,
    get_score_terminal_padrao,
    heatmap_terminal,
    heatmap_roda_eu,
    resetar_estado,
)

Modo = Literal["conservador", "normal", "agressivo"]


class SpinRequest(BaseModel):
    numero: int = Field(..., ge=0, le=36)
    modo: Modo = "agressivo"
    source: Optional[str] = "manual"


app = FastAPI(title="Viper Vegas Engine", version="1.0.0")


@app.get("/")
def root():
    return {"status": "online", "engine": "Viper Vegas"}


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/reset")
def reset():
    resetar_estado()
    return {"ok": True}


@app.post("/spin")
def spin(req: SpinRequest):
    return gerar_sinal(req.numero, req.modo, source=req.source or "manual")


@app.get("/stats")
def api_stats():
    return get_stats()


@app.get("/historico")
def api_historico():
    return get_historico()


@app.get("/scores/terminal")
def api_scores_terminal():
    return get_score_terminal()


@app.get("/scores/padrao")
def api_scores_padrao():
    return get_score_padrao()


@app.get("/scores/terminal-padrao")
def api_scores_terminal_padrao():
    return get_score_terminal_padrao()


@app.get("/heatmap/terminal")
def api_heatmap_terminal(window: int = 120):
    return heatmap_terminal(window=window)


@app.get("/heatmap/roda-eu")
def api_heatmap_roda(window: int = 120):
    return heatmap_roda_eu(window=window)
