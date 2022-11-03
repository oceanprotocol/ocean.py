#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import pytest

from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.contract_base import ContractBase


class MyFactory(ContractBase):
    CONTRACT_NAME = "ERC721Factory"


@pytest.mark.unit
def test_name_is_None(config):
    with pytest.raises(Exception):
        # self.name will become None, triggering the error
        ContractBase(config, None)


@pytest.mark.unit
def test_main(network, alice_wallet, alice_ocean, nft_factory_address, config):
    # test super-simple functionality of child
    factory = MyFactory(config, nft_factory_address)
    factory.deployERC721Contract(
        "NFT",
        "NFTS",
        1,
        ZERO_ADDRESS,
        ZERO_ADDRESS,
        "https://oceanprotocol.com/nft/",
        True,
        alice_wallet.address,
        {"from": alice_wallet},
    )

    # test attributes
    assert factory.name == "ERC721Factory"
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
