#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_lib.models.erc721_token import ERC721Token
from tests.resources.helper_functions import deploy_erc721_erc20


def test_nft_factory(
    publisher_ocean_instance, publisher_wallet, consumer_wallet, config, web3
):
    ocn = publisher_ocean_instance
    assert ocn.get_nft_factory()

    erc721, erc20 = deploy_erc721_erc20(web3, config, publisher_wallet, consumer_wallet)
    assert ocn.get_nft_token(erc721.address).address == erc721.address
    assert ocn.get_datatoken(erc20.address).address == erc20.address

    created_nft = ocn.create_nft_token(
        name="TEST",
        symbol="TEST2",
        token_uri="http://oceanprotocol.com/nft",
        from_wallet=publisher_wallet,
    )
    assert isinstance(created_nft, ERC721Token)
    assert created_nft.contract.caller.name() == "TEST"
    assert created_nft.symbol() == "TEST2"
    assert created_nft.address
    assert created_nft.token_uri(1) == "http://oceanprotocol.com/nft"
