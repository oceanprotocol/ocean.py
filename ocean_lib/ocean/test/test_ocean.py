#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest

from ocean_lib.models.data_nft import DataNFT
from ocean_lib.models.data_nft_factory import DataNFTFactoryContract
from ocean_lib.models.datatoken import Datatoken
from ocean_lib.models.dispenser import Dispenser
from ocean_lib.models.factory_router import FactoryRouter
from ocean_lib.models.fixed_rate_exchange import FixedRateExchange
from ocean_lib.models.ve_ocean import VeOcean
from ocean_lib.models.ve_allocate import VeAllocate
from ocean_lib.models.ve_fee_distributor import VeFeeDistributor


@pytest.mark.unit
def test_nft_factory(data_nft, datatoken, publisher_ocean_instance, publisher_wallet):
    ocn = publisher_ocean_instance
    assert ocn.get_nft_factory()

    assert ocn.get_nft_token(data_nft.address).address == data_nft.address
    assert ocn.get_datatoken(datatoken.address).address == datatoken.address

    created_nft = ocn.create_data_nft(
        name="TEST",
        symbol="TEST2",
        token_uri="http://oceanprotocol.com/nft",
        from_wallet=publisher_wallet,
    )
    assert isinstance(created_nft, DataNFT)
    assert created_nft.contract.name() == "TEST"
    assert created_nft.symbol() == "TEST2"
    assert created_nft.address
    assert created_nft.tokenURI(1) == "http://oceanprotocol.com/nft"

    
@pytest.mark.unit
def test_contract_objects(publisher_ocean_instance):
    ocn = publisher_ocean_instance
    
    assert ocn.OCEAN_address[:2] == "0x"
    assert isinstance(ocn.OCEAN_token, Datatoken)
    assert isinstance(ocn.get_nft_factory(), DataNFTFactoryContract)
        
    assert isinstance(ocn.dispenser, Dispenser)
    assert isinstance(ocn.fixed_rate_exchange, FixedRateExchange)
    assert isinstance(ocn.factory_router, FactoryRouter)
    
    assert isinstance(ocn.ve_ocean, VeOcean)
    assert isinstance(ocn.ve_allocate, VeAllocate)
    assert isinstance(ocn.ve_fee_distributor, VeFeeDistributor)
    
