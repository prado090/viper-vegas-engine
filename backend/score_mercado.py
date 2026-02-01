from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional
from collections import deque

# Mapa simples de cores da roleta europeia
RED = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
BLACK = {2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35}

def cor(n: int) -> str:
    if n == 0:
        return "green"
    return "red" if n in RED else "black"

def paridade(n: int) -> str:
    if n == 0:
        return "zero"
    return "par" if (n % 2 == 0) else "impar"

def alto_baixo(n: int) -> str:
    if n == 0:
        return "zero"
    return "alto" if n >= 19 else "baixo"

def duzia(n: int) -> str:
    if n == 0:
        return "zero"
    if 1 <= n <= 12:
        return "d1"
    if 13 <= n <= 24:
        return "d2"
    return "d3"

def coluna(n: int) -> str:
    if n == 0:
        return "zero"
    r = n % 3
    if r == 1:
        return "c1"
    if r == 2:
        return "c2"
    return "c3"

@dataclass
class AssocStats:
    hit: int = 0
    total: int = 0

class ScoreMercadoEngine:
    """
    Ideia:
    - Observa o 'mercado' (últimos spins) e extrai features:
      cor, paridade, duzia, coluna, alto/baixo.
    - Quando um padrão "paga" (GREEN), registra quais features estavam presentes,
      criando co-ocorrência: padrão X costuma pagar quando mercado mostra (ex.: red+par+d2).
    - Na hora de liberar entrada, calcula score 0..100 baseado na compatibilidade
      do mercado atual com o histórico de "pagamentos" daquele padrão.
    """

    def __init__(self, janela_mercado: int = 12):
        self.historico = deque(maxlen=2000)
        self.janela_mercado = janela_mercado

        # assocs[padrao][feature_value] -> AssocStats
        self.assocs: Dict[str, Dict[str, AssocStats]] = {}

    def observar_spin(self, numero: int) -> None:
        self.historico.append(numero)

    def _features_de_numero(self, n: int) -> Dict[str, str]:
        return {
            "cor": cor(n),
            "paridade": paridade(n),
            "duzia": duzia(n),
            "coluna": coluna(n),
            "altura": alto_baixo(n),
        }

    def _snapshot_mercado(self) -> Dict[str, Any]:
        ult = list(self.historico)[-self.janela_mercado:]
        if not ult:
            return {"ultimos": []}

        feats = [self._features_de_numero(n) for n in ult]
        # simples: "tendência" = moda por feature
        def moda(chave: str) -> str:
            freq: Dict[str, int] = {}
            for f in feats:
                v = f[chave]
                freq[v] = freq.get(v, 0) + 1
            return sorted(freq.items(), key=lambda x: x[1], reverse=True)[0][0]

        return {
            "ultimos": ult,
            "t_cor": moda("cor"),
            "t_par": moda("paridade"),
            "t_duzia": moda("duzia"),
            "t_coluna": moda("coluna"),
            "t_altura": moda("altura"),
        }

    def registrar_pagamento(self, padrao: str, numero_que_pagou: int) -> None:
        if padrao not in self.assocs:
            self.assocs[padrao] = {}

        snap = self._snapshot_mercado()
        feats_num = self._features_de_numero(numero_que_pagou)

        # Co-ocorrência: junta tendência do mercado + features do número que pagou
        lista_features = [
            f"t_cor={snap.get('t_cor')}",
            f"t_par={snap.get('t_par')}",
            f"t_duzia={snap.get('t_duzia')}",
            f"t_coluna={snap.get('t_coluna')}",
            f"t_altura={snap.get('t_altura')}",
            f"hit_cor={feats_num['cor']}",
            f"hit_par={feats_num['paridade']}",
            f"hit_duzia={feats_num['duzia']}",
            f"hit_coluna={feats_num['coluna']}",
            f"hit_altura={feats_num['altura']}",
        ]

        for key in lista_features:
            if key not in self.assocs[padrao]:
                self.assocs[padrao][key] = AssocStats()
            self.assocs[padrao][key].hit += 1

        # também incrementa total
        for k in list(self.assocs[padrao].keys()):
            self.assocs[padrao][k].total += 1

    def score(self, padrao: str) -> float:
        if len(self.historico) < self.janela_mercado:
            return 0.0

        snap = self._snapshot_mercado()
        atual = {
            f"t_cor={snap.get('t_cor')}",
            f"t_par={snap.get('t_par')}",
            f"t_duzia={snap.get('t_duzia')}",
            f"t_coluna={snap.get('t_coluna')}",
            f"t_altura={snap.get('t_altura')}",
        }

        data = self.assocs.get(padrao)
        if not data:
            return 50.0  # neutro enquanto não tem aprendizado

        # média ponderada dos sinais compatíveis
        pontos = 0.0
        peso = 0.0
        for k in atual:
            st = data.get(k)
            if not st or st.total == 0:
                continue
            # taxa de ocorrência daquele feature quando pagou
            rate = st.hit / st.total  # 0..1
            pontos += rate
            peso += 1.0

        if peso == 0:
            return 50.0

        # normaliza para 0..100
        return round((pontos / peso) * 100, 2)
