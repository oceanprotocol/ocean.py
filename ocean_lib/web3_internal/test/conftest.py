#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

# Directory ../ocean_lib/models/test holds test_btoken.py and more.
# Those tests grab ../ocean_lib/models/test/conftest.py, which
#  sets up convenient-to-use wallets/accounts for Alice & Bob, datatokens, more.
# *This* directory wants similar items. To avoid code repetition,
#  here we simply import that conftest's contents.

import pytest
from ocean_lib.example_config import ExampleConfig
from ocean_lib.models.test.conftest import *  # noqa: F401 F403

# Other things to set up, specific to here...


@pytest.fixture
def example_config():
    return ExampleConfig.get_config()
