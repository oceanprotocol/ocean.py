#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest

from conftest_ganache import *

from ocean_lib.ocean.ocean import Ocean


@pytest.fixture
def ocean(config):
    return Ocean(config)


@pytest.fixture
def ve_allocate(ocean):
    return ocean.ve_allocate
