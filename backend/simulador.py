import requests
import random
import time

URL = "http://127.0.0.1:8000/spin"
TOTAL_GIROS = 300
INTERVALO = 0.2

greens = 0
reds = 0
gales = 0
entradas = 0

print("=== SIMULADOR VIPER VEGAS ===\n")

for i in range(TOTAL_GIROS):
    numero = random.randint(0, 36)

    try:
        r = requests.post(URL, json={
            "numero": numero,
            "modo": "normal"
        })
        data = r.json()
    except Exception as e:
        print(f"[ERRO] Falha na requisição: {e}")
        break

    status = data.get("status")

    if status and status.startswith("ENTRADA"):
        entradas += 1

    if status == "GREEN":
        greens += 1
    elif status == "RED":
        reds += 1
    elif status == "GALE":
        gales += 1

    print(f"[{i+1:03d}] Número: {numero:02d} | Status: {status}")

    time.sleep(INTERVALO)

print("\n=== RESULTADO FINAL ===")
print(f"Entradas: {entradas}")
print(f"Greens:   {greens}")
print(f"Gales:    {gales}")
print(f"Reds:     {reds}")
