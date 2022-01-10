#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from tests.resources.helper_functions import deploy_erc721_erc20


def test_nft_factory(
    publisher_ocean_instance, publisher_wallet, consumer_wallet, config, web3
):
    ocn = publisher_ocean_instance
    assert ocn.get_nft_factory()

    erc721, erc20 = deploy_erc721_erc20(web3, config, publisher_wallet, consumer_wallet)
    assert ocn.get_nft_token(erc721.address).address == erc721.address
    assert ocn.get_data_token(erc20.address).address == erc20.address
