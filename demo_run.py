"""
demo_run.py
Smoke test ultra-ligero de AnimaCore usando MockBroker y stubs,
sin depender de iqoptionapi, gym ni conectar al broker real.
"""

import sys
import types
from datetime import datetime

# ── Stub para iqoptionapi ─────────────────────────────────────
iq = types.ModuleType("iqoptionapi")
stable = types.ModuleType("iqoptionapi.stable_api")
# IQ_Option stub: no se usará porque conectaremos al MockBroker
stable.IQ_Option = lambda *args, **kwargs: None
iq.stable_api = stable
sys.modules["iqoptionapi"] = iq
sys.modules["iqoptionapi.stable_api"] = stable

# ── Stub para gym y gym.spaces ─────────────────────────────────
gym = types.ModuleType("gym")
gym.Env = object
spaces = types.ModuleType("gym.spaces")
spaces.Discrete = lambda *args, **kwargs: None
spaces.Box      = lambda *args, **kwargs: None
gym.spaces = spaces
sys.modules["gym"]        = gym
sys.modules["gym.spaces"] = spaces

# ── MockBroker ────────────────────────────────────────────────
class MockBroker:
    def __init__(self):
        self._balance = 1000.0
    def comprar(self, par, direccion, monto, tiempo):
        return "TICKET123"
    def check_win(self, ticket):
        return True
    def get_balance(self):
        return self._balance
    def ping(self):
        pass

# ── Override conectar_broker para usar MockBroker ─────────────
import anima_broker
anima_broker.conectar_broker = lambda cred: MockBroker()

# ── Importar AnimaCore tras el override ────────────────────────
from core.anima_core import AnimaCore

def main():
    print(">> Inicio demo_run")  # Confirmación de arranque
    core = AnimaCore()           # Usará MockBroker automáticamente
    for i in range(5):
        signal = {
            "timestamp": datetime.utcnow(),
            "pair":      "EURUSD",
            "direction": "CALL",
            "strategy":  "mhi1_maioria"
        }
        core.bus.publish(signal)
        senal = core.bus.get()
        core.ejecutar_operacion(senal)
    print("✅ Demo completada: 5 operaciones con MockBroker.")

if __name__ == "__main__":
    main()