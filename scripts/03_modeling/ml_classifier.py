import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib

# ── Load data ──────────────────────────────────────────────────────────────────
data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'gidabo_degradation_samples.csv'))
df = pd.read_csv(data_path)
# Drop columns from any previous run to avoid conflicts
cols_to_drop = [c for c in df.columns if '_norm' in c or c in ['CLDI', 'CLDI_2000']]
df = df.drop(columns=cols_to_drop)
print(f"Loaded {len(df)} samples with columns: {', '.join(df.columns)}")

# ── Normalize NDVI, BSI, SI columns to [0, 1] ─────────────────────────────────
index_cols = ['NDVI_2000', 'NDVI_2024', 'BSI_2000', 'BSI_2024', 'SI_2000', 'SI_2024']
scaler = MinMaxScaler()
normed = scaler.fit_transform(df[index_cols])
normed_df = pd.DataFrame(normed, columns=[c + '_norm' for c in index_cols], index=df.index)
df = pd.concat([df, normed_df], axis=1)

# ── Compute CLDI (2024) ────────────────────────────────────────────────────────
# NDVI weighted 0.5 (primary vegetation-loss signal at 30 m in Ethiopian Rift context)
# BSI weighted 0.3 (soil exposure follows vegetation removal)
# SI weighted 0.2 (salinity is localised to lower rift floor)
df['CLDI'] = (
    0.5 * (1 - df['NDVI_2024_norm'])
    + 0.3 * df['BSI_2024_norm']
    + 0.2 * df['SI_2024_norm']
)

# ── Compute CLDI_2000 for temporal comparison ──────────────────────────────────
df['CLDI_2000'] = (
    0.5 * (1 - df['NDVI_2000_norm'])
    + 0.3 * df['BSI_2000_norm']
    + 0.2 * df['SI_2000_norm']
)

# ── Re-derive Degradation_Status from CLDI ────────────────────────────────────
def classify_cldi(cldi):
    if cldi > 0.5:
        return 'Degraded'
    elif cldi < 0.3:
        return 'Improved'
    return 'Stable'

df['Degradation_Status'] = df['CLDI'].apply(classify_cldi)
print("\nDegradation status distribution:")
print(df['Degradation_Status'].value_counts())

# ── Features and target ────────────────────────────────────────────────────────
# Features are raw spectral indices only. CLDI is used for label generation but
# excluded from features to avoid circularity.
features = ['NDVI_2000', 'NDVI_2024', 'BSI_2000', 'BSI_2024',
            'SI_2000', 'SI_2024', 'NDVI_Change', 'SI_Change']
X = df[features]
y = df['Degradation_Status']

# ── Train / test split ─────────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# ── Random Forest classifier ───────────────────────────────────────────────────
rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X_train, y_train)
y_pred = rf.predict(X_test)

# ── Evaluation ─────────────────────────────────────────────────────────────────
print(f"\nAccuracy: {accuracy_score(y_test, y_pred):.4f}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred))
print("Confusion Matrix:")
print(confusion_matrix(y_test, y_pred, labels=['Degraded', 'Stable', 'Improved']))

# ── Validation 1: 5-fold cross-validation ─────────────────────────────────────
cv_scores = cross_val_score(
    RandomForestClassifier(n_estimators=100, random_state=42),
    X, y, cv=5, scoring='accuracy'
)
print("\n5-Fold Cross-Validation Accuracy:")
print(f"  Folds:  {[f'{s:.4f}' for s in cv_scores]}")
print(f"  Mean:   {cv_scores.mean():.4f}")
print(f"  Std:    {cv_scores.std():.4f}")

# ── Validation 2: Stratified 5-fold cross-validation ──────────────────────────
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
skf_scores = cross_val_score(
    RandomForestClassifier(n_estimators=100, random_state=42),
    X, y, cv=skf, scoring='accuracy'
)
print("\nStratified 5-Fold Cross-Validation Accuracy:")
print(f"  Folds:  {[f'{s:.4f}' for s in skf_scores]}")
print(f"  Mean:   {skf_scores.mean():.4f}")
print(f"  Std:    {skf_scores.std():.4f}")

# ── Validation 3: Learning curve ──────────────────────────────────────────────
print("\nLearning Curve (accuracy vs training set size):")
print(f"  {'Train size':>12}  {'N samples':>10}  {'Accuracy':>10}")
for frac in [0.2, 0.4, 0.6, 0.8, 1.0]:
    n = max(int(len(X_train) * frac), 1)
    X_sub, y_sub = X_train.iloc[:n], y_train.iloc[:n]
    lc_rf = RandomForestClassifier(n_estimators=100, random_state=42)
    lc_rf.fit(X_sub, y_sub)
    acc = accuracy_score(y_test, lc_rf.predict(X_test))
    print(f"  {frac*100:>11.0f}%  {n:>10}  {acc:>10.4f}")

# ── Save model ─────────────────────────────────────────────────────────────────
models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models'))
os.makedirs(models_dir, exist_ok=True)
model_path = os.path.join(models_dir, 'rf_model.pkl')
joblib.dump(rf, model_path)
print(f"\nModel saved to {model_path}")

# ── Persist updated CSV (with CLDI columns and revised Degradation_Status) ─────
df.to_csv(data_path, index=False)
print(f"Updated CSV saved to {data_path}")
