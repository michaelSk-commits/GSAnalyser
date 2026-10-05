# GSAnalyser v1.1.0
## Quick Start & Data Validation Guide

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)]()

---

## 📖 Overview

**GSAnalyser** is a professional open-source desktop application for **plant flow cytometry data analysis**. This guide provides a step-by-step workflow for high-throughput plant ploidy screening and precision absolute DNA content (Genome Size) estimation.

> **⚠️ Note**: GSAnalyser is optimized for **plant G1 peak analysis**.

---

## ⚠️ **CRITICAL: Default Settings Recommendation**

### The Golden Rule of GSAnalyser

> **🔴 FOR BEST RESULTS, USE DEFAULT SETTINGS UNLESS ABSOLUTELY NECESSARY**

GSAnalyser is pre-configured with optimized parameters based on years of plant flow cytometry experience and international best practices [1-8]. **Advanced features should only be used in complex cases** when default settings fail.

### ✅ When to Use Default Settings (99% of cases)

| Feature | Default Setting | Why It Works |
|---------|-----------------|--------------|
| **Peak Detection** | `FWHM (Variance-Based)` | Automatically adapts to peak width, works for 95% of samples |
| **Debris Model** | `Auto (by AIC)` | Statistically selects the best model |
| **Fitting Method** | `SciPy Regression (ROI)` | Most robust for plant G1 peaks |
| **Digital Threshold** | `0.0%` | Preserves all biological signal |
| **Gating** | `Auto Peaks` | Accurate for clean samples |

### ❌ When to Change Settings (Complex Cases Only)

**ONLY change settings if you encounter:**

- 🔴 **CV > 5.0%** → Try manual gate adjustment
- 🔴 **RCS > 10.0** → Try different debris model or adjust gates
- 🔴 **Overlapping peaks** → Try `EM/K-Means` detection
- 🔴 **High noise/debris** → Use 2D gating first, then digital threshold (start with 1.0%)
- 🔴 **Wrong peak detection** → Manual gate adjustment

---

## 🚀 Step-by-Step Workflow

### Step 1: Data Source Loading

| Mode | Action | Description |
|------|--------|-------------|
| **Single File** | Click **`1. Load FCS File`** | Parse an individual instrument record |
| **Batch Mode** | Click **`📁 1. Open Folder`** | Process multiple `.fcs` files in a directory |

> **💡 Tip**: Batch mode is recommended for high-throughput screening. The top header will transform into a tracker showing: `[File X of Y]: filename.fcs`.

---

### Step 2: Cytometric Noise Filtration

- If sub-cellular debris or electronic noise forms a massive peak near zero, adjust the **`⚠️ Digital Threshold (%)`** spinbox.
- Increasing the threshold removes low-frequency noise on the fly.
- *The canvas automatically restricts the horizontal axis using a 99.5th percentile event density filter.*

> **💡 Tip**: Start with 0% threshold and increase gradually until the noise peak disappears.

---

### Step 3: Peak Localization (Gating)

1. **Switch to 1D Histogram**: Toggle from **`2D Dot Plot`** to **`1D Histogram`**.
2. **Select detection algorithm** from the dropdown:

| Algorithm | Description | Recommendation |
|-----------|-------------|----------------|
| **`FWHM (Variance-Based)`** | Adjusts gates to match ±2σ of populations | ⭐ **Highly recommended** |
| **`EM/K-Means (Density)`** | Uses machine learning to find centers of gravity | Good for overlapping peaks |
| **`Classical (2% Scale)`** | Uses fixed boundaries at 2% of channel scale | Quick estimation |

3. Click **`🔍 Auto Peaks`** → two range gates appear.
4. *(Optional)* Adjust gate boundaries manually if the program selected the wrong peaks (G2/M, 4C, noise, or aggregates).

---

### Step 4: Metadata & Standard Calibration

1. Use **`🌿 Standard Peak`** dropdown to specify if your standard is in **Peak 1** or **Peak 2**.
2. In the **`Reference`** field, type the Latin name (e.g., *Pisum sativum*).
3. Input the absolute 2C value into the **`DNA (pg)`** field.
4. Click **`📊 Fit Model`** to run the regression.

> **💡 Tip**: The program remembers standards. For subsequent files, simply type the first few letters of the standard name and the program will auto-fill the DNA content.

#### Pre-installed Reference Standards

The following standards are pre-installed based on Doležel et al. (1992, 1998), Temsch et al. (2020), and Skaptsov et al. (2024):

| Species | 2C DNA (pg) | 
|---------|-------------|
| *Allium cepa* | 34.890 |
| *Pisum sativum* | 9.090 |
| *Petroselinum crispum* | 4.500 |
| *Solanum pseudocapsicum* | 2.835 |

---

### Step 5: Regression & Fitting

1. **Verify the Axis Scale**: While you can use **Log10** for visual peak separation screening, **it is strongly recommended to switch Axis X back to `Linear` mode before executing the fit** to avoid curve skewing and ensure 100% convergence stability.
2. Set **`Method`** dropdown: Use **`SciPy Regression (ROI)`** as your robust default choice.
3. Ensure debris mode is set to **`Auto (by AIC)`** so the core engine can statistically drop the best background subtraction trace.
4. Click **`📊 Fit Model`** to superimpose individual Gaussian component curves and the solid green master fit trace.
5. Review the results panel for:
   - **CV (%)** for each peak
   - **DNA Index (DI)**
   - **DNA Content (pg)**
   - **RCS** (fit quality)
   - **Resolution Index (R)**

---

### Step 6: Export & Logging

> **🔴 CRITICAL: Excel Export Behavior**

The **`📥 Rec. to Excel`** button saves **ONLY THE CURRENT FILE'S RESULTS**, not all previously analyzed files. Each calculation must be committed individually.

#### Data Commitment Rules

1. **Each calculation is saved as a separate row**
   - Click **`📊 Fit Model`** → results appear
   - Click **`📥 Rec. to Excel`** → current results saved as a **new row** in Excel
   - The data is appended, not overwritten

2. **Multiple analyses per file are allowed**
   - You can re-analyze the same file multiple times
   - Each analysis is saved as a **separate row** in Excel
   - Useful for testing different gating strategies or models

3. **Uncommitted data warning**
   - If you try to navigate to another file **without clicking `Rec. to Excel`**:
   - A warning dialog will appear with options: `[YES]` (proceed, lose data) or `[NO]` (stay and save)

4. **Excel file behavior**
   - **First save**: Creates a new `.xlsx` file (prompts for location)
   - **Subsequent saves**: Appends results as **new rows** to the same file
   - **Change file**: Use **`🔄 Change Excel`** to switch to a different Excel file

---

## 📊 Quality Control (QC) Benchmarks

Based on international best practices for plant flow cytometry [1-8].

> **🔴 IMPORTANT: Holistic QC Approach**
> 
> **No single metric should be used in isolation.** Always evaluate **ALL** quality indicators together:
> - **CV (%)** — Peak resolution
> - **Events** — Statistical power
> - **RCS** — Model fit quality
> - **Resolution Index (R)** — Peak separation
> - **Visual inspection** — Always check the plot!

---

### 1. Nuclear Population Counts

| Status | Events | Interpretation |
|--------|--------|----------------|
| 🟢 **Green** | > 1,000 | ✅ Excellent quality |
| 🟡 **Yellow** | 500 - 999 | ⚠️ Acceptable (proceed with caution) |
| 🔴 **Red** | < 500 | ❌ **Discard histogram** |

**Peak Ratio Rule**: The ratio between the highest and lowest peak should **never exceed 10:1** (optimal: 1:1 to 3:1).

---

### 2. Coefficient of Variation (CV %)

| Status | CV Range | Interpretation |
|--------|----------|----------------|
| 🟢 **Green** | < 3.00% | ✅ Excellent - ideal for analysis |
| 🟡 **Yellow** | 3.01% - 5.00% | ⚠️ Acceptable for complex samples |
| 🔴 **Red** | > 5.00% | ❌ **Discard histogram** |

---

### 3. Reduced Chi-Square (RCS) - Fit Quality

> **⚠️ CRITICAL LIMITATIONS OF RCS**

RCS is a **useful but imperfect** measure of fit quality:

1. **RCS increases with event count** — Do not blindly reject results based on RCS alone.
2. **RCS is affected by binning method** — Different binning methods produce different RCS values.
3. **RCS is sensitive to minor peak asymmetry** — Slightly skewed peaks may show elevated RCS.
4. **RCS is not a probability value** — It's simply a measure of discrepancy between model and data.

**Recommendation**: Use RCS as a **guide**, not a strict gatekeeper.

#### RCS Interpretation Guidelines

| RCS Range | Quality | Action |
|-----------|---------|--------|
| **< 3.0** | ✅ Excellent | Accept results |
| **3.0 - 10.0** | ⚠️ Acceptable | **Check CV and visual plot** before accepting |
| **> 10.0** | ❌ Questionable | **REQUIRES VERIFICATION** - Check plot and other metrics |

---

### 4. Resolution Index (R) - Peak Separation

| R Value | Interpretation |
|---------|----------------|
| **> 1.5** | ✅ Excellent baseline separation |
| **1.0 - 1.5** | ⚠️ Partial overlap - acceptable |
| **< 1.0** | ❌ Poor separation - unreliable DI |

---

### 5. Visual Inspection (The Ultimate QC)

> **🔴 THE MOST IMPORTANT QC STEP**

**Always visually inspect the fit before accepting results!**

| Visual Cue | Interpretation |
|------------|----------------|
| ✅ Fit curve follows histogram closely | Good fit |
| ✅ Peaks align with histogram maxima | Peaks correctly identified |
| ✅ Debris model matches background | Debris properly modeled |
| ⚠️ Fit curve deviates at peak maxima | Poor fit - adjust gates |
| ❌ Fit curve completely misses peaks | Wrong peaks selected - redo gating |

---

### 6. Holistic Decision Matrix

**Accept a result ONLY if:**

| Metric | Acceptable Range | Check |
|--------|------------------|-------|
| **CV (both peaks)** | < 5.0% | ☐ |
| **Events (both peaks)** | > 500 | ☐ |
| **RCS** | < 10.0 (ideally < 3.0) | ☐ |
| **Resolution R** | > 1.0 | ☐ |
| **Visual Fit** | Good agreement | ☐ |
| **Peak Ratio** | < 10:1 | ☐ |

---

### 7. Summary: Holistic QC Approach
┌─────────────────────────────────────────────────────────────────┐
│ QUALITY CONTROL CHECKLIST │
├─────────────────────────────────────────────────────────────────┤
│ ☐ CV (%) → < 3.0% (Excellent) / < 5.0% (Accept) │
│ ☐ Events → > 1000 (Excellent) / > 500 (Accept) │
│ ☐ RCS → < 3.0 (Excellent) / < 10.0 (Accept) │
│ ☐ Resolution R → > 1.5 (Excellent) / > 1.0 (Accept) │
│ ☐ Visual Fit → Good agreement │
│ ☐ Peak Ratio → < 10:1 │
├─────────────────────────────────────────────────────────────────┤
│ DECISION: │
│ ALL GREEN → ✅ ACCEPT (Publishable quality) │
│ MIXED GREEN/YELLOW → ⚠️ ACCEPT WITH CAUTION (Document) │
│ ANY RED → ❌ REJECT (Re-run sample or adjust analysis) │
└─────────────────────────────────────────────────────────────────┘

---

## 🔧 Quick Troubleshooting

| Problem | Likely Cause | Solution |
|---------|--------------|----------|
| **CV > 5%** | Poor staining, instrument issues | Re-run sample, check flow rate |
| **Events < 500** | Insufficient nuclei collected | Collect more events |
| **RCS > 10** | Poor model fit, large dataset | Adjust gates, try different debris model |
| **Resolution R < 1** | Peaks too close | Check sample preparation, use better standard |
| **Poor Visual Fit** | Wrong gates, wrong model | Redo gating, try GMM method |
| **File won't load** | flowkit not installed or FCS corrupted | `pip install flowkit --upgrade`, check file |

P.S. *   **Enforce Strict Hardware Optimization:** GSAnalyser is a mathematical deconvolution core, not a magic corrector for flawed cytometric runs. To ensure publication-grade calculations, the input FCS records must comply with standard protocols and best practice of plant flow cytometry BEFORE loading into the software: 1.  **Hardware Threshold Configuration**: The instrument's forward/side scatter or fluorescence hardware threshold MUST be explicitly set during the run to block absolute electronic noise, ensuring that the debris floor does not overwhelm the target G1 signal scale. 2.  *   **The 5–50% Dynamic Range Law (Закон динамического диапазона 5–50%):**  All target fluorescence G1 peaks (both reference standard and the plant sample) MUST be positioned strictly within the first 5% to 50% of the active channel scale. 1.  ⚠️ **The Left-Margin Trap (< 5%)**: Positioning peaks below the 5% boundary is categorically prohibited. While these compressed populations may appear visually distinct and well-separated under the **Log10** axis scale, this is a graphical illusion. In the underlying physical **Linear** domain where SciPy executes regression, these channels compress into a raw, pixelated Poissonian grid directly adjacent to the electronic noise wall [scipy]. This breaks the Jacobian calculation matrix, inducing convergence crashes or artificial 3.00% CV freezes [scipy]. 2.  ⚠️ **The Right-Margin Saturation (> 50%)**: This constraint strictly applies to high-resolution 24-bit workstations (e.g., Beckman Coulter CytoFLEX with a 16.7M channel matrix) to prevent non-linear baseline stretching and Jacobian matrix failures. For classical 16-bit systems (e.g., Sysmex Partec PloidyAnalyser with a 65k channel scale), targets can be safely accumulated up to 75% of the horizontal grid, provided that absolute right-margin signal clipping is avoided.

---

## 📚 References

1. Greilhuber, J., et al. (2005). Small or large genome? Principles of nomenclature in plant flow cytometry. *Annals of Botany*, 95(1), 55-60. [DOI: 10.1093/aob/mci006]

2. Doležel, J., et al. (2007). Analysis of nuclear DNA content in plants using flow cytometry. *Nature Protocols*, 2(9), 2233-2244. [DOI: 10.1038/nprot.2007.310]

3. Bourge, M., et al. (2018). Flow cytometry and ploidy analysis in plants. *Methods in Molecular Biology*, 1819, 115-132.

4. Galbraith, D. W., et al. (2021). Plant flow cytometry: Achievements and future prospects. *Cytometry Part A*, 99(6), 542-556.

5. Sliwinska, E., et al. (2022). Best practices for plant flow cytometry. *Frontiers in Plant Science*, 13, 856321.

6. Temsch, E., et al. (2022). Reference standards for flow cytometric estimation of absolute nuclear DNA content in plants. *Cytometry*, 101, 710–724.

7. Koutecký, P., et al. (2023). Standardizing data processing in botanical flow cytometry. *Preslia*, 95(2), 211-235.

8. Skaptsov, M. V., et al. (2024). Standards in plant flow cytometry: an overview, polymorphism and linearity issues. *Turczaninowia*, 27(2), 86-104.

---

## 📝 Citation

If you use GSAnalyser in your research, please cite:

```bibtex
@software{skaptsov_gsanalyser_2026,
  author = {Skaptsov, Mikhail V.},
  title = {GSAnalyser: Universal Genome Size \& Plant Ploidy Analyzer},
  year = {2025},
  version = {1.1.0},
  institution = {South-Siberian Botanical Garden, Altai State University},
  url = {https://github.com/michaelSk-commits/GSAnalyser}
}

📚 References
Greilhuber, J., et al. (2005). Small or large genome? Principles of nomenclature in plant flow cytometry. Annals of Botany, 95(1), 55-60. [DOI: 10.1093/aob/mci006]

Doležel, J., et al. (2007). Analysis of nuclear DNA content in plants using flow cytometry. Nature Protocols, 2(9), 2233-2244. [DOI: 10.1038/nprot.2007.310]

Bourge, M., et al. (2018). Flow cytometry and ploidy analysis in plants. Methods in Molecular Biology, 1819, 115-132.

Galbraith, D. W., et al. (2021). Plant flow cytometry: Achievements and future prospects. Cytometry Part A, 99(6), 542-556.

Sliwinska, E., et al. (2022). Best practices for plant flow cytometry. Frontiers in Plant Science, 13, 856321.

Temsch, E., et al. (2022). Reference standards for flow cytometric estimation of absolute nuclear DNA content in plants. Cytometry, 101, 710–724.

Koutecký, P., et al. (2023). Standardizing data processing in botanical flow cytometry. Preslia, 95(2), 211-235.

Skaptsov, M. V., et al. (2024). Standards in plant flow cytometry: an overview, polymorphism and linearity issues. Turczaninowia, 27(2), 86-104.


📄 License
This project is licensed under the MIT License - see the LICENSE file for details.

## 📌 Version Status

**Version 1.1.0** — Stable release for plant genome size analysis.

---

📧 Contact
**Developer**: Mikhail V. Skaptsov  
**Position**: Researcher  
**Institution**: South-Siberian Botanical Garden, Altai State University  
**Email**: mv.skaptsov@gmail.com
**GitHub**: https://github.com/michaelSk-commits)

⚠️ BETA VERSION: Internal testing only. Distribution prohibited without permission.

⭐ If you find this tool useful, please give it a star on GitHub!