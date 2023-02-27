#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest

from conftest_ganache import *


@pytest.fixture
def ocean(publisher_ocean):
    return publisher_ocean
