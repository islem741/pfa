# tracker.py
# Un chronomètre pour mesurer le temps d'exécution.
# Utilisation avec "with" (context manager).

import time
import logging
from dataclasses import dataclass
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@dataclass
class TimingRecord:
    label:      str
    latency_ms: int = 0


@contextmanager
def track_latency(label: str):
    """
    Chronomètre automatique.
    
    Exemple :
        with track_latency("llm_call") as t:
            response = gateway.complete(...)
        print(t.latency_ms)   # ex: 1243 ms
    """
    record = TimingRecord(label=label)
    start  = time.monotonic()
    try:
        yield record
    finally:
        record.latency_ms = int((time.monotonic() - start) * 1000)
        logger.info("latency label=%s ms=%d", label, record.latency_ms)