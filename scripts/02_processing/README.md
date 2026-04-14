# 02_processing

Utilities for computing the Combined Land Degradation Index (CLDI) from spectral indices.

## Scripts

### `cldi_processor.py`
Defines functions used by the analysis notebook to compute per-pixel CLDI scores and assign degradation labels.

**CLDI formula:**
```
CLDI = 0.5 * (1 - NDVI_norm) + 0.3 * BSI_norm + 0.2 * SI_norm
```

All index columns are normalised to [0, 1] with `MinMaxScaler` before combining.

**Classification thresholds:**
| CLDI range | Label |
|---|---|
| > 0.5 | Degraded |
| 0.3 – 0.5 | Stable |
| < 0.3 | Improved |

This module is imported by `notebooks/analysis.ipynb` and `scripts/03_modeling/ml_classifier.py`. It is not normally run as a standalone script, but contains a `__main__` block for testing:

```bash
cd scripts/02_processing
python cldi_processor.py
```

## Note on label circularity

CLDI labels are derived from the same NDVI, BSI, and SI values used as classifier features. The Random Forest in `03_modeling/` therefore learns the CLDI threshold function, not an independent degradation signal. See `README.md` (repo root) for a full discussion of this limitation.
