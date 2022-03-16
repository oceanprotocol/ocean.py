#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from web3 import exceptions
from web3.main import Web3

from ocean_lib.models.dispenser import Dispenser
from ocean_lib.models.erc20_token import ERC20Token
from ocean_lib.models.erc721_factory import ERC721FactoryContract
from ocean_lib.models.erc721_nft import ERC721NFT
from ocean_lib.structures.abi_tuples import (
    OrderData,
)
from ocean_lib.utils.utilities import create_checksum
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.currency import to_wei
from ocean_lib.web3_internal.utils import split_signature
from tests.resources.helper_functions import get_address_of_type


@pytest.mark.unit
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
    assert (
        erc721_factory.event_Transfer.abi["name"]
        == ERC721FactoryContract.EVENT_TRANSFER
    )


@pytest.mark.unit
def test_main(web3, config, publisher_wallet, consumer_wallet, another_consumer_wallet):
    """Tests the utils functions."""
    erc721_factory_address = get_address_of_type(
        config, ERC721FactoryContract.CONTRACT_NAME
    )
    erc721_factory = ERC721FactoryContract(web3, erc721_factory_address)

    tx = erc721_factory.deploy_erc721_contract(
        name="DT1",
        symbol="DTSYMBOL",
        template_index=1,
        additional_metadata_updater=ZERO_ADDRESS,
        additional_erc20_deployer=ZERO_ADDRESS,
        token_uri="https://oceanprotocol.com/nft/",
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
        datatoken_name="ERC20DT1",
        datatoken_symbol="ERC20DT1Symbol",
        datatoken_minter=publisher_wallet.address,
        datatoken_fee_manager=consumer_wallet.address,
        datatoken_publishing_market_address=publisher_wallet.address,
        fee_token_address=ZERO_ADDRESS,
        datatoken_cap=to_wei("0.5"),
        publishing_market_fee_amount=0,
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

    erc20_token = ERC20Token(web3, erc20_address)
    erc20_token.add_minter(consumer_wallet.address, publisher_wallet)

    # Tests creating NFT with ERC20 successfully
    tx = erc721_factory.create_nft_with_erc20(
        nft_name="72120Bundle",
        nft_symbol="72Bundle",
        nft_template=1,
        token_uri="https://oceanprotocol.com/nft/",
        datatoken_template=1,
        datatoken_name="ERC20B1",
        datatoken_symbol="ERC20DT1Symbol",
        datatoken_minter=publisher_wallet.address,
        datatoken_fee_manager=consumer_wallet.address,
        datatoken_publishing_market_address=publisher_wallet.address,
        fee_token_address=ZERO_ADDRESS,
        datatoken_cap=to_wei(10),
        publishing_market_fee_amount=0,
        bytess=[b""],
        from_wallet=publisher_wallet,
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
    erc721_token2 = ERC721NFT(web3, erc721_address2)
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
    initial_pool_liquidity = to_wei("0.02")

    erc20_token.mint(publisher_wallet.address, initial_pool_liquidity, publisher_wallet)
    erc20_token.approve(
        erc721_factory_address, initial_pool_liquidity, publisher_wallet
    )
    tx = erc721_factory.create_nft_erc20_with_pool(
        nft_name="72120Bundle",
        nft_symbol="72Bundle",
        nft_template=1,
        token_uri="https://oceanprotocol.com/nft/",
        datatoken_template=1,
        datatoken_name="ERC20WithPool",
        datatoken_symbol="ERC20P",
        datatoken_minter=publisher_wallet.address,
        datatoken_fee_manager=consumer_wallet.address,
        datatoken_publishing_market_address=publisher_wallet.address,
        fee_token_address=ZERO_ADDRESS,
        datatoken_cap=to_wei("0.05"),
        publishing_market_fee_amount=0,
        bytess=[b""],
        pool_ss_params=[
            to_wei("1"),
            erc20_token.decimals(),
            initial_pool_liquidity
            // 100
            * 9,  # max 10% vesting amount of the total cap
            2500000,
            initial_pool_liquidity,
        ],
        swap_fees=[to_wei("0.001"), to_wei("0.001")],
        pool_addresses=[
            side_staking_address,
            erc20_address,
            erc721_factory_address,
            publisher_wallet.address,
            consumer_wallet.address,
            pool_template_address,
        ],
        from_wallet=publisher_wallet,
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
    erc721_token3 = ERC721NFT(web3, erc721_token3)
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

    tx = erc721_nft.create_erc20(
        template_index=1,
        datatoken_name="ERC20DT1P",
        datatoken_symbol="ERC20DT1SymbolP",
        datatoken_minter=publisher_wallet.address,
        datatoken_fee_manager=consumer_wallet.address,
        datatoken_publishing_market_address=publisher_wallet.address,
        fee_token_address=ZERO_ADDRESS,
        datatoken_cap=to_wei("0.5"),
        publishing_market_fee_amount=to_wei("0.0005"),
        bytess=[b""],
        from_wallet=publisher_wallet,
    )
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

    tx = erc721_factory.create_nft_erc20_with_fixed_rate(
        nft_name="72120Bundle",
        nft_symbol="72Bundle",
        nft_template=1,
        token_uri="https://oceanprotocol.com/nft/",
        datatoken_template=1,
        datatoken_name="ERC20WithPool",
        datatoken_symbol="ERC20P",
        datatoken_minter=publisher_wallet.address,
        datatoken_fee_manager=consumer_wallet.address,
        datatoken_publishing_market_address=publisher_wallet.address,
        fee_token_address=ZERO_ADDRESS,
        datatoken_cap=to_wei("0.05"),
        publishing_market_fee_amount=0,
        bytess=[b""],
        fixed_price_address=fixed_rate_address,
        fixed_rate_addresses=[
            fee_erc20_address,
            publisher_wallet.address,
            consumer_wallet.address,
            ZERO_ADDRESS,
        ],
        fixed_rate_uints=[18, 18, to_wei("1"), to_wei("0.001"), 0],
        from_wallet=publisher_wallet,
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
    erc721_token4 = ERC721NFT(web3, erc721_address4)
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
    dispenser_address = get_address_of_type(config, Dispenser.CONTRACT_NAME)

    tx = erc721_factory.create_nft_erc20_with_dispenser(
        nft_name="72120Bundle",
        nft_symbol="72Bundle",
        nft_template=1,
        token_uri="https://oceanprotocol.com/nft/",
        datatoken_template=1,
        datatoken_name="ERC20WithPool",
        datatoken_symbol="ERC20P",
        datatoken_minter=publisher_wallet.address,
        datatoken_fee_manager=consumer_wallet.address,
        datatoken_publishing_market_address=publisher_wallet.address,
        fee_token_address=ZERO_ADDRESS,
        datatoken_cap=to_wei("0.05"),
        publishing_market_fee_amount=0,
        bytess=[b""],
        dispenser_address=dispenser_address,
        max_tokens=to_wei(1),
        max_balance=to_wei(1),
        with_mint=True,
        allowed_swapper=ZERO_ADDRESS,
        from_wallet=publisher_wallet,
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
    erc721_token5 = ERC721NFT(web3, erc721_address5)
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

    dispenser = Dispenser(web3, dispenser_address)

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

    # Create a new erc721 with metadata in one single call and get address
    tx = erc721_factory.create_nft_with_metadata(
        nft_name="72120Bundle",
        nft_symbol="72Bundle",
        nft_template=1,
        token_uri="https://oceanprotocol.com/nft/",
        metadata_state=1,
        metadata_decryptor_url="http://myprovider:8030",
        metadata_decryptor_address="0x123",
        flags=bytes(0),
        data=Web3.toHex(text="my cool metadata."),
        data_hash=create_checksum("my cool metadata."),
        metadata_proofs=[],
        from_wallet=publisher_wallet,
    )
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    registered_nft_event = erc721_factory.get_event_log(
        ERC721FactoryContract.EVENT_NFT_CREATED,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    assert registered_nft_event[0].event == "NFTCreated", "Cannot find NFTCreated event"
    assert (
        registered_nft_event[0].args.admin == publisher_wallet.address
    ), "Invalid NFT owner!"
    erc721_nft_address = registered_nft_event[0].args.newTokenAddress
    erc721_nft = ERC721NFT(web3, erc721_nft_address)
    assert (
        erc721_nft.token_name() == "72120Bundle"
    ), "NFT name doesn't match with the expected one."
    metadata_info = erc721_nft.get_metadata()
    assert metadata_info[3] is True
    assert metadata_info[0] == "http://myprovider:8030"


@pytest.mark.unit
def test_start_multiple_order(
    web3, config, publisher_wallet, consumer_wallet, another_consumer_wallet
):
    """Tests the utils functions."""
    erc721_factory_address = get_address_of_type(
        config, ERC721FactoryContract.CONTRACT_NAME
    )
    erc721_factory = ERC721FactoryContract(web3, erc721_factory_address)

    tx = erc721_factory.deploy_erc721_contract(
        name="DT1",
        symbol="DTSYMBOL",
        template_index=1,
        additional_metadata_updater=ZERO_ADDRESS,
        additional_erc20_deployer=ZERO_ADDRESS,
        token_uri="https://oceanprotocol.com/nft/",
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
        datatoken_name="ERC20DT1",
        datatoken_symbol="ERC20DT1Symbol",
        datatoken_minter=publisher_wallet.address,
        datatoken_fee_manager=consumer_wallet.address,
        datatoken_publishing_market_address=publisher_wallet.address,
        fee_token_address=ZERO_ADDRESS,
        datatoken_cap=to_wei(2),
        publishing_market_fee_amount=0,
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
    dt_amount = to_wei("2")
    mock_dai_contract_address = get_address_of_type(config, "MockDAI")
    assert erc20_token.balanceOf(consumer_wallet.address) == 0

    erc20_token.add_minter(consumer_wallet.address, publisher_wallet)
    erc20_token.mint(consumer_wallet.address, dt_amount, consumer_wallet)
    assert erc20_token.balanceOf(consumer_wallet.address) == dt_amount

    erc20_token.approve(erc721_factory_address, dt_amount, consumer_wallet)

    erc20_token.set_payment_collector(another_consumer_wallet.address, publisher_wallet)

    provider_fee_token = mock_dai_contract_address
    provider_fee_amount = 0
    provider_fee_address = publisher_wallet.address
    # provider_data = json.dumps({"timeout": 0}, separators=(",", ":"))
    provider_data = b"\x00"

    message = Web3.solidityKeccak(
        ["bytes", "address", "address", "uint256", "uint256"],
        [
            provider_data,
            provider_fee_address,
            provider_fee_token,
            provider_fee_amount,
            0,
        ],
    )
    signed = web3.eth.sign(provider_fee_address, data=message)
    signature = split_signature(signed)

    order_data = OrderData(
        erc20_address,
        consumer_wallet.address,
        1,
        (
            provider_fee_address,
            provider_fee_token,
            provider_fee_amount,
            signature.v,
            signature.r,
            signature.s,
            0,
            provider_data,
        ),
        (
            consumer_wallet.address,
            mock_dai_contract_address,
            0,
        ),
    )

    orders = [order_data, order_data]

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
    assert erc20_token.balanceOf(erc20_token.get_payment_collector()) == (
        dt_amount * 0.97
    )


@pytest.mark.unit
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


@pytest.mark.unit
def test_fail_create_erc20(
    web3, config, publisher_wallet, consumer_wallet, another_consumer_wallet
):
    """Tests multiple failures for creating ERC20 token."""

    erc721_factory_address = get_address_of_type(
        config, ERC721FactoryContract.CONTRACT_NAME
    )
    erc721_factory = ERC721FactoryContract(web3, erc721_factory_address)

    tx = erc721_factory.deploy_erc721_contract(
        name="DT1",
        symbol="DTSYMBOL",
        template_index=1,
        additional_metadata_updater=ZERO_ADDRESS,
        additional_erc20_deployer=ZERO_ADDRESS,
        token_uri="https://oceanprotocol.com/nft/",
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
    erc721_nft.add_to_create_erc20_list(consumer_wallet.address, publisher_wallet)

    # Should fail to create a specific ERC20 Template if the index is ZERO
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_nft.create_erc20(
            template_index=0,
            datatoken_name="ERC20DT1",
            datatoken_symbol="ERC20DT1Symbol",
            datatoken_minter=publisher_wallet.address,
            datatoken_fee_manager=consumer_wallet.address,
            datatoken_publishing_market_address=publisher_wallet.address,
            fee_token_address=ZERO_ADDRESS,
            datatoken_cap=to_wei("0.5"),
            publishing_market_fee_amount=0,
            bytess=[b""],
            from_wallet=consumer_wallet,
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC20Factory: Template index "
        "doesnt exist"
    )

    # Should fail to create a specific ERC20 Template if the index doesn't exist
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_nft.create_erc20(
            template_index=3,
            datatoken_name="ERC20DT1",
            datatoken_symbol="ERC20DT1Symbol",
            datatoken_minter=publisher_wallet.address,
            datatoken_fee_manager=consumer_wallet.address,
            datatoken_publishing_market_address=publisher_wallet.address,
            fee_token_address=ZERO_ADDRESS,
            datatoken_cap=to_wei("0.5"),
            publishing_market_fee_amount=0,
            bytess=[b""],
            from_wallet=consumer_wallet,
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC20Factory: Template index "
        "doesnt exist"
    )

    # Should fail to create a specific ERC20 Template if the user is not added on the ERC20 deployers list
    assert erc721_nft.get_permissions(another_consumer_wallet.address)[1] is False
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_nft.create_erc20(
            template_index=1,
            datatoken_name="ERC20DT1",
            datatoken_symbol="ERC20DT1Symbol",
            datatoken_minter=publisher_wallet.address,
            datatoken_fee_manager=consumer_wallet.address,
            datatoken_publishing_market_address=publisher_wallet.address,
            fee_token_address=ZERO_ADDRESS,
            datatoken_cap=to_wei("0.5"),
            publishing_market_fee_amount=0,
            bytess=[b""],
            from_wallet=another_consumer_wallet,
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721Template: NOT "
        "ERC20DEPLOYER_ROLE"
    )
