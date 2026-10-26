"""Sphinx configuration for the SWI notebook documentation."""

import os
from datetime import datetime

on_rtd = os.environ.get("READTHEDOCS") == "True"

project = "hawaii-swi-dev"
author = "INTERA Incorporated"
copyright = f"{datetime.now():%Y}, {author}"

extensions = ["nbsphinx"]

# On Read the Docs, replace the notebooks directory with the executed notebooks
# uploaded by the docs workflow, so they render with output.
if on_rtd:
    extensions.append("rtds_action")
    rtds_action_github_repo = "INTERA-Inc/hawaii-swi-dev"
    rtds_action_path = "notebooks"
    rtds_action_artifact_prefix = "rendered-notebooks-"
    rtds_action_github_token = os.environ["GITHUB_TOKEN"]

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"

nbsphinx_execute = "never"
