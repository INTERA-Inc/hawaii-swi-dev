"""Global water budgets of the MODFLOW-2005 and MODFLOW 6 island models.

Rates are in million gallons per day. The MODFLOW-2005 rates are averages of the
last two saved time steps, the same steps as its heads and interface.
"""

from pathlib import Path

import flopy
import numpy as np
import pandas as pd
from flopy.plot import styles
from mf2005_to_mf6 import (
    SCENARIOS,
    load_mf2005,
    mf2005_heads_zeta,
    mf2005_name,
    mf2005_output,
)

# budget text of each boundary in the MODFLOW-2005 and MODFLOW 6 budget files
BOUNDARIES = {
    "Recharge": ("RECHARGE", "RCHA"),
    "Wells": ("WELLS", "WEL"),
    "Drains": ("DRAINS", "DRN"),
    "Coast (GHB)": ("HEAD DEP BOUNDS", "GHB"),
}
# rows of a budget, inflows and then outflows, as boundary and direction
ROWS = (
    ("Recharge", "in"),
    ("Coast (GHB)", "in"),
    ("Wells", "out"),
    ("Drains", "out"),
    ("Coast (GHB)", "out"),
)

MF2005_COLOR = "#eb6834"
MF6_COLOR = "#2a78d6"
MF2005_LABEL = "MODFLOW-2005 SWI2"
MF6_LABEL = "MODFLOW 6 SWI"
# a cell with less freshwater than this, in feet, is counted as saltwater
MIN_FRESH_THICKNESS = 1.0
MGAL_PER_CUBIC_FOOT = 7.48052e-6


def _record_names(cbc: flopy.utils.CellBudgetFile) -> set[str]:
    """Budget text in a budget file."""
    return {name.decode().strip() for name in cbc.get_unique_record_names()}


def _in_out(q: np.ndarray, boundary: str) -> dict:
    """Inflow and outflow of a boundary, in million gallons per day."""
    return {
        (boundary, "in"): q[q > 0.0].sum() * MGAL_PER_CUBIC_FOOT,
        (boundary, "out"): -q[q < 0.0].sum() * MGAL_PER_CUBIC_FOOT,
    }


def mf2005_budget(island: str, scenario: int = 0) -> tuple[dict, dict]:
    """Budget of a data release model, for all cells and for saltwater cells."""
    name = mf2005_name(island, scenario)
    cbc = flopy.utils.CellBudgetFile(mf2005_output(island, scenario) / f"{name}.cbc")
    names = _record_names(cbc)

    m = load_mf2005(island, scenario)
    botm = m.dis.botm.array
    layer_top = np.vstack((m.dis.top.array[np.newaxis], botm[:-1]))
    head, zeta = mf2005_heads_zeta(island, scenario)
    fresh = np.minimum(head, layer_top) - np.clip(zeta, botm, layer_top)
    salt = fresh < MIN_FRESH_THICKNESS

    total, saltwater = {}, {}
    for boundary, (text, _) in BOUNDARIES.items():
        q = np.zeros_like(botm)
        if text in names:
            steps = cbc.get_data(text=text, full3D=True)[-2:]
            q = 0.5 * (np.ma.filled(steps[0], 0.0) + np.ma.filled(steps[1], 0.0))
        total |= _in_out(q, boundary)
        saltwater |= _in_out(q[salt], boundary)
    return total, saltwater


def mf6_budget(ws: Path, name: str) -> dict:
    """Budget of a converted MODFLOW 6 model."""
    cbc = flopy.utils.CellBudgetFile(Path(ws) / "output" / f"{name}.cbc")
    names = _record_names(cbc)
    budget = {}
    for boundary, (_, text) in BOUNDARIES.items():
        q = np.zeros(1)
        if text in names:
            q = np.concatenate([rec["q"] for rec in cbc.get_data(text=text)])
        budget |= _in_out(q, boundary)
    return budget


def budget_table(island: str, scenario: int, ws: Path) -> pd.DataFrame:
    """Budgets of both models; the MODFLOW 6 columns are empty if it has not run.

    Percent difference is MODFLOW 6 compared to MODFLOW-2005. Rows without flow in
    either model are dropped.
    """
    mf2005, saltwater = mf2005_budget(island, scenario)
    mf6 = {}
    if (Path(ws) / "output" / f"{island}.cbc").exists():
        mf6 = mf6_budget(ws, island)
    table = pd.DataFrame(
        {
            "MODFLOW-2005": [mf2005[row] for row in ROWS],
            "MODFLOW-2005 saltwater cells": [saltwater[row] for row in ROWS],
            "MODFLOW 6": [mf6.get(row, np.nan) for row in ROWS],
        },
        index=[f"{boundary} {direction}" for boundary, direction in ROWS],
    ).astype(float)
    reference = table["MODFLOW-2005"].where(table["MODFLOW-2005"] > 0.0)
    table["Percent difference"] = 100.0 * (table["MODFLOW 6"] - reference) / reference
    return table[table[["MODFLOW-2005", "MODFLOW 6"]].max(axis=1) > 0.0]


def plot_budget(ax, island: str, scenario: int, table: pd.DataFrame):
    """Plot the budget of an island, with the percent difference of each row."""
    y = np.arange(len(table))
    height = 0.38
    ax.barh(
        y - 0.5 * height,
        table["MODFLOW-2005"],
        height * 0.95,
        color=MF2005_COLOR,
        label=MF2005_LABEL,
    )
    has_mf6 = table["MODFLOW 6"].notna().any()
    if has_mf6:
        ax.barh(
            y + 0.5 * height,
            table["MODFLOW 6"],
            height * 0.95,
            color=MF6_COLOR,
            label=MF6_LABEL,
        )
    largest = table[["MODFLOW-2005", "MODFLOW 6"]].max(axis=1)
    for row, value, percent in zip(y, largest, table["Percent difference"]):
        if np.isfinite(percent):
            ax.text(
                value + 0.01 * largest.max(),
                row,
                f"{percent:+.1f}%".replace("-", "\N{MINUS SIGN}"),
                va="center",
                fontsize=8,
            )
    ax.set_yticks(y, table.index)
    ax.tick_params(axis="y", length=0)
    ax.invert_yaxis()
    # room for the percent differences to the right of the longest bar
    ax.set_xlim(0.0, 1.12 * largest.max())
    label = "Rate, in million gallons per day"
    if has_mf6:
        label += (
            "\nLabels are the percent difference, MODFLOW 6 compared to MODFLOW-2005"
        )
    styles.xlabel(ax=ax, label=label)
    styles.heading(
        ax=ax,
        heading=f"{island.title()}, scenario {scenario}, {SCENARIOS[scenario]}",
    )
    handles, labels = ax.get_legend_handles_labels()
    styles.graph_legend(
        ax,
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.2),
        ncol=2,
    )
    return ax
