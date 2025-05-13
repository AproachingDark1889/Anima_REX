# anima_utils.py
def parse_timeframe(tf: str) -> int:
    units = {'m': 60, 'h': 3600, 'd': 86400}
    try:
        unit = tf[-1]
        value = int(tf[:-1])
        return value * units[unit]
    except Exception as e:
        raise ValueError(f"Timeframe inválido: {tf}") from e

    # Implementación aquí

# anima_market.py
from anima_utils import parse_timeframe

# anima_broker.py
def some_function():
    # Usa parse_timeframe aquí
    from anima_utils import parse_timeframe  # Lazy import para prevenir conflictos

# tests/test_parse_timeframe.py
from anima_utils import parse_timeframe

### Utilidades
# La función `parse_timeframe` ahora reside en `anima_utils.py`.

## [1.2.0] – 2025-05-03
### Fixed
