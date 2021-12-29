#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from ocean_lib.models.v4.dispenser import DispenserV4
from ocean_lib.models.v4.erc20_token import ERC20Token
from ocean_lib.models.v4.erc721_factory import ERC721FactoryContract
from ocean_lib.models.v4.erc721_token import ERC721Token
from ocean_lib.models.v4.models_structures import ErcCreateData
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from tests.resources.helper_functions import get_address_of_type
from web3 import exceptions


def test_properties(web3, config):
    """Tests the events' properties."""
    erc721_factory_address = get_address_of_type(
        config, ERC721FactoryContract.CONTRACT_NAME
    )
    erc721_factory = ERC721FactoryContract(web3, erc721_factory_address)

    assert (
        erc721_factory.event_NFTCreated.abi["name"]
        == ERC721FactoryContract.EVENT_NFT_CREATED
    )
    assert (
        erc721_factory.event_TokenCreated.abi["name"]
        == ERC721FactoryContract.EVENT_TOKEN_CREATED
    )
    assert (
        erc721_factory.event_Template721Added.abi["name"]
        == ERC721FactoryContract.EVENT_TEMPLATE721_ADDED
    )
    assert (
        erc721_factory.event_Template20Added.abi["name"]
        == ERC721FactoryContract.EVENT_TEMPLATE20_ADDED
    )
    assert (
        erc721_factory.event_NewPool.abi["name"] == ERC721FactoryContract.EVENT_NEW_POOL
    )
    assert (
        erc721_factory.event_NewFixedRate.abi["name"]
        == ERC721FactoryContract.EVENT_NEW_FIXED_RATE
    )
    assert (
        erc721_factory.event_DispenserCreated.abi["name"]
        == ERC721FactoryContract.EVENT_DISPENSER_CREATED
    )


def test_main(web3, config, publisher_wallet, consumer_wallet, another_consumer_wallet):
    """Tests the utils functions."""
    erc721_factory_address = get_address_of_type(
        config, ERC721FactoryContract.CONTRACT_NAME
    )
    erc721_factory = ERC721FactoryContract(web3, erc721_factory_address)

    tx = erc721_factory.deploy_erc721_contract(
        "DT1",
        "DTSYMBOL",
        1,
        ZERO_ADDRESS,
        "https://oceanprotocol.com/nft/",
        publisher_wallet,
    )
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    registered_event = erc721_factory.get_event_log(
        ERC721FactoryContract.EVENT_NFT_CREATED,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    assert registered_event[0].event == "NFTCreated"
    assert registered_event[0].args.admin == publisher_wallet.address
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
        publisher_wallet,
    )
    assert erc721_factory.get_current_nft_count() == current_nft_count + 1

    # Tests get NFT template
    nft_template_address = get_address_of_type(config, ERC721Token.CONTRACT_NAME, "1")
    nft_template = erc721_factory.get_nft_template(1)
    assert nft_template[0] == nft_template_address
    assert nft_template[1] is True

    # Tests creating successfully an ERC20 token
    erc721_token.add_to_create_erc20_list(consumer_wallet.address, publisher_wallet)
    erc_create_data = ErcCreateData(
        1,
        ["ERC20DT1", "ERC20DT1Symbol"],
        [
            publisher_wallet.address,
            consumer_wallet.address,
            publisher_wallet.address,
            ZERO_ADDRESS,
        ],
        [web3.toWei("0.5", "ether"), 0],
        [b""],
    )
    tx_result = erc721_token.create_erc20(erc_create_data, consumer_wallet)
    assert tx_result, "Failed to create ERC20 token."
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_result)
    registered_token_event = erc721_factory.get_event_log(
        ERC721FactoryContract.EVENT_TOKEN_CREATED,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    assert registered_token_event, "Cannot find TokenCreated event."
    erc20_address = registered_token_event[0].args.newTokenAddress

    # Tests templateCount function (one of them should be the Enterprise template)
    assert erc721_factory.template_count() == 2

    # Tests ERC20 token template list
    erc20_template_address = get_address_of_type(config, ERC20Token.CONTRACT_NAME, "1")
    template = erc721_factory.get_token_template(1)
    assert template[0] == erc20_template_address
    assert template[1] is True

    # Tests current token template (one of them should be the Enterprise template)
    assert erc721_factory.get_current_template_count() == 2

    # Tests starting multiple token orders successfully
    erc20_token = ERC20Token(web3, erc20_address)
    dt_amount = web3.toWei("0.05", "ether")
    mock_dai_contract_address = get_address_of_type(config, "MockDAI")
    assert erc20_token.balanceOf(consumer_wallet.address) == 0

    erc20_token.add_minter(consumer_wallet.address, publisher_wallet)
    erc20_token.mint(consumer_wallet.address, dt_amount, consumer_wallet)
    assert erc20_token.balanceOf(consumer_wallet.address) == dt_amount

    erc20_token.approve(erc721_factory_address, dt_amount, consumer_wallet)

    erc20_token.set_payment_collector(another_consumer_wallet.address, publisher_wallet)

    provider_fee_address = ZERO_ADDRESS
    provider_data = b"\x00"
    provider_fee_token = mock_dai_contract_address
    provider_fee_amount = 0

    msg_hash, v, r, s = erc721_factory.sign_provider_fees(
        provider_data, provider_fee_address, provider_fee_token, provider_fee_amount
    )

    orders = [
        {
            "tokenAddress": erc20_address,
            "consumer": consumer_wallet.address,
            "serviceIndex": 1,
            "providerFeeAddress": provider_fee_address,
            "providerFeeToken": provider_fee_token,
            "providerFeeAmount": provider_fee_amount,
            "providerData": provider_data,
            "v": v,
            "r": r,
            "s": s,
        }
    ]

    tx = erc721_factory.start_multiple_token_order(orders, consumer_wallet)

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    registered_erc20_start_order_event = erc20_token.get_event_log(
        ERC20Token.EVENT_ORDER_STARTED,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert tx, "Failed starting multiple token orders."
    assert (
        registered_erc20_start_order_event[0].args.consumer == consumer_wallet.address
    )

    assert erc20_token.balanceOf(consumer_wallet.address) == 0
    assert erc20_token.balanceOf(erc20_token.get_payment_collector()) == dt_amount

    # Tests creating NFT with ERC20 successfully
    nft_create_data = {
        "name": "72120Bundle",
        "symbol": "72Bundle",
        "templateIndex": 1,
        "tokenURI": "https://oceanprotocol.com/nft/",
    }
    erc_create_data = {
        "strings": ["ERC20B1", "ERC20DT1Symbol"],
        "templateIndex": 1,
        "addresses": [
            publisher_wallet.address,
            consumer_wallet.address,
            publisher_wallet.address,
            ZERO_ADDRESS,
        ],
        "uints": [web3.toWei("10", "ether"), 0],
        "bytess": [b""],
    }

    tx = erc721_factory.create_nft_with_erc(
        nft_create_data, erc_create_data, publisher_wallet
    )
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    registered_nft_event = erc721_factory.get_event_log(
        ERC721FactoryContract.EVENT_NFT_CREATED,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    # Verify if the NFT was created.
    assert registered_nft_event, "Cannot find NFTCreated event."
    assert registered_nft_event[0].event == "NFTCreated"
    assert registered_nft_event[0].args.admin == publisher_wallet.address
    erc721_address2 = registered_nft_event[0].args.newTokenAddress
    erc721_token2 = ERC721Token(web3, erc721_address2)
    assert erc721_token2.contract.caller.name() == "72120Bundle"
    assert erc721_token2.symbol() == "72Bundle"

    registered_token_event = erc721_factory.get_event_log(
        ERC721FactoryContract.EVENT_TOKEN_CREATED,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    # Verify if the ERC20 token was created.
    assert registered_token_event, "Cannot find TokenCreated event."
    erc20_address2 = registered_token_event[0].args.newTokenAddress
    erc20_token2 = ERC20Token(web3, erc20_address2)
    assert erc20_token2.contract.caller.name() == "ERC20B1"
    assert erc20_token2.symbol() == "ERC20DT1Symbol"

    # Tests creating NFT with ERC20 and with Pool successfully.
    side_staking_address = get_address_of_type(config, "Staking")
    pool_template_address = get_address_of_type(config, "poolTemplate")
    initial_pool_liquidity = web3.toWei("0.02", "ether")

    erc20_token.mint(publisher_wallet.address, initial_pool_liquidity, publisher_wallet)
    erc20_token.approve(
        erc721_factory_address, initial_pool_liquidity, publisher_wallet
    )

    erc_create_data_pool = {
        "strings": ["ERC20WithPool", "ERC20P"],
        "templateIndex": 1,
        "addresses": [
            publisher_wallet.address,
            consumer_wallet.address,
            publisher_wallet.address,
            ZERO_ADDRESS,
        ],
        "uints": [web3.toWei("0.05", "ether"), 0],
        "bytess": [b""],
    }
    pool_data = {
        "addresses": [
            side_staking_address,
            erc20_address,
            erc721_factory_address,
            publisher_wallet.address,
            consumer_wallet.address,
            pool_template_address,
        ],
        "ssParams": [
            web3.toWei("1.0", "ether"),
            erc20_token.decimals(),
            initial_pool_liquidity
            // 100
            * 9,  # max 10% vesting amount of the total cap
            2500000,
            initial_pool_liquidity,
        ],
        "swapFees": [web3.toWei("0.001", "ether"), web3.toWei("0.001", "ether")],
    }
    tx = erc721_factory.create_nft_erc_with_pool(
        nft_create_data, erc_create_data_pool, pool_data, publisher_wallet
    )
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    registered_nft_event = erc721_factory.get_event_log(
        ERC721FactoryContract.EVENT_NFT_CREATED,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    # Verify if the NFT was created.
    assert registered_nft_event, "Cannot find NFTCreated event."
    assert registered_nft_event[0].event == "NFTCreated"
    assert registered_nft_event[0].args.admin == publisher_wallet.address
    erc721_token3 = registered_nft_event[0].args.newTokenAddress
    erc721_token3 = ERC721Token(web3, erc721_token3)
    assert erc721_token3.contract.caller.name() == "72120Bundle"
    assert erc721_token3.symbol() == "72Bundle"

    registered_token_event = erc721_factory.get_event_log(
        ERC721FactoryContract.EVENT_TOKEN_CREATED,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    # Verify if the ERC20 token was created.
    assert registered_token_event, "Cannot find TokenCreated event."
    erc20_address3 = registered_token_event[0].args.newTokenAddress
    erc20_token3 = ERC20Token(web3, erc20_address3)
    assert erc20_token3.contract.caller.name() == "ERC20WithPool"
    assert erc20_token3.symbol() == "ERC20P"

    registered_pool_event = erc20_token3.get_event_log(
        ERC721FactoryContract.EVENT_NEW_POOL,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    # Verify if the pool was created.
    assert registered_pool_event, "Cannot find NewPool event."
    pool_address = registered_pool_event[0].args.poolAddress
    pool_token = ERC20Token(web3, pool_address)

    assert pool_token.balanceOf(publisher_wallet.address) > 0, "Invalid pool share."

    # Tests creating NFT with ERC20 and with Fixed Rate Exchange successfully.
    fixed_rate_address = get_address_of_type(config, "FixedPrice")

    # Create ERC20 data token for fees.
    fee_address = "0xF9f2DB837b3db03Be72252fAeD2f6E0b73E428b9"

    erc_create_data = ErcCreateData(
        1,
        ["ERC20DT1P", "ERC20DT1SymbolP"],
        [
            publisher_wallet.address,
            consumer_wallet.address,
            fee_address,
            mock_dai_contract_address,
        ],
        [web3.toWei("0.5", "ether"), web3.toWei("0.0005", "ether")],
        [b""],
    )
    tx = erc721_token.create_erc20(erc_create_data, publisher_wallet)
    assert tx, "Failed to create ERC20 token."
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    registered_fee_token_event = erc721_factory.get_event_log(
        ERC721FactoryContract.EVENT_TOKEN_CREATED,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    assert registered_fee_token_event, "Cannot find TokenCreated event."
    fee_erc20_address = registered_fee_token_event[0].args.newTokenAddress

    fixed_rate_data = {
        "fixedPriceAddress": fixed_rate_address,
        "addresses": [
            fee_erc20_address,
            publisher_wallet.address,
            consumer_wallet.address,
            ZERO_ADDRESS,
        ],
        "uints": [18, 18, web3.toWei("1.0", "ether"), web3.toWei("0.001", "ether"), 0],
    }
    tx = erc721_factory.create_nft_erc_with_fixed_rate(
        nft_create_data, erc_create_data_pool, fixed_rate_data, publisher_wallet
    )
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    registered_nft_event = erc721_factory.get_event_log(
        ERC721FactoryContract.EVENT_NFT_CREATED,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    # Verify if the NFT was created.
    assert registered_nft_event, "Cannot find NFTCreated event."
    assert registered_nft_event[0].event == "NFTCreated"
    assert registered_nft_event[0].args.admin == publisher_wallet.address
    erc721_address4 = registered_nft_event[0].args.newTokenAddress
    erc721_token4 = ERC721Token(web3, erc721_address4)
    assert erc721_token4.contract.caller.name() == "72120Bundle"
    assert erc721_token4.symbol() == "72Bundle"

    registered_token_event = erc721_factory.get_event_log(
        ERC721FactoryContract.EVENT_TOKEN_CREATED,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    # Verify if the ERC20 token was created.
    assert registered_token_event, "Cannot find TokenCreated event."
    erc20_address4 = registered_token_event[0].args.newTokenAddress
    erc20_token4 = ERC20Token(web3, erc20_address4)
    assert erc20_token4.contract.caller.name() == "ERC20WithPool"
    assert erc20_token4.symbol() == "ERC20P"

    registered_fixed_rate_event = erc20_token4.get_event_log(
        ERC721FactoryContract.EVENT_NEW_FIXED_RATE,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    # Verify if the Fixed Rate Exchange was created.
    assert registered_fixed_rate_event, "Cannot find NewFixedRate event."
    assert registered_fixed_rate_event[0].args.exchangeId, "Invalid exchange id."

    # Tests creating NFT with ERC20 and with Dispenser successfully.
    dispenser_address = get_address_of_type(config, DispenserV4.CONTRACT_NAME)
    dispenser_data = {
        "dispenserAddress": dispenser_address,
        "maxTokens": web3.toWei("1.0", "ether"),
        "maxBalance": web3.toWei("1.0", "ether"),
        "withMint": True,
        "allowedSwapper": ZERO_ADDRESS,
    }

    tx = erc721_factory.create_nft_erc_with_dispenser(
        nft_create_data, erc_create_data_pool, dispenser_data, publisher_wallet
    )
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    registered_nft_event = erc721_factory.get_event_log(
        ERC721FactoryContract.EVENT_NFT_CREATED,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    # Verify if the NFT was created.
    assert registered_nft_event, "Cannot find NFTCreated event."
    assert registered_nft_event[0].event == "NFTCreated"
    assert registered_nft_event[0].args.admin == publisher_wallet.address
    erc721_address5 = registered_nft_event[0].args.newTokenAddress
    erc721_token5 = ERC721Token(web3, erc721_address5)
    assert erc721_token5.contract.caller.name() == "72120Bundle"
    assert erc721_token5.symbol() == "72Bundle"

    registered_token_event = erc721_factory.get_event_log(
        ERC721FactoryContract.EVENT_TOKEN_CREATED,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    # Verify if the ERC20 token was created.
    assert registered_token_event, "Cannot find TokenCreated event."
    erc20_address5 = registered_token_event[0].args.newTokenAddress
    erc20_token5 = ERC20Token(web3, erc20_address5)
    assert erc20_token5.contract.caller.name() == "ERC20WithPool"
    assert erc20_token5.symbol() == "ERC20P"

    dispenser = DispenserV4(web3, dispenser_address)

    registered_dispenser_event = dispenser.get_event_log(
        ERC721FactoryContract.EVENT_DISPENSER_CREATED,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    # Verify if the Dispenser data token was created.
    assert registered_dispenser_event, "Cannot find DispenserCreated event."
    assert registered_dispenser_event[
        0
    ].args.datatokenAddress, "Invalid data token address by dispenser."


def test_fail_get_templates(web3, config):
    """Tests multiple failures for getting tokens' templates."""
    erc721_factory_address = get_address_of_type(
        config, ERC721FactoryContract.CONTRACT_NAME
    )
    erc721_factory = ERC721FactoryContract(web3, erc721_factory_address)

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


def test_fail_create_erc20(
    web3, config, publisher_wallet, consumer_wallet, another_consumer_wallet
):
    """Tests multiple failures for creating ERC20 token."""

    erc721_factory_address = get_address_of_type(
        config, ERC721FactoryContract.CONTRACT_NAME
    )
    erc721_factory = ERC721FactoryContract(web3, erc721_factory_address)

    # Should fail to create an ERC20 calling the factory directly
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_factory.create_token(
            1,
            ["ERC20DT1", "ERC20DT1Symbol"],
            [
                publisher_wallet.address,
                publisher_wallet.address,
                publisher_wallet.address,
                ZERO_ADDRESS,
            ],
            [web3.toWei("1.0", "ether"), 0],
            [b""],
            publisher_wallet,
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
        publisher_wallet,
    )
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    registered_event = erc721_factory.get_event_log(
        ERC721FactoryContract.EVENT_NFT_CREATED,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    assert registered_event[0].event == "NFTCreated"
    assert registered_event[0].args.admin == publisher_wallet.address
    token_address = registered_event[0].args.newTokenAddress
    erc721_token = ERC721Token(web3, token_address)
    erc721_token.add_to_create_erc20_list(consumer_wallet.address, publisher_wallet)

    # Should fail to create a specific ERC20 Template if the index is ZERO
    erc_create_data = ErcCreateData(
        0,
        ["ERC20DT1", "ERC20DT1Symbol"],
        [
            publisher_wallet.address,
            consumer_wallet.address,
            publisher_wallet.address,
            ZERO_ADDRESS,
        ],
        [web3.toWei("0.5", "ether"), 0],
        [b""],
    )
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_token.create_erc20(erc_create_data, consumer_wallet)
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC20Factory: Template index "
        "doesnt exist"
    )

    # Should fail to create a specific ERC20 Template if the index doesn't exist
    erc_create_data = ErcCreateData(
        3,
        ["ERC20DT1", "ERC20DT1Symbol"],
        [
            publisher_wallet.address,
            consumer_wallet.address,
            publisher_wallet.address,
            ZERO_ADDRESS,
        ],
        [web3.toWei("0.5", "ether"), 0],
        [b""],
    )
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_token.create_erc20(erc_create_data, consumer_wallet)
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC20Factory: Template index "
        "doesnt exist"
    )

    # Should fail to create a specific ERC20 Template if the user is not added on the ERC20 deployers list
    assert erc721_token.get_permissions(another_consumer_wallet.address)[1] is False
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_token.create_erc20(erc_create_data, another_consumer_wallet)
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721Template: NOT "
        "ERC20DEPLOYER_ROLE"
    )
