#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

# Directory ../ocean_lib/models/test holds test_btoken.py and more.
# Those tests grab ../ocean_lib/models/test/conftest.py, which
#  sets up convenient-to-use wallets/accounts for Alice & Bob, datatokens, more.
# *This* directory wants similar items. To avoid code repetition,
#  here we simply import that conftest's contents.
from conftest_ganache import *
