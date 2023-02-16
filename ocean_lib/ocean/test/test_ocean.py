#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest

from ocean_lib.models.data_nft_factory import DataNFTFactoryContract
from ocean_lib.models.datatoken1 import Datatoken1
from ocean_lib.models.df.df_rewards import DFRewards
from ocean_lib.models.df.df_strategy_v1 import DFStrategyV1
from ocean_lib.models.dispenser import Dispenser
from ocean_lib.models.factory_router import FactoryRouter
from ocean_lib.models.fixed_rate_exchange import FixedRateExchange
from ocean_lib.models.ve.smart_wallet_checker import SmartWalletChecker
from ocean_lib.models.ve.ve_allocate import VeAllocate
from ocean_lib.models.ve.ve_delegation import VeDelegation
from ocean_lib.models.ve.ve_delegation_proxy import VeDelegationProxy
from ocean_lib.models.ve.ve_fee_distributor import VeFeeDistributor
from ocean_lib.models.ve.ve_fee_estimate import VeFeeEstimate
from ocean_lib.models.ve.ve_ocean import VeOcean
from tests.resources.helper_functions import deploy_erc721_erc20


@pytest.mark.unit
def test_nft_factory(config, publisher_ocean, publisher_wallet):
    data_nft, datatoken = deploy_erc721_erc20(
        config, publisher_wallet, publisher_wallet
    )
    ocean = publisher_ocean
    assert ocean.data_nft_factory

    assert ocean.get_nft_token(data_nft.address).address == data_nft.address
    assert ocean.get_datatoken(datatoken.address).address == datatoken.address


@pytest.mark.unit
def test_contract_objects(publisher_ocean):
    ocean = publisher_ocean

    assert ocean.OCEAN_address[:2] == "0x"
    assert isinstance(ocean.OCEAN_token, Datatoken1)
    assert isinstance(ocean.OCEAN, Datatoken1)
    assert ocean.OCEAN_address == ocean.OCEAN_token.address
    assert ocean.OCEAN_address == ocean.OCEAN.address

    assert isinstance(ocean.data_nft_factory, DataNFTFactoryContract)
    assert isinstance(ocean.dispenser, Dispenser)
    assert isinstance(ocean.fixed_rate_exchange, FixedRateExchange)
    assert isinstance(ocean.factory_router, FactoryRouter)

    assert isinstance(ocean.df_rewards, DFRewards)
    assert isinstance(ocean.df_strategy_v1, DFStrategyV1)
    assert isinstance(ocean.smart_wallet_checker, SmartWalletChecker)
    assert isinstance(ocean.ve_allocate, VeAllocate)
    assert isinstance(ocean.ve_delegation, VeDelegation)
    assert isinstance(ocean.ve_delegation_proxy, VeDelegationProxy)
    assert isinstance(ocean.ve_fee_distributor, VeFeeDistributor)
    assert isinstance(ocean.ve_fee_estimate, VeFeeEstimate)
    assert isinstance(ocean.ve_ocean, VeOcean)
    assert isinstance(ocean.veOCEAN, VeOcean)

    assert ocean.config == ocean.config_dict  # test alias
