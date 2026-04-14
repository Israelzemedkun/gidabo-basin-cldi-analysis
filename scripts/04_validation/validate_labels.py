"""
validate_labels.py

Purpose: Validate CLDI-derived degradation labels against ESA WorldCover 2021
as an independent ground reference. This script tests whether points labelled
"Degraded" by our CLDI formula correspond to land cover classes that are
independently consistent with degradation in the Ethiopian Rift Valley context.

Academic rationale: CLDI labels are derived from Landsat spectral indices, so
using another Landsat-derived product to validate them would be circular. ESA
WorldCover 2021 is based on Sentinel-1 SAR and Sentinel-2 optical data at 10 m
resolution and is therefore a genuinely independent reference.
"""

import os
import ee
import pandas as pd

# ---------------------------------------------------------------------------
# Step 1 - Load the CSV
# ---------------------------------------------------------------------------
data_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'data', 'gidabo_degradation_samples.csv')
)
df = pd.read_csv(data_path)
print(f"Loaded {len(df)} samples.")
print(f"Degradation_Status distribution:\n{df['Degradation_Status'].value_counts().to_string()}\n")

# ---------------------------------------------------------------------------
# Step 2 - Extract ESA WorldCover 2021 values from GEE
#
# WorldCover v200 is the 2021 product. It is derived from Sentinel-1 and
# Sentinel-2, making it independent of our Landsat-based CLDI labels.
# ---------------------------------------------------------------------------
print("Initialising Google Earth Engine...")
try:
    ee.Initialize(project='ee-my-israelzemedkungebre')
except Exception:
    ee.Authenticate()
    ee.Initialize(project='ee-my-israelzemedkungebre')

worldcover = ee.Image('ESA/WorldCover/v200/2021')

# Build an ee.FeatureCollection from the CSV lat/lon points
def row_to_feature(row):
    return ee.Feature(
        ee.Geometry.Point([row['longitude'], row['latitude']]),
        {'row_index': int(row.name)}
    )

print("Building point feature collection...")
features = [row_to_feature(row) for _, row in df.iterrows()]
fc = ee.FeatureCollection(features)

# Sample the WorldCover band at each point using native 10 m resolution
print("Sampling ESA WorldCover 2021 at each point (scale=10 m)...")
sampled = worldcover.select('Map').sampleRegions(
    collection=fc,
    scale=10,
    geometries=False
)

# Retrieve results; 'Map' holds the integer land cover class value
results = sampled.getInfo()
wc_values = {
    feat['properties']['row_index']: feat['properties'].get('Map', None)
    for feat in results['features']
}

df['WorldCover_Class'] = df.index.map(wc_values)
print(f"WorldCover values extracted. Missing: {df['WorldCover_Class'].isna().sum()} points.\n")

# ---------------------------------------------------------------------------
# WorldCover class lookup table
# ---------------------------------------------------------------------------
WC_LABELS = {
    10:  'Tree cover',
    20:  'Shrubland',
    30:  'Grassland',
    40:  'Cropland',
    50:  'Built-up',
    60:  'Bare/sparse vegetation',
    70:  'Snow and ice',
    80:  'Permanent water bodies',
    90:  'Herbaceous wetland',
    95:  'Mangroves',
    100: 'Moss and lichen',
}
df['WorldCover_Label'] = df['WorldCover_Class'].map(WC_LABELS).fillna('Unknown')

# ---------------------------------------------------------------------------
# Step 3 - Classify WorldCover values as degradation-consistent or not
#
# Degradation-consistent classes for the Ethiopian Rift Valley context:
#   - Bare/sparse vegetation (60): direct indicator of severe land degradation
#   - Cropland (40): agricultural expansion is a primary driver of degradation
#   - Shrubland (20): often represents woody encroachment after forest loss
#   - Grassland (30): degraded woodland frequently transitions to grassland
#
# Degradation-inconsistent classes:
#   - Tree cover (10): intact or recovering forest - not degraded
#   - Built-up (50): urban/infrastructure - not the degradation type we model
#   - Water (80): permanent water bodies - not applicable
#   - Wetland (90): wetland - not applicable
# ---------------------------------------------------------------------------
DEGRADATION_CONSISTENT = {20, 30, 40, 60}
DEGRADATION_INCONSISTENT = {10, 50, 80, 90}

def consistency_label(wc_class):
    if wc_class in DEGRADATION_CONSISTENT:
        return 'Consistent'
    elif wc_class in DEGRADATION_INCONSISTENT:
        return 'Inconsistent'
    return 'Other'

df['WC_Consistency'] = df['WorldCover_Class'].apply(
    lambda v: consistency_label(int(v)) if pd.notna(v) else 'Unknown'
)

# ---------------------------------------------------------------------------
# Step 4 - Compute validation statistics
#
# Cross-tabulate Degradation_Status against WC_Consistency to measure how
# well CLDI-derived labels align with the independent WorldCover reference.
# ---------------------------------------------------------------------------
print("=== CROSS-TABULATION: Degradation_Status x WorldCover Consistency ===\n")
crosstab = pd.crosstab(
    df['Degradation_Status'],
    df['WC_Consistency'],
    margins=True,
    margins_name='Total'
)
print(crosstab.to_string())
print()

print("=== FULL CROSS-TABULATION: Degradation_Status x WorldCover Class ===\n")
crosstab_full = pd.crosstab(
    df['Degradation_Status'],
    df['WorldCover_Label'],
    margins=True,
    margins_name='Total'
)
print(crosstab_full.to_string())
print()

# ---------------------------------------------------------------------------
# Step 5 - Print validation summary
# ---------------------------------------------------------------------------
report_lines = []

def add(line=''):
    print(line)
    report_lines.append(line)

add("=== LABEL VALIDATION AGAINST ESA WorldCover 2021 ===")
add()

# Thresholds for the written conclusion
DEFENSIBLE_THRESHOLD = 65   # >= this % consistent -> labels are defensible
REVISION_THRESHOLD   = 50   # <  this % consistent -> labels need revision

for status in ['Degraded', 'Stable', 'Improved']:
    subset = df[df['Degradation_Status'] == status]
    n = len(subset)
    n_consistent   = (subset['WC_Consistency'] == 'Consistent').sum()
    n_inconsistent = (subset['WC_Consistency'] == 'Inconsistent').sum()
    n_other        = n - n_consistent - n_inconsistent
    pct_consistent   = 100 * n_consistent   / n if n > 0 else 0
    pct_inconsistent = 100 * n_inconsistent / n if n > 0 else 0

    # List the actual WorldCover classes found in this status group
    wc_breakdown = (
        subset.groupby('WorldCover_Label')
        .size()
        .sort_values(ascending=False)
        .to_string()
    )

    add(f"{status.upper()} points (n={n}):")
    add(f"  - {pct_consistent:.1f}% fall on degradation-consistent land cover "
        f"(Bare/Cropland/Shrubland/Grassland)  [n={n_consistent}]")
    add(f"  - {pct_inconsistent:.1f}% fall on degradation-inconsistent land cover "
        f"(Tree cover/Water/etc)  [n={n_inconsistent}]")
    if n_other > 0:
        add(f"  - {100*n_other/n:.1f}% fall on other/unclassified classes  [n={n_other}]")
    add(f"  WorldCover breakdown:")
    for line in wc_breakdown.split('\n'):
        add(f"    {line}")
    add()

# Compute the Degraded-point consistency rate for the conclusion
degraded_subset = df[df['Degradation_Status'] == 'Degraded']
n_deg = len(degraded_subset)
pct_deg_consistent = (
    100 * (degraded_subset['WC_Consistency'] == 'Consistent').sum() / n_deg
    if n_deg > 0 else 0
)

add("VALIDATION CONCLUSION:")
add(f"  If >={DEFENSIBLE_THRESHOLD}% of Degraded points fall on degradation-consistent classes -> labels are defensible")
add(f"  If < {REVISION_THRESHOLD}% -> label methodology needs revision")
add()
if pct_deg_consistent >= DEFENSIBLE_THRESHOLD:
    add(f"  RESULT: {pct_deg_consistent:.1f}% of Degraded points are on degradation-consistent "
        f"WorldCover classes.")
    add("  CONCLUSION: CLDI-derived labels are defensible as training targets for the "
        "Random Forest classifier.")
elif pct_deg_consistent >= REVISION_THRESHOLD:
    add(f"  RESULT: {pct_deg_consistent:.1f}% of Degraded points are on degradation-consistent "
        f"WorldCover classes.")
    add("  CONCLUSION: Moderate alignment. Labels are borderline defensible but consider "
        "reviewing CLDI threshold or weighting.")
else:
    add(f"  RESULT: {pct_deg_consistent:.1f}% of Degraded points are on degradation-consistent "
        f"WorldCover classes.")
    add("  CONCLUSION: Poor alignment. Label methodology needs revision before the classifier "
        "results can be considered scientifically defensible.")

# ---------------------------------------------------------------------------
# Step 6 - Save results
# ---------------------------------------------------------------------------

# Save updated CSV with WorldCover columns appended
df.to_csv(data_path, index=False)
print(f"\nUpdated CSV saved to {data_path}")

# Save plain-text validation report
report_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', 'data', 'label_validation_report.txt')
)
with open(report_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(report_lines) + '\n')
print(f"Validation report saved to {report_path}")
