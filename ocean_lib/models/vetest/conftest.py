#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest

from conftest_ganache import *
from ocean_lib.models.ve_allocate import VeAllocate
from ocean_lib.models.ve_fee_distributor import VeFeeDistributor
from ocean_lib.models.ve_ocean import VeOcean
from ocean_lib.ocean.util import get_address_of_type


@pytest.fixture
def veOCEAN(config):
    return VeOcean(config, get_address_of_type(config, "veOCEAN"))


@pytest.fixture
def ve_allocate(config):
    return VeAllocate(config, get_address_of_type(config, "veAllocate"))


@pytest.fixture
def ve_fee_distributor(config):
    return VeFeeDistributor(config, get_address_of_type(config, "veFeeDistributor"))


def to_wei(amt_eth) -> int:
    return int(amt_eth * 1e18)


def from_wei(amt_wei: int) -> float:
    return float(amt_wei / 1e18)
