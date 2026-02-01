from collections import defaultdict, deque

class ScorePadroesEngine:
    def __init__(self, max_hist=500):
        self.historico = deque(maxlen=max_hist)
        self.combinacoes = defaultdict(lambda: {"green": 0, "red": 0})

    # ==========================
    # EXTRAIR PADRÕES DO NÚMERO
    # ==========================
    def extrair(self, n: int):
        if n == 0:
            return ["zero"]

        padroes = []

        # cor
        vermelhos = {
            1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36
        }
        padroes.append("vermelho" if n in vermelhos else "preto")

        # par/impar
        padroes.append("par" if n % 2 == 0 else "impar")

        # dúzia
        if n <= 12:
            padroes.append("duzia1")
        elif n <= 24:
            padroes.append("duzia2")
        else:
            padroes.append("duzia3")

        # coluna
        if n % 3 == 1:
            padroes.append("coluna1")
        elif n % 3 == 2:
            padroes.append("coluna2")
        else:
            padroes.append("coluna3")

        return padroes

    # ==========================
    # REGISTRAR RESULTADO
    # ==========================
    def registrar(self, numero: int, green: bool):
        padroes = self.extrair(numero)
        self.historico.append(padroes)

        # todas combinações 2 a 2
        for i in range(len(padroes)):
            for j in range(i + 1, len(padroes)):
                chave = f"{padroes[i]}+{padroes[j]}"
                if green:
                    self.combinacoes[chave]["green"] += 1
                else:
                    self.combinacoes[chave]["red"] += 1

    # ==========================
    # SCORE DE MERCADO
    # ==========================
    def score(self, numero: int):
        padroes = self.extrair(numero)
        scores = []

        for i in range(len(padroes)):
            for j in range(i + 1, len(padroes)):
                chave = f"{padroes[i]}+{padroes[j]}"
                data = self.combinacoes.get(chave)

                if not data:
                    continue

                g = data["green"]
                r = data["red"]
                if g + r < 5:
                    continue

                scores.append(g / (g + r))

        if not scores:
            return 0.0

        return round(sum(scores) / len(scores) * 100, 2)
