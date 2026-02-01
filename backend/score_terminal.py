from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Optional
from collections import deque
import math

@dataclass
class TerminalStats:
    green: int = 0
    red: int = 0

class TerminalScoreEngine:
    """
    Score avançado por terminal:
    - Mantém estatística (green/red)
    - Mantém uma janela recente de resultados por terminal (pra sentir fase)
    - Retorna score 0..100 com suavização
    """

    def __init__(self, janela_fase: int = 30):
        self.stats: Dict[int, TerminalStats] = {}
        self.fase: Dict[int, deque[bool]] = {}
        self.janela_fase = janela_fase

    def registrar(self, terminal: Optional[int], green: bool) -> None:
        if terminal is None:
            return
        if terminal not in self.stats:
            self.stats[terminal] = TerminalStats()
        if terminal not in self.fase:
            self.fase[terminal] = deque(maxlen=self.janela_fase)

        if green:
            self.stats[terminal].green += 1
        else:
            self.stats[terminal].red += 1

        self.fase[terminal].append(green)

    def score(self, terminal: int) -> float:
        st = self.stats.get(terminal, TerminalStats())
        total = st.green + st.red
        if total == 0:
            return 0.0

        # Winrate global
        wr_global = st.green / total  # 0..1

        # Fase recente (janela)
        fase = self.fase.get(terminal)
        if not fase or len(fase) < 5:
            wr_fase = wr_global
        else:
            wr_fase = sum(1 for x in fase if x) / len(fase)

        # confiança cresce com amostra (log)
        conf = 1 - math.exp(-total / 20)  # 0..~1

        # mix: fase pesa mais quando há dados
        wr_mix = (wr_global * (1 - conf)) + (wr_fase * conf)

        return round(wr_mix * 100, 2)
