#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_lib.models.v4.erc721_factory import ERC721FactoryContract
from ocean_lib.models.v4.erc721_token import ERC721Token
from ocean_lib.models.v4.models_structures import ErcCreateData
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN
from ocean_lib.web3_internal.constants import (
    ERC721_FACTORY_ADDRESS,
    ZERO_ADDRESS,
)
from tests.resources.helper_functions import get_publisher_wallet


# TODO: WIP - draft publish flow
def test_publish_flow(web3, config):
    publisher = get_publisher_wallet()

    erc721_factory = ERC721FactoryContract(web3, ERC721_FACTORY_ADDRESS)

    # Publisher deploys NFT contract
    tx = erc721_factory.deploy_erc721_contract(
        "DT1",
        "DTSYMBOL",
        1,
        ZERO_ADDRESS,
        "https://oceanprotocol.com/nft/",
        publisher,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    registered_event = erc721_factory.get_event_log(
        ERC721FactoryContract.EVENT_NFT_CREATED,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    assert registered_event[0].event == "NFTCreated"
    assert registered_event[0].args.admin == publisher.address
    token_address = registered_event[0].args.newTokenAddress
    erc721_token = ERC721Token(web3, token_address)

    # Publisher creates ERC20 token
    erc_create_data = ErcCreateData(
        1,
        ["ERC20DT1", "ERC20DT1Symbol"],
        [publisher.address, publisher.address, publisher.address, ZERO_ADDRESS],
        [web3.toWei("0.5", "ether"), 0],
        [b""],
    )
    tx_result = erc721_token.create_erc20(erc_create_data, publisher)
    assert tx_result, "Failed to create ERC20 token."
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_result)

    token_created_event = erc721_factory.get_event_log(
        ERC721FactoryContract.EVENT_TOKEN_CREATED,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    dt_address = token_created_event[0].args.newTokenAddress

    # Publisher interacts with ERC20 contract and creates a pool
    mint_fake_OCEAN(config)

    # FIXME: BTokenBase contract address does not exist.
