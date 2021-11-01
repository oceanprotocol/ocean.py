#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest

from web3 import exceptions

from ocean_lib.models.v4.erc20_token import ERC20Token
from ocean_lib.models.v4.erc721_factory import ERC721FactoryContract
from ocean_lib.models.v4.erc721_token import ERC721Token
from ocean_lib.models.v4.models_structures import ErcCreateData
from ocean_lib.utils.addresses_utils import (
    get_nft_factory_address,
    get_nft_template_address,
    get_erc20_template_address,
    get_mock_dai_contract,
)
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from tests.resources.helper_functions import (
    get_publisher_wallet,
    get_consumer_wallet,
    get_another_consumer_wallet,
)


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
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_result)
    registered_token_event = erc721_factory.get_event_log(
        ERC721FactoryContract.EVENT_TOKEN_CREATED,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    data_token = registered_token_event[0].args.newTokenAddress

    # Tests templateCount function (one of them should be the Enterprise template)
    assert erc721_factory.template_count() == 2

    # Tests ERC20 token template list
    template = erc721_factory.get_token_template(1)
    assert template[0] == get_erc20_template_address(config)
    assert template[1] is True

    # Tests current token template (one of them should be the Enterprise template)
    assert erc721_factory.get_current_template_count() == 2

    # Tests starting multiple token orders successfully
    erc20_token = ERC20Token(web3, data_token)
    dt_amount = web3.toWei("0.05", "ether")
    assert erc20_token.balanceOf(consumer.address) == 0

    erc20_token.add_minter(consumer.address, publisher)
    erc20_token.mint(consumer.address, dt_amount, consumer)
    assert erc20_token.balanceOf(consumer.address) == dt_amount

    erc20_token.approve(get_nft_factory_address(config), dt_amount, consumer)

    tx = erc721_factory.start_multiple_token_order(
        data_token,
        consumer.address,
        dt_amount,
        1,
        ZERO_ADDRESS,
        get_mock_dai_contract(config),
        0,
        consumer,
    )
    assert tx, "Failed starting multiple token orders."
    assert erc20_token.balanceOf(consumer.address) == 0
    assert erc20_token.balanceOf(erc20_token.get_fee_collector()) == dt_amount


def test_fail_get_templates(web3, config):
    """Tests multiple failures for getting tokens' templates."""
    erc721_factory = ERC721FactoryContract(web3, get_nft_factory_address(config))

    # Should fail to get the ERC20token template if index = 0
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_factory.get_token_template(0)
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC20Factory: "
        "Template index doesnt exist"
    )

    # Should fail to get the ERC20token template if index > templateCount
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_factory.get_token_template(3)
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC20Factory: "
        "Template index doesnt exist"
    )


def test_fail_create_erc20(web3, config):
    """Tests multiple failures for creating ERC20 token."""

    publisher = get_publisher_wallet()
    consumer = get_consumer_wallet()
    another_consumer = get_another_consumer_wallet()

    erc721_factory = ERC721FactoryContract(web3, get_nft_factory_address(config))

    # Should fail to create an ERC20 calling the factory directly
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
    erc721_token.add_to_create_erc20_list(consumer.address, publisher)

    # Should fail to create a specific ERC20 Template if the index is ZERO
    erc_create_data = ErcCreateData(
        0,
        ["ERC20DT1", "ERC20DT1Symbol"],
        [publisher.address, consumer.address, publisher.address, ZERO_ADDRESS],
        [web3.toWei("0.5", "ether"), 0],
        [b""],
    )
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_token.create_erc20(erc_create_data, consumer)
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC20Factory: Template index "
        "doesnt exist"
    )

    # Should fail to create a specific ERC20 Template if the index doesn't exist
    erc_create_data = ErcCreateData(
        3,
        ["ERC20DT1", "ERC20DT1Symbol"],
        [publisher.address, consumer.address, publisher.address, ZERO_ADDRESS],
        [web3.toWei("0.5", "ether"), 0],
        [b""],
    )
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_token.create_erc20(erc_create_data, consumer)
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC20Factory: Template index "
        "doesnt exist"
    )

    # Should fail to create a specific ERC20 Template if the user is not added on the ERC20 deployers list
    assert erc721_token.get_permissions(another_consumer.address)[1] is False
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_token.create_erc20(erc_create_data, another_consumer)
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721Template: NOT "
        "ERC20DEPLOYER_ROLE"
    )
