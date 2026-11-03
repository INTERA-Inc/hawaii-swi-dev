"""Cross sections of the island models along the rows of PP 1876 figure 26.

Izuka, S.K., and Rotzoll, K., 2023, Volcanic aquifers of Hawaii--Contributions
to assessing groundwater availability on Kauai, Oahu, and Maui: U.S. Geological
Survey Professional Paper 1876, https://doi.org/10.3133/pp1876.
"""

from pathlib import Path

import flopy
import numpy as np
from mf2005_to_mf6 import load_mf2005, mf2005_heads_zeta

# model row (one-based) and end labels of each cross section in figure 26
SECTIONS = {
    "kauai": (210, "A", "A'"),
    "oahu": (167, "B", "B'"),
    "maui": (119, "C", "C'"),
}

FRESH = "#6fcfdf"
SALT = "#d4ecf2"
MF6_ONLY = "tab:blue"
MF2005_ONLY = "tab:red"
ZETA_DIFF = "tab:purple"
HEAD_DIFF = "tab:orange"
# heads of this magnitude or larger are dry or no-flow cells
HEAD_NODATA = 1.0e20
FEET_PER_MILE = 5280.0


def mf2005_results(island: str, scenario: int = 0) -> dict:
    """Grid, heads, and interface of a data release model.

    Heads and interface are averages of the last two saved time steps.
    """
    m = load_mf2005(island, scenario)
    head, zeta = mf2005_heads_zeta(island, scenario)
    return {
        "delr": m.dis.delr.array,
        "top": m.dis.top.array,
        "botm": m.dis.botm.array,
        "active": m.bas6.ibound.array != 0,
        "head": head,
        "zeta": zeta,
    }


def mf6_results(ws: Path, name: str) -> dict:
    """Heads and interface of a converted MODFLOW 6 model."""
    ws = Path(ws)
    return {
        "head": flopy.utils.HeadFile(ws / "output" / f"{name}.hds").get_data(),
        "zeta": flopy.utils.HeadFile(
            ws / "output" / f"{name}.zta", text="zeta"
        ).get_data(),
    }


def _steps(x_edges: np.ndarray, v: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Step outline of cell values between cell edges."""
    return np.repeat(x_edges, 2)[1:-1], np.repeat(v, 2)


def _section(island: str, results: dict) -> dict:
    """Grid along the figure 26 row of an island, without the inactive ends."""
    i = SECTIONS[island][0] - 1
    active = results["active"][:, i, :]
    cols = np.flatnonzero(active.any(axis=0))
    j0, j1 = cols[0], cols[-1] + 1
    top = results["top"][i, j0:j1]
    botm = results["botm"][:, i, j0:j1]
    return {
        "i": i,
        "j0": j0,
        "j1": j1,
        "x_edges": np.concatenate(([0.0], np.cumsum(results["delr"][j0:j1])))
        / FEET_PER_MILE,
        "active": active[:, j0:j1],
        "top": top,
        "botm": botm,
        "layer_top": np.vstack((top, botm[:-1])),
    }


def _fresh_zone(sec: dict, results: dict, k: int) -> tuple[np.ndarray, np.ndarray]:
    """Top and bottom of the freshwater in a layer; equal where there is none."""
    ltop, lbot = sec["layer_top"][k], sec["botm"][k]
    head = results["head"][k, sec["i"], sec["j0"] : sec["j1"]]
    zeta = np.clip(results["zeta"][k, sec["i"], sec["j0"] : sec["j1"]], lbot, ltop)
    wet = sec["active"][k] & (head > lbot)
    fresh_top = np.where(wet, np.minimum(head, ltop), lbot)
    fresh_bot = np.where(wet, np.minimum(zeta, fresh_top), lbot)
    return fresh_top, fresh_bot


def _plot_grid(ax, island: str, sec: dict, title: str):
    """Draw the layer boundaries, model top, sea level, and labels of a section."""
    row, left, right = SECTIONS[island]
    x_edges = sec["x_edges"]
    for k in range(1, sec["botm"].shape[0]):
        ax.plot(
            *_steps(x_edges, np.where(sec["active"][k], sec["layer_top"][k], np.nan)),
            color="0.3",
            lw=0.6,
            label="Layer boundary" if k == 1 else None,
        )
    ax.plot(*_steps(x_edges, sec["top"]), color="k", lw=0.8, label="Model top")
    ax.axhline(0.0, color="k", lw=0.8, ls=(0, (6, 4)), label="Sea level")

    ax.set_xlim(x_edges[0], x_edges[-1])
    ax.set_ylabel("Altitude, in feet relative to sea level")
    ax.text(0.0, 1.01, left, transform=ax.transAxes, fontweight="bold", style="italic")
    ax.text(
        1.0,
        1.01,
        right,
        transform=ax.transAxes,
        ha="right",
        fontweight="bold",
        style="italic",
    )
    ax.set_title(
        f"{island.title()}, row {row}, {title}", loc="left", fontsize=10, pad=14
    )


def plot_difference_profile(ax, island: str, grid: dict, mf2005: dict, mf6: dict):
    """Plot MODFLOW 6 minus MODFLOW-2005 interface and head along a row, in feet.

    The interface difference is summed over the layers of a column, and the head
    difference is that of the uppermost active layer.
    """
    row, left, right = SECTIONS[island]
    sec = _section(island, grid)
    i, j0, j1 = sec["i"], sec["j0"], sec["j1"]
    active = sec["active"]
    ltop, lbot = sec["layer_top"], sec["botm"]
    z5 = np.clip(mf2005["zeta"][:, i, j0:j1], lbot, ltop)
    z6 = np.clip(mf6["zeta"][:, i, j0:j1], lbot, ltop)
    dzeta = np.where(active, z6 - z5, 0.0).sum(axis=0)

    # first active layer of each column
    upper = active.argmax(axis=0)
    cols = np.arange(active.shape[1])
    h5 = mf2005["head"][:, i, j0:j1][upper, cols]
    h6 = mf6["head"][:, i, j0:j1][upper, cols]
    # exclude dry and no-flow values
    valid = (np.abs(h5) < HEAD_NODATA) & (np.abs(h6) < HEAD_NODATA)
    dhead = np.where(valid, h6 - h5, np.nan)

    x_edges = sec["x_edges"]
    ax.axhline(0.0, color="k", lw=0.8)
    ax.plot(*_steps(x_edges, dzeta), color=ZETA_DIFF, lw=0.9, label="Interface")
    ax.plot(*_steps(x_edges, dhead), color=HEAD_DIFF, lw=0.9, label="Head")
    # differences span several orders of magnitude; linear within 10 ft of zero
    ax.set_yscale("symlog", linthresh=10.0)
    ax.set_xlim(x_edges[0], x_edges[-1])
    ax.set_ylabel("Difference, in feet")
    ax.text(0.0, 1.01, left, transform=ax.transAxes, fontweight="bold", style="italic")
    ax.text(
        1.0,
        1.01,
        right,
        transform=ax.transAxes,
        ha="right",
        fontweight="bold",
        style="italic",
    )
    ax.set_title(
        f"{island.title()}, row {row}, MODFLOW 6 minus MODFLOW-2005",
        loc="left",
        fontsize=10,
        pad=14,
    )
    return ax


def plot_cross_section(ax, island: str, grid: dict, results: dict, title: str):
    """Plot freshwater and saltwater along the figure 26 row of an island.

    ``grid`` holds the grid of the data release model and ``results`` the heads
    and interface to plot, which can be those of a converted model.
    """
    sec = _section(island, grid)
    x_edges = sec["x_edges"]
    for k in range(sec["botm"].shape[0]):
        act = sec["active"][k]
        lbot = sec["botm"][k]
        fresh_top, fresh_bot = _fresh_zone(sec, results, k)
        x, y = _steps(x_edges, fresh_top)
        _, yb = _steps(x_edges, fresh_bot)
        ax.fill_between(
            x, yb, y, color=FRESH, lw=0, label="Fresh water" if k == 0 else None
        )
        _, ys = _steps(x_edges, np.where(act, fresh_bot, np.nan))
        _, yl = _steps(x_edges, np.where(act, lbot, np.nan))
        ax.fill_between(
            x, yl, ys, color=SALT, lw=0, label="Salt water" if k == 0 else None
        )
    _plot_grid(ax, island, sec, title)
    return ax


def plot_difference(ax, island: str, grid: dict, mf2005: dict, mf6: dict):
    """Plot where the freshwater of MODFLOW 6 and MODFLOW-2005 differ along a row."""
    sec = _section(island, grid)
    x_edges = sec["x_edges"]
    for k in range(sec["botm"].shape[0]):
        act = sec["active"][k]
        top5, bot5 = _fresh_zone(sec, mf2005, k)
        top6, bot6 = _fresh_zone(sec, mf6, k)
        for tops, bots, other_top, other_bot, color, label in (
            (top6, bot6, top5, bot5, MF6_ONLY, "Fresh water in MODFLOW 6 only"),
            (top5, bot5, top6, bot6, MF2005_ONLY, "Fresh water in MODFLOW-2005 only"),
        ):
            # the part of the freshwater below and above that of the other model
            lower = np.maximum(bots, np.minimum(other_bot, tops))
            upper = np.minimum(tops, np.maximum(other_top, bots))
            for y0, y1, name in (
                (bots, lower, label),
                (upper, tops, None),
            ):
                x, ya = _steps(x_edges, np.where(act, y0, np.nan))
                _, yb = _steps(x_edges, np.where(act, y1, np.nan))
                ax.fill_between(
                    x,
                    ya,
                    yb,
                    color=color,
                    lw=0,
                    label=name if k == 0 else None,
                )
    _plot_grid(ax, island, sec, "MODFLOW 6 minus MODFLOW-2005")
    return ax


def interface_difference(island: str, grid: dict, mf2005: dict, mf6: dict) -> dict:
    """Summarize MODFLOW 6 minus MODFLOW-2005 interface along the row, in feet.

    Only the cells with the interface within the layer, in either model, count.
    """
    sec = _section(island, grid)
    nlay = sec["botm"].shape[0]
    diffs = []
    for k in range(nlay):
        act = sec["active"][k]
        ltop, lbot = sec["layer_top"][k], sec["botm"][k]
        z5 = np.clip(mf2005["zeta"][k, sec["i"], sec["j0"] : sec["j1"]], lbot, ltop)
        z6 = np.clip(mf6["zeta"][k, sec["i"], sec["j0"] : sec["j1"]], lbot, ltop)
        within = act & (
            ((z5 > lbot + 1.0) & (z5 < ltop - 1.0))
            | ((z6 > lbot + 1.0) & (z6 < ltop - 1.0))
        )
        diffs.append((z6 - z5)[within])
    d = np.concatenate(diffs)
    return {
        "cells": d.size,
        "mean": d.mean() if d.size else np.nan,
        "max_abs": np.abs(d).max() if d.size else np.nan,
    }
