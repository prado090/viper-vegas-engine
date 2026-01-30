from backend.terminals import get_terminal
from backend.schemas import SignalResponse


# ============================
# CONFIGURAÇÕES
# ============================
MIN_HISTORICO = 25
MIN_SCORE = 50

MODOS = {
    "conservador": 70,
    "normal": 50,
    "agressivo": 30
}

# ============================
# ESTADO GLOBAL
# ============================
estado = {
    "ativo": False,
    "terminal": None,
    "numeros": [],
    "gale": 0,
    "tipo": None
}

historico = []
historico_terminals = []

stats_terminal = {}
stats_tipo = {
    "normal": {"green": 0, "red": 0},
    "escadinha": {"green": 0, "red": 0}
}


# ============================
# FUNÇÕES AUXILIARES
# ============================
def atualizar_historico(num):
    historico.append(num)
    if len(historico) > MIN_SCORE:
        historico.pop(0)


def registrar_resultado(green):
    t = estado["terminal"]
    tipo = estado["tipo"]

    stats_terminal.setdefault(t, {"green": 0, "red": 0})

    if green:
        stats_terminal[t]["green"] += 1
        stats_tipo[tipo]["green"] += 1
    else:
        stats_terminal[t]["red"] += 1
        stats_tipo[tipo]["red"] += 1


def calcular_score(terminal, tipo):
    if len(historico) < MIN_SCORE:
        return 0

    t = stats_terminal.get(terminal, {"green": 0, "red": 0})
    s = stats_tipo.get(tipo, {"green": 0, "red": 0})

    total_t = t["green"] + t["red"]
    total_s = s["green"] + s["red"]

    score_t = (t["green"] / total_t) if total_t > 0 else 0.5
    score_s = (s["green"] / total_s) if total_s > 0 else 0.5

    return round(((score_t * 0.7) + (score_s * 0.3)) * 100, 2)


def get_terminal(num):
    for t, nums in TERMINAIS.items():
        if num in nums:
            return t
    return None


def vizinhos(num):
    i = ROLETAC.index(num)
    return [ROLETAC[i], ROLETAC[(i - 1) % 37], ROLETAC[(i + 1) % 37]]


def numeros_entrada(terminal):
    entrada = []
    for n in TERMINAIS[terminal]:
        entrada.extend(vizinhos(n))
    return sorted(set(entrada))


def terminal_bloqueado(terminal):
    for n in historico[-3:]:
        if n in numeros_entrada(terminal):
            return True
    return False


def detectar_escadinha():
    if len(historico_terminals) < 3:
        return None

    a, b, c = historico_terminals[-3:]
    d1 = b - a
    d2 = c - b

    if d1 == d2 and d1 != 0:
        return (c + d1) % 10
    return None


# ============================
# MOTOR PRINCIPAL
# ============================
def gerar_sinal(num, modo="normal") -> SignalResponse:
    global estado

    # aquecimento
    if len(historico) < MIN_HISTORICO:
        atualizar_historico(num)
        t = get_terminal(num)
        if t is not None:
            historico_terminals.append(t)
        return SignalResponse(
            status="AQUECENDO",
            mensagem=f"Aquecendo histórico ({len(historico)}/{MIN_HISTORICO})"
        )

    terminal = get_terminal(num)
    if terminal is not None:
        historico_terminals.append(terminal)
        if len(historico_terminals) > 10:
            historico_terminals.pop(0)

    limite = MODOS.get(modo, 50)

    # ESCADINHA
    escada = detectar_escadinha()
    if escada is not None and not estado["ativo"]:
        score = calcular_score(escada, "escadinha")
        if score < limite:
            atualizar_historico(num)
            return SignalResponse(
                status="BLOQUEADO",
                forca=score,
                mensagem=f"Escadinha bloqueada ({score}% < {limite}%)"
            )

        estado = {
            "ativo": True,
            "terminal": escada,
            "numeros": numeros_entrada(escada),
            "gale": 0,
            "tipo": "escadinha"
        }

        atualizar_historico(num)
        return SignalResponse(
            status="ENTRADA_ESCADINHA",
            terminal=escada,
            gale=0,
            numeros=estado["numeros"],
            forca=score,
            mensagem=f"Escadinha liberada ({score}%)"
        )

    # ESTRATÉGIA ATIVA
    if estado["ativo"]:
        if num in estado["numeros"]:
            registrar_resultado(True)
            score = calcular_score(estado["terminal"], estado["tipo"])
            atualizar_historico(num)
            estado["ativo"] = False
            return SignalResponse(
                status="GREEN",
                terminal=estado["terminal"],
                gale=estado["gale"],
                numeros=estado["numeros"],
                forca=score,
                mensagem="GREEN confirmado"
            )

        estado["gale"] += 1
        if estado["gale"] > 2:
            registrar_resultado(False)
            score = calcular_score(estado["terminal"], estado["tipo"])
            atualizar_historico(num)
            estado["ativo"] = False
            return SignalResponse(
                status="RED",
                terminal=estado["terminal"],
                gale=2,
                numeros=estado["numeros"],
                forca=score,
                mensagem="RED após gale 2"
            )

        atualizar_historico(num)
        return SignalResponse(
            status="GALE",
            terminal=estado["terminal"],
            gale=estado["gale"],
            numeros=estado["numeros"],
            forca=calcular_score(estado["terminal"], estado["tipo"]),
            mensagem=f"Gale {estado['gale']} em andamento"
        )

    # GATILHO NORMAL
    if terminal is not None and not terminal_bloqueado(terminal):
        score = calcular_score(terminal, "normal")
        if score < limite:
            atualizar_historico(num)
            return SignalResponse(
                status="BLOQUEADO",
                forca=score,
                mensagem=f"Entrada bloqueada ({score}% < {limite}%)"
            )

        estado = {
            "ativo": True,
            "terminal": terminal,
            "numeros": numeros_entrada(terminal),
            "gale": 0,
            "tipo": "normal"
        }

        atualizar_historico(num)
        return SignalResponse(
            status="ENTRADA",
            terminal=terminal,
            gale=0,
            numeros=estado["numeros"],
            forca=score,
            mensagem=f"Entrada liberada ({score}%)"
        )

    atualizar_historico(num)
    return SignalResponse(status="IGNORE", mensagem="Número ignorado")
