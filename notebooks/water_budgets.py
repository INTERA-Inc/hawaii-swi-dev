# ---
# jupyter:
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Water budgets of the island models
#
# Global water budgets from the MODFLOW-2005 SWI2 output of the data release and
# from the converted MODFLOW 6 model where it has been run in
# `notebooks/models/<island>/` (see `compare_mf2005_mf6`). Inflows and outflows of
# each boundary are compared in million gallons per day, and the percent difference
# is MODFLOW 6 compared to MODFLOW-2005. Figures are written to `figures/`.
#
# Run `pixi run get-data` first.

# %%
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from flopy.plot import styles

root = next(p for p in (Path.cwd(), *Path.cwd().parents) if (p / "pixi.toml").exists())
sys.path.insert(0, str(root / "scripts"))
from mf2005_to_mf6 import default_ws
from water_budgets import budget_table, plot_budget

# %% [markdown]
# ## Scenario
#
# Scenario 0 is the Current scenario (2010 conditions).

# %%
scenario = 0
islands = ["kauai", "oahu", "maui"]

# %% [markdown]
# ## Compare the budgets
#
# The saltwater cells column is the part of each MODFLOW-2005 rate in cells with
# less than 1 ft of freshwater. SWI2 simulates flow of saltwater, which enters
# through the coastal boundary and leaves through the coastal boundary and through
# drains in those cells. The single-fluid MODFLOW 6 model simulates only freshwater,
# so it has almost no coastal inflow and little discharge from those cells.

# %%
tables = {}
for island in islands:
    tables[island] = budget_table(island, scenario, default_ws(island, scenario))
    print(island.title())
    print(tables[island].round(1).to_string(), end="\n\n")

# %% [markdown]
# ## Plot the budgets

# %%
figures = root / "figures"
figures.mkdir(exist_ok=True)
for island in islands:
    with styles.USGSPlot():
        fig, ax = plt.subplots(figsize=(7.5, 3.6), layout="constrained")
        plot_budget(ax, island, scenario, tables[island])
        fig.savefig(
            figures / f"water_budget_{island}_{scenario}.png", transparent=False
        )
plt.show()

# %% [markdown]
# ## Reference
#
# Rotzoll, K., and Izuka, S.K., 2023, MODFLOW-2005 and SWI2 models for assessing
# groundwater availability scenarios in volcanic aquifers on Kauai, Oahu, and
# Maui, Hawaii: U.S. Geological Survey data release,
# https://doi.org/10.5066/P97CPK5C.
