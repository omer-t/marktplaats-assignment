"""Re-export the SMB bundle analysis functions used by the notebooks."""

import sys
from pathlib import Path

MODULE_DIR = str(Path(__file__).resolve().parent)
if MODULE_DIR not in sys.path:
    sys.path.insert(0, MODULE_DIR)

for module_name in ["common", "q2_analysis", "q2_scoring", "q3_eda", "q3_model", "q3_charts"]:
    loaded_module = sys.modules.get(module_name)
    loaded_path = Path(getattr(loaded_module, "__file__", "")).resolve().parent if loaded_module else None
    if loaded_path and str(loaded_path) != MODULE_DIR:
        del sys.modules[module_name]

# Review route:
# - q2_analysis.py: load Q2 data and build exploratory seller summaries.
# - q2_scoring.py: score sellers for outreach and bundle targeting.
# - q3_eda.py: load Q3 data and summarize interval structure.
# - q3_model.py: build dashboard metrics, revenue, cohorts, and segments.
# - q3_charts.py: draw Q3 sales and revenue charts.

from common import *
from q2_analysis import *
from q2_scoring import *
from q3_eda import *
from q3_model import *
from q3_charts import *
