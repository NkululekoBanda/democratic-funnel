# The Democratic Funnel
**Where local democracy leaks before 4 November 2026** — Team UL, DIRISA Student Datathon Challenge 2026

We decompose each municipality's participation shortfall into a **registration leak** (eligible adults not registered)
and a **turnout leak** (registered voters not voting), forecast 2026 turnout, and explain the factors associated
with each municipality's risk, delivered through an interactive dashboard.

## Repository layout
```
src/            shared code: config (paths), io_utils (robust readers), privacy
notebooks/      one notebook per pipeline stage, run in order (00_setup first)
web/            the dashboard: Flask + HTML, Chart.js charts and a Leaflet map
app/artifacts/  the small data files the dashboard reads (written by 09_dashboard_prep)
docs/           sources.csv - every dataset, URL, access date, snapshot date
data/           raw -> interim -> processed   (not in Git; lives on the shared Drive)
models/         trained models                (not in Git)
reports/figures charts for slides             (not in Git)
```

## Where things live
| | Location |
|---|---|
| Code | This GitHub repo |
| Data, models, figures | Shared Drive folder `DIRISA_SDC` |

`src/config.py` resolves paths automatically:
1. `DIRISA_ROOT` environment variable, if set (e.g. the Drive-for-Desktop folder `G:/My Drive/DIRISA_SDC`)
2. Colab -> `/content/drive/MyDrive/DIRISA_SDC`
3. Otherwise -> this repo (so judges can run it with data placed in `data/`)

## Setup
**Colab:** open `notebooks/00_setup.ipynb` and run all. (One-time: add a shortcut to `DIRISA_SDC` in My Drive; for a
private repo, add a `GITHUB_TOKEN` in Colab Secrets.)

**Local (PyCharm / VS Code):**
```bash
git clone https://github.com/Thato20-M/democratic-funnel.git
cd democratic-funnel
python -m venv .venv && .venv\Scripts\activate      # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
# optional: point at the shared data synced by Google Drive for Desktop
setx DIRISA_ROOT "G:\My Drive\DIRISA_SDC"            # macOS/Linux: export DIRISA_ROOT=...
pip install -r web/requirements.txt && python web/app.py   # dashboard on http://localhost:5000
```

## Reproducing the results
1. Download each source listed in `docs/sources.csv` into `data/raw/<raw_folder>/`
2. Run the notebooks in numeric order
3. Package versions used are logged in `environment.json` by `00_setup`

## Data and privacy
All data is publicly available; sources and access dates are in `docs/sources.csv`.
Candidate lists contain personal information: personal columns are dropped on load (`src/privacy.py`),
only aggregate counts are kept, and the raw files are never committed.
