# ---
# jupyter:
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Cross sections of the island models
#
# Freshwater and saltwater along the model rows of figure 26 of Izuka and
# Rotzoll (2023), from the MODFLOW-2005 SWI2 output of the data release and from
# the converted MODFLOW 6 model where it has been run in
# `notebooks/models/<island>/` (see `compare_mf2005_mf6`). Two more panels show
# where the two models differ in freshwater and the MODFLOW 6 minus MODFLOW-2005
# interface and head along the row, in feet, positive where MODFLOW 6 is higher.
# Figures are written to `figures/`.
#
# Run `pixi run get-data` first.

# %%
import sys
from pathlib import Path

import matplotlib.pyplot as plt

root = next(p for p in (Path.cwd(), *Path.cwd().parents) if (p / "pixi.toml").exists())
sys.path.insert(0, str(root / "scripts"))
from cross_sections import (
    SECTIONS,
    interface_difference,
    mf6_results,
    mf2005_results,
    plot_cross_section,
    plot_difference,
    plot_difference_profile,
)
from mf2005_to_mf6 import default_ws

# %% [markdown]
# ## Scenario
#
# Scenario 0 is the Current scenario (2010 conditions) shown in figure 26.

# %%
scenario = 0
islands = ["kauai", "oahu", "maui"]

# %% [markdown]
# ## Plot the cross sections

# %%
figures = root / "figures"
figures.mkdir(exist_ok=True)
for island in islands:
    mf2005 = mf2005_results(island, scenario)
    ws = default_ws(island, scenario)
    mf6 = (
        mf6_results(ws, island) if (ws / "output" / f"{island}.zta").exists() else None
    )
    ratios = [1.0] if mf6 is None else [1.0, 1.0, 1.0, 0.6]
    fig, axes = plt.subplots(
        len(ratios),
        1,
        figsize=(10, 3.4 * sum(ratios)),
        sharex=True,
        height_ratios=ratios,
        constrained_layout=True,
        squeeze=False,
    )
    axes = axes[:, 0]
    plot_cross_section(axes[0], island, mf2005, mf2005, "MODFLOW-2005 SWI2")
    if mf6 is not None:
        plot_cross_section(axes[1], island, mf2005, mf6, "MODFLOW 6 SWI")
        plot_difference(axes[2], island, mf2005, mf2005, mf6)
        plot_difference_profile(axes[3], island, mf2005, mf2005, mf6)
        axes[1].sharey(axes[0])
        axes[2].sharey(axes[0])
        d = interface_difference(island, mf2005, mf2005, mf6)
        print(
            f"{island:6s} interface, MODFLOW 6 minus MODFLOW-2005: "
            f"n={d['cells']:4d}  mean={d['mean']:8.1f} ft  "
            f"max |d|={d['max_abs']:7.1f} ft"
        )
    axes[-1].set_xlabel("Distance along the row, in miles")
    # one legend for the entries of every panel, outside so it hides no results
    entries = {}
    for ax in axes:
        for handle, label in zip(*ax.get_legend_handles_labels()):
            entries.setdefault(label, handle)
    fig.legend(
        entries.values(),
        entries.keys(),
        loc="outside lower center",
        fontsize=8,
        ncol=4,
    )
    fig.savefig(
        figures / f"cross_section_{island}_{scenario}.png",
        dpi=300,
        transparent=False,
    )
plt.show()

# %% [markdown]
# ## Rows
#
# The model rows, which are one-based as in figure 26.

# %%
for island, (row, left, right) in SECTIONS.items():
    print(f"{island:6s} row {row:3d}  {left}-{right}")

# %% [markdown]
# ## Reference
#
# Izuka, S.K., and Rotzoll, K., 2023, Volcanic aquifers of Hawaii--Contributions
# to assessing groundwater availability on Kauai, Oahu, and Maui: U.S. Geological
# Survey Professional Paper 1876, https://doi.org/10.3133/pp1876.
