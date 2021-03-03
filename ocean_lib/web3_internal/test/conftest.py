#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

# Directory ../tests/models/test holds test_btoken.py and more.
# Those tests grab ../tests/models/conftest.py, which
#  sets up convenient-to-use wallets/accounts for Alice & Bob, datatokens, more.
# *This* directory wants similar items. To avoid code repetition,
#  here we simply import that conftest's contents.

import pytest
from examples import ExampleConfig
from tests.models.conftest import *  # noqa: F401 F403

# Other things to set up, specific to here...


@pytest.fixture
def example_config():
    return ExampleConfig.get_config()
