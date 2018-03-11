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

.. code::

    In[1]:  %load_ext iminizinc
            
    In[2]:  n=8
            
    In[3]:  %%minizinc
            
            include "globals.mzn";
            int: n;
            array[1..n] of var 1..n: queens;
            constraint all_different(queens);
            constraint all_different([queens[i]+i | i in 1..n]);
            constraint all_different([queens[i]-i | i in 1..n]);
            solve satisfy;
    Out[3]: {u'queens': [4, 2, 7, 3, 6, 8, 5, 1]}
            
As you can see, the model binds variables in the environment (in this case, ``n``) to MiniZinc parameters, and returns an object with fields for all declared decision variables.

Alternatively, you can bind the decision variables to Python variables:

.. code::

    In[1]:  %load_ext iminizinc
            
    In[2]:  n=8
            
    In[3]:  %%minizinc -m bind
            
            include "globals.mzn";
            int: n;
            array[1..n] of var 1..n: queens;
            constraint all_different(queens);
            constraint all_different([queens[i]+i | i in 1..n]);
            constraint all_different([queens[i]-i | i in 1..n]);
            solve satisfy;
            
    In[4]:  queens
    
    Out[4]: [4, 2, 7, 3, 6, 8, 5, 1]

If you want to find all solutions of a satisfaction problem, or all intermediate solutions of an optimisation problem, you can use the ``-a`` flag:

.. code::

    In[1]:  %load_ext iminizinc
            
    In[2]:  n=6
            
    In[3]:  %%minizinc -a
            
            include "globals.mzn";
            int: n;
            array[1..n] of var 1..n: queens;
            constraint all_different(queens);
            constraint all_different([queens[i]+i | i in 1..n]);
            constraint all_different([queens[i]-i | i in 1..n]);
            solve satisfy;
            
    Out[3]: [{u'queens': [5, 3, 1, 6, 4, 2]},
             {u'queens': [4, 1, 5, 2, 6, 3]},
             {u'queens': [3, 6, 2, 5, 1, 4]},
             {u'queens': [2, 4, 6, 1, 3, 5]}]

The magic supports a number of additional options, take a look at the help using

.. code::

    In[1]:  %%minizinc?
