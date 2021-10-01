#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""The setup script."""

#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

from setuptools import find_namespace_packages, setup

with open("README.md", encoding="utf8") as readme_file:
    readme = readme_file.read()

# Installed by pip install ocean-lib
# or pip install -e .
install_requirements = [
    "ocean-contracts==0.6.9",
    "coloredlogs",
    "pyopenssl",
    "PyJWT",  # not jwt
    "PyYAML==5.4.1",
    "requests>=2.21.0",
    "deprecated",
    "pycryptodomex",
    "tqdm",
    "pytz",
    "web3==5.19.0",
    "cryptography==3.3.2",
    "scipy",
    "enforce-typing==1.0.0.post1",
    "json-sempai==0.4.0",
    # web3 requires eth-abi, requests, and more,
    # so those will be installed too.
    # See https://github.com/ethereum/web3.py/blob/master/setup.py
]

# Required to run setup.py:
setup_requirements = ["pytest-runner"]

test_requirements = [
    "codacy-coverage",
    "coverage",
    "docker",
    "mccabe",
    "pylint",
    "pytest",
    "pytest-watch",
    "tox",
]

# Possibly required by developers of ocean-lib:
dev_requirements = [
    "bumpversion",
    "pkginfo",
    "twine",
    "watchdog",
    "flake8",
    "isort",
    "black==21.4b0",
    "pre-commit",
    # for the following: maybe needed, maybe not
    "pytest",
    "licenseheaders",
    "pytest-env",
]

packages = find_namespace_packages(include=["ocean_lib*"], exclude=["*test*"])

setup(
    author="leucothia",
    author_email="devops@oceanprotocol.com",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.8",
    ],
    description="🐳 Ocean protocol library.",
    extras_require={
        "test": test_requirements,
        "dev": dev_requirements + test_requirements,
    },
    install_requires=install_requirements,
    license="Apache Software License 2.0",
    long_description=readme,
    long_description_content_type="text/markdown",
    include_package_data=True,
    keywords="ocean-lib",
    name="ocean-lib",
    packages=packages,
    setup_requires=setup_requirements,
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/oceanprotocol/ocean.py",
    # fmt: off
    # bumpversion.sh needs single-quotes
    version='0.8.3',
    # fmt: on
    zip_safe=False,
)
