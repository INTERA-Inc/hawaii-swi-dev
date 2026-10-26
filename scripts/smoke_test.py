#!/usr/bin/env python
"""Build and run a small SWI model to check the installed mf6 and flopy classes.

A steady-state, one-row freshwater lens discharging to the sea at the right
edge. Model files are written to a temporary directory and output to its
output/ subdirectory.
"""

import sys
import tempfile
from pathlib import Path

import flopy


def build(ws: Path) -> flopy.mf6.MFSimulation:
    name = "swi"
    nlay, nrow, ncol = 1, 1, 20

    sim = flopy.mf6.MFSimulation(sim_name=name, sim_ws=ws, exe_name="mf6")
    flopy.mf6.ModflowTdis(sim)
    flopy.mf6.ModflowIms(sim, complexity="complex")
    gwf = flopy.mf6.ModflowGwf(sim, modelname=name, save_flows=True)
    flopy.mf6.ModflowGwfdis(
        gwf,
        nlay=nlay,
        nrow=nrow,
        ncol=ncol,
        delr=100.0,
        delc=1.0,
        top=10.0,
        botm=-100.0,
    )
    flopy.mf6.ModflowGwfnpf(gwf, icelltype=0, k=10.0)
    flopy.mf6.ModflowGwfic(gwf, strt=0.0)
    flopy.mf6.ModflowGwfrcha(gwf, recharge=1.0e-3)
    flopy.mf6.ModflowGwfchd(gwf, stress_period_data=[((0, 0, ncol - 1), 0.0)])
    flopy.mf6.ModflowGwfswi(gwf, zeta_filerecord=f"output/{name}.zta")
    flopy.mf6.ModflowGwfoc(
        gwf,
        head_filerecord=f"output/{name}.hds",
        budget_filerecord=f"output/{name}.cbc",
        saverecord=[("head", "all"), ("budget", "all")],
    )
    return sim


def main() -> int:
    with tempfile.TemporaryDirectory() as tmpdir:
        ws = Path(tmpdir)
        (ws / "output").mkdir()
        sim = build(ws)
        sim.write_simulation(silent=True)
        success, _ = sim.run_simulation(silent=True)
        if not success:
            print((ws / "mfsim.lst").read_text())
            return 1
        head = sim.get_model().output.head().get_data()
        print(f"mf6 ran; maximum head {head.max():.3f}")
        if not (ws / "output" / "swi.zta").is_file():
            print("zeta file not written")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
