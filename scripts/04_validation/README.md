# 04_validation

Independent validation of CLDI-derived degradation labels against ESA WorldCover 2021.

## Scripts

### `validate_labels.py`
Queries ESA WorldCover 2021 land cover class for each sampled pixel and compares it to the CLDI-derived `Degradation_Status` label. WorldCover is derived from Sentinel-1 SAR + Sentinel-2 optical data at 10 m resolution — a genuinely independent data source from the Landsat-derived CLDI labels.

**Run after** `01_data_extraction/generate_csv_data.py`.

```bash
cd scripts/04_validation
python validate_labels.py
```

**What it does:**
1. Loads `data/gidabo_degradation_samples.csv`
2. For each pixel centroid, samples ESA WorldCover 2021 (`ESA/WorldCover/v200`)
3. Maps WorldCover classes to degradation-consistent / non-degradation-consistent categories in the Ethiopian Rift Valley context
4. Computes consistency rate between WorldCover classification and CLDI label
5. Writes a summary report to `data/label_validation_report.txt`

## Validation logic

WorldCover classes treated as consistent with "Degraded" CLDI label:
- Bare/sparse vegetation (class 60)
- Cropland (class 40) — in the Gidabo context, reflects woodland conversion
- Built-up (class 50)

Classes inconsistent with "Degraded":
- Tree cover (class 10)
- Shrubland (class 20)
- Grassland (class 30)
- Wetlands (class 90)

## Result

94.9% of CLDI-labelled pixels are consistent with their WorldCover class. This provides partial independent support for label validity but does not constitute field-validated ground truth.
