#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from web3 import exceptions

from ocean_lib.models.v4.dispenser import DispenserV4
from ocean_lib.models.v4.erc20_token import ERC20Token
from ocean_lib.models.v4.erc721_factory import ERC721FactoryContract
from ocean_lib.models.v4.erc721_token import ERC721Token
from ocean_lib.models.v4.models_structures import ErcCreateData
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from tests.resources.helper_functions import get_address_of_type


def test_deploy_erc721_and_manage(
    web3, config, factory_deployer_wallet, consumer_wallet, another_consumer_wallet
):
    """
    Owner deploys a new ERC721 contract
    """
    erc721_factory = ERC721FactoryContract(
        web3, get_address_of_type(config, "ERC721Factory")
    )
    tx = erc721_factory.deploy_erc721_contract(
        "NFT",
        "SYMBOL",
        1,
        ZERO_ADDRESS,
        "https://oceanprotocol.com/nft/",
        factory_deployer_wallet,
    )
    tx_receipt = web3.eth.waitForTransactionReceipt(tx)

    event = erc721_factory.get_event_log(
        erc721_factory.EVENT_NFT_CREATED,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert event is not None

    token_address = event[0].args.newTokenAddress
    erc721_token = ERC721Token(web3, token_address)

    assert erc721_token.balance_of(factory_deployer_wallet.address) == 1

    erc721_token.add_manager(consumer_wallet.address, factory_deployer_wallet)
    erc721_token.add_to_725_store_list(
        another_consumer_wallet.address, factory_deployer_wallet
    )
    erc721_token.add_to_create_erc20_list(
        another_consumer_wallet.address, factory_deployer_wallet
    )
    erc721_token.add_to_metadata_list(
        another_consumer_wallet.address, factory_deployer_wallet
    )

    permissions = erc721_token.get_permissions(another_consumer_wallet.address)

    assert permissions[1] == True
    assert permissions[2] == True
    assert permissions[3] == True

    # * user3 deploys a new erc20DT, assigning himself as minter

    cap = web3.toWei(100000, "ether")
    tx = erc721_token.create_erc20(
        ErcCreateData(
            1,
            ["ERC20DT1", "ERC20DT1Symbol"],
            [
                another_consumer_wallet.address,
                factory_deployer_wallet.address,
                another_consumer_wallet.address,
                "0x0000000000000000000000000000000000000000",
            ],
            [cap, 0],
            [],
        ),
        another_consumer_wallet,
    )
    tx_receipt = web3.eth.waitForTransactionReceipt(tx)
    event = erc721_factory.get_event_log(
        erc721_token.EVENT_TOKEN_CREATED,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    erc20_address = event[0].args.newTokenAddress
    erc20_token = ERC20Token(web3, erc20_address)

    assert erc20_token.permissions(another_consumer_wallet.address)[0] == True

    #* NOW user3 has 2 options, minting on his own and create custom pool, or using the staking contract and deploy a pool.
    #* Pool with ocean token and market fee 0.1%

    swap_fee = web3.toWei(0.001, "ether")
    swap_ocean_fee = web3.toWei(0.001, "ether")
    swap_market_fee = web3.toWei(0.001, "ether")

    