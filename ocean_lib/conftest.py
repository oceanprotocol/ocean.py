#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

# Directory ../tests/ holds many unit tests in its subdirectories.
# Those tests grab tests/conftest.py::setup_all() which has autouse=True,
# to get the web3 provider and more. *This* directory needs to access
# all of those as well. The following import accomplishes that.
from tests.conftest import setup_all  # noqa: F401
