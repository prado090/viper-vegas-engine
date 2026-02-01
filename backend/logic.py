# backend/logic.py
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
import time
from typing import Deque, Dict, List, Optional, Set, Tuple


# ==============================
# CONFIG
# ==============================
MAX_HISTORY = 500

MIN_SPINS_AQUECIMENTO = 12          # depois disso começa a detectar padrões
GALE_MAX = 2                        # até gale 2
SCORE_THRESHOLD = 0.62              # limiar para liberar ENTRADA (ajustável)
SCORE_TERMINAL_WEIGHT = 0.55
SCORE_PADRAO_WEIGHT = 0.45

# vizinhos pela RODA europeia (race)
# Ordem padrão da roleta europeia (0-36)
WHEEL_EU = [
    0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30,
    8, 23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7,
    28, 12, 35, 3, 26
]

RED_NUMBERS = {
    1, 3, 5, 7, 9, 12, 14, 16, 18,
    19, 21, 23, 25, 27, 30, 32, 34, 36
}
BLACK_NUMBERS = {
    2, 4, 6, 8, 10, 11, 13, 15, 17,
    20, 22, 24, 26, 28, 29, 31, 33, 35
}


# ==============================
# ESTADO
# ==============================
historico: Deque[Dict] = deque(maxlen=MAX_HISTORY)

stats = {
    "spins": 0,
    "entradas": 0,   # entradas SUGERIDAS (liberadas)
    "greens": 0,
    "reds": 0,
    "gales": 0,
    "padroes": 0,
}

# scores (hit/miss)
terminal_stats = defaultdict(lambda: {"hits": 0, "miss": 0})
padrao_stats = defaultdict(lambda: {"hits": 0, "miss": 0})
terminal_padrao_stats = defaultdict(lambda: {"hits": 0, "miss": 0})


@dataclass
class EntradaAtiva:
    estrategia: str                # "terminal_vizinhos" | "escadinha"
    terminal_previsto: int
    numeros_alvo: Set[int]         # conjunto completo para cobrir
    padrao: str
    gale: int = 0                  # 0 = entrada base, 1 = gale1, 2 = gale2


entrada_ativa: Optional[EntradaAtiva] = None


# ==============================
# HELPERS
# ==============================
def resetar_estado() -> None:
    global historico, stats, terminal_stats, padrao_stats, terminal_padrao_stats, entrada_ativa

    historico.clear()
    entrada_ativa = None

    stats["spins"] = 0
    stats["entradas"] = 0
    stats["greens"] = 0
    stats["reds"] = 0
    stats["gales"] = 0
    stats["padroes"] = 0

    terminal_stats.clear()
    padrao_stats.clear()
    terminal_padrao_stats.clear()


def cor_numero(n: int) -> str:
    if n == 0:
        return "GREEN"
    if n in RED_NUMBERS:
        return "RED"
    if n in BLACK_NUMBERS:
        return "BLACK"
    return "UNKNOWN"


def terminal(n: int) -> int:
    return n % 10


def wheel_index(n: int) -> int:
    return WHEEL_EU.index(n)


def wheel_neighbors(n: int, k: int = 1) -> List[int]:
    """Retorna os vizinhos pela RODA (race), k para cada lado."""
    idx = wheel_index(n)
    res = []
    for d in range(1, k + 1):
        res.append(WHEEL_EU[(idx - d) % len(WHEEL_EU)])
        res.append(WHEEL_EU[(idx + d) % len(WHEEL_EU)])
    # remove duplicados e mantém ordem
    seen = set()
    out = []
    for x in res:
        if x not in seen:
            out.append(x)
            seen.add(x)
    return out


def grupo_terminal(t: int) -> List[int]:
    """Números 0..36 com terminal t (ex: 6 -> 6,16,26,36)."""
    return [n for n in range(0, 37) if n % 10 == t]


def grupo_terminal_com_vizinhos_roda(t: int, k: int = 1) -> List[int]:
    """
    Estratégia 'terminal + 1 vizinho (pela roda)':
    - pega todos os números do terminal
    - para cada um, adiciona vizinhos na RODA europeia (k por lado)
    """
    base = grupo_terminal(t)
    s: Set[int] = set(base)
    for n in base:
        s.update(wheel_neighbors(n, k=k))
    return sorted(s)


def score_from_counts(hits: int, miss: int) -> float:
    total = hits + miss
    if total <= 0:
        return 0.0
    return hits / total


def calcular_score_terminal(t: int) -> float:
    d = terminal_stats[t]
    return score_from_counts(d["hits"], d["miss"])


def calcular_score_padrao(p: str) -> float:
    d = padrao_stats[p]
    return score_from_counts(d["hits"], d["miss"])


def calcular_score_combinado(t: int, p: str) -> float:
    """Score combinado terminal+padrao também é registrado (para ranking)."""
    d = terminal_padrao_stats[f"{t}|{p}"]
    return score_from_counts(d["hits"], d["miss"])


# ==============================
# DETECÇÃO DE PADRÕES
# ==============================
def detectar_terminal_vizinhos() -> Optional[Tuple[str, int]]:
    """
    Gatilho simples pro "terminal + vizinhos":
    - se os últimos 3 terminais forem iguais -> sugere esse terminal
    """
    if len(historico) < 3:
        return None
    t3 = [historico[-i]["terminal"] for i in range(1, 4)]
    if t3[0] == t3[1] == t3[2]:
        t = t3[0]
        return ("repeticao_terminal", t)
    return None


def detectar_escadinha() -> Optional[Tuple[str, int, int, str]]:
    """
    Escadinha completa (2 a 9):
    - lê os últimos 3 terminais
    - se a diferença (mod 10) for constante e estiver em {2..9}
      considera escadinha e prevê o próximo terminal
    Retorna: (padrao, terminal_previsto, passo, direcao)
    """
    if len(historico) < 3:
        return None

    t1 = historico[-3]["terminal"]
    t2 = historico[-2]["terminal"]
    t3 = historico[-1]["terminal"]

    d1 = (t2 - t1) % 10
    d2 = (t3 - t2) % 10

    # subida
    if d1 == d2 and 2 <= d1 <= 9:
        passo = d1
        previsto = (t3 + passo) % 10
        padrao = f"escadinha_p{passo}_up"
        return (padrao, previsto, passo, "up")

    # descida (ex: 8 equivale a -2 mod10)
    # para descer de X em X, você vai ver d1=d2=(10-passo)
    if d1 == d2 and 2 <= (10 - d1) <= 9:
        passo = 10 - d1
        previsto = (t3 - passo) % 10
        padrao = f"escadinha_p{passo}_down"
        return (padrao, previsto, passo, "down")

    return None


# ==============================
# RESOLVER ENTRADA (GREEN/GALE/RED)
# ==============================
def _registrar_resultado(t: int, padrao: str, hit: bool) -> None:
    if hit:
        terminal_stats[t]["hits"] += 1
        padrao_stats[padrao]["hits"] += 1
        terminal_padrao_stats[f"{t}|{padrao}"]["hits"] += 1
        stats["greens"] += 1
    else:
        terminal_stats[t]["miss"] += 1
        padrao_stats[padrao]["miss"] += 1
        terminal_padrao_stats[f"{t}|{padrao}"]["miss"] += 1


def _resolver_entrada_ativa(numero: int, term_atual: int) -> Tuple[str, str]:
    """
    Retorna (status, mensagem)
    status: GREEN | GALE | RED
    """
    global entrada_ativa

    assert entrada_ativa is not None

    hit = numero in entrada_ativa.numeros_alvo
    if hit:
        _registrar_resultado(entrada_ativa.terminal_previsto, entrada_ativa.padrao, True)
        entrada_ativa = None
        return ("GREEN", "Green confirmado (bateu no alvo)")
    else:
        # miss => gale ou red final
        if entrada_ativa.gale < GALE_MAX:
            entrada_ativa.gale += 1
            stats["gales"] += 1
            return ("GALE", f"Gale {entrada_ativa.gale}/{GALE_MAX} (não bateu no alvo)")
        else:
            _registrar_resultado(entrada_ativa.terminal_previsto, entrada_ativa.padrao, False)
            entrada_ativa = None
            stats["reds"] += 1
            return ("RED", "Red confirmado (fechou ciclo)")


# ==============================
# GERAÇÃO DE SINAL
# ==============================
def gerar_sinal(numero: int, modo: str = "agressivo", source: str = "manual") -> Dict:
    """
    Retorna um dict pronto pro painel.
    - Não promete acerto; é análise estatística + gatilhos.
    """
    global entrada_ativa

    stats["spins"] += 1

    term = terminal(numero)
    cor = cor_numero(numero)

    registro = {
        "time": time.strftime("%H:%M:%S"),
        "source": source,
        "numero": int(numero),
        "cor": cor,
        "terminal": int(term),
        "status": "ANALISE",
        "padroes": None,                 # string ou None
        "score_terminal": 0.0,
        "score_padrao": 0.0,
        "score_combinado": 0.0,
        "grupo_terminal": grupo_terminal(term),
        "vizinhos_roda": wheel_neighbors(numero, k=1),
        "mensagem": "",
        "entrada": None,                 # dict quando ENTRADA ativa
        "debug": {},
    }

    # salva no histórico primeiro
    historico.append(registro)

    # aquecimento
    if len(historico) < MIN_SPINS_AQUECIMENTO:
        registro["mensagem"] = f"Aquecendo histórico ({len(historico)}/{MIN_SPINS_AQUECIMENTO})"
        return registro

    # Se existe entrada ativa, resolve (GREEN/GALE/RED)
    if entrada_ativa is not None:
        status, msg = _resolver_entrada_ativa(numero, term)
        registro["status"] = status
        registro["mensagem"] = msg
        registro["padroes"] = entrada_ativa.padrao if entrada_ativa else None
        return registro

    # ==============================
    # DETECTAR PADRÕES (prioridade: escadinha -> repetição terminal)
    # ==============================
    padrao_detectado = None
    entrada_terminal_previsto = None
    estrategia = None

    esc = detectar_escadinha()
    if esc:
        padrao, previsto, passo, direcao = esc
        padrao_detectado = padrao
        entrada_terminal_previsto = previsto
        estrategia = "escadinha"
        stats["padroes"] += 1
        registro["debug"]["escadinha"] = {"passo": passo, "direcao": direcao, "previsto": previsto}

    if padrao_detectado is None:
        rep = detectar_terminal_vizinhos()
        if rep:
            padrao, previsto = rep
            padrao_detectado = padrao
            entrada_terminal_previsto = previsto
            estrategia = "terminal_vizinhos"
            stats["padroes"] += 1

    # se não detectou nada, apenas calcula score terminal e retorna
    if padrao_detectado is None or entrada_terminal_previsto is None:
        st_score = calcular_score_terminal(term)
        registro["score_terminal"] = round(st_score, 6)
        registro["mensagem"] = f"Sem padrão detectado | Score terminal: {round(st_score, 2)}"
        return registro

    # ==============================
    # SCORE (terminal previsto + padrão)
    # ==============================
    score_t = calcular_score_terminal(entrada_terminal_previsto)
    score_p = calcular_score_padrao(padrao_detectado)
    score_c = (SCORE_TERMINAL_WEIGHT * score_t) + (SCORE_PADRAO_WEIGHT * score_p)

    # modo altera agressividade
    if modo == "conservador":
        threshold = SCORE_THRESHOLD + 0.08
    elif modo == "normal":
        threshold = SCORE_THRESHOLD + 0.03
    else:
        threshold = SCORE_THRESHOLD

    registro["padroes"] = padrao_detectado
    registro["score_terminal"] = round(score_t, 6)
    registro["score_padrao"] = round(score_p, 6)
    registro["score_combinado"] = round(score_c, 6)

    registro["mensagem"] = (
        f"Padrão detectado: {padrao_detectado} | "
        f"Prev terminal: {entrada_terminal_previsto} | "
        f"Score: {round(score_c, 2)} (T:{round(score_t,2)} P:{round(score_p,2)})"
    )

    # ==============================
    # LIBERAR ENTRADA
    # ==============================
    if score_c >= threshold:
        # entrada sempre = terminal previsto + vizinhos pela roda para cada número do terminal (k=1)
        alvo = set(grupo_terminal_com_vizinhos_roda(entrada_terminal_previsto, k=1))

        entrada_ativa = EntradaAtiva(
            estrategia=strategia,
            terminal_previsto=entrada_terminal_previsto,
            numeros_alvo=alvo,
            padrao=padrao_detectado,
            gale=0,
        )

        stats["entradas"] += 1

        registro["status"] = "ENTRADA"
        registro["entrada"] = {
            "estrategia": estrategia,
            "terminal_previsto": entrada_terminal_previsto,
            "numeros_terminal": grupo_terminal(entrada_terminal_previsto),
            "numeros_alvo": sorted(list(alvo)),
            "gale_max": GALE_MAX,
            "padrao": padrao_detectado,
        }
        registro["mensagem"] = f"ENTRADA LIBERADA ✅ | {registro['mensagem']}"
        return registro

    # não liberou entrada
    registro["mensagem"] = f"Score abaixo do limiar ({round(score_c,2)} < {round(threshold,2)}) | {registro['mensagem']}"
    return registro


# ==============================
# EXPORTS (PARA API)
# ==============================
def get_historico() -> List[Dict]:
    return list(historico)


def get_stats() -> Dict:
    return dict(stats)


def get_score_terminal() -> List[Dict]:
    out = []
    for t in range(10):
        d = terminal_stats[t]
        out.append({
            "terminal": t,
            "hits": d["hits"],
            "miss": d["miss"],
            "score": round(score_from_counts(d["hits"], d["miss"]), 4),
        })
    return out


def get_score_padrao() -> List[Dict]:
    out = []
    for p, d in padrao_stats.items():
        out.append({
            "padrao": p,
            "hits": d["hits"],
            "miss": d["miss"],
            "score": round(score_from_counts(d["hits"], d["miss"]), 4),
        })
    # ordena por score desc
    out.sort(key=lambda x: x["score"], reverse=True)
    return out


def get_score_terminal_padrao() -> List[Dict]:
    out = []
    for k, d in terminal_padrao_stats.items():
        out.append({
            "terminal_padrao": k,
            "hits": d["hits"],
            "miss": d["miss"],
            "score": round(score_from_counts(d["hits"], d["miss"]), 4),
        })
    out.sort(key=lambda x: x["score"], reverse=True)
    return out


def heatmap_terminal(window: int = 120) -> List[Dict]:
    tail = list(historico)[-window:]
    counts = defaultdict(int)
    for h in tail:
        counts[h["terminal"]] += 1
    return [{"terminal": t, "count": counts.get(t, 0), "window": window} for t in range(10)]


def heatmap_roda_eu(window: int = 120) -> List[Dict]:
    tail = list(historico)[-window:]
    counts = defaultdict(int)
    for h in tail:
        counts[h["numero"]] += 1
    # retorna lista ordenada pela posição na roda
    out = []
    for idx, n in enumerate(WHEEL_EU):
        out.append({
            "wheel_index": idx,
            "numero": n,
            "count": counts.get(n, 0),
            "window": window,
        })
    return out
