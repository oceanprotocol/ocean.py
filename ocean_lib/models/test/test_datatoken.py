#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import json

import pytest
from brownie import network
from brownie.network.transaction import TransactionReceipt
from web3.main import Web3

from ocean_lib.models.data_nft import DataNFT
from ocean_lib.models.datatoken import Datatoken, DatatokenRoles
from ocean_lib.ocean.util import get_address_of_type
from ocean_lib.web3_internal.constants import MAX_UINT256
from ocean_lib.web3_internal.currency import to_wei
from ocean_lib.web3_internal.utils import split_signature


@pytest.mark.unit
def test_main(
    publisher_wallet,
    consumer_wallet,
    data_nft: DataNFT,
    datatoken: Datatoken,
):
    """Tests successful function calls"""

    # Check datatoken params
    assert datatoken.get_id() == 1
    assert datatoken.contract.name() == "DT1"
    assert datatoken.symbol() == "DT1Symbol"
    assert datatoken.decimals() == 18
    assert datatoken.cap() == MAX_UINT256

    # Check data NFT address
    assert datatoken.get_erc721_address() == data_nft.address

    # Check that the Datatoken contract is initialized
    assert datatoken.is_initialized()

    # Check publish market payment collector
    assert datatoken.get_payment_collector() == publisher_wallet.address

    # Set payment collector to consumer
    datatoken.set_payment_collector(
        publish_market_order_fee_address=consumer_wallet.address,
        from_wallet=publisher_wallet,
    )
    assert datatoken.get_payment_collector() == consumer_wallet.address

    # Check minter permissions
    assert datatoken.get_permissions(publisher_wallet.address)[DatatokenRoles.MINTER]
    assert datatoken.is_minter(publisher_wallet.address)

    # Mint Datatoken to user2 from publisher
    datatoken.mint(consumer_wallet.address, 1, {"from": publisher_wallet})
    assert datatoken.balanceOf(consumer_wallet.address) == 1

    # Add minter
    assert not datatoken.get_permissions(consumer_wallet.address)[DatatokenRoles.MINTER]
    datatoken.add_minter(consumer_wallet.address, publisher_wallet)
    assert datatoken.get_permissions(consumer_wallet.address)[DatatokenRoles.MINTER]

    # Mint Datatoken to user2 from consumer
    datatoken.mint(consumer_wallet.address, 1, {"from": consumer_wallet})
    assert datatoken.balanceOf(consumer_wallet.address) == 2

    # Should succeed to removeMinter if erc20Deployer
    datatoken.remove_minter(consumer_wallet.address, publisher_wallet)
    assert not datatoken.get_permissions(consumer_wallet.address)[DatatokenRoles.MINTER]

    # Should succeed to addFeeManager if erc20Deployer (permission to deploy the erc20Contract at 721 level)
    assert not datatoken.get_permissions(consumer_wallet.address)[
        DatatokenRoles.PAYMENT_MANAGER
    ]
    datatoken.add_payment_manager(consumer_wallet.address, publisher_wallet)
    assert datatoken.get_permissions(consumer_wallet.address)[
        DatatokenRoles.PAYMENT_MANAGER
    ]

    # Should succeed to removeFeeManager if erc20Deployer
    datatoken.remove_payment_manager(
        fee_manager=consumer_wallet.address, from_wallet=publisher_wallet
    )
    assert not datatoken.get_permissions(consumer_wallet.address)[
        DatatokenRoles.PAYMENT_MANAGER
    ]

    # Should succeed to setData if erc20Deployer
    value = Web3.toHex(text="SomeData")
    key = Web3.keccak(hexstr=datatoken.address)

    datatoken.set_data(data=value, from_wallet=publisher_wallet)

    assert Web3.toHex(data_nft.get_data(key)) == value

    # Should succeed to call cleanPermissions if NFTOwner
    datatoken.clean_permissions(from_wallet=publisher_wallet)

    permissions = datatoken.get_permissions(publisher_wallet.address)
    assert not permissions[DatatokenRoles.MINTER]
    assert not permissions[DatatokenRoles.PAYMENT_MANAGER]


def test_start_order(config, publisher_wallet, consumer_wallet, data_nft, datatoken):
    """Tests startOrder functionality without publish fees, consume fees."""
    # Mint datatokens to use
    datatoken.mint(consumer_wallet.address, to_wei("10"), {"from": publisher_wallet})
    datatoken.mint(publisher_wallet.address, to_wei("10"), {"from": publisher_wallet})

    # Set the fee collector address
    datatoken.set_payment_collector(
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

    signed = network.web3.eth.sign(provider_fee_address, data=message)
    signature = split_signature(signed)

    tx = datatoken.start_order(
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
        consume_market_order_fee_token=datatoken.address,
        consume_market_order_fee_amount=0,
        from_wallet=publisher_wallet,
    )
    receipt = TransactionReceipt(tx)
    # Check erc20 balances
    assert datatoken.balanceOf(publisher_wallet.address) == to_wei("9")
    assert datatoken.balanceOf(
        get_address_of_type(config, "OPFCommunityFeeCollector")
    ) == to_wei("1")

    provider_message = Web3.solidityKeccak(
        ["bytes32", "bytes"],
        [receipt.txid, Web3.toHex(Web3.toBytes(text=provider_data))],
    )
    provider_signed = network.web3.eth.sign(provider_fee_address, data=provider_message)

    message = Web3.solidityKeccak(
        ["bytes"],
        [Web3.toHex(Web3.toBytes(text="12345"))],
    )
    consumer_signed = network.web3.eth.sign(consumer_wallet.address, data=message)

    tx = datatoken.order_executed(
        order_tx_id=receipt.txid,
        provider_data=Web3.toHex(Web3.toBytes(text=provider_data)),
        provider_signature=provider_signed,
        consumer_data=Web3.toHex(Web3.toBytes(text="12345")),
        consumer_signature=consumer_signed,
        consumer=consumer_wallet.address,
        from_wallet=publisher_wallet,
    )
    receipt_interm = TransactionReceipt(tx)
    executed_event = receipt_interm.events[Datatoken.EVENT_ORDER_EXECUTED]
    assert executed_event["orderTxId"] == receipt.txid
    assert executed_event["providerAddress"] == provider_fee_address

    # Tests exceptions for order_executed
    consumer_signed = network.web3.eth.sign(provider_fee_address, data=message)
    with pytest.raises(Exception, match="Consumer signature check failed"):
        datatoken.order_executed(
            receipt.txid,
            provider_data=Web3.toHex(Web3.toBytes(text=provider_data)),
            provider_signature=provider_signed,
            consumer_data=Web3.toHex(Web3.toBytes(text="12345")),
            consumer_signature=consumer_signed,
            consumer=consumer_wallet.address,
            from_wallet=publisher_wallet,
        )

    message = Web3.solidityKeccak(
        ["bytes"],
        [Web3.toHex(Web3.toBytes(text="12345"))],
    )
    consumer_signed = network.web3.eth.sign(consumer_wallet.address, data=message)

    with pytest.raises(Exception, match="Provider signature check failed"):
        datatoken.order_executed(
            receipt.txid,
            provider_data=Web3.toHex(Web3.toBytes(text=provider_data)),
            provider_signature=signed,
            consumer_data=Web3.toHex(Web3.toBytes(text="12345")),
            consumer_signature=consumer_signed,
            consumer=consumer_wallet.address,
            from_wallet=publisher_wallet,
        )

    # Tests reuses order
    tx = datatoken.reuse_order(
        receipt.txid,
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
    receipt_interm = TransactionReceipt(tx)
    reused_event = receipt_interm.events[Datatoken.EVENT_ORDER_REUSED]
    assert reused_event, "Cannot find OrderReused event"
    assert reused_event["orderTxId"] == receipt.txid
    assert reused_event["caller"] == publisher_wallet.address

    provider_fee_event = receipt.events[Datatoken.EVENT_PROVIDER_FEE]
    assert provider_fee_event, "Cannot find ProviderFee event"

    # Set and get publishing market fee params
    datatoken.set_publishing_market_fee(
        publish_market_order_fee_address=publisher_wallet.address,
        publish_market_order_fee_token=get_address_of_type(config, "MockUSDC"),
        publish_market_order_fee_amount=to_wei("1.2"),
        from_wallet=publisher_wallet,
    )

    publish_fees = datatoken.get_publishing_market_fee()

    # PublishMarketFeeAddress set previously
    assert publish_fees[0] == publisher_wallet.address
    # PublishMarketFeeToken set previously
    assert publish_fees[1] == get_address_of_type(config, "MockUSDC")
    # PublishMarketFeeAmount set previously
    assert publish_fees[2] == to_wei("1.2")
    # Fee collector
    assert datatoken.get_payment_collector() == get_address_of_type(
        config, "OPFCommunityFeeCollector"
    )

    # Publisher should succeed to burn some consumer's tokens using burnFrom
    initial_total_supply = datatoken.get_total_supply()
    initial_consumer_balance = datatoken.balanceOf(consumer_wallet.address)

    # Approve publisher to burn
    datatoken.approve(publisher_wallet.address, to_wei("10"), consumer_wallet)

    allowance = datatoken.allowance(consumer_wallet.address, publisher_wallet.address)
    assert allowance == to_wei("10")
    datatoken.burn_from(consumer_wallet.address, to_wei("2"), publisher_wallet)

    assert datatoken.get_total_supply() == initial_total_supply - to_wei("2")
    assert datatoken.balanceOf(
        consumer_wallet.address
    ) == initial_consumer_balance - to_wei("2")

    # Test transterFrom too
    initial_consumer_balance = datatoken.balanceOf(consumer_wallet.address)
    datatoken.transferFrom(
        consumer_wallet.address, publisher_wallet.address, to_wei("1"), publisher_wallet
    )
    assert datatoken.balanceOf(
        consumer_wallet.address
    ) == initial_consumer_balance - to_wei("1")

    # Consumer should be able to burn his tokens too
    initial_consumer_balance = datatoken.balanceOf(consumer_wallet.address)
    datatoken.burn(to_wei("1"), consumer_wallet)
    assert datatoken.balanceOf(
        consumer_wallet.address
    ) == initial_consumer_balance - to_wei("1")

    # Consumer should be able to transfer too
    initial_consumer_balance = datatoken.balanceOf(consumer_wallet.address)
    datatoken.transfer(publisher_wallet.address, to_wei("1"), consumer_wallet)
    assert datatoken.balanceOf(
        consumer_wallet.address
    ) == initial_consumer_balance - to_wei("1")


@pytest.mark.unit
def test_exceptions(consumer_wallet, datatoken):
    """Tests revert statements in contracts functions"""

    # Should fail to mint if wallet is not a minter
    with pytest.raises(Exception, match="NOT MINTER"):
        datatoken.mint(
            consumer_wallet.address,
            to_wei("1"),
            {"from": consumer_wallet},
        )

    #  Should fail to set new FeeCollector if not NFTOwner
    with pytest.raises(Exception, match="NOT PAYMENT MANAGER or OWNER"):
        datatoken.set_payment_collector(
            publish_market_order_fee_address=consumer_wallet.address,
            from_wallet=consumer_wallet,
        )

    # Should fail to addMinter if not erc20Deployer (permission to deploy the erc20Contract at 721 level)
    with pytest.raises(Exception, match="NOT DEPLOYER ROLE"):
        datatoken.add_minter(
            minter_address=consumer_wallet.address, from_wallet=consumer_wallet
        )

    #  Should fail to removeMinter even if it's minter
    with pytest.raises(Exception, match="NOT DEPLOYER ROLE"):
        datatoken.remove_minter(
            minter_address=consumer_wallet.address, from_wallet=consumer_wallet
        )

    # Should fail to addFeeManager if not erc20Deployer (permission to deploy the erc20Contract at 721 level)
    with pytest.raises(Exception, match="NOT DEPLOYER ROLE"):
        datatoken.add_payment_manager(
            fee_manager=consumer_wallet.address, from_wallet=consumer_wallet
        )

    # Should fail to removeFeeManager if NOT erc20Deployer
    with pytest.raises(Exception, match="NOT DEPLOYER ROLE"):
        datatoken.remove_payment_manager(
            fee_manager=consumer_wallet.address, from_wallet=consumer_wallet
        )

    # Should fail to setData if NOT erc20Deployer
    with pytest.raises(Exception, match="NOT DEPLOYER ROLE"):
        datatoken.set_data(
            data=Web3.toHex(text="SomeData"), from_wallet=consumer_wallet
        )

    # Should fail to call cleanPermissions if NOT NFTOwner
    with pytest.raises(Exception, match="not NFTOwner"):
        datatoken.clean_permissions(from_wallet=consumer_wallet)

    # Clean from nft should work shouldn't be callable by publisher or consumer, only by erc721 contract
    with pytest.raises(Exception, match="NOT 721 Contract"):
        datatoken.clean_from_721(from_wallet=consumer_wallet)
