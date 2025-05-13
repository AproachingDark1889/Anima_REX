try:
    from prometheus_client import start_http_server, Gauge, Histogram, Counter
    HAS_PROMETHEUS = True
except ImportError:
    HAS_PROMETHEUS = False
    print("[Observability] prometheus_client no instalado; métricas deshabilitadas.")
    # Definición de métricas dummy
    def start_http_server(port: int = 8000):
        print(f"[Observability] Iniciando modo dummy; servidor de métricas omitido.")
    class Gauge:
        def __init__(self, *args, **kwargs): pass
        def set(self, *args, **kwargs): pass
    class Histogram:
        def __init__(self, *args, **kwargs): pass
        def time(self):
            class DummyContext:
                def __enter__(self): pass
                def __exit__(self, *args): pass
            return DummyContext()
    class Counter:
        def __init__(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass

# Métricas de Prometheus
ohlcv_ingestion_latency = Histogram(
    'ohlcv_ingestion_latency_seconds',
    'Tiempo de latencia de ingesta OHLCV en segundos'
)
signal_processing_time = Histogram(
    'signal_processing_time_seconds',
    'Tiempo de procesamiento por señal en core'
)
error_counter = Counter(
    'error_count_total',
    'Número de errores por componente',
    ['component']
)
thread_heartbeat = Gauge(
    'thread_last_heartbeat_timestamp',
    'Timestamp del último latido de hilo',
    ['thread']
)

def start_metrics_server(port: int = 8000):
    """
    Inicia el servidor HTTP en el puerto dado para exponer /metrics.
    """
    start_http_server(port)
    print(f"[Observability] Metrics server started on port {port}")