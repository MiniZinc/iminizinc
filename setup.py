from setuptools import setup
from codecs import open
from os import path

with open(path.join(path.abspath(path.dirname(__file__)), 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='iminizinc',
    version='0.3',
    description='IPython extensions for the MiniZinc constraint modelling language',
    long_description=long_description,
    author='Guido Tack',
    author_email='guido.tack@monash.edu',
    packages=['iminizinc'],
    install_requires=['ipython'],
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',

        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Scientific/Engineering :: Mathematics',
        
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
        'Operating System :: OS Independent',
        
        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    keywords = 'minizinc ipython',
    project_urls={
        'Source': 'https://github.com/MiniZinc/iminizinc/',
        'Tracker': 'https://github.com/MiniZinc/iminizinc/issues',
    },
)
