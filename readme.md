# GSAnalyser: An Open-Source Tool for Objective DNA Content Estimation and Quality Control in Plant Flow Cytometry

**Version**: 1.1.0  
**License**: MIT  
**Python**: 3.13.9 (or 3.8+)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23163447.svg)](https://doi.org/10.5281/zenodo.23163447)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/release/python-3139/)

---

## 📖 Overview

**GSAnalyser** is a high-performance desktop application for plant ploidy screening and precision absolute nuclear DNA content (2C Genome Size) calculation from instrument FCS files. 

The core feature of the software is its **decoupled computing architecture** (simulating commercial suites like CytExpert): while you can use Log10 or Biexponential scales for visual peak separation, the underlying SciPy engine always maps boundaries back into raw linear channel arrays to ensure publication-grade, un-skewed 2C statistics.

> ⚠️ **Optimized for plants**. Developed and tested on **Python 3.13.9**. Focused strictly on G1-only truncated modeling to prevent mathematical overfitting.

---

## ✨ Key Features

- 🔬 **G1 Peak Analysis**: Truncated model with automatic gating (FWHM, EM/K-Means, Classical).
- 📊 **Multi-Model Debris Subtraction**: Evaluates Exponential, Linear-Exp, and Polynomial-Exp baselines with automated Akaike Information Criterion (AIC) selection.
- 🧮 **Dual-Engine Fitting**: Powered by non-linear **SciPy regression** (ROI-focused) and unsupervised **Scikit-Learn GMM** clustering (global).
- 📁 **Batch Processing**: Smart conveyor loop with automatic layout caching and sequential Excel data tracking.
- 🎯 **Real-Time Quality Control**: Live traffic-light dashboard monitoring experiment fidelity parameters.
- 🌿 **Reference Standards Pre-sets**: Autocomplete database records for *Pisum sativum*, *Allium cepa*, etc.

---

## 🚀 Quick Start

```bash
# Install dependencies
pip install numpy pandas scipy scikit-learn PyQt6 pyqtgraph matplotlib openpyxl

# Install flowkit (may require --upgrade for Python 3.13+)
pip install flowkit --upgrade

# Run
python GSAnalyser.py
```

### Basic Workflow:
1. Load FCS directory → 2. Perform 2D gating if needed → 3. Switch to 1D Histogram (**Linear scale is strongly recommended for fitting**) → 4. Click `🔍 Auto Peaks` → 5. Set standard metadata → 6. Click `📊 Fit Model` → 7. Press `📥 Rec. to Excel`.

📖 *Full operational manual and tips: see `QUICK_GUIDE.md`*

---

## 🛠️ Standalone Executable Compilation

To compile a standalone, zero-dependency execution binary package tested on **Python 3.13.9**, run:

```bash
pyinstaller --onefile --noconsole --collect-all flowkit --collect-all pyqtgraph --collect-all PyQt6 --hidden-import=PyQt6.uic --hidden-import=flowkit --hidden-import=scipy.special.cython_special --exclude-module PyQt5 GSAnalyser.py
```

---

## 📊 Quality Control (QC) Benchmarks

The software features an automated evaluation matrix based on Best practice in flow cytometry of plants:

| Metric | Excellent (🟢) | Acceptable (🟡) | Reject (🔴) |
| :--- | :--- | :--- | :--- |
| **CV (%)** | $< 3.0\%$ | $3.0\% - 5.0\%$ | $> 5.0\%$ |
| **Events** | $> 1000$ cells | $500 - 999$ cells | $< 500$ cells |
| **RCS** | $< 3.0$ | $3.0 - 10.0$ | $> 10.0^*$ |

> ⚠️ **CRITICAL EXPERT RULES**:
> 1. **Peak Disparity Ratio**: The absolute event count ratio between the highest and lowest peaks **must not exceed 10:1** (optimal targets: 1:1 to 3:1). Over-skewed ratios induce covariance matrix weight bias, displacing minor centroids. Monitor this rule visually!
> 2. $*$ **RCS Exceptions**: For large or high-density nuclear datasets, a stable RCS between 10.0 and 15.0 combined with clean symmetric Gaussian hulls is a sign of a perfectly sound, valid fit. Never widen gates artificially just to chase an RCS = 1.0.

---

## 📚 Citation

If you utilize this computational workstation or any derived code modules in your peer-reviewed manuscripts or taxometrical screenings, please cite the engine as follows:

```bibtex
@software{skaptsov_gsanalyser_2026,
  author = {Skaptsov, Mikhail V.},
  title = {GSAnalyser: Universal Genome Size \& Plant Ploidy Analyzer},
  year = {2026},
  version = {1.1.0},
  institution = {South-Siberian Botanical Garden, Altai State University},
  note = {Open-source tool developed and validated on Python 3.13.9}
}
```

---

## 📌 Version Status

**Version 1.1.0 (Beta)** — Stable core deployment release for plant genome size analysis workflows.
- ✅ Fully tested and verified with FCS 2.0 and 3.0 records (CytoFLEX, Partec).
- ✅ Batch automation conveyor pipelines validated.
- ✅ Secure data-integrity Excel tracking and layout recovery confirmed.
- 📧 *Please report computational issues or instrument crashes directly to the GitHub Issues tracker.*

---

## 📄 License

Distributed under the open-source **MIT License** — see the `LICENSE` file for details.

---

## 📧 Contact Information

- **Developer**: Mikhail V. Skaptsov  
- **Position**: Researcher  
- **Institution**: South-Siberian Botanical Garden, Altai State University  
- **Email**: mv.skaptsov@gmail.com  
- **ORCID**: [0000-0002-4884-0768](https://orcid.org)  
- **GitHub Repository**: [michaelSk-commits/GSAnalyser](https://github.com/michaelSk-commits/GSAnalyser)
