#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2023 Ocean Protocol Foundation
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
    "ocean-contracts==1.1.12",
    "coloredlogs==15.0.1",
    "requests>=2.21.0",
    "pytz",  # used minimally and unlikely to change, common dependency
    "enforce-typing==1.0.0.post1",
    "eciespy==0.3.11",
    "eth-brownie==1.19.3",
    "cryptography==40.0.2",
    "yarl==1.8.1",
    "bitarray>=2.6.0,<3",
    # brownie requires web3.py, eth-abi, requests, and more,
    # so those will be installed too.
    # See https://github.com/ethereum/web3.py/blob/master/setup.py
]
# Required to run setup.py:
setup_requirements = ["pytest-runner"]

test_requirements = [
    "codacy-coverage==1.3.11",
    "coverage==7.2.5",
    "mccabe==0.7.0",
    "pytest==6.2.5",
    "pytest-watch==4.2.0",
    "pytest-env==0.6.2",
    "matplotlib",  # just used in a readme test and unlikely to change, common dependency
    "mkcodes==0.1.1",
    "pytest-sugar==0.9.7",
]

# Possibly required by developers of ocean-lib:
dev_requirements = [
    "bumpversion==0.6.0",
    "pkginfo==1.9.6",
    "twine==4.0.2",
    "watchdog==3.0.0",
    "isort==5.12.0",
    "flake8==6.0.0",
    "black",  # need to keep this up to date to brownie
    "pre-commit==3.3.2",
    "licenseheaders==0.8.8",
]

packages = find_namespace_packages(include=["ocean_lib*"], exclude=["*test*"])

setup(
    author="ocean-core-team",
    author_email="devops@oceanprotocol.com",
    classifiers=[
        "Development Status :: 4 - Beta",
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
    version='2.2.4',
    # fmt: on
    zip_safe=False,
)
