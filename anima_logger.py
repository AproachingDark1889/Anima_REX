
import logging
import os
from datetime import datetime

def setup_logger(nombre="anima", nivel=logging.INFO):
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    fecha = datetime.now().strftime("%Y-%m-%d")
    log_path = os.path.join(log_dir, f"{nombre}_{fecha}.log")

    logger = logging.getLogger(nombre)
    logger.setLevel(nivel)

    if not logger.handlers:
        fh = logging.FileHandler(log_path, encoding='utf-8')
        formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        sh = logging.StreamHandler()
        sh.setFormatter(formatter)
        logger.addHandler(sh)

    return logger
