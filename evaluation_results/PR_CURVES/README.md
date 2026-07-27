# PR Curves

To generate precision-recall curves for all models, run:

```python
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import precision_recall_curve, average_precision_score

# Load predictions from evaluation_results/*_results.json
# and plot PR curves for all models
```

Data files: `evaluation_results/*_results.json`
Raw data: `evaluation_results/benchmark_raw.csv`
