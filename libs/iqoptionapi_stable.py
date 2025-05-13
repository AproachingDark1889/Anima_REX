# iqoptionapi_stable.py

import logging
import time
import threading
from websocket import create_connection
import json
import ssl

class IQ_Option:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.ws = None
        self.ssid = None
        self.connected = False
        self._balance_type = "PRACTICE"
        self._lock = threading.Lock()

    def connect(self):
        try:
            self.ws = create_connection("wss://iqoption.com/echo/websocket", sslopt={"cert_reqs": ssl.CERT_NONE})
            self._send_auth()
            for _ in range(10):
                msg = self.ws.recv()
                if "ssid" in msg:
                    self.connected = True
                    return True, "OK"
            return False, "No se pudo autenticar"
        except Exception as e:
            return False, str(e)

    def _send_auth(self):
        data = {
            "name": "ssid",
            "msg": self.password  # en la práctica se usa token, esta versión requiere adaptación a token real
        }
        self.ws.send(json.dumps(data))

    def check_connect(self):
        return self.connected

    def close(self):
        if self.ws:
            self.ws.close()
        self.connected = False

    def change_balance(self, tipo):
        # PRACTICE o REAL
        self._balance_type = tipo.upper()

    def get_balance(self):
        # Simulación para entorno demo – debería consultar el endpoint real en producción
        return 1000.0

    def buy_digital_spot(self, par, monto, direccion, tiempo):
        if not self.connected:
            return False, None
        trade_id = int(time.time())
        logging.info(f"[DUMMY API] Simulando orden: {direccion.upper()} {par} | ${monto} | {tiempo}m")
        return True, trade_id

    def check_win_digital_v2(self, trade_id):
        time.sleep(2)
        return True, 50.0  # Dummy: siempre retorna ganancia
