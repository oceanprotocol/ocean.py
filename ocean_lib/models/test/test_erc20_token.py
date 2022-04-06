#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import json

import pytest
from web3 import exceptions
from web3.main import Web3

from ocean_lib.models.erc20_token import ERC20Token, RolesERC20
from ocean_lib.models.erc721_factory import ERC721FactoryContract
from ocean_lib.models.erc721_nft import ERC721NFT
from ocean_lib.web3_internal.constants import MAX_UINT256, ZERO_ADDRESS
from ocean_lib.web3_internal.currency import to_wei
from ocean_lib.web3_internal.utils import split_signature
from tests.resources.helper_functions import get_address_of_type


@pytest.mark.unit
def test_properties(web3, config, publisher_wallet, erc20_token):
    """Tests the events' properties."""
    assert erc20_token.event_NewPool.abi["name"] == ERC20Token.EVENT_NEW_POOL
    assert erc20_token.event_NewFixedRate.abi["name"] == ERC20Token.EVENT_NEW_FIXED_RATE
    assert (
        erc20_token.event_MinterProposed.abi["name"] == ERC20Token.EVENT_MINTER_PROPOSED
    )
    assert erc20_token.event_OrderStarted.abi["name"] == ERC20Token.EVENT_ORDER_STARTED
    assert (
        erc20_token.event_MinterApproved.abi["name"] == ERC20Token.EVENT_MINTER_APPROVED
    )
    assert erc20_token.event_OrderReused.abi["name"] == ERC20Token.EVENT_ORDER_REUSED
    assert (
        erc20_token.event_OrderExecuted.abi["name"] == ERC20Token.EVENT_ORDER_EXECUTED
    )
    assert (
        erc20_token.event_PublishMarketFeeChanged.abi["name"]
        == ERC20Token.EVENT_PUBLISH_MARKET_FEE_CHANGED
    )
    assert (
        erc20_token.event_ConsumeMarketFee.abi["name"]
        == ERC20Token.EVENT_CONSUME_MARKET_FEE
    )
    assert erc20_token.event_ProviderFee.abi["name"] == ERC20Token.EVENT_PROVIDER_FEE


@pytest.mark.unit
def test_main(web3, config, publisher_wallet, consumer_wallet, factory_router):
    """Tests successful function calls"""
    erc721_factory_address = get_address_of_type(
        config, ERC721FactoryContract.CONTRACT_NAME
    )
    erc721_factory = ERC721FactoryContract(web3, erc721_factory_address)

    publish_market_order_fee = 5

    tx = erc721_factory.deploy_erc721_contract(
        name="DT1",
        symbol="DTSYMBOL",
        template_index=1,
        additional_metadata_updater=ZERO_ADDRESS,
        additional_erc20_deployer=ZERO_ADDRESS,
        token_uri="https://oceanprotocol.com/nft/",
        transferable=True,
        owner=publisher_wallet.address,
        from_wallet=publisher_wallet,
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
    erc721_nft = ERC721NFT(web3, token_address)
    assert erc721_nft.contract.caller.name() == "DT1"
    assert erc721_nft.symbol() == "DTSYMBOL"

    # Tests current NFT count
    current_nft_count = erc721_factory.get_current_nft_count()
    erc721_factory.deploy_erc721_contract(
        name="DT2",
        symbol="DTSYMBOL1",
        template_index=1,
        additional_metadata_updater=ZERO_ADDRESS,
        additional_erc20_deployer=ZERO_ADDRESS,
        token_uri="https://oceanprotocol.com/nft/",
        transferable=True,
        owner=publisher_wallet.address,
        from_wallet=publisher_wallet,
    )
    assert erc721_factory.get_current_nft_count() == current_nft_count + 1

    # Tests get NFT template
    nft_template_address = get_address_of_type(config, ERC721NFT.CONTRACT_NAME, "1")
    nft_template = erc721_factory.get_nft_template(1)
    assert nft_template[0] == nft_template_address
    assert nft_template[1] is True

    # Tests creating successfully an ERC20 token
    erc721_nft.add_to_create_erc20_list(consumer_wallet.address, publisher_wallet)
    tx_result = erc721_nft.create_erc20(
        template_index=1,
        name="ERC20DT1",
        symbol="ERC20DT1Symbol",
        minter=publisher_wallet.address,
        fee_manager=consumer_wallet.address,
        publish_market_order_fee_address=publisher_wallet.address,
        publish_market_order_fee_token=ZERO_ADDRESS,
        cap=to_wei(5),  # ERC20 cap is always MAX_UINT256
        publish_market_order_fee_amount=0,
        bytess=[b""],
        from_wallet=consumer_wallet,
    )
    assert tx_result, "Failed to create ERC20 token."

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_result)
    registered_token_event = erc721_factory.get_event_log(
        ERC721FactoryContract.EVENT_TOKEN_CREATED,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    assert registered_token_event, "Cannot find TokenCreated event."

    # Tests templateCount function (one of them should be the Enterprise template)
    assert erc721_factory.template_count() == 2

    # Tests ERC20 token template list
    erc20_template_address = get_address_of_type(config, ERC20Token.CONTRACT_NAME, "1")
    template = erc721_factory.get_token_template(1)
    assert template[0] == erc20_template_address
    assert template[1] is True

    # Create an ERC20 with order fees ( 5 USDC, going to publishMarketAddress)
    tx = erc721_nft.create_erc20(
        template_index=1,
        name="ERC20DT1",
        symbol="ERC20DT1Symbol",
        minter=publisher_wallet.address,
        fee_manager=erc721_nft.address,
        publish_market_order_fee_address=publisher_wallet.address,
        publish_market_order_fee_token=ZERO_ADDRESS,
        cap=to_wei(1000),  # ERC20 cap is always MAX_UINT256
        publish_market_order_fee_amount=to_wei(publish_market_order_fee),
        bytess=[b""],
        from_wallet=publisher_wallet,
    )
    tx_receipt2 = web3.eth.wait_for_transaction_receipt(tx)

    registered_event2 = erc721_factory.get_event_log(
        ERC721FactoryContract.EVENT_TOKEN_CREATED,
        tx_receipt2.blockNumber,
        web3.eth.block_number,
        None,
    )

    erc20_address = registered_event2[0].args.newTokenAddress
    erc20 = ERC20Token(web3, erc20_address)

    # Check erc20 params
    assert erc20.get_id() == 1
    assert erc20.contract.caller.name() == "ERC20DT1"
    assert erc20.symbol() == "ERC20DT1Symbol"
    assert erc20.decimals() == 18
    assert erc20.cap() == MAX_UINT256
    # Check publish fee info
    assert erc20.get_publishing_market_fee()[0] == publisher_wallet.address
    assert erc20.get_publishing_market_fee()[1] == ZERO_ADDRESS
    assert erc20.get_publishing_market_fee()[2] == to_wei(publish_market_order_fee)
    assert erc20.get_erc721_address() == erc721_nft.address

    # Check minter permissions
    assert erc20.get_permissions(publisher_wallet.address)[RolesERC20.MINTER]
    assert erc20.is_minter(publisher_wallet.address)

    # Check that the erc20Token contract is initialized
    assert erc20.is_initialized()

    # Should succeed to mint 1 ERC20Token to user2
    erc20.mint(consumer_wallet.address, 1, publisher_wallet)
    assert erc20.balanceOf(consumer_wallet.address) == 1

    # Should succeed to set new FeeCollector if feeManager
    erc20.set_payment_collector(
        publish_market_order_fee_address=publisher_wallet.address,
        from_wallet=publisher_wallet,
    )

    # Should succeed to removeMinter if erc20Deployer
    erc20.remove_minter(
        minter_address=consumer_wallet.address, from_wallet=publisher_wallet
    )

    # Should succeed to addFeeManager if erc20Deployer (permission to deploy the erc20Contract at 721 level)
    erc20.add_payment_manager(
        fee_manager=consumer_wallet.address, from_wallet=publisher_wallet
    )

    # Should succeed to removeFeeManager if erc20Deployer
    erc20.remove_payment_manager(
        fee_manager=consumer_wallet.address, from_wallet=publisher_wallet
    )

    # Should succeed to setData if erc20Deployer
    value = web3.toHex(text="SomeData")
    key = web3.keccak(hexstr=erc20.address)

    erc20.set_data(data=value, from_wallet=publisher_wallet)

    assert web3.toHex(erc721_nft.get_data(key)) == value

    # Should succeed to call cleanPermissions if NFTOwner
    erc20.clean_permissions(from_wallet=publisher_wallet)

    permissions = erc20.get_permissions(publisher_wallet.address)
    assert not permissions[RolesERC20.MINTER]
    assert not permissions[RolesERC20.PAYMENT_MANAGER]


def test_start_order(
    web3, config, publisher_wallet, consumer_wallet, erc721_nft, erc20_token
):
    """Tests startOrder functionality without publish fees, consume fees."""
    # Mint erc20 tokens to use
    erc20_token.mint(consumer_wallet.address, to_wei("10"), publisher_wallet)
    erc20_token.mint(publisher_wallet.address, to_wei("10"), publisher_wallet)

    # Set the fee collector address
    erc20_token.set_payment_collector(
        get_address_of_type(config, "OPFCommunityFeeCollector"), publisher_wallet
    )

    provider_fee_address = publisher_wallet.address
    provider_fee_token = get_address_of_type(config, "MockUSDC")
    provider_fee_amount = 0
    provider_data = json.dumps({"timeout": 0}, separators=(",", ":"))

    message = Web3.solidityKeccak(
        ["bytes", "address", "address", "uint256", "uint256"],
        [
            Web3.toHex(Web3.toBytes(text=provider_data)),
            provider_fee_address,
            provider_fee_token,
            provider_fee_amount,
            0,
        ],
    )
    signed = web3.eth.sign(provider_fee_address, data=message)
    signature = split_signature(signed)

    tx = erc20_token.start_order(
        consumer=consumer_wallet.address,
        service_index=1,
        provider_fee_address=provider_fee_address,
        provider_fee_token=provider_fee_token,
        provider_fee_amount=provider_fee_amount,
        provider_data=Web3.toHex(Web3.toBytes(text=provider_data)),
        # make it compatible with last openzepellin https://github.com/OpenZeppelin/openzeppelin-contracts/pull/1622
        v=signature.v,
        r=signature.r,
        s=signature.s,
        valid_until=0,
        consume_market_order_fee_address=publisher_wallet.address,
        consume_market_order_fee_token=erc20_token.address,
        consume_market_order_fee_amount=0,
        from_wallet=publisher_wallet,
    )
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    # Check erc20 balances
    assert erc20_token.balanceOf(publisher_wallet.address) == to_wei("9")
    assert erc20_token.balanceOf(
        get_address_of_type(config, "OPFCommunityFeeCollector")
    ) == to_wei("1")

    provider_message = Web3.solidityKeccak(
        ["bytes32", "bytes"],
        [tx_receipt.transactionHash, Web3.toHex(Web3.toBytes(text=provider_data))],
    )
    provider_signed = web3.eth.sign(provider_fee_address, data=provider_message)

    message = Web3.solidityKeccak(
        ["bytes"],
        [Web3.toHex(Web3.toBytes(text="12345"))],
    )
    consumer_signed = web3.eth.sign(consumer_wallet.address, data=message)

    erc20_token.order_executed(
        order_tx_id=tx_receipt.transactionHash,
        provider_data=Web3.toHex(Web3.toBytes(text=provider_data)),
        provider_signature=provider_signed,
        consumer_data=Web3.toHex(Web3.toBytes(text="12345")),
        consumer_signature=consumer_signed,
        consumer=consumer_wallet.address,
        from_wallet=publisher_wallet,
    )
    executed_event = erc20_token.get_event_log(
        ERC20Token.EVENT_ORDER_EXECUTED,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    assert executed_event[0].event == "OrderExecuted", "Cannot find OrderExecuted event"
    assert executed_event[0].args.orderTxId == tx_receipt.transactionHash
    assert executed_event[0].args.providerAddress == provider_fee_address

    # Tests exceptions for order_executed
    consumer_signed = web3.eth.sign(provider_fee_address, data=message)
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc20_token.order_executed(
            tx_receipt.transactionHash,
            provider_data=Web3.toHex(Web3.toBytes(text=provider_data)),
            provider_signature=provider_signed,
            consumer_data=Web3.toHex(Web3.toBytes(text="12345")),
            consumer_signature=consumer_signed,
            consumer=consumer_wallet.address,
            from_wallet=publisher_wallet,
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert Consumer signature check failed"
    )

    message = Web3.solidityKeccak(
        ["bytes"],
        [Web3.toHex(Web3.toBytes(text="12345"))],
    )
    consumer_signed = web3.eth.sign(consumer_wallet.address, data=message)

    with pytest.raises(exceptions.ContractLogicError) as err:
        erc20_token.order_executed(
            tx_receipt.transactionHash,
            provider_data=Web3.toHex(Web3.toBytes(text=provider_data)),
            provider_signature=signed,
            consumer_data=Web3.toHex(Web3.toBytes(text="12345")),
            consumer_signature=consumer_signed,
            consumer=consumer_wallet.address,
            from_wallet=publisher_wallet,
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert Provider signature check failed"
    )

    # Tests reuses order
    erc20_token.reuse_order(
        tx_receipt.transactionHash,
        provider_fee_address=provider_fee_address,
        provider_fee_token=provider_fee_token,
        provider_fee_amount=provider_fee_amount,
        v=signature.v,
        r=signature.r,
        s=signature.s,
        valid_until=0,
        provider_data=Web3.toHex(Web3.toBytes(text=provider_data)),
        # make it compatible with last openzepellin https://github.com/OpenZeppelin/openzeppelin-contracts/pull/1622
        from_wallet=publisher_wallet,
    )
    reused_event = erc20_token.get_event_log(
        ERC20Token.EVENT_ORDER_REUSED,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    assert reused_event[0].event == "OrderReused", "Cannot find OrderReused event"
    assert reused_event[0].args.orderTxId == tx_receipt.transactionHash
    assert reused_event[0].args.caller == publisher_wallet.address

    provider_fee_event = erc20_token.get_event_log(
        ERC20Token.EVENT_PROVIDER_FEE,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    assert provider_fee_event[0].event == "ProviderFee", "Cannot find ProviderFee event"

    # Set and get publishing market fee params
    erc20_token.set_publishing_market_fee(
        publish_market_order_fee_address=publisher_wallet.address,
        publish_market_order_fee_token=get_address_of_type(config, "MockUSDC"),
        publish_market_order_fee_amount=to_wei("1.2"),
        from_wallet=publisher_wallet,
    )

    publish_fees = erc20_token.get_publishing_market_fee()

    # PublishMarketFeeAddress set previously
    assert publish_fees[0] == publisher_wallet.address
    # PublishMarketFeeToken set previously
    assert publish_fees[1] == get_address_of_type(config, "MockUSDC")
    # PublishMarketFeeAmount set previously
    assert publish_fees[2] == to_wei("1.2")
    # Fee collector
    assert erc20_token.get_payment_collector() == get_address_of_type(
        config, "OPFCommunityFeeCollector"
    )

    # Publisher should succeed to burn some consumer's tokens using burnFrom
    initial_total_supply = erc20_token.get_total_supply()
    initial_consumer_balance = erc20_token.balanceOf(consumer_wallet.address)

    # Approve publisher to burn
    erc20_token.approve(publisher_wallet.address, to_wei("10"), consumer_wallet)

    assert erc20_token.allowance(
        consumer_wallet.address, publisher_wallet.address
    ) == to_wei("10")
    erc20_token.burn_from(consumer_wallet.address, to_wei("2"), publisher_wallet)

    assert erc20_token.get_total_supply() == initial_total_supply - to_wei("2")
    assert erc20_token.balanceOf(
        consumer_wallet.address
    ) == initial_consumer_balance - to_wei("2")

    # Test transterFrom too
    initial_consumer_balance = erc20_token.balanceOf(consumer_wallet.address)
    erc20_token.transferFrom(
        consumer_wallet.address, publisher_wallet.address, to_wei("1"), publisher_wallet
    )
    assert erc20_token.balanceOf(
        consumer_wallet.address
    ) == initial_consumer_balance - to_wei("1")

    # Consumer should be able to burn his tokens too
    initial_consumer_balance = erc20_token.balanceOf(consumer_wallet.address)
    erc20_token.burn(to_wei("1"), consumer_wallet)
    assert erc20_token.balanceOf(
        consumer_wallet.address
    ) == initial_consumer_balance - to_wei("1")

    # Consumer should be able to transfer too
    initial_consumer_balance = erc20_token.balanceOf(consumer_wallet.address)
    erc20_token.transfer(publisher_wallet.address, to_wei("1"), consumer_wallet)
    assert erc20_token.balanceOf(
        consumer_wallet.address
    ) == initial_consumer_balance - to_wei("1")


@pytest.mark.unit
def test_exceptions(
    web3, config, publisher_wallet, consumer_wallet, factory_router, erc20_token
):
    """Tests revert statements in contracts functions"""

    # Should fail to mint if wallet is not a minter
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc20_token.mint(
            account_address=consumer_wallet.address,
            value=to_wei("1"),
            from_wallet=consumer_wallet,
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC20Template: NOT MINTER"
    )

    #  Should fail to set new FeeCollector if not NFTOwner
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc20_token.set_payment_collector(
            publish_market_order_fee_address=consumer_wallet.address,
            from_wallet=consumer_wallet,
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC20Template: NOT PAYMENT MANAGER or OWNER"
    )

    # Should fail to addMinter if not erc20Deployer (permission to deploy the erc20Contract at 721 level)
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc20_token.add_minter(
            minter_address=consumer_wallet.address, from_wallet=consumer_wallet
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC20Template: NOT DEPLOYER ROLE"
    )

    #  Should fail to removeMinter even if it's minter
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc20_token.remove_minter(
            minter_address=consumer_wallet.address, from_wallet=consumer_wallet
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC20Template: NOT DEPLOYER ROLE"
    )

    # Should fail to addFeeManager if not erc20Deployer (permission to deploy the erc20Contract at 721 level)
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc20_token.add_payment_manager(
            fee_manager=consumer_wallet.address, from_wallet=consumer_wallet
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC20Template: NOT DEPLOYER ROLE"
    )

    # Should fail to removeFeeManager if NOT erc20Deployer
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc20_token.remove_payment_manager(
            fee_manager=consumer_wallet.address, from_wallet=consumer_wallet
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC20Template: NOT DEPLOYER ROLE"
    )

    # Should fail to setData if NOT erc20Deployer
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc20_token.set_data(
            data=web3.toHex(text="SomeData"), from_wallet=consumer_wallet
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC20Template: NOT DEPLOYER ROLE"
    )

    # Should fail to call cleanPermissions if NOT NFTOwner
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc20_token.clean_permissions(from_wallet=consumer_wallet)
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC20Template: not NFTOwner"
    )

    # Clean from nft should work shouldn't be callable by publisher or consumer, only by erc721 contract
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc20_token.clean_from_721(from_wallet=consumer_wallet)
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC20Template: NOT 721 Contract"
    )
