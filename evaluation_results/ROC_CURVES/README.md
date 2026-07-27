# ROC Curves

To generate ROC curves for all models, run:

```python
# This script requires matplotlib
# pip install matplotlib seaborn

from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc

# Load predictions from evaluation_results/*_results.json
# and plot ROC curves for all models
```

Data files: `evaluation_results/*_results.json`
Raw data: `evaluation_results/benchmark_raw.csv`
