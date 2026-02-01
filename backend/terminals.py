# ==========================
# TERMINAIS (0 a 9)
# ==========================
TERMINAIS = {
    0: [0, 10, 20, 30],
    1: [1, 11, 21, 31],
    2: [2, 12, 22, 32],
    3: [3, 13, 23, 33],
    4: [4, 14, 24, 34],
    5: [5, 15, 25, 35],
    6: [6, 16, 26, 36],
    7: [7, 17, 27],
    8: [8, 18, 28],
    9: [9, 19, 29],
}

# ==========================
# ORDEM DA ROLETA EUROPEIA
# (para vizinhos reais)
# ==========================
ORDEM_ROLETA = [
    0, 32, 15, 19, 4, 21, 2, 25, 17,
    34, 6, 27, 13, 36, 11, 30, 8,
    23, 10, 5, 24, 16, 33, 1,
    20, 14, 31, 9, 22, 18, 29,
    7, 28, 12, 35, 3, 26
]

def _vizinho(numero: int, offset: int) -> int:
    idx = ORDEM_ROLETA.index(numero)
    return ORDEM_ROLETA[(idx + offset) % len(ORDEM_ROLETA)]

def get_terminal(numero: int):
    for t, nums in TERMINAIS.items():
        if numero in nums:
            return t
    return None

def get_terminal_com_vizinhos(terminal: int):
    if terminal not in TERMINAIS:
        return {"terminal": None, "numeros": []}

    numeros = set()
    for n in TERMINAIS[terminal]:
        numeros.add(n)
        numeros.add(_vizinho(n, -1))
        numeros.add(_vizinho(n, 1))

    return {"terminal": terminal, "numeros": sorted(numeros)}

# ==========================
# BLOQUEIO (corrigido)
# Antes: bloqueava se últimos 3 números caíssem no "set" de entrada (muito amplo)
# Agora: bloqueia se o MESMO terminal repetiu nos últimos N spins
# ==========================
def terminal_bloqueado(terminal: int, historico: list[int], ultimos: int = 3) -> bool:
    if terminal is None or len(historico) < ultimos:
        return False

    ult = historico[-ultimos:]
    ult_term = [get_terminal(n) for n in ult]
    # bloqueia se o terminal atual apareceu em todos (ou quase todos) últimos N
    return all(t == terminal for t in ult_term if t is not None)
