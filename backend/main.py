from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.logic import gerar_sinal


app = FastAPI(title="Viper Vegas Engine")

app.mount("/static", StaticFiles(directory="backend/static"), name="static")

@app.get("/")
def painel():
    return FileResponse("backend/static/index.html")

@app.post("/spin")
def spin(data: dict):
    num = data["num"]
    modo = data.get("modo", "normal")
    return gerar_sinal(num, modo)
