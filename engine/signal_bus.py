# engine/signal_bus.py
# Módulo de cola para señales generadas por los workers

import queue
import logging
from signal_model import Signal

logger = logging.getLogger(__name__)

class SignalBus:
    """
    Cola de mensajes para transmitir señales entre workers y filtros.
    """
    def __init__(self):
        self._queue = queue.Queue()

    def get(self, timeout=None):
        """Devuelve la siguiente señal, bloqueante o con timeout opcional."""
        if timeout is None:
            return self._queue.get()
        return self._queue.get(timeout=timeout)

    def publish(self, signal: Signal):
        """Publica una señal en la cola."""
        logger.debug(f"[Bus] Publicando señal → {signal}")
        self._queue.put(signal)

    def subscribe(self):
        """
        Iterador que cede señales conforme llegan.

        Uso:
            for signal in bus.subscribe():
                procesar(signal)
        """
        while True:
            logger.debug("[Bus] Esperando señal…")
            signal = self._queue.get()
            logger.debug(f"[Bus] Señal entregada → {signal}")
            yield signal
