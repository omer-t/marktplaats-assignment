"""Re-export the cars analysis functions used by the notebooks."""

import sys
from pathlib import Path

MODULE_DIR = str(Path(__file__).resolve().parent)
if MODULE_DIR not in sys.path:
    sys.path.insert(0, MODULE_DIR)

for module_name in ["common", "data", "analysis", "display"]:
    loaded_module = sys.modules.get(module_name)
    loaded_path = Path(getattr(loaded_module, "__file__", "")).resolve().parent if loaded_module else None
    if loaded_path and str(loaded_path) != MODULE_DIR:
        del sys.modules[module_name]

# Review route:
# - data.py: load, clean, and prepare the analysis tables.
# - analysis.py: compute experiment checks, lift, and segment summaries.
# - display.py: format tables and draw charts.

from common import *
from data import *
from analysis import *
from display import *
