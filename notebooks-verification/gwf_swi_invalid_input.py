# ---
# jupyter:
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Configurations the SWI Package does not allow
#
# Each small model below uses a configuration that the SWI Package rejects. The
# model is run, it must stop, and the error it reports is shown in the table.
#
# | Model | Configuration |
# | --- | --- |
# | `swi-xt3d` | SWI with the XT3D formulation |
# | `swi-hfb` | SWI with the HFB Package |
# | `swi2f-grid` | Freshwater and saltwater models with different cell bottoms |
# | `swi2f-sy` | Freshwater and saltwater models with different specific yield (SY) |
# | `swi2f-tvg` | A two-fluid freshwater model with a TVG file for the saltwater head, which the saltwater model simulates |
#
# Two other notebooks also run models that must stop with an error:
# `gwf_swi_require_sy` (storage without SY) and `gwf_swi_wel_afr` (an out-of-range
# well flow reduction).
#
# The five models are from `autotest/test_gwf_swi_checks.py` on the `feat-swi` branch
# of
# [christianlangevin/modflow6](https://github.com/christianlangevin/modflow6/tree/feat-swi).
# Its other four cases, which must run, are not included.

# %%
from pathlib import Path

import flopy
import numpy as np
import pandas as pd

# %% [markdown]
# ## Model parameters
#
# Model files are written to `models/<case>/` beside the notebooks, and output
# to its `output/` subdirectory.

# %%
root = next(p for p in (Path.cwd(), *Path.cwd().parents) if (p / "pixi.toml").exists())
model_root = root / "notebooks-verification" / "models"

name = "swi"
# text that the error in mfsim.lst must contain
errors = {
    "swi-xt3d": "cannot be used with XT3D",
    "swi-hfb": "cannot be used with the HFB Package",
    "swi2f-grid": "cell bottoms, and cell areas",
    "swi2f-sy": "Specific yield (SY) must be the same",
    "swi2f-tvg": "A TVG file supplies SALTWATER_HEAD",
}

# %% [markdown]
# ## Build the models


# %%
def get_ims(sim):
    return flopy.mf6.ModflowIms(
        sim,
        outer_maximum=200,
        inner_maximum=300,
        outer_dvclose=1.0e-8,
        inner_dvclose=1.0e-9,
        linear_acceleration="bicgstab",
    )


def get_oc(gwf, mname):
    return flopy.mf6.ModflowGwfoc(
        gwf,
        budget_filerecord=f"output/{mname}.bud",
        head_filerecord=f"output/{mname}.hds",
        saverecord=[("HEAD", "ALL"), ("BUDGET", "ALL")],
    )


def build_strip(ws, case):
    """Confined five-cell strip between two CHD cells."""
    sim = flopy.mf6.MFSimulation(sim_name=name, sim_ws=ws, exe_name="mf6")
    flopy.mf6.ModflowTdis(sim)
    get_ims(sim)
    gwf = flopy.mf6.ModflowGwf(
        sim, modelname=name, save_flows=True, newtonoptions="newton"
    )
    flopy.mf6.ModflowGwfdis(
        gwf, nlay=1, nrow=1, ncol=5, delr=100.0, delc=1.0, top=0.0, botm=-10.0
    )
    flopy.mf6.ModflowGwfic(gwf, strt=1.0)
    flopy.mf6.ModflowGwfnpf(gwf, icelltype=0, k=10.0, xt3doptions=(case == "swi-xt3d"))
    flopy.mf6.ModflowGwfswi(gwf)
    if case == "swi-hfb":
        flopy.mf6.ModflowGwfhfb(
            gwf, stress_period_data=[[(0, 0, 1), (0, 0, 2), 1.0e-3]]
        )
    flopy.mf6.ModflowGwfchd(
        gwf, stress_period_data=[[(0, 0, 0), 1.0], [(0, 0, 4), 0.5]]
    )
    get_oc(gwf, name)
    return sim


def build_two_fluid(ws, case):
    """Two-fluid strip whose saltwater model differs from the freshwater model."""
    sim = flopy.mf6.MFSimulation(sim_name=name, sim_ws=ws, exe_name="mf6")
    flopy.mf6.ModflowTdis(sim, nper=1, perioddata=[(10.0, 5, 1.0)])
    ims = get_ims(sim)
    models = []
    for mname in ("freshwater", "saltwater"):
        is_salt = mname == "saltwater"
        gwf = flopy.mf6.ModflowGwf(
            sim, modelname=mname, save_flows=True, newtonoptions="newton"
        )
        botm = -81.0 if (is_salt and case == "swi2f-grid") else -80.0
        flopy.mf6.ModflowGwfdis(
            gwf, nlay=1, nrow=1, ncol=5, delr=100.0, delc=1.0, top=10.0, botm=botm
        )
        flopy.mf6.ModflowGwfic(gwf, strt=0.0 if is_salt else 0.001)
        flopy.mf6.ModflowGwfnpf(gwf, icelltype=1, k=10.0)
        sy = 0.25 if (is_salt and case == "swi2f-sy") else 0.2
        flopy.mf6.ModflowGwfsto(gwf, iconvert=1, ss=0.0, sy=sy, transient={0: True})
        if case == "swi2f-tvg" and not is_salt:
            swi = flopy.mf6.ModflowGwfswi(gwf, tvg6_filerecord=f"{mname}.swi.tvg")
            swi.tvg.initialize(
                auxiliary=["saltwater_head"], aux={0: [np.full((1, 1, 5), 0.0)]}
            )
        else:
            flopy.mf6.ModflowGwfswi(gwf)
        flopy.mf6.ModflowGwfchd(
            gwf, stress_period_data=[[(0, 0, 0), 0.0], [(0, 0, 4), 0.0]]
        )
        get_oc(gwf, mname)
        models.append(gwf)
    flopy.mf6.ModflowSwiswi(
        sim, exgtype="SWI6-SWI6", exgmnamea="freshwater", exgmnameb="saltwater"
    )
    sim.register_ims_package(ims, [m.name for m in models])
    return sim


def error_report(ws):
    """Text of the error report in mfsim.lst."""
    lines = (ws / "mfsim.lst").read_text().splitlines()
    report = []
    for line in lines[lines.index("ERROR REPORT:") + 2 :]:
        if not line.strip():
            break
        report.append(line.strip())
    return " ".join(report)


# %% [markdown]
# ## Run the models and check the errors
#
# Each model must stop, with an error that contains the expected text.

# %%
rows = []
for case, message in errors.items():
    ws = model_root / case
    (ws / "output").mkdir(parents=True, exist_ok=True)
    build = build_two_fluid if case.startswith("swi2f") else build_strip
    sim = build(ws, case)
    sim.write_simulation(silent=True)
    success, _ = sim.run_simulation(silent=True)
    assert not success, f"{case} should stop with an error"
    report = error_report(ws)
    assert message in report, f"{case}: '{message}' is not in '{report}'"
    rows.append({"Model": case, "Error": report})

pd.set_option("display.max_colwidth", None)
pd.DataFrame(rows).set_index("Model")
