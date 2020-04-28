# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Resources is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Invenio Resources module to create REST APIs"""

import os

from setuptools import find_packages, setup

readme = open("README.rst").read()
history = open("CHANGES.rst").read()

tests_require = [
    "pytest-invenio>=1.3.2",
    "invenio-app>=1.3.0",
    'psycopg2-binary>=2.7.4',
    'elasticsearch>=7.0.0,<8.0.0',
    'elasticsearch-dsl>=7.0.0,<8.0.0',
]

extras_require = {
    "docs": ["Sphinx>=1.5.1,<3"],
    "tests": tests_require,
}

extras_require["all"] = []
for reqs in extras_require.values():
    extras_require["all"].extend(reqs)

setup_requires = [
    "Babel>=1.3",
    "pytest-runner>=3.0.0,<5",
]

install_requires = [
    # TODO pin versions
    "Flask-BabelEx>=0.9.4",
    "invenio-base>=1.2.3",
    "invenio-db>=1.0.5",
    "invenio-pidstore>=1.2.0",
    "invenio-search>=1.3.1",  # FIXME: this avoids elastic to be installed in tests
    "invenio-indexer>=1.1.1",
    "invenio-records>=1.3.1",
    # "invenio-records-agent>=",  # FIXME: will be renamed
    "invenio-rest>=1.2.1",
    # "flask-resources",
]

packages = find_packages()


# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join("invenio_resources", "version.py"), "rt") as fp:
    exec(fp.read(), g)
    version = g["__version__"]

setup(
    name="invenio-resources",
    version=version,
    description=__doc__,
    long_description=readme + "\n\n" + history,
    keywords="invenio TODO",
    license="MIT",
    author="CERN",
    author_email="info@inveniosoftware.org",
    url="https://github.com/inveniosoftware/invenio-resources",
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms="any",
    entry_points={
        "invenio_base.apps": [
            "invenio_resources = invenio_resources:InvenioResources",
        ],
        "invenio_base.api_apps": [
            "invenio_resources = invenio_resources:InvenioResources",
        ],
        "invenio_i18n.translations": ["messages = invenio_resources",],
    },
    extras_require=extras_require,
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
    classifiers=[
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Development Status :: 1 - Planning",
    ],
)
