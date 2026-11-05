# Agent instructions

Rules for working in this repository. `README.md` and `notebooks/README.md`
describe the project; this file does not repeat them.

## Layout

- `notebooks-verification/`: SWI Package tests ported from the MODFLOW 6
  autotests. Generated models go in its `models/` directory.
- `notebooks/`: the converted USGS island models. Generated models go in its
  `models/` directory.
- Model output always goes in an `output/` directory beside the model input.
- Figures go in `figures/` in the repository root.
- `data/`, `dfn/`, `figures/`, `output/`, the `models/` directories, and `.ipynb`
  files are not tracked. Never edit `data/`. To rerun a data release model, copy
  its input and change the copy.

## Notebooks

- A notebook is a jupytext percent-format `.py` file, which is the tracked source.
  Plotting and model code that is more than a few lines goes in `scripts/`, and
  the notebook imports it.
- `pixi run sync-notebooks` creates or updates the `.ipynb` files without running
  them. Whichever of the pair was edited last wins.
- `pixi run execute-notebooks` builds and runs the notebooks in `notebooks/` that
  only read model output. Add a new notebook of that kind to the task in
  `pixi.toml`. Do not add a notebook that runs a model: `compare_mf2005_mf6` takes
  about 5 to 6 minutes for Kauai or Oahu.
- List each notebook in `notebooks/` in the table in `notebooks/README.md`.

## SWI verification tests

Compare the tests with the `feat-swi` branch of
[christianlangevin/modflow6](https://github.com/christianlangevin/modflow6/tree/feat-swi)
when working on a verification notebook or updating the MODFLOW 6 build, when
asked, and when the nightly `SWI tests` workflow opens an issue.

`notebooks-verification/feat-swi-commit.txt` records the last `feat-swi` commit the
notebooks were brought up to date with. This lists the tests that are new or have
changed since then:

```shell
pixi run check-swi-tests
```

Do not judge this from the dates of the notebook commits, because a commit can
touch a notebook without bringing it up to date with its test.

- `autotest/test_gwf_swi_<name>.py` is ported to
  `notebooks-verification/gwf_swi_<name>.py`. Port any test that has no notebook.
  `NOTEBOOKS` in `scripts/check_swi_tests.py` lists the exceptions.
- `test_gwf_swi_checks.py` is used only for the invalid configurations in
  `gwf_swi_invalid_input`. When it changes, add any new configuration that must stop
  with an error to that notebook.
- Update the notebook of each test that changed so that it has the same models and
  criteria, and run it with `pixi run run-verification-notebooks`.
- Report a test that was removed upstream, and do not delete its notebook without
  asking.
- Update `feat-swi-commit.txt` in the same pull request, which closes the issue on
  the next nightly run.
- A test can need a fix that is not yet in the
  [preview release](https://github.com/jdhughes-dev/modflow6-feat-swi-preview).
  Check before porting, because `pixi run run-verification-notebooks` runs against
  that release. If the fix is not released, report it and wait.
- A ported notebook names its source test in the first markdown cell, checks the
  test's criteria, and fails if they are not met. A case that must stop with an
  error is run and checked for that error, as in `gwf_swi_require_sy`.
- A notebook must run in 30 s or less.
- `run-verification-notebooks` and the Read the Docs index both find notebooks by
  the pattern `gwf_swi*.py`, so a notebook with that name needs no other change to
  join them.

## Reporting results

- Write for hydrologists. Report heads, interfaces, rates, and budgets, and name
  figure axes and legends for those quantities, with units.
- Use the names MODFLOW-2005 and MODFLOW 6.
- MODFLOW-2005 heads, interface, and budgets are averages of the last two saved
  time steps, as in Izuka and Rotzoll (2023).
- A difference is stated as MODFLOW 6 compared to, or minus, MODFLOW-2005.
- Compute a number from the output before stating it, and name the set of cells or
  times it covers. Keep what was measured separate from what is inferred about the
  cause, and say when a cause has not been tested.

## Figures

- Draw new figures inside `flopy.plot.styles.USGSPlot()`, or `USGSMap()` for maps,
  with its heading, label, and legend helpers.
- Save PNG files with `transparent=False`, because the style sets it to true.
- Do not hardcode limits or category lists that can be derived from the data.
- Choose colors that remain distinct with color vision deficiency, and use the
  same color for the same model within a figure set.

## Code

- Docstrings and comments are short: what the thing does, not a narrative of why
  or how.
- Name a constant for what it holds, with its units where they are not obvious.
- Use U.S. spelling.

## Before pushing

Run these over the whole repository. All must pass, including for files the branch
did not touch.

```shell
pixi run ruff format --check .
pixi run lint
pixi run spell
```

Also run `pixi run run-verification-notebooks` if a verification notebook or the
MODFLOW 6 build changed.

## Git and GitHub

- `upstream` (INTERA-Inc) is the repository of record and `origin` (jdhughes-dev)
  is the fork. Fetch before reading a remote ref, and do not use `origin` to learn
  the state of the project.
- Branch from an up-to-date `upstream/main`. Push to `origin` and open the pull
  request against `upstream/main`.
- Commit or open a pull request only when asked.
- Use conventional commits: `feat(notebooks): compare the cross sections`. The
  subject is imperative and lowercase, with no trailing period. The body contrasts
  the previous and new behavior.
- The commit author is the sole author. Do not add `Co-Authored-By` trailers,
  "Generated with" footers, session links, or other tool attribution to commits,
  pull requests, issues, or comments.
- A pull request title is a conventional commit header. The repository has no
  template, so the description is one to three sentences stating what was wrong and
  what changed, with no added sections.
- Issue and pull request comments are two or three short sentences, with numbers
  inline and no tables or headings.
