# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern Universtiy.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Invenio Resources module to create REST APIs."""

import os

from setuptools import find_packages, setup

readme = open("README.rst").read()
history = open("CHANGES.rst").read()

tests_require = [
    "invenio-app>=1.3.0",
    "pytest-invenio>=1.3.4",
    # TODO: Remove all lines below with pytest-invenio v1.4.0:
    "pytest-cov>=2.10.1",
    "pytest-isort>=1.2.0",
    "pytest-pycodestyle>=2.2.0",
    "pytest-pydocstyle>=2.2.0",
    "pytest>=6,<7",

]

# Should follow inveniosoftware/invenio versions
invenio_search_version = '>=1.3.0,<2.0.0'
invenio_db_version = '>=1.0.5,<2.0.0'

extras_require = {
    "docs": ["Sphinx>=2.4,<3"],
    # Elasticsearch version
    'elasticsearch6': [
        'invenio-search[elasticsearch6]{}'.format(invenio_search_version),
    ],
    'elasticsearch7': [
        'invenio-search[elasticsearch7]{}'.format(invenio_search_version),
    ],
    # Databases
    'mysql': [
        'invenio-db[mysql,versioning]{}'.format(invenio_db_version),
    ],
    'postgresql': [
        'invenio-db[postgresql,versioning]{}'.format(invenio_db_version),
    ],
    'sqlite': [
        'invenio-db[versioning]{}'.format(invenio_db_version),
    ],
    "tests": tests_require,
}

all_requires = []
for key, reqs in extras_require.items():
    if key in {"elasticsearch6", "elasticsearch7"}:
        continue
    all_requires.extend(reqs)
extras_require["all"] = all_requires

setup_requires = [
    "Babel>=2.8",
]

install_requires = [
    "flask-resources>=0.3.1,<1.0.0",
    "invenio-accounts>=1.3.0",
    "invenio-base>=1.2.3",
    "invenio-files-rest>=1.2.0",
    "invenio-i18n>=1.2.0",
    "invenio-indexer>=1.2.0",
    "invenio-jsonschemas>=1.1.0",
    "invenio-pidstore>=1.2.0",
    "invenio-records-permissions>=0.9.0,<1.0.0",
    "invenio-records>=1.4.0a1",
    "marshmallow-utils>=0.1.3",
    "ftfy<5.0,>=4.4.3",  # TODO: temporary until invenio-records-rest unpins
    "xmltodict~=0.12.0",
    "uritemplate>=3.0.1",
]

packages = find_packages()


# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join("invenio_records_resources", "version.py"), "rt") as fp:
    exec(fp.read(), g)
    version = g["__version__"]

setup(
    name="invenio-records-resources",
    version=version,
    description=__doc__,
    long_description=readme + "\n\n" + history,
    keywords="invenio records rest apis",
    license="MIT",
    author="CERN",
    author_email="info@inveniosoftware.org",
    url="https://github.com/inveniosoftware/invenio-records-resources",
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms="any",
    entry_points={
        "invenio_base.apps": [
            "invenio_records_resources = "
            "invenio_records_resources:InvenioRecordsResources",
        ],
        "invenio_base.api_apps": [
            "invenio_records_resources = "
            "invenio_records_resources:InvenioRecordsResources",
        ],
        'invenio_config.module': [
            'invenio_records_resources = invenio_records_resources.config',
        ],
        "invenio_i18n.translations": [
            "messages = invenio_records_resources", ],
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
        "Development Status :: 3 - Alpha",
    ],
)
