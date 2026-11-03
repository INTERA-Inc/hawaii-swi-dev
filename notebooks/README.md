# Hawaii island models

These notebooks convert the MODFLOW-2005 SWI2 models of Kauai, Oahu, and Maui
of Rotzoll and Izuka (2023) to MODFLOW 6 models with the SWI Package, run them,
and compare the results with the MODFLOW-2005 output in the data release.

| Notebook | Description |
| --- | --- |
| `compare_mf2005_mf6` | Converts and runs one island model and compares the MODFLOW 6 interface and heads with MODFLOW-2005 |
| `cross_sections` | Plots the MODFLOW-2005 and MODFLOW 6 freshwater and saltwater along the rows of figure 26 of Izuka and Rotzoll (2023), where they differ, and the differences in feet along the row |

The conversion is done by `scripts/mf2005_to_mf6.py`, which the notebooks
import and which can also be run from the command line.

The notebooks write their figures to `figures/` in the repository root, which is
excluded from the repository.

## Build a model

From the repository root, after `pixi install` and `pixi run install`
(see the [README](../README.md)):

1. Download the data release for the island, if it has not been downloaded.

   ```
   pixi run get-data oahu
   ```

2. Convert the model, and run it with `--run`.

   ```
   pixi run convert oahu --run
   ```

   `pixi run convert -h` lists the options:

   | Option | Description |
   | --- | --- |
   | `island` | `kauai`, `maui`, or `oahu` |
   | `--scenario` | Data release scenario; default 0 |
   | `--ws` | Model workspace; default `notebooks/models/<island>` |
   | `--two-fluid` | Add a saltwater model coupled by an SWI-SWI Exchange |
   | `--reduction-length` | Freshwater thickness, in feet, below which well rates are reduced; default 10 |
   | `--run` | Run MODFLOW 6 after writing the input |

3. Or open `compare_mf2005_mf6` in JupyterLab (`pixi run jupyter`), set
   `island` and `scenario` in the second cell, and run all cells. The notebook
   converts and runs the model and plots the comparison.

The scenarios are

| Scenario | Name | Islands |
| --- | --- | --- |
| 0 | Current (2010 conditions) | all |
| 1 | No Withdrawal | all |
| 2 | Predevelopment | all |
| 3 | Increased Withdrawal | Oahu |
| 4 | Future Rain | Oahu |

## Model files

Model files are written to `notebooks/models/<island>` for scenario 0 and to
`notebooks/models/<island>.<scenario>` for the others, with the output in its
`output/` directory. `notebooks/models/` is excluded from the repository.

```
notebooks/models/oahu/
    mfsim.nam
    oahu.dis
    ...
    output/
        oahu.hds
        oahu.cbc
        oahu.zta
```

## The MODFLOW 6 model

The MODFLOW-2005 models are steady-state flow models in which SWI2 moves the
interface toward equilibrium over a long stress period. The MODFLOW 6 model is
a steady-state, single-fluid SWI simulation with one time step, in which the
interface is in equilibrium with the freshwater head.

- LPF, GHB, DRN, WEL, and RCH are converted to NPF, GHB, DRN, WEL, and RCHA.
  The model uses Newton-Raphson, which SWI requires.
- A positive LPF `CHANI` (Kauai and Maui) is the horizontal anisotropy of the
  layer; otherwise the `HANI` array is used (Oahu).
- Boundaries in inactive cells, which MODFLOW-2005 skips, are dropped.
- The relative density difference is the difference of the SWI2 `NU` values.
- An SWI2 well pumps whichever zone it is in, but the freshwater model can only
  pump freshwater. Well rates are reduced (WEL `AUTO_FLOW_REDUCE` with
  `FLOW_REDUCTION_LENGTH`) as the freshwater zone in the cell thins to less
  than 10 ft (`--reduction-length`), and the reduced wells are written to
  `output/<island>.afr.csv`. Without this, the Kauai and Maui models do not
  converge.
- The IMS outer closure (0.1 ft) matches the MODFLOW-2005 PCG `HCLOSE`, and the
  outer iterations are written to `output/<island>.outer.csv`.
- The MODFLOW-2005 heads and interface used for the comparison are the averages
  of the last two saved time steps, as in Izuka and Rotzoll (2023).

Scenario 0 of each island converges with the mf6 SWI preview build d94462a:

| Island | Outer iterations | Run time | Reduced wells (shut off) | Pumping removed | Mean interface difference |
| --- | --- | --- | --- | --- | --- |
| Kauai | 756 | 6 min | 19 (8) | 2.57 million ft³/d (39 percent) | +63 ft |
| Maui | 31 | 6 s | 5 (2) | 0.03 million ft³/d (0.3 percent) | +22 ft |
| Oahu | 1,002 | 5 min | 1 (0) | 0.14 million ft³/d (0.6 percent) | +31 ft |

The interface difference is MODFLOW 6 minus MODFLOW-2005 in cells where the
MODFLOW-2005 interface is within the aquifer. Eight of the reduced Kauai wells,
which account for 1.57 million ft³/d of the reduction, are in cells that
MODFLOW-2005 fills with saltwater; the others are in cells where the MODFLOW 6
freshwater zone is thinner than in MODFLOW-2005. Scenarios 1 and 2, which have
no wells, also converge on all three islands; scenarios 3 and 4 have not been
run.

## References

Izuka, S.K., and Rotzoll, K., 2023, Volcanic aquifers of Hawaii--Contributions
to assessing groundwater availability on Kauai, Oahu, and Maui: U.S. Geological
Survey Professional Paper 1876, https://doi.org/10.3133/pp1876.

Rotzoll, K., and Izuka, S.K., 2023, MODFLOW-2005 and SWI2 models for assessing
groundwater availability scenarios in volcanic aquifers on Kauai, Oahu, and
Maui, Hawaii: U.S. Geological Survey data release,
https://doi.org/10.5066/P97CPK5C.
