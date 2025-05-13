# File: anima_autoconsciencia.py
import logging

logger = logging.getLogger(__name__)

class AutoconscienciaFinanciera:
    """
    Controla suspensión temporal basada en drawdown % y derrotas consecutivas,
    y recupera automáticamente cuando la cuenta se normaliza.
    """

    def __init__(self, config):
        ac_cfg = config.get("autoconsciencia", {})
        self.max_drawdown_pct = ac_cfg.get("max_drawdown_pct", 0.1)  # 10%
        self.max_losses = ac_cfg.get("max_derrotas_consecutivas", 4)
        self.suspender_por_riesgo = ac_cfg.get("suspender_si_riesgo", True)

        self.peak_balance = None
        self.current_losses = 0
        self.suspended = False

    def evaluar_estado(self, resultado: str, balance_actual: float) -> bool:
        """
        Llamar tras cada trade. Devuelve True si seguimos activos, False si debemos suspender.
        Recupera suspensión si balance supera el peak anterior.
        """
        # Inicializa peak
        if self.peak_balance is None or balance_actual > self.peak_balance:
            self.peak_balance = balance_actual
            if self.suspended:
                self.suspended = False
                logger.info("Autoconsciencia: cuentas en nuevo máximo. Reactivando sistema.")

        # Actualiza racha de pérdidas
        if resultado == "LOSS":
            self.current_losses += 1
        else:
            self.current_losses = 0

        # Calcula drawdown %
        drawdown_pct = (self.peak_balance - balance_actual) / self.peak_balance if self.peak_balance else 0.0

        logger.debug(
            f"Autoconsciencia: losses={self.current_losses}, "
            f"drawdown={drawdown_pct:.2%}"
        )

        if not self.suspender_por_riesgo:
            return True

        # Suspender por racha de pérdidas
        if self.current_losses >= self.max_losses:
            self.suspended = True
            logger.warning(
                f"Autoconsciencia: {self.current_losses} pérdidas consecutivas ≥ {self.max_losses}. Suspendiendo."
            )
            return False

        # Suspender por drawdown
        if drawdown_pct >= self.max_drawdown_pct:
            self.suspended = True
            logger.warning(
                f"Autoconsciencia: drawdown {drawdown_pct:.2%} ≥ {self.max_drawdown_pct:.2%}. Suspendiendo."
            )
            return False

        return not self.suspended

    def esta_suspendido(self) -> bool:
        return self.suspended
