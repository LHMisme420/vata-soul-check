class RollingContext:
    def __init__(self, max_chars=2000):
        self.max_chars = max_chars
        self.messages = []

    def add(self, role, text):
        self.messages.append((role, text))
        self._trim()

    def _trim(self):
        total = 0
        kept = []
        for r, t in reversed(self.messages):
            total += len(t) + 10
            kept.append((r, t))
            if total >= self.max_chars:
                break
        self.messages = list(reversed(kept))

    def render(self):
        return "\n".join([f"{r}: {t}" for r, t in self.messages])
