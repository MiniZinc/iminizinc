==========================
IPython MiniZinc extension
==========================

:author: Guido Tack <guido.tack@monash.edu>
:homepage: https://github.com/minizinc/iminizinc

This module provides a cell magic extension for IPython / Jupyter notebooks that lets you solve MiniZinc models.

The module requires an existing installation of MiniZinc.

Installation
============

You can install or upgrade this module via pip

    pip install -U iminizinc

Make sure that the ``mzn2fzn`` binary as well as solver binaries (currently only ``fzn-gecode`` and ``mzn-cbc`` are supported) are on the PATH when you start the notebook server.

Basic usage
===========

After installing the module, you have to load the extension using ``%load_ext iminizinc``. This will enable the cell magic ``%%minizinc``, which lets you solve MiniZinc models. Here is a simple example:

    In[1]:  %load_ext iminizinc
            
    In[2]:  n=8
            
    In[3]:  %%minizinc gecode
            
            include "globals.mzn";
            int: n;
            array[1..n] of var 1..n: queens;
            constraint all_different(queens);
            constraint all_different([queens[i]+i | i in 1..n]);
            constraint all_different([queens[i]-i | i in 1..n]);
            solve satisfy;
            
    In[4]:  queens
    
    Out[4]: [4, 2, 7, 3, 6, 8, 5, 1]

As you can see, the model binds variables in the environment (in this case, ``n``) to MiniZinc parameters, and binds the variables in a solution (``queens``) back to Python variables.
