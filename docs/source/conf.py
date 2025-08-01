import os
import sys
import django

# Point to your project root
sys.path.insert(0, os.path.abspath('../../'))

# Configure Django settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'news_portal.settings'
django.setup()

# -- Sphinx extensions -----------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',       # support for Google/NumPy docstring styles
    'sphinx.ext.viewcode',       # add links to source
]

# -- HTML theme ------------------------------------------------------------
html_theme = 'sphinx_rtd_theme'

# -- Autodoc options -------------------------------------------------------
autodoc_default_options = {
    'members': True,
    'undoc-members': False,
    'show-inheritance': True,
}
