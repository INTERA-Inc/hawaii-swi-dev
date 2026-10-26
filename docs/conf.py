"""Sphinx configuration for the SWI notebook documentation."""

import shutil
from pathlib import Path

# copy the jupytext notebooks into the source tree for myst-nb to execute
root = Path(__file__).parents[1]
dst = Path(__file__).parent / "notebooks"
dst.mkdir(exist_ok=True)
for f in sorted((root / "notebooks-verification").glob("gwf_swi*.py")):
    shutil.copy2(f, dst / f.name)

project = "hawaii-swi-dev"
author = "INTERA"
extensions = ["myst_nb"]
exclude_patterns = ["_build", "conf.py"]

html_theme = "sphinx_book_theme"
html_title = "MODFLOW 6 SWI Package tests"
html_theme_options = {
    "repository_url": "https://github.com/INTERA-Inc/hawaii-swi-dev",
    "use_repository_button": True,
}

nb_custom_formats = {".py": ["jupytext.reads", {"fmt": "py:percent"}]}
nb_execution_mode = "force"
nb_execution_timeout = 300
nb_execution_raise_on_error = True
nb_execution_show_tb = True
