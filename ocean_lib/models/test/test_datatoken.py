#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from brownie import network
from web3.main import Web3

from ocean_lib.models.datatoken import DatatokenRoles, TokenFeeInfo
from ocean_lib.ocean.util import get_address_of_type, to_wei
from ocean_lib.web3_internal.constants import MAX_UINT256
from tests.resources.helper_functions import get_mock_provider_fees


@pytest.mark.unit
def test_main(
    publisher_wallet, consumer_wallet, another_consumer_wallet, data_NFT_and_DT
):
    """Tests successful function calls"""
    data_nft, datatoken = data_NFT_and_DT

    # Check datatoken params
    assert datatoken.getId() == 1
    assert datatoken.contract.name() == "DT1"
    assert datatoken.symbol() == "DT1Symbol"
    assert datatoken.decimals() == 18
    assert datatoken.cap() == MAX_UINT256

    # Check data NFT address
    assert datatoken.getERC721Address() == data_nft.address

    # Check that the Datatoken contract is initialized
    assert datatoken.isInitialized()

    # Check publish market payment collector
    assert datatoken.getPaymentCollector() == publisher_wallet.address

    # Set payment collector to consumer
    datatoken.setPaymentCollector(
        consumer_wallet.address,
        {"from": publisher_wallet},
    )
    assert datatoken.getPaymentCollector() == consumer_wallet.address

    # Check minter permissions
    assert datatoken.getPermissions(publisher_wallet.address)[DatatokenRoles.MINTER]
    assert datatoken.isMinter(publisher_wallet.address)

    # Mint Datatoken to user2 from publisher
    datatoken.mint(consumer_wallet.address, 1, {"from": publisher_wallet})
    assert datatoken.balanceOf(consumer_wallet.address) == 1

    # Add minter
    assert not datatoken.getPermissions(consumer_wallet.address)[DatatokenRoles.MINTER]
    datatoken.addMinter(consumer_wallet.address, {"from": publisher_wallet})
    assert datatoken.getPermissions(consumer_wallet.address)[DatatokenRoles.MINTER]

    # Mint Datatoken to user2 from consumer
    datatoken.mint(consumer_wallet.address, 1, {"from": consumer_wallet})
    assert datatoken.balanceOf(consumer_wallet.address) == 2

    # Should succeed to removeMinter if erc20Deployer
    datatoken.removeMinter(consumer_wallet.address, {"from": publisher_wallet})
    assert not datatoken.getPermissions(consumer_wallet.address)[DatatokenRoles.MINTER]

    # Should succeed to addFeeManager if erc20Deployer (permission to deploy the erc20Contract at 721 level)
    assert not datatoken.getPermissions(consumer_wallet.address)[
        DatatokenRoles.PAYMENT_MANAGER
    ]
    datatoken.addPaymentManager(consumer_wallet.address, {"from": publisher_wallet})
    assert datatoken.getPermissions(consumer_wallet.address)[
        DatatokenRoles.PAYMENT_MANAGER
    ]

    # Should succeed to removeFeeManager if erc20Deployer
    datatoken.removePaymentManager(consumer_wallet.address, {"from": publisher_wallet})
    assert not datatoken.getPermissions(consumer_wallet.address)[
        DatatokenRoles.PAYMENT_MANAGER
    ]

    # Should succeed to setData if erc20Deployer
    value = Web3.toHex(text="SomeData")
    key = Web3.keccak(hexstr=datatoken.address)

    datatoken.setData(value, {"from": publisher_wallet})

    assert Web3.toHex(data_nft.getData(key)) == value

    # Should succeed to call cleanPermissions if NFTOwner
    datatoken.cleanPermissions({"from": publisher_wallet})

    permissions = datatoken.getPermissions(publisher_wallet.address)
    assert not permissions[DatatokenRoles.MINTER]
    assert not permissions[DatatokenRoles.PAYMENT_MANAGER]

    with pytest.raises(Exception, match="NOT ERC20DEPLOYER_ROLE"):
        data_nft.create_datatoken(
            {"from": another_consumer_wallet},
            name="DT1",
            symbol="DT1Symbol",
        )


def test_start_order(config, publisher_wallet, consumer_wallet, data_NFT_and_DT):
    """Tests startOrder functionality without publish fees, consume fees."""
    data_nft, datatoken = data_NFT_and_DT
    # Mint datatokens to use
    datatoken.mint(consumer_wallet.address, to_wei(10), {"from": publisher_wallet})
    datatoken.mint(publisher_wallet.address, to_wei(10), {"from": publisher_wallet})

    # Set the fee collector address
    datatoken.setPaymentCollector(
        get_address_of_type(config, "OPFCommunityFeeCollector"),
        {"from": publisher_wallet},
    )

    provider_fees = get_mock_provider_fees("MockUSDC", publisher_wallet)

    receipt = datatoken.start_order(
        consumer=consumer_wallet.address,
        service_index=1,
        provider_fees=provider_fees,
        consume_market_fees=TokenFeeInfo(
            address=publisher_wallet.address,
            token=datatoken.address,
        ),
        tx_dict={"from": publisher_wallet},
    )
    # Check erc20 balances
    assert datatoken.balanceOf(publisher_wallet.address) == to_wei(9)
    assert datatoken.balanceOf(
        get_address_of_type(config, "OPFCommunityFeeCollector")
    ) == to_wei(1)

    provider_fee_address = publisher_wallet.address
    provider_data = provider_fees["providerData"]
    provider_message = Web3.solidityKeccak(
        ["bytes32", "bytes"],
        [receipt.txid, provider_data],
    )
    provider_signed = network.web3.eth.sign(provider_fee_address, data=provider_message)

    message = Web3.solidityKeccak(
        ["bytes"],
        [Web3.toHex(Web3.toBytes(text="12345"))],
    )
    consumer_signed = network.web3.eth.sign(consumer_wallet.address, data=message)

    receipt_interm = datatoken.orderExecuted(
        receipt.txid,
        provider_data,
        provider_signed,
        Web3.toHex(Web3.toBytes(text="12345")),
        consumer_signed,
        consumer_wallet.address,
        {"from": publisher_wallet},
    )
    executed_event = receipt_interm.events["OrderExecuted"]
    assert executed_event["orderTxId"] == receipt.txid
    assert executed_event["providerAddress"] == provider_fee_address

    # Tests exceptions for order_executed
    consumer_signed = network.web3.eth.sign(provider_fee_address, data=message)
    with pytest.raises(Exception, match="Consumer signature check failed"):
        datatoken.orderExecuted(
            receipt.txid,
            provider_data,
            provider_signed,
            Web3.toHex(Web3.toBytes(text="12345")),
            consumer_signed,
            consumer_wallet.address,
            {"from": publisher_wallet},
        )

    message = Web3.solidityKeccak(
        ["bytes"],
        [Web3.toHex(Web3.toBytes(text="12345"))],
    )
    consumer_signed = network.web3.eth.sign(consumer_wallet.address, data=message)

    with pytest.raises(Exception, match="Provider signature check failed"):
        datatoken.orderExecuted(
            receipt.txid,
            provider_data,
            consumer_signed,
            Web3.toHex(Web3.toBytes(text="12345")),
            consumer_signed,
            consumer_wallet.address,
            {"from": publisher_wallet},
        )

    # Tests reuses order
    receipt_interm = datatoken.reuse_order(
        receipt.txid,
        provider_fees=provider_fees,
        tx_dict={"from": publisher_wallet},
    )
    reused_event = receipt_interm.events["OrderReused"]
    assert reused_event, "Cannot find OrderReused event"
    assert reused_event["orderTxId"] == receipt.txid
    assert reused_event["caller"] == publisher_wallet.address

    provider_fee_event = receipt.events["ProviderFee"]
    assert provider_fee_event, "Cannot find ProviderFee event"

    # Set and get publishing market fee params
    datatoken.setPublishingMarketFee(
        publisher_wallet.address,
        get_address_of_type(config, "MockUSDC"),
        to_wei(1.2),
        {"from": publisher_wallet},
    )

    publish_fees = datatoken.get_publish_market_order_fees()

    # PublishMarketFeeAddress set previously
    assert publish_fees.address == publisher_wallet.address
    # PublishMarketFeeToken set previously
    assert publish_fees.token == get_address_of_type(config, "MockUSDC")
    # PublishMarketFeeAmount set previously
    assert publish_fees.amount == to_wei(1.2)
    # Fee collector
    assert datatoken.getPaymentCollector() == get_address_of_type(
        config, "OPFCommunityFeeCollector"
    )

    # Publisher should succeed to burn some consumer's tokens using burnFrom
    initial_total_supply = datatoken.totalSupply()
    initial_consumer_balance = datatoken.balanceOf(consumer_wallet.address)

    # Approve publisher to burn
    datatoken.approve(publisher_wallet.address, to_wei(10), {"from": consumer_wallet})

    allowance = datatoken.allowance(consumer_wallet.address, publisher_wallet.address)
    assert allowance == to_wei(10)
    datatoken.burnFrom(consumer_wallet.address, to_wei(2), {"from": publisher_wallet})

    assert datatoken.totalSupply() == initial_total_supply - to_wei(2)
    assert datatoken.balanceOf(
        consumer_wallet.address
    ) == initial_consumer_balance - to_wei(2)

    # Test transterFrom too
    initial_consumer_balance = datatoken.balanceOf(consumer_wallet.address)
    datatoken.transferFrom(
        consumer_wallet.address,
        publisher_wallet.address,
        to_wei(1),
        {"from": publisher_wallet},
    )
    assert datatoken.balanceOf(
        consumer_wallet.address
    ) == initial_consumer_balance - to_wei(1)

    # Consumer should be able to burn his tokens too
    initial_consumer_balance = datatoken.balanceOf(consumer_wallet.address)
    datatoken.burn(to_wei(1), {"from": consumer_wallet})
    assert datatoken.balanceOf(
        consumer_wallet.address
    ) == initial_consumer_balance - to_wei(1)

    # Consumer should be able to transfer too
    initial_consumer_balance = datatoken.balanceOf(consumer_wallet.address)
    datatoken.transfer(publisher_wallet.address, to_wei(1), {"from": consumer_wallet})
    assert datatoken.balanceOf(
        consumer_wallet.address
    ) == initial_consumer_balance - to_wei(1)


@pytest.mark.unit
def test_exceptions(consumer_wallet, config, publisher_wallet, DT):
    """Tests revert statements in contracts functions"""
    datatoken = DT

    # Should fail to mint if wallet is not a minter
    with pytest.raises(Exception, match="NOT MINTER"):
        datatoken.mint(
            consumer_wallet.address,
            to_wei(1),
            {"from": consumer_wallet},
        )

    #  Should fail to set new FeeCollector if not NFTOwner
    with pytest.raises(Exception, match="NOT PAYMENT MANAGER or OWNER"):
        datatoken.setPaymentCollector(
            consumer_wallet.address,
            {"from": consumer_wallet},
        )

    # Should fail to addMinter if not erc20Deployer (permission to deploy the erc20Contract at 721 level)
    with pytest.raises(Exception, match="NOT DEPLOYER ROLE"):
        datatoken.addMinter(consumer_wallet.address, {"from": consumer_wallet})

    #  Should fail to removeMinter even if it's minter
    with pytest.raises(Exception, match="NOT DEPLOYER ROLE"):
        datatoken.removeMinter(consumer_wallet.address, {"from": consumer_wallet})

    # Should fail to addFeeManager if not erc20Deployer (permission to deploy the erc20Contract at 721 level)
    with pytest.raises(Exception, match="NOT DEPLOYER ROLE"):
        datatoken.addPaymentManager(consumer_wallet.address, {"from": consumer_wallet})

    # Should fail to removeFeeManager if NOT erc20Deployer
    with pytest.raises(Exception, match="NOT DEPLOYER ROLE"):
        datatoken.removePaymentManager(
            consumer_wallet.address, {"from": consumer_wallet}
        )

    # Should fail to setData if NOT erc20Deployer
    with pytest.raises(Exception, match="NOT DEPLOYER ROLE"):
        datatoken.setData(Web3.toHex(text="SomeData"), {"from": consumer_wallet})

    # Should fail to call cleanPermissions if NOT NFTOwner
    with pytest.raises(Exception, match="not NFTOwner"):
        datatoken.cleanPermissions({"from": consumer_wallet})

    # Clean from nft should work shouldn't be callable by publisher or consumer, only by erc721 contract
    with pytest.raises(Exception, match="NOT 721 Contract"):
        datatoken.cleanFrom721({"from": consumer_wallet})
