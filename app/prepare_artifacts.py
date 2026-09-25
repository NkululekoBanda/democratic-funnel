"""Copy the small files the dashboard needs into app/artifacts/.

The deployed app (Streamlit Community Cloud) only sees what is in the GitHub repo, and data
normally lives on the Drive. This script copies the three files the dashboard reads:

    data/processed/master.csv            -> app/artifacts/master.csv
    data/processed/predictions_2026.csv  -> app/artifacts/predictions_2026.csv
    data/interim/boundaries.gpkg         -> app/artifacts/municipalities.geojson  (simplified, small)

Run it after 08_model, then commit app/artifacts/ to GitHub:

    python app/prepare_artifacts.py                   # uses src/config.py paths (Drive on Colab)
    DIRISA_ROOT="G:/My Drive/DIRISA_SDC" python app/prepare_artifacts.py

All three files are public, aggregate data (no personal information).
"""
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from src.config import INTERIM, PROCESSED  # noqa: E402

ARTIFACTS = Path(__file__).resolve().parent / "artifacts"
ARTIFACTS.mkdir(exist_ok=True)

for name in ["master.csv", "predictions_2026.csv"]:
    shutil.copy(PROCESSED / name, ARTIFACTS / name)
    print(f"copied {name}")

boundaries = INTERIM / "boundaries.gpkg"
if boundaries.exists():
    import geopandas as gpd

    gdf = gpd.read_file(boundaries)[["muni_code", "geometry"]].to_crs(epsg=4326)
    # ~1 km tolerance: plenty for a national map, and keeps the file small enough for Git
    gdf["geometry"] = gdf.geometry.simplify(0.01, preserve_topology=True)
    out = ARTIFACTS / "municipalities.geojson"
    gdf.to_file(out, driver="GeoJSON", COORDINATE_PRECISION=4)
    print(f"wrote {out.name}: {len(gdf)} municipalities, {out.stat().st_size / 1e6:.1f} MB")
else:
    print(f"{boundaries} not found - the dashboard will run without the map")
