"""Module de télémesure et d'observabilité fondé sur l'écosystème LangChain."""
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional
from langchain_core.callbacks import BaseCallbackHandler

logger = logging.getLogger("ai_orchestration")


def setup_observability():
    """Initialise le formatage et l'écriture des logs en console et fichier."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "orchestration.log"

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Handler console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Handler fichier pour écriture persistante
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger("ai_orchestration")
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)


class JumboTelemetryCallbackHandler(BaseCallbackHandler):
    """Handler de callbacks LangChain enregistrant la télémesure des outils et LLM."""

    def __init__(self):
        super().__init__()
        self._tool_start_times: Dict[str, float] = {}

    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        run_id: Optional[Any] = None,
        **kwargs: Any,
    ) -> None:
        """Déclenché au lancement d'un outil LangChain."""
        tool_name = serialized.get("name", "outil_inconnu")
        if run_id:
            self._tool_start_times[str(run_id)] = time.perf_counter()
        logger.info(f"Lancement de l'outil {tool_name} avec les arguments: {input_str}")

    def on_tool_end(
        self,
        output: Any,
        run_id: Optional[Any] = None,
        **kwargs: Any,
    ) -> None:
        """Déclenché à la fin d'exécution réussie d'un outil."""
        start_time = self._tool_start_times.pop(str(run_id), None) if run_id else None
        duration_ms = ((time.perf_counter() - start_time) * 1000) if start_time else 0.0
        logger.info(f"Outil terminé avec succès en {duration_ms:.2f}ms")

    def on_tool_error(
        self,
        error: BaseException,
        run_id: Optional[Any] = None,
        **kwargs: Any,
    ) -> None:
        """Déclenché lors d'une erreur d'exécution d'un outil."""
        start_time = self._tool_start_times.pop(str(run_id), None) if run_id else None
        duration_ms = ((time.perf_counter() - start_time) * 1000) if start_time else 0.0
        logger.error(f"Échec de l'outil après {duration_ms:.2f}ms: {error}")

    def on_chain_error(
        self,
        error: BaseException,
        run_id: Optional[Any] = None,
        **kwargs: Any,
    ) -> None:
        """Déclenché lors d'une erreur d'exécution de chaîne ou graphe."""
        logger.error(f"Erreur d'exécution du workflow: {error}")
