from __future__ import absolute_import
from .mzn import MznMagics, checkMzn

from IPython.core.display import display, HTML, Javascript
from os import path

with open(path.join(path.abspath(path.dirname(__file__)), 'static/minizinc.js')) as f:
    initHighlighter = f.read()

def load_ipython_extension(ipython):
    """
    Any module file that define a function named `load_ipython_extension`
    can be loaded via `%load_ext module.path` or be configured to be
    autoloaded by IPython at startup time.
    """
    # You can register the class itself without instantiating it.  IPython will
    # call the default constructor on it.    
    display(Javascript(initHighlighter))
    if checkMzn():
        ipython.register_magics(MznMagics)
