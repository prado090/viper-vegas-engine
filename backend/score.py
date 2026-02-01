class TerminalScoreEngine:
    def __init__(self):
        self.stats = {}

    def registrar(self, terminal: int, green: bool):
        if terminal not in self.stats:
            self.stats[terminal] = {"g": 0, "r": 0}
        if green:
            self.stats[terminal]["g"] += 1
        else:
            self.stats[terminal]["r"] += 1

    def score(self, terminal: int):
        s = self.stats.get(terminal)
        if not s:
            return 0
        total = s["g"] + s["r"]
        return round((s["g"] / total) * 100, 2) if total else 0
