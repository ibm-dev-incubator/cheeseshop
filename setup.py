#!/usr/bin/env python

from setuptools import setup
from setuptools.extension import Extension
from Cython.Build import cythonize

extensions = [
    Extension(
        "cheeseshop.demoparser.util",
        ["cheeseshop/demoparser/util.pyx"]
    ),
    Extension(
        "cheeseshop.demoparser.props",
        ["cheeseshop/demoparser/props.pyx"]
    ),
    Extension(
        "cheeseshop.demoparser.bitbuf",
        ["cheeseshop/demoparser/bitbuf.pyx"]
    ),
]
setup(
    setup_requires=['pbr>=1.9', 'setuptools>=17.1'],
    pbr=True,
    ext_modules=cythonize(extensions)
)
