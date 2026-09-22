"""
Project configuration: paths and global settings.

Works in three environments without code changes:
  1. Google Colab      -> data lives on the shared Drive folder DIRISA_SDC
  2. Local + Drive     -> set env var DIRISA_ROOT to the synced Drive folder
                          (e.g. "G:/My Drive/DIRISA_SDC" with Google Drive for Desktop)
  3. Local / judges    -> falls back to the repository itself (data/ inside the repo)

Code lives in GitHub. Data, models and figures live under WORK_ROOT.
"""
import os
import sys
import random
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------- environment
REPO_ROOT = Path(__file__).resolve().parents[1]
IN_COLAB = "google.colab" in sys.modules
DRIVE_PROJECT = Path("/content/drive/MyDrive/DIRISA_SDC")


def _work_root() -> Path:
    """Where data/models/figures are read from and written to."""
    if os.environ.get("DIRISA_ROOT"):
        return Path(os.environ["DIRISA_ROOT"])
    if IN_COLAB:
        return DRIVE_PROJECT
    return REPO_ROOT


WORK_ROOT = _work_root()

# ---------------------------------------------------------------- folders
DATA = WORK_ROOT / "data"
RAW = DATA / "raw"               # original downloads - NEVER edit
INTERIM = DATA / "interim"       # cleaned tables, one per source
PROCESSED = DATA / "processed"   # master table(s) used for modelling
MODELS = WORK_ROOT / "models"    # trained models (.joblib)
FIGURES = WORK_ROOT / "reports" / "figures"

RAW_SOURCES = {
    "iec_lge":          "Municipal (LGE) results 2011 / 2016 / 2021 - one sub-folder per year",
    "iec_npe":          "National/provincial results incl. 2024 (post-COVID signal)",
    "iec_byelections":  "Municipal by-elections since Nov 2021",
    "registration":     "Voter registration dashboard extract (record snapshot date!)",
    "candidate_lists":  "LGE 2026 candidate lists - PERSONAL DATA, counts only, never commit",
    "party_stats":      "Party registration statistics",
    "ward_councillors": "Current ward councillors",
    "census":           "Stats SA Census 2022 (adjusted) + Census 2011 / CS 2016",
    "boundaries":       "Municipal Demarcation Board boundary files",
}

# Documentation (always in the repo, so it ships with the submission)
SOURCES_LOG = REPO_ROOT / "docs" / "sources.csv"

# ---------------------------------------------------------------- settings
SEED = 42
ELECTIONS_LGE = [2011, 2016, 2021, 2026]
ELECTION_DATE_2026 = "2026-11-04"


def make_dirs() -> None:
    """Create the standard folder structure. Safe to re-run."""
    for p in (INTERIM, PROCESSED, MODELS, FIGURES):
        p.mkdir(parents=True, exist_ok=True)
    for s in RAW_SOURCES:
        (RAW / s).mkdir(parents=True, exist_ok=True)


def set_seed(seed: int = SEED) -> None:
    """Seed python and numpy for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)


def describe() -> str:
    env = "Colab" if IN_COLAB else ("Local (DIRISA_ROOT)" if os.environ.get("DIRISA_ROOT") else "Local (repo)")
    return f"Environment: {env}\nRepo root:   {REPO_ROOT}\nWork root:   {WORK_ROOT}"
