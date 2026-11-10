"""v2 roof check: is surface emissivity lower in dense, low-tree wards (metal roofs)?

Landsat Collection 2 surface temperature uses emissivity from ASTER GED (2000 to 2008), adjusted for
the scene's vegetation with NDVI. The Level-2 product ships that emissivity (ST_EMIS, asset `emis`)
and its uncertainty (ST_EMSD, asset `emsd`). If bare metal (mabati) roofs lower the true emissivity
but the product assumes a typical high value, the retrieved temperature there is too low.

Reads `emis` and `emsd` for the 12 hot-season scenes on the analysis grid, takes the per-cell median,
and compares wards. Writes analysis/tables/ward_emissivity.csv, rasters/emis_hot_season_median.tif
and results_extra.json["roof_emissivity"].

Run: uv run python -m src.analysis.emissivity
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
import planetary_computer
import pystac_client

from src.analysis.layers import load
from src.config import PROCESSED, RASTERS, ROOT, get_logger
from src.pipeline.s2_landsat import COLLECTION, QA_MASK_BITS, STAC, _read_band
from src.rasterio_utils import read_grid, write_cog

log = get_logger("emissivity")

DENSE_LOW_TREE = ["Mlango Kubwa", "Mabatini", "Eastleigh North", "Pangani", "Ngei"]
LEAFY = ["Karen", "Kitisuru", "Kileleshwa", "Karura", "Parklands/Highridge"]
CBD = ["Nairobi Central"]
OUT = RASTERS / "emis_hot_season_median.tif"
EXTRA = ROOT / "analysis" / "results_extra.json"


def build() -> tuple[np.ndarray, np.ndarray]:
    t, w, h = read_grid()
    if OUT.exists():
        from src.rasterio_utils import read
        return read(OUT), read(RASTERS / "emsd_hot_season_median.tif")
    meta = json.loads((PROCESSED / "composites_meta.json").read_text())
    ids = meta["hot_season"]["scenes"]
    cat = pystac_client.Client.open(STAC)
    emis, emsd = [], []
    for sid in ids:
        item = planetary_computer.sign(cat.get_collection(COLLECTION).get_item(sid))
        a = item.assets
        qa = _read_band(a["qa_pixel"].href, t, w, h)
        bad = (qa & QA_MASK_BITS) != 0
        for key, store in (("emis", emis), ("emsd", emsd)):
            sc = a[key].extra_fields["raster:bands"][0]
            dn = _read_band(a[key].href, t, w, h)
            v = dn.astype("float32") * sc.get("scale", 1e-4) + sc.get("offset", 0.0)
            v[bad | (dn == -9999) | (dn <= 0)] = np.nan
            store.append(v)
        log.info("read emis/emsd for %s", sid)
    e = np.nanmedian(np.stack(emis), axis=0).astype("float32")
    s = np.nanmedian(np.stack(emsd), axis=0).astype("float32")
    write_cog(OUT, e, t)
    write_cog(RASTERS / "emsd_hot_season_median.tif", s, t)
    return e, s


def main() -> dict:
    e, s = build()
    L = load()
    rows = []
    for i, wd in L.wards.iterrows():
        m = (L.ward_idx == i + 1) & np.isfinite(e)
        rows.append(dict(ward_name=wd.ward_name, emis_median=float(np.median(e[m])),
                         emis_p10=float(np.percentile(e[m], 10)), emsd_median=float(np.nanmedian(s[m])),
                         tree_pct=100 * float(np.nanmean(L.tree[m])), built_pct=100 * float(np.nanmean(L.built[m])),
                         lst_median_c=float(np.nanmedian(L.hot[m]))))
    df = pd.DataFrame(rows).sort_values("emis_median")
    df.round(4).to_csv(ROOT / "analysis" / "tables" / "ward_emissivity.csv", index=False)

    def grp(names):
        g = df[df["ward_name"].isin(names)]
        return dict(wards=names, emis_median=round(float(g["emis_median"].median()), 4),
                    emsd_median=round(float(g["emsd_median"].median()), 4),
                    tree_pct=round(float(g["tree_pct"].mean()), 1), lst_median_c=round(float(g["lst_median_c"].median()), 1))

    ok = L.county & np.isfinite(e)
    by_wc = {}
    names = {10: "Tree cover", 30: "Grassland", 50: "Built-up", 60: "Bare or sparse vegetation"}
    for k, n in names.items():
        m = ok & (L.wc == k)
        if m.sum() > 100:
            by_wc[n] = round(float(np.median(e[m])), 4)
    from scipy import stats
    rho = stats.spearmanr(df["emis_median"], df["built_pct"])[0]
    out = dict(
        dense_low_tree=grp(DENSE_LOW_TREE), leafy=grp(LEAFY), cbd=grp(CBD),
        county_emis_median=round(float(np.median(e[ok])), 4),
        county_emis_p05=round(float(np.percentile(e[ok], 5)), 4),
        by_landcover=by_wc,
        ward_emis_range=[round(float(df["emis_median"].min()), 4), round(float(df["emis_median"].max()), 4)],
        lowest_emis_wards=df.head(5)[["ward_name", "emis_median"]].round(4).to_dict("records"),
        spearman_emis_vs_built=round(float(rho), 2),
        scenes=12,
    )
    # Sensitivity: how much would a lower true emissivity raise the temperature? For a grey body in the
    # 10.9 um band, dT ~ T/n * d(eps)/eps with n ~ 4.5 (Planck exponent near 300 K at 10.9 um).
    T = 273.15 + out["dense_low_tree"]["lst_median_c"]
    out["sensitivity_c_per_0p01_emis"] = round(T / 4.5 * 0.01 / out["dense_low_tree"]["emis_median"], 2)
    allx = json.loads(EXTRA.read_text()) if EXTRA.exists() else {}
    allx["roof_emissivity"] = out
    EXTRA.write_text(json.dumps(allx, indent=2))
    print(json.dumps(out, indent=1))
    print(df.head(12).round(3).to_string())
    return out


if __name__ == "__main__":
    main()
