#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from web3 import exceptions

from ocean_lib.models.v4.erc20_token import ERC20Token, RolesERC20
from ocean_lib.models.v4.erc721_factory import ERC721FactoryContract
from ocean_lib.models.v4.erc721_token import ERC721Token
from ocean_lib.models.v4.models_structures import ErcCreateData
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from tests.resources.helper_functions import get_address_of_type, deploy_erc721_erc20


def test_properties(web3, config, publisher_wallet):
    """Tests the events' properties."""
    erc721_factory_address = get_address_of_type(
        config, ERC721FactoryContract.CONTRACT_NAME
    )
    _, erc20 = deploy_erc721_erc20(
        web3=web3,
        config=config,
        erc721_publisher=publisher_wallet,
        erc20_minter=publisher_wallet,
        cap=web3.toWei("1", "ether"),
    )

    assert erc20.event_NewPool.abi["name"] == ERC20Token.EVENT_NEW_POOL
    assert erc20.event_NewFixedRate.abi["name"] == ERC20Token.EVENT_NEW_FIXED_RATE
    assert erc20.event_MinterProposed.abi["name"] == ERC20Token.EVENT_MINTER_PROPOSED
    assert erc20.event_OrderStarted.abi["name"] == ERC20Token.EVENT_ORDER_STARTED
    assert erc20.event_MinterApproved.abi["name"] == ERC20Token.EVENT_MINTER_APPROVED


def test_main(web3, config, publisher_wallet, consumer_wallet, factory_router):
    """Tests the utils functions."""
    erc721_factory_address = get_address_of_type(
        config, ERC721FactoryContract.CONTRACT_NAME
    )
    erc721_factory = ERC721FactoryContract(web3, erc721_factory_address)

    publishMarketFeeAmount = 5

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

    # Tests templateCount function (one of them should be the Enterprise template)
    assert erc721_factory.template_count() == 2

    # Tests ERC20 token template list
    erc20_template_address = get_address_of_type(config, ERC20Token.CONTRACT_NAME, "1")
    template = erc721_factory.get_token_template(1)
    assert template[0] == erc20_template_address
    assert template[1] is True

    # Create an ERC20 with publish Fees ( 5 USDC, going to publishMarketAddress)
    erc721, erc20 = deploy_erc721_erc20(
        web3=web3,
        config=config,
        erc721_publisher=publisher_wallet,
        erc20_minter=publisher_wallet,
        cap=web3.toWei(publishMarketFeeAmount, "ether"),
    )

    # Check erc20 params
    assert erc20.get_id() == 1
    assert erc20.contract.caller.name() == "ERC20DT1"
    assert erc20.symbol() == "ERC20DT1Symbol"
    assert erc20.decimals() == 18
    assert erc20.cap() == web3.toWei(publishMarketFeeAmount, "ether")

    # Check minter permissions
    assert erc20.permissions(publisher_wallet.address)[RolesERC20.MINTER]
    assert erc20.is_minter(publisher_wallet.address)

    # Check that the erc20Token contract is initialized
    assert erc20.is_initialized()

    # Should fail to re-initialize the contracts
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc20.initialize(
            strings=["ERC20DT1", "ERC20DT1Symbol"],
            addresses=[
                publisher_wallet.address,
                consumer_wallet.address,
                publisher_wallet.address,
                ZERO_ADDRESS,
            ],
            factory_addresses=[
                erc721.address,
                get_address_of_type(config, "OPFCommunityFeeCollector"),
                factory_router.address,
            ],
            uints=[web3.toWei("10", "ether"), 0],
            bytess=[b""],
            from_wallet=publisher_wallet,
        ),

    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC20Template: "
        "token instance already initialized"
    )

    # Should succeed to mint 1 ERC20Token to user2
    erc20.mint(consumer_wallet.address, 1, publisher_wallet)
    assert erc20.balanceOf(consumer_wallet.address) == 1

    # Should fail to mint if wallet is not a minter
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc20.mint(
            account_address=consumer_wallet.address,
            value=web3.toWei(1, "ether"),
            from_wallet=consumer_wallet,
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC20Template: NOT MINTER"
    )

    #  Should fail to set new FeeCollector if not NFTOwner
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc20.set_fee_collector(
            fee_collector_address=consumer_wallet.address,
            from_wallet=consumer_wallet,
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC20Template: NOT FEE MANAGER"
    )

    # Should succeed to set new FeeCollector if feeManager
    erc20.set_fee_collector(
        fee_collector_address=publisher_wallet.address,
        from_wallet=publisher_wallet,
    )

    # Should fail to addMinter if not erc20Deployer (permission to deploy the erc20Contract at 721 level)
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc20.add_minter(
            minter_address=consumer_wallet.address, from_wallet=consumer_wallet
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC20Template: NOT DEPLOYER ROLE"
    )

    #  Should fail to removeMinter even if it's minter
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc20.remove_minter(
            minter_address=consumer_wallet.address, from_wallet=consumer_wallet
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC20Template: NOT DEPLOYER ROLE"
    )

    # Should succeed to removeMinter if erc20Deployer
    erc20.remove_minter(
        minter_address=consumer_wallet.address, from_wallet=publisher_wallet
    )

    # Should fail to addFeeManager if not erc20Deployer (permission to deploy the erc20Contract at 721 level)
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc20.add_fee_manager(
            fee_manager=consumer_wallet.address, from_wallet=consumer_wallet
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC20Template: NOT DEPLOYER ROLE"
    )

    # Should succeed to addFeeManager if erc20Deployer (permission to deploy the erc20Contract at 721 level)
    erc20.add_fee_manager(
        fee_manager=consumer_wallet.address, from_wallet=publisher_wallet
    )

    # Should fail to removeFeeManager if NOT erc20Deployer
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc20.remove_fee_manager(
            fee_manager=consumer_wallet.address, from_wallet=consumer_wallet
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC20Template: NOT DEPLOYER ROLE"
    )

    # Should succeed to removeFeeManager if erc20Deployer
    erc20.remove_fee_manager(
        fee_manager=consumer_wallet.address, from_wallet=publisher_wallet
    )

    # Should fail to setData if NOT erc20Deployer
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc20.set_data(
            data=web3.toHex(text="SomeData"),
            from_wallet=consumer_wallet,
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC20Template: NOT DEPLOYER ROLE"
    )

    # Should succeed to setData if erc20Deployer
    value = web3.toHex(text="SomeData")
    key = web3.keccak(hexstr=erc20.address)

    erc20.set_data(
        data=value,
        from_wallet=publisher_wallet,
    )

    assert web3.toHex(erc721.get_data(key)) == value

    # Should fail to call cleanPermissions if NOT NFTOwner
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc20.clean_permissions(
            from_wallet=consumer_wallet,
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC20Template: not NFTOwner"
    )

    # Should succeed to call cleanPermissions if NFTOwner
    erc20.clean_permissions(
        from_wallet=publisher_wallet,
    )

    permissions = erc20.permissions(publisher_wallet.address)
    assert not permissions[RolesERC20.MINTER]
    assert not permissions[RolesERC20.FEE_MANAGER]

    # User should succeed to call startOrder on a ERC20 without publishFees, consumeFeeAmount on top is ZERO
    # Get new tokens
    erc721, erc20 = deploy_erc721_erc20(
        web3=web3,
        config=config,
        erc721_publisher=publisher_wallet,
        erc20_minter=publisher_wallet,
        cap=web3.toWei("200", "ether"),
    )
    # Mint erc20 tokens to use
    erc20.mint(consumer_wallet.address, web3.toWei(10, "ether"), publisher_wallet)

    # Set the fee collector address
    erc20.set_fee_collector(
        get_address_of_type(config, "OPFCommunityFeeCollector"), publisher_wallet
    )

    erc20.start_order(
        consumer=consumer_wallet.address,
        amount=web3.toWei(1, "ether"),
        service_id=1,
        mrkt_fee_collector=publisher_wallet.address,
        fee_token=get_address_of_type(config, "MockUSDC"),
        fee_amount=0,
        from_wallet=consumer_wallet,
    )

    # Check erc20 balances
    assert erc20.balanceOf(consumer_wallet.address) == web3.toWei(9, "ether")
    assert erc20.balanceOf(
        get_address_of_type(config, "OPFCommunityFeeCollector")
    ) == web3.toWei(1, "ether")

    # Set and get publishing market fee params
    erc20.set_publishing_market_fee(
        publish_market_fee_token=get_address_of_type(config, "MockUSDC"),
        publish_market_fee_address=publisher_wallet.address,
        publish_market_fee_amount=web3.toWei("1.2", "ether"),
        from_wallet=publisher_wallet,
    )

    publish_fees = erc20.get_publishing_market_fee()

    # PublishMarketFeeAddress set previously
    assert publish_fees[0] == publisher_wallet.address
    # PublishMarketFeeToken set previously
    assert publish_fees[1] == get_address_of_type(config, "MockUSDC")
    # PublishMarketFeeAmount set previously
    assert publish_fees[2] == web3.toWei("1.2", "ether")
    # Fee collector
    assert erc20.get_fee_collector() == get_address_of_type(
        config, "OPFCommunityFeeCollector"
    )

    # Publisher should succeed to burn some consumer's tokens using burnFrom
    initial_total_supply = erc20.get_total_supply()
    initial_consumer_balance = erc20.balanceOf(consumer_wallet.address)

    # Approve publisher to burn
    erc20.approve(publisher_wallet.address, web3.toWei("10", "ether"), consumer_wallet)

    assert erc20.allowance(
        consumer_wallet.address, publisher_wallet.address
    ) == web3.toWei("10", "ether")
    erc20.burn_from(consumer_wallet.address, web3.toWei("2", "ether"), publisher_wallet)

    assert erc20.get_total_supply() == initial_total_supply - web3.toWei("2", "ether")
    assert erc20.balanceOf(
        consumer_wallet.address
    ) == initial_consumer_balance - web3.toWei("2", "ether")

    # Test transterFrom too
    initial_consumer_balance = erc20.balanceOf(consumer_wallet.address)
    erc20.transferFrom(
        consumer_wallet.address,
        publisher_wallet.address,
        web3.toWei("1", "ether"),
        publisher_wallet,
    )
    assert erc20.balanceOf(
        consumer_wallet.address
    ) == initial_consumer_balance - web3.toWei("1", "ether")

    # Consumer should be able to burn his tokens too
    initial_consumer_balance = erc20.balanceOf(consumer_wallet.address)
    erc20.burn(web3.toWei("1", "ether"), consumer_wallet)
    assert erc20.balanceOf(
        consumer_wallet.address
    ) == initial_consumer_balance - web3.toWei("1", "ether")

    # Consumer should be able to transfer too
    initial_consumer_balance = erc20.balanceOf(consumer_wallet.address)
    erc20.transfer(publisher_wallet.address, web3.toWei("1", "ether"), consumer_wallet)
    assert erc20.balanceOf(
        consumer_wallet.address
    ) == initial_consumer_balance - web3.toWei("1", "ether")
