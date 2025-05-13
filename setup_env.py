"""
Módulo de configuración de entorno de alto rendimiento para Anima Rex.
Configura variables de entorno para BLAS/MKL y levanta un cluster Dask para paralelismo.
"""
import os
import multiprocessing
from dask.distributed import Client
from anima_verificador import verificar_config

def setup_environment():
    """
    Inicializa el entorno de ejecución paralelo:
      - Ajusta variables de entorno para que BLAS/MKL use todos los núcleos
      - Crea un cliente Dask con un worker por núcleo y un hilo por worker
    :return: instancia de Client de Dask
    """
    # 1. Validar config
    valido, mensaje = verificar_config("config.yml")
    if not valido:
        raise SystemExit(f"Config inválida: {mensaje}")

    cpu_count = multiprocessing.cpu_count()

    # Limitar BLAS/OpenBLAS/MKL a usar todos los hilos disponibles
    os.environ["OMP_NUM_THREADS"] = str(cpu_count)
    os.environ["OPENBLAS_NUM_THREADS"] = str(cpu_count)
    os.environ["MKL_NUM_THREADS"] = str(cpu_count)

    # Afinar timeouts y heartbeat de Dask a nivel global
    from dask import config as dask_config
    dask_config.set({
        'distributed.comm.timeouts.connect': '60s',
        'distributed.comm.timeouts.tcp': '60s',
        'distributed.scheduler.worker-timeout': '60s',
        'distributed.scheduler.worker-heartbeat-interval': '20s'
    })

    # Crear y devolver el cliente Dask con reconexión automática
    client = Client(
        n_workers=cpu_count,
        threads_per_worker=1,
        processes=True,
        memory_limit="auto",
        reconnect=True
    )

    # Log básico de arranque
    print(f"[ENV] Dask cluster iniciado: {cpu_count} workers, 1 hilo por worker.")

    return client


if __name__ == "__main__":
    # Prueba rápida de setup
    print("Inicializando entorno de Anima Rex...")
    client = setup_environment()
    print("Entorno listo.")
    # Mostrar información del cluster
    print(client)
