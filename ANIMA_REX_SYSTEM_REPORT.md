# Informe Técnico Exhaustivo: Anima REX

---

## 1. Resumen Ejecutivo

**Anima REX** es una plataforma modular de trading algorítmico diseñada para automatizar, optimizar y monitorizar estrategias sobre mercados financieros, con foco en IQ Option. Su propósito es permitir a traders cuantitativos, desarrolladores y equipos de investigación ejecutar estrategias complejas, realizar backtesting, optimizar parámetros mediante algoritmos genéticos y aprendizaje por refuerzo, y operar en tiempo real con tolerancia a fallos. Los usuarios principales son:

- **Traders cuantitativos**: Buscan automatizar y optimizar estrategias.
- **Desarrolladores**: Extienden el sistema con nuevas estrategias o integraciones.
- **Investigadores**: Analizan resultados y experimentan con RL y optimización evolutiva.

Los objetivos principales son: robustez operativa, extensibilidad, trazabilidad de operaciones, y capacidad de auto-optimización y aprendizaje continuo.

---

## 2. Visión General de la Arquitectura

### anima_broker.py
- **Responsabilidad:** Abstrae la conexión y operaciones con IQ Option usando `iqoptionapi`. Implementa reconexión automática, keep-alive, y métodos para comprar, consultar balance, ping, etc.
- **Relaciones:** Es consumido por el núcleo (`anima_core.py`) y los workers para ejecutar operaciones reales. Usa configuración de `anima_config`.

### anima_market.py
- **Responsabilidad:** Provee funciones para obtener datos históricos OHLCV desde el broker.
- **Relaciones:** Es llamado por `anima_data.py` para la ingesta de datos de mercado.

### anima_data.py
- **Responsabilidad:** Orquesta la descarga y almacenamiento de datos de mercado en Parquet y SQLite. Llama a `anima_market` para obtener datos y gestiona la persistencia.
- **Relaciones:** Es invocado en el arranque por `main.py` para asegurar la disponibilidad de datos históricos.

### engine/worker_pool.py
- **Responsabilidad:** Lanza hilos (`StrategyWorker`) por cada combinación de par y estrategia. Cada worker obtiene datos, ejecuta la lógica de la estrategia y publica señales en el `SignalBus`.
- **Relaciones:** Usa `anima_market` para datos, `anima_strategies` para lógica de trading, y publica en `engine/signal_bus`.

### anima_rl_agent.py
- **Responsabilidad:** Define el entorno RL (`AnimaTradingEnv`) y el agente Q-learning (`AnimaRLLightAgent`). Decide si aceptar/rechazar señales, cambiar estrategia, ajustar martingala, etc.
- **Relaciones:** Es instanciado y utilizado por el núcleo (`anima_core.py`) para la toma de decisiones inteligentes.

### anima_scheduler.py
- **Responsabilidad:** Programa tareas periódicas (ej. optimización diaria vía GA) usando `apscheduler`.
- **Relaciones:** Es invocado por `main.py` para lanzar optimizaciones automáticas.

### anima_supervisor.py
- **Responsabilidad:** Evalúa el rendimiento reciente de las operaciones y ajusta dinámicamente los niveles de martingala si la tasa de aciertos cae por debajo de un umbral.
- **Relaciones:** Es instanciado por el núcleo y consulta la configuración de martingala.

### main.py
- **Responsabilidad:** Orquesta la inicialización del sistema: carga configuración, prepara entorno, descarga datos, lanza el scheduler, inicia workers y el núcleo principal, y gestiona el shutdown.
- **Relaciones:** Es el punto de entrada y conecta todos los módulos anteriores.

---

## 3. Flujos de Datos

### 3.1. Diagrama ASCII del flujo principal

```
[config.yml]
     |
     v
[main.py] ---> [setup_env.py] ---> [Dask Cluster]
     |
     v
[anima_data.py] ---> [anima_market.py] ---> [anima_broker.py] ---> [IQ Option API]
     |
     v
[Parquet/SQLite] <---+
     |               |
     v               |
[engine/worker_pool.py] <--- [anima_strategies] 
     |
     v
[engine/signal_bus.py] <---+
     |                     |
     v                     |
[anima_core.py] <----------+
     |
     v
[anima_rl_agent.py] <--- [anima_supervisor.py]
     |
     v
[anima_broker.py] (ejecución de operaciones)
     |
     v
[anima_db.py] (registro de señales y operaciones)
```

### 3.2. Paso a paso

1. **Carga de configuración:** `main.py` lee `config.yml` usando `anima_config`.
2. **Inicialización de entorno:** `setup_env.py` configura variables de entorno y lanza un cluster Dask.
3. **Descarga de datos:** `anima_data.py` descarga OHLCV históricos usando `anima_market.py` y los almacena en Parquet y SQLite.
4. **Lanzamiento de workers:** `engine/worker_pool.py` crea hilos por cada par/estrategia, que obtienen datos y publican señales en `engine/signal_bus.py`.
5. **Consumo de señales:** `anima_core.py` consume señales, las normaliza, pasa por ensemble y RL, y decide si ejecutar la operación.
6. **Ejecución de operaciones:** Si procede, llama a `anima_broker.py` para operar en IQ Option.
7. **Registro:** Todas las señales y operaciones se registran en `anima_db.py`.
8. **Supervisión y RL:** `anima_supervisor.py` y `anima_rl_agent.py` monitorizan y ajustan la toma de decisiones y la martingala.

---

## 4. Dependencias Clave

| Librería         | Versión Recomendada | Rol en el Sistema                                      |
|------------------|--------------------|--------------------------------------------------------|
| iqoptionapi      | >=1.0.4            | Conexión y operaciones con IQ Option                   |
| Dask             | >=2023.0           | Paralelismo y cluster local para procesamiento         |
| Gym              | >=0.26             | Definición de entornos RL                              |
| PyYAML           | >=6.0              | Carga de configuración desde YAML                      |
| NumPy            | >=1.23             | Cálculo numérico, manipulación de arrays               |
| Pandas           | >=1.5              | Manipulación y almacenamiento de datos tabulares       |
| APScheduler      | >=3.9              | Programación de tareas periódicas                      |
| SQLite3          | stdlib             | Persistencia local de señales y operaciones            |
| Tkinter          | stdlib             | GUI básica para monitorización                         |
| logging          | stdlib             | Registro estructurado de eventos                       |
| threading        | stdlib             | Concurrencia y gestión de hilos                        |

---

## 5. Puntos Críticos y Riesgos

### 5.1. Ciclos de Importación
- **Error:** ImportError por ciclo entre `anima_broker`, `anima_market` y `anima_data`.
- **Causa:** Llamadas cruzadas entre módulos para obtener datos y conectar broker.
- **Solución:** Centralizar la obtención de OHLCV en `anima_data` y ajustar imports para evitar referencias circulares.

### 5.2. ModuleNotFoundError
- **Error:** ModuleNotFoundError al importar módulos no presentes en el entorno.
- **Causa:** Falta de instalación de dependencias o errores en el PYTHONPATH.
- **Solución:** Añadir requirements.txt y documentar instalación; usar virtualenv.

### 5.3. TypeError de firma
- **Error:** TypeError por firmas inconsistentes en métodos sobrescritos o decorados.
- **Causa:** Cambios en la API de IQ Option o en la definición de métodos.
- **Solución:** Revisar y unificar las firmas de métodos, especialmente en decoradores como `ensure_connection`.

### 5.4. AttributeError en broker
- **Error:** AttributeError al acceder a métodos inexistentes en el stub/mock del broker.
- **Causa:** Uso de mocks incompletos en pruebas (`demo_run.py`).
- **Solución:** Asegurar que los mocks implementen todos los métodos requeridos por la interfaz.

### 5.5. División por string
- **Error:** TypeError al intentar dividir por un string en la lógica de estrategias.
- **Causa:** Parámetros mal tipados o datos corruptos.
- **Solución:** Validar tipos y valores antes de operaciones aritméticas.

### 5.6. Otros riesgos
- **Persistencia SQLite:** Riesgo de corrupción bajo alta concurrencia.
- **Gestión de credenciales:** Almacenamiento plano en disco, sin cifrado.
- **Cambios en la API de IQ Option:** Podrían romper la reconexión y la lógica de operaciones.

---

## 6. Configuración y Despliegue

### 6.1. Renombrar carpeta y entorno virtual
1. Renombrar la carpeta raíz a `AnimaREX` (sin espacios ni caracteres especiales).
2. Crear entorno virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```
3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

### 6.2. Variables de entorno requeridas
- `BROKER_API_KEY` (si se integra con brokers que lo requieran en el futuro).
- `DASK_WORKER_MEMORY_LIMIT` (opcional, para tuning de Dask).
- `PYTHONPATH` debe incluir la carpeta raíz del proyecto.

### 6.3. Configuración
- Editar `config.yml` para definir credenciales, pares, estrategias, parámetros de martingala, RL, GA, etc.

### 6.4. Ejecución
- Lanzar el sistema:
   ```bash
   python main.py
   ```
- Para pruebas rápidas sin broker real:
   ```bash
   python demo_run.py
   ```

---

## 7. Recomendaciones y Hoja de Ruta

### 7.1. Refactor y Modularidad
- **Responsable:** Copilot, Fran
- **Tareas:**
  - Separar lógica de negocio y acceso a datos (2 días)
  - Unificar gestión de errores en una capa común (1 día)
  - Mejorar documentación de módulos y funciones (2 días)
- **Criterio de aceptación:** Código desacoplado, fácil de testear y documentado.

### 7.2. Pruebas Unitarias y de Integración
- **Responsable:** Copilot, Ánima
- **Tareas:**
  - Implementar tests para cada componente (broker, worker, RL, supervisor) (5 días)
  - Usar mocks para IQ Option y base de datos en tests (2 días)
- **Criterio de aceptación:** Cobertura >80%, tests automáticos en CI.

### 7.3. Seguridad
- **Responsable:** Fran
- **Tareas:**
  - Cifrado de credenciales en disco y memoria (2 días)
  - Validación de entradas en puntos críticos (1 día)
- **Criterio de aceptación:** Credenciales nunca en texto plano, inputs validados.

### 7.4. Monitoreo y Escalabilidad
- **Responsable:** Copilot, Ánima
- **Tareas:**
  - Logs estructurados y métricas exportables (ej. Prometheus) (2 días)
  - Alertas ante caídas de conexión o anomalías (1 día)
  - Migrar a PostgreSQL si el volumen crece (3 días)
- **Criterio de aceptación:** Logs y métricas accesibles, alertas funcionales.

### 7.5. Robustez y Tolerancia a Fallos
- **Responsable:** Fran, Copilot
- **Tareas:**
  - Persistencia de estado para recuperación tras caídas (2 días)
  - Supervisión externa (systemd, supervisord) (1 día)
- **Criterio de aceptación:** Sistema se recupera automáticamente tras fallo.

---

## 8. Conclusión

Anima REX es una plataforma avanzada y modular para trading algorítmico, con una arquitectura robusta y extensible. Se recomienda priorizar la cobertura de pruebas, la seguridad de credenciales y la monitorización para garantizar su uso en entornos productivos y de investigación.

