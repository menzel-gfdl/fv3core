#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open("README.md") as readme_file:
    readme = readme_file.read()

with open("HISTORY.md") as history_file:
    history = history_file.read()

requirements = [
    "f90nml>=1.1.0",
    "gt4py",
    "numpy",
    "fv3util>=0.4.3",
]

setup_requirements = []

test_requirements = ["pytest==5.2.2", "pytest-subtests>=0.3.0", "serialbox"]

setup(
    author="Vulcan Technologies LLC",
    author_email="RheaG@vulcan.com",
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    description="fv3core is a gt4py-based FV3 dynamical core for atmospheric models",
    install_requires=requirements,
    extras_require={},
    license="BSD license",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords="fv3core",
    name="fv3core",
    packages=find_packages(include=["fv3core", "fv3core.*"]),
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/VulcanClimateModeling/fv3core",
    version="0.1.0",
    zip_safe=False,
)