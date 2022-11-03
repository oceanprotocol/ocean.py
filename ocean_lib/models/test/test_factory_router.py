#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from web3 import Web3

from ocean_lib.models.factory_router import FactoryRouter
from ocean_lib.ocean.util import get_address_of_type
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.currency import to_wei

# Constants copied from FactoryRouter.sol, used for testing purposes
OPC_SWAP_FEE_APPROVED = to_wei("0.001")  # 0.1%
OPC_SWAP_FEE_NOT_APPROVED = to_wei("0.002")  # 0.2%
OPC_CONSUME_FEE = to_wei("0.03")  # 0.03 DT
OPC_PROVIDER_FEE = to_wei("0")  # 0%


# FactoryRouter methods
@pytest.mark.unit
def test_router_owner(factory_router: FactoryRouter):
    assert Web3.isChecksumAddress(factory_router.routerOwner())


@pytest.mark.unit
def test_factory(config: dict, factory_router: FactoryRouter):
    assert factory_router.factory() == get_address_of_type(config, "ERC721Factory")


@pytest.mark.unit
def test_swap_ocean_fee(factory_router: FactoryRouter):
    assert factory_router.swapOceanFee() == OPC_SWAP_FEE_APPROVED


@pytest.mark.unit
def test_swap_non_ocean_fee(factory_router: FactoryRouter):
    assert factory_router.swapNonOceanFee() == OPC_SWAP_FEE_NOT_APPROVED


@pytest.mark.unit
def test_is_approved_token(
    config: dict, factory_router: FactoryRouter, ocean_address: str
):
    """Tests that Ocean token has been added to the mapping"""
    assert factory_router.isApprovedToken(ocean_address)
    assert not (factory_router.isApprovedToken(ZERO_ADDRESS))


@pytest.mark.unit
def test_is_ss_contract(config: dict, factory_router: FactoryRouter):
    """Tests if ssContract address has been added to the mapping"""
    assert factory_router.isSSContract(get_address_of_type(config, "Staking"))


@pytest.mark.unit
def test_is_fixed_rate_contract(config: dict, factory_router: FactoryRouter):
    """Tests that fixedRateExchange address is added to the mapping"""
    assert factory_router.isFixedRateContract(get_address_of_type(config, "FixedPrice"))


@pytest.mark.unit
def test_is_dispenser_contract(config: dict, factory_router: FactoryRouter):
    assert factory_router.isDispenserContract(get_address_of_type(config, "Dispenser"))


@pytest.mark.unit
def test_get_opc_fee(config: dict, factory_router: FactoryRouter, ocean_address: str):
    assert factory_router.getOPCFee(ocean_address) == OPC_SWAP_FEE_APPROVED
    assert factory_router.getOPCFee(ZERO_ADDRESS) == OPC_SWAP_FEE_NOT_APPROVED


@pytest.mark.unit
def test_get_opc_fees(factory_router: FactoryRouter):
    assert factory_router.getOPCFees() == [
        OPC_SWAP_FEE_APPROVED,
        OPC_SWAP_FEE_NOT_APPROVED,
    ]


@pytest.mark.unit
def test_get_opc_consume_fee(factory_router: FactoryRouter):
    assert factory_router.getOPCConsumeFee() == OPC_CONSUME_FEE


@pytest.mark.unit
def test_get_opc_provider_fee(factory_router: FactoryRouter):
    assert factory_router.getOPCProviderFee() == OPC_PROVIDER_FEE


@pytest.mark.unit
def test_opc_collector(config: dict, factory_router: FactoryRouter):
    assert factory_router.getOPCCollector() == get_address_of_type(
        config, "OPFCommunityFeeCollector"
    )
