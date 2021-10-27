#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import json

import pytest

from web3 import exceptions

from ocean_lib.models.v4.erc721_factory import ERC721FactoryContract
from ocean_lib.models.v4.erc721_token import ERC721Token
from ocean_lib.models.v4.models_structures import ErcCreateData
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.contract_utils import get_contract_definition
from tests.resources.helper_functions import (
    get_publisher_wallet,
    get_consumer_wallet,
    get_another_consumer_wallet,
)

_NETWORK = "development"


def get_nft_factory_address(config):
    """Helper function to retrieve a known ERC721 factory address."""

    # FIXME: fix get_contract_addresses bug to use here
    with open(config.address_file) as f:
        network_addresses = json.load(f)

    return network_addresses[_NETWORK]["v4"][ERC721FactoryContract.CONTRACT_NAME]


def get_nft_template_address(config):
    """Helper function to retrieve a known ERC721 template address."""

    # FIXME: fix get_contract_addresses bug to use here
    with open(config.address_file) as f:
        network_addresses = json.load(f)

    return network_addresses[_NETWORK]["v4"][ERC721Token.CONTRACT_NAME]


def test_properties(web3, config):
    """Tests the events' properties."""
    erc721_factory = ERC721FactoryContract(web3, get_nft_factory_address(config))
    assert (
        erc721_factory.event_NFTCreated.abi["name"]
        == ERC721FactoryContract.EVENT_NFT_CREATED
    )
    assert (
        erc721_factory.event_TokenCreated.abi["name"]
        == ERC721FactoryContract.EVENT_TOKEN_CREATED
    )
    assert (
        erc721_factory.event_NewPool.abi["name"] == ERC721FactoryContract.EVENT_NEW_POOL
    )
    assert (
        erc721_factory.event_NewFixedRate.abi["name"]
        == ERC721FactoryContract.EVENT_NEW_FIXED_RATE
    )


def test_main(web3, config):
    """Tests the utils functions."""
    publisher = get_publisher_wallet()
    consumer = get_consumer_wallet()
    another_consumer = get_another_consumer_wallet()

    erc721_factory = ERC721FactoryContract(web3, get_nft_factory_address(config))
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
    assert erc721_token.contract.caller.name() == "DT1"
    assert erc721_token.symbol() == "DTSYMBOL"

    # Tests current NFT count
    current_nft_count = erc721_factory.get_current_nft_count()
    erc721_factory.deploy_erc721_contract(
        "DT2",
        "DTSYMBOL1",
        1,
        ZERO_ADDRESS,
        "https://oceanprotocol.com/nft/",
        publisher,
    )
    assert erc721_factory.get_current_nft_count() == current_nft_count + 1

    # Tests get NFT template
    nft_template = erc721_factory.get_nft_template(1)
    assert nft_template[0] == get_nft_template_address(config)
    assert nft_template[1] is True

    # Tests creating successfully an ERC20 token
    erc721_token.add_to_create_erc20_list(consumer.address, publisher)
    erc_create_data = ErcCreateData(
        1,
        ["ERC20DT1", "ERC20DT1Symbol"],
        [publisher.address, consumer.address, publisher.address, ZERO_ADDRESS],
        [web3.toWei("0.5", "ether"), 0],
        [b""],
    )
    tx_result = erc721_token.create_erc20(erc_create_data, consumer)
    assert tx_result, "Failed to create ERC20 token."

    # Tests failed creation of ERC20
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_token.create_erc20(erc_create_data, another_consumer)
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721Template: NOT "
        "ERC20DEPLOYER_ROLE"
    )


def test_fail_create_erc20(web3, config):
    publisher = get_publisher_wallet()

    erc721_factory = ERC721FactoryContract(web3, get_nft_factory_address(config))

    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_factory.create_token(
            1,
            ["ERC20DT1", "ERC20DT1Symbol"],
            [publisher.address, publisher.address, publisher.address, ZERO_ADDRESS],
            [web3.toWei("1.0", "ether"), 0],
            [b""],
            publisher,
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721Factory: ONLY ERC721 "
        "INSTANCE FROM ERC721FACTORY"
    )


def test_nonexistent_template_index(web3, config):
    publisher = get_publisher_wallet()
    erc721_factory = ERC721FactoryContract(web3, get_nft_factory_address(config))
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_factory.deploy_erc721_contract(
            "DT1",
            "DTSYMBOL",
            7,
            ZERO_ADDRESS,
            "https://oceanprotocol.com/nft/",
            publisher,
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721DTFactory: Template index "
        "doesnt exist"
    )
