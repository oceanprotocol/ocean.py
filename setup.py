#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import os
from os.path import join

from setuptools import setup

with open('README.md') as readme_file:
    readme = readme_file.read()

# Installed by pip install ocean-lib
# or pip install -e .
install_requirements = [
    'ocean-contracts',
    'coloredlogs',
    'pyopenssl',
    'PyJWT',  # not jwt
    'PyYAML==5.3.1',
    'ocean-utils==0.4.1',
    'requests>=2.23.0',
    'deprecated',
    'pycryptodomex',
    'tqdm',
    'pytz',
    'web3==4.7.1',
    # web3 requires eth-abi, requests, and more,
    # so those will be installed too.
    # See https://github.com/ethereum/web3.py/blob/master/setup.py
]

# Required to run setup.py:
setup_requirements = ['pytest-runner', ]

test_requirements = [
    'codacy-coverage',
    'coverage',
    'docker',
    'mccabe',
    'pylint',
    'pytest',
    'pytest-watch',
    'tox',
]

# Possibly required by developers of ocean-lib:
dev_requirements = [
    'bumpversion',
    'pkginfo',
    'twine',
    'watchdog',
    #for the following: maybe needed, maybe not
    'pytest',

]

docs_requirements = [
    'Sphinx',
    'sphinxcontrib-apidoc',
]

packages = []
for d, _, _ in os.walk('ocean_lib'):
    if os.path.exists(join(d, '__init__.py')):
        packages.append(d.replace(os.path.sep, '.'))

setup(
    author="leucothia",
    author_email='devops@oceanprotocol.com',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
    ],
    description="🐳 Ocean protocol library.",
    extras_require={
        'test': test_requirements,
        'dev': dev_requirements + test_requirements + docs_requirements,
        'docs': docs_requirements,
    },
    install_requires=install_requirements,
    license="Apache Software License 2.0",
    long_description=readme,
    long_description_content_type="text/markdown",
    include_package_data=True,
    keywords='ocean-lib',
    name='ocean-lib',
    packages=packages,
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/oceanprotocol/ocean-lib-py',
    version='0.3.1',
    zip_safe=False,
)
