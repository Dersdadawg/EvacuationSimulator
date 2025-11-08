"""Visualization module - Pygame UI, rendering, and exports"""

# Import only charts by default (no pygame dependency)
from .charts import ChartGenerator

# Lazy imports for pygame-dependent modules
def _get_visualizer():
    from .visualizer import Visualizer
    return Visualizer

def _get_renderer():
    from .renderer import Renderer
    return Renderer

__all__ = ['ChartGenerator', 'Visualizer', 'Renderer']

# Provide access via attributes
def __getattr__(name):
    if name == 'Visualizer':
        return _get_visualizer()
    elif name == 'Renderer':
        return _get_renderer()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

