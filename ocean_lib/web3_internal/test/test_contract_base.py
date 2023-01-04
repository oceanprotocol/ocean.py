#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import pytest

from ocean_lib.ocean.util import get_address_of_type
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.contract_base import ContractBase
from tests.resources.helper_functions import get_wallet


class MyFactory(ContractBase):
    CONTRACT_NAME = "ERC721Factory"


@pytest.mark.unit
def test_name_is_None(config):
    with pytest.raises(Exception):
        # self.name will become None, triggering the error
        ContractBase(config, None)


@pytest.mark.unit
def test_main(config):
    alice_wallet = get_wallet(1)
    # test super-simple functionality of child
    nft_factory_address = get_address_of_type(config, "ERC721Factory")
    factory = MyFactory(config, nft_factory_address)
    factory.deployERC721Contract(
        "NFT",
        "NFTS",
        1,
        ZERO_ADDRESS,
        ZERO_ADDRESS,
        "http://someurl",
        True,
        alice_wallet.address,
        {"from": alice_wallet},
    )

    # test attributes
    assert factory.contract_name == "ERC721Factory"
    assert factory.contract is not None
    assert factory.contract.address == nft_factory_address
    assert ContractBase.to_checksum_address(nft_factory_address) == nft_factory_address

    # test methods
    assert factory.contract_name == "ERC721Factory"
    assert factory.address == nft_factory_address
    assert str(factory) == f"{factory.contract_name} @ {factory.address}"
    assert factory.contract.createToken
    assert factory.contract.getCurrentTokenCount
    assert factory.contract.getTokenTemplate
