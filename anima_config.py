# File: anima_config.py
import yaml
import logging

logger = logging.getLogger(__name__)

# Carga de configuración desde YAML
def cargar_config(ruta="config.yml"):
    with open(ruta, "r") as f:
        config = yaml.safe_load(f)
        if not isinstance(config, dict):
            raise ValueError("El archivo de configuración no contiene un diccionario válido.")
        return config