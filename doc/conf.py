# Copyright (C) 2023 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
#
# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

import inspect

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))
import os
import textwrap

import minarca_client
import minarca_client.core.exceptions as exceptions

# -- Project information -----------------------------------------------------

project = 'Minarca Docs'
copyright = '(C) IKUS Software. All rights reserved.'
author = 'Patrik Dufresne'
version = minarca_client.__version__

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'myst_parser',
    'sphinx.ext.autosectionlabel',
    'sphinx_design',  # Required for {tab-set}
    'sphinx_argparse_cli',  # Required to generate doc from argparse.
]

myst_enable_extensions = ["colon_fence"]  # Required for :::{tab-set}

autosectionlabel_prefix_document = True

# Enable anchors for cross references
myst_heading_anchors = 2

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "pydata_sphinx_theme"
# Ref: https://alabaster.readthedocs.io/en/latest/customization.html#theme-options

html_theme_options = {
    "logo": {
        "text": project,
    },
    "footer_start": ["copyright"],
    "footer_end": ["version"],
    'use_edit_page_button': True,
}

# Allow edit in Gitlab.
html_context = {
    "gitlab_user": "ikus-soft",
    "gitlab_repo": "minarca",
    "gitlab_version": "master",
    "doc_path": "doc",
}

# Hide source code.
html_show_sourcelink = False

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

html_logo = "_static/favicon-128x128px.png"
html_favicon = "_static/favicon-128x128px.png"

# -- Output file configuration ------------------------------------------------
# Output directory for Markdown files
output_dir = os.path.abspath('.')


# Function to create the error code markdown table
def generate_error_code_table():
    error_code_list = []
    for name, obj in inspect.getmembers(exceptions):
        if inspect.isclass(obj) and hasattr(obj, 'error_code'):
            error_code = getattr(obj, 'error_code')
            message = obj.message.strip() if getattr(obj, 'message', False) else 'No message available'
            description = textwrap.dedent(obj.__doc__) if getattr(obj, '__doc__', False) else 'No description available'
            error_code_list.append((error_code, name, message, description))

    # Write the markdown table
    with open(os.path.join(output_dir, 'errors-codes-list.md'), 'w') as f:
        f.write('# Error Codes\n\n')
        for error_code, name, message, description in sorted(error_code_list):
            f.write(f'## {name} (Error: {error_code})\n\n')
            f.write(f'**Message:** {message}\n\n')
            f.write(f'**Description:**\n{description}\n\n')


# Call the function to generate the table before building docs
generate_error_code_table()
