"""Sphinx configuration."""

import os
import sys

sys.path.insert(0, os.path.abspath("../.."))  # Source code dir relative to this file


project = "Cytomine Utils"
author = "Andre Rendeiro"
copyright = "2022, Andre Rendeiro"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
]
autosummary_generate = True  # Turn on sphinx.ext.autosummary
autodoc_typehints = "description"
html_theme = "furo"
templates_path = ["_templates"]
intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}
