# 03_modeling

Random Forest classifier training, evaluation, and model persistence.

## Scripts

### `ml_classifier.py`
Trains a Random Forest classifier on CLDI-derived degradation labels and evaluates it with held-out test data and stratified k-fold cross-validation.

**Run after** `01_data_extraction/generate_csv_data.py` has produced `data/gidabo_degradation_samples.csv`.

```bash
cd scripts/03_modeling
python ml_classifier.py
```

**What it does:**
1. Loads `data/gidabo_degradation_samples.csv`
2. Normalises `NDVI_2000`, `NDVI_2024`, `BSI_2000`, `BSI_2024`, `SI_2000`, `SI_2024` with `MinMaxScaler`
3. Computes CLDI and assigns `Degradation_Status` labels (via `02_processing/cldi_processor.py`)
4. Trains `RandomForestClassifier(n_estimators=100, random_state=42)` on 80% of data
5. Evaluates on 20% test split and via 5-fold cross-validation
6. Saves the trained model to `models/rf_model.pkl`

**Console output:** accuracy, precision/recall/F1 per class, confusion matrix, CV accuracy (mean ± std).

## Model performance

| Metric | Value |
|---|---|
| Test accuracy | ~97% |
| CV accuracy (5-fold) | 95% ± ~2% |

**Interpretation:** These figures reflect the model's ability to replicate CLDI threshold decisions from the raw index values — not independent degradation detection ability. See the Limitations section of `README.md`.
