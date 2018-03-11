from setuptools import setup
from codecs import open
from os import path

with open(path.join(path.abspath(path.dirname(__file__)), 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='iminizinc',
    version='0.1',
    description='IPython extensions for the MiniZinc constraint modelling language',
    long_description=long_description,
    author='Guido Tack',
    author_email='guido.tack@monash.edu',
    packages=['iminizinc'],
    install_requires=['ipython'],
    include_package_data=True
)
