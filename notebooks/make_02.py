"""Writes notebooks/02_analysis.ipynb. Run: uv run python notebooks/make_02.py"""
import nbformat as nbf

md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
cells = [
md("""# 02. Analysis: heat and cooling inequality in Nairobi

This notebook runs `src/analysis/` and shows each answer in story order. The numbers used in the story are written to `analysis/results.json` and then to `analysis/FINDINGS.md`, so every number can be traced to a function.

All temperatures are **land surface temperature** from Landsat 8 and 9 (how hot the ground and roofs were on clear mornings, measured at about 100 m), except question 8, which uses air temperature from a weather model."""),
code("""import sys, os, json
from pathlib import Path
ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
os.chdir(ROOT); sys.path.insert(0, str(ROOT))
import pandas as pd
from IPython.display import Image, Markdown, display
from src.analysis import core, checks, web, figures, findings
res = core.main()
pd.set_option("display.precision", 1)"""),
md("## 1. Where is Nairobi hottest on a hot day?"),
code("""display(Image("outputs/figures/hero_map_hot_season.png", width=900))
{k: v for k, v in res["q1"].items() if not isinstance(v, list)}"""),
code("""pd.read_csv("analysis/tables/ward_stats.csv")[["ward_name", "lst_median_c", "lst_anomaly_c", "pop_total", "tree_pct", "rank_hottest"]].head(10)"""),
md("## 2. How big is the gap between the hottest and coolest places?"),
code("""res["q2"]"""),
md("## 3. What do the hottest places have in common?"),
code("""display(Image("outputs/figures/chart_tree_cover_bands.png", width=750))
display(Image("outputs/figures/chart_landcover.png", width=750))
pd.read_csv("analysis/tables/lst_by_landcover.csv")"""),
md("## 4. Who lives in the hottest places?"),
code("""display(Image("outputs/figures/table_top_wards.png", width=700))
{k: v for k, v in res["q4"].items() if k != "top10_pop_weighted"}"""),
md("""## 5. How does a park cool its neighbours?

Built-up cells only, in 100 m rings outside the park edge. The signal is small and noisy; see F9 in FINDINGS for how far to trust it."""),
code("""pd.read_csv("analysis/tables/park_rings.csv").pivot(index="ring_to_m", columns="park", values="median_c")"""),
md("## 6. Is it getting hotter as the city grows?"),
code("""display(Image("outputs/figures/chart_hot_season_by_year.png", width=750))
print("Mann-Kendall:", res["q6"]["mann_kendall_trend"], "p =", res["q6"]["mann_kendall_p"])
pd.read_csv("analysis/tables/ghsl_built_by_epoch.csv")"""),
md("## 7. How unequal is the heat?"),
code("""q7 = res["q7"]
pd.DataFrame({k: {kk: vv for kk, vv in q7[k].items() if kk != "wards"} for k in ("hottest_fifth", "coolest_fifth")})"""),
md("## 8. Hot one day, cool the next (air temperature)"),
code("""display(Image("outputs/figures/chart_daily_air_temp.png", width=900))
{k: v for k, v in res["q8"].items() if k != "days_above_p90_by_year"}"""),
md("## Independent checks"),
code("""chk = checks.main()
{k: (v.get("match") if isinstance(v, dict) and "match" in v else v) for k, v in chk.items()}"""),
md("## Write FINDINGS.md"),
code("""findings.main()
print(Path("analysis/FINDINGS.md").read_text()[:1500])"""),
]
nb = nbf.v4.new_notebook(cells=cells, metadata={"kernelspec": {"name": "python3", "display_name": "Python 3"}})
nbf.write(nb, "notebooks/02_analysis.ipynb")
