"""Camouzer — reduce facial redness and publish to a Windows virtual camera."""

from .filter import reduce_redness
from .pipeline import run_pipeline

__all__ = ["reduce_redness", "run_pipeline", "__version__"]
__version__ = "0.1.0"
