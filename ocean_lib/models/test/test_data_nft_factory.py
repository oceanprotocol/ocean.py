#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from brownie import network
from web3.main import Web3

from ocean_lib.models.arguments import DataNFTArguments
from ocean_lib.models.data_nft import DataNFT
from ocean_lib.models.datatoken import Datatoken
from ocean_lib.models.dispenser import Dispenser
from ocean_lib.ocean.util import create_checksum, get_address_of_type
from ocean_lib.structures.abi_tuples import OrderData
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.utils import split_signature


@pytest.mark.unit
def test_main(
    config,
    publisher_wallet,
    consumer_wallet,
    data_nft_factory,
):
    """Tests the utils functions."""
    data_nft = data_nft_factory.create_data_nft(
        DataNFTArguments("DT1", "DTSYMBOL"), publisher_wallet
    )
    assert data_nft.contract.name() == "DT1"
    assert data_nft.symbol() == "DTSYMBOL"

    # Tests current NFT count
    current_nft_count = data_nft_factory.getCurrentNFTCount()
    data_nft = data_nft_factory.create_data_nft(
        DataNFTArguments("DT2", "DTSYMBOL1"), publisher_wallet
    )
    assert data_nft_factory.getCurrentNFTCount() == current_nft_count + 1

    # Tests get NFT template
    nft_template_address = get_address_of_type(config, DataNFT.CONTRACT_NAME, "1")
    nft_template = data_nft_factory.getNFTTemplate(1)
    assert nft_template[0] == nft_template_address
    assert nft_template[1] is True

    # Tests creating successfully an ERC20 token
    data_nft.addToCreateERC20List(consumer_wallet.address, {"from": publisher_wallet})
    receipt = data_nft.create_datatoken(
        template_index=1,
        name="DT1",
        symbol="DT1Symbol",
        minter=publisher_wallet.address,
        fee_manager=consumer_wallet.address,
        publish_market_order_fee_address=publisher_wallet.address,
        publish_market_order_fee_token=ZERO_ADDRESS,
        publish_market_order_fee_amount=0,
        bytess=[b""],
        transaction_parameters={"from": consumer_wallet},
        wrap_as_object=False,
    )
    assert receipt, "Failed to create ERC20 token."
    registered_token_event = receipt.events["TokenCreated"]
    assert registered_token_event, "Cannot find TokenCreated event."
    datatoken_address = registered_token_event["newTokenAddress"]

    # Tests templateCount function (one of them should be the Enterprise template)
    assert data_nft_factory.templateCount() == 2

    # Tests datatoken template list
    datatoken_template_address = get_address_of_type(
        config, Datatoken.CONTRACT_NAME, "1"
    )
    template = data_nft_factory.getTokenTemplate(1)
    assert template[0] == datatoken_template_address
    assert template[1] is True

    # Tests current token template (one of them should be the Enterprise template)
    assert data_nft_factory.getCurrentTemplateCount() == 2

    datatoken = Datatoken(config, datatoken_address)
    datatoken.addMinter(consumer_wallet.address, {"from": publisher_wallet})

    # Tests creating NFT with ERC20 successfully
    receipt = data_nft_factory.create_nft_with_erc20(
        DataNFTArguments("72120Bundle", "72Bundle"),
        datatoken_template=1,
        datatoken_name="DTB1",
        datatoken_symbol="DT1Symbol",
        datatoken_minter=publisher_wallet.address,
        datatoken_fee_manager=consumer_wallet.address,
        datatoken_publish_market_order_fee_address=publisher_wallet.address,
        datatoken_publish_market_order_fee_token=ZERO_ADDRESS,
        datatoken_publish_market_order_fee_amount=0,
        datatoken_bytess=[b""],
        wallet=publisher_wallet,
    )
    registered_nft_event = receipt.events["NFTCreated"]

    # Verify if the NFT was created.
    assert registered_nft_event, "Cannot find NFTCreated event."
    assert registered_nft_event["admin"] == publisher_wallet.address
    data_nft_address2 = registered_nft_event["newTokenAddress"]
    data_nft_token2 = DataNFT(config, data_nft_address2)
    assert data_nft_token2.contract.name() == "72120Bundle"
    assert data_nft_token2.symbol() == "72Bundle"

    registered_token_event = receipt.events["TokenCreated"]

    # Verify if the ERC20 token was created.
    assert registered_token_event, "Cannot find TokenCreated event."
    datatoken_address2 = registered_token_event["newTokenAddress"]
    datatoken2 = Datatoken(config, datatoken_address2)
    assert datatoken2.contract.name() == "DTB1"
    assert datatoken2.symbol() == "DT1Symbol"

    # Tests creating NFT with ERC20 and with Fixed Rate Exchange successfully.
    fixed_rate_address = get_address_of_type(config, "FixedPrice")

    # Create ERC20 data token for fees.
    receipt = data_nft.create_datatoken(
        template_index=1,
        name="DT1P",
        symbol="DT1SymbolP",
        minter=publisher_wallet.address,
        fee_manager=consumer_wallet.address,
        publish_market_order_fee_address=publisher_wallet.address,
        publish_market_order_fee_token=ZERO_ADDRESS,
        publish_market_order_fee_amount=Web3.toWei("0.0005", "ether"),
        bytess=[b""],
        transaction_parameters={"from": publisher_wallet},
        wrap_as_object=False,
    )
    assert receipt, "Failed to create ERC20 token."
    registered_fee_token_event = receipt.events["TokenCreated"]
    assert registered_fee_token_event, "Cannot find TokenCreated event."
    fee_datatoken_address = registered_fee_token_event["newTokenAddress"]

    receipt = data_nft_factory.create_nft_erc20_with_fixed_rate(
        DataNFTArguments("72120Bundle", "72Bundle"),
        datatoken_template=1,
        datatoken_name="DTWithPool",
        datatoken_symbol="DTP",
        datatoken_minter=publisher_wallet.address,
        datatoken_fee_manager=consumer_wallet.address,
        datatoken_publish_market_order_fee_address=publisher_wallet.address,
        datatoken_publish_market_order_fee_token=ZERO_ADDRESS,
        datatoken_publish_market_order_fee_amount=0,
        datatoken_bytess=[b""],
        fixed_price_address=fixed_rate_address,
        fixed_price_base_token=fee_datatoken_address,
        fixed_price_owner=publisher_wallet.address,
        fixed_price_publish_market_swap_fee_collector=consumer_wallet.address,
        fixed_price_allowed_swapper=ZERO_ADDRESS,
        fixed_price_base_token_decimals=18,
        fixed_price_datatoken_decimals=18,
        fixed_price_rate=Web3.toWei("1", "ether"),
        fixed_price_publish_market_swap_fee_amount=Web3.toWei("0.001", "ether"),
        fixed_price_with_mint=0,
        wallet=publisher_wallet,
    )
    registered_nft_event = receipt.events["NFTCreated"]

    # Verify if the NFT was created.
    assert registered_nft_event, "Cannot find NFTCreated event."
    assert registered_nft_event["admin"] == publisher_wallet.address
    data_nft_address4 = registered_nft_event["newTokenAddress"]
    data_nft_token4 = DataNFT(config, data_nft_address4)
    assert data_nft_token4.contract.name() == "72120Bundle"
    assert data_nft_token4.symbol() == "72Bundle"

    registered_token_event = receipt.events["TokenCreated"]

    # Verify if the ERC20 token was created.
    assert registered_token_event, "Cannot find TokenCreated event."
    datatoken_address4 = registered_token_event["newTokenAddress"]
    datatoken4 = Datatoken(config, datatoken_address4)
    assert datatoken4.contract.name() == "DTWithPool"
    assert datatoken4.symbol() == "DTP"

    registered_fixed_rate_event = receipt.events["NewFixedRate"]

    # Verify if the Fixed Rate Exchange was created.
    assert registered_fixed_rate_event, "Cannot find NewFixedRate event."
    assert registered_fixed_rate_event["exchangeId"], "Invalid exchange id."

    # Tests creating NFT with ERC20 and with Dispenser successfully.
    dispenser_address = get_address_of_type(config, Dispenser.CONTRACT_NAME)

    receipt = data_nft_factory.create_nft_erc20_with_dispenser(
        DataNFTArguments("72120Bundle", "72Bundle"),
        datatoken_template=1,
        datatoken_name="DTWithPool",
        datatoken_symbol="DTP",
        datatoken_minter=publisher_wallet.address,
        datatoken_fee_manager=consumer_wallet.address,
        datatoken_publish_market_order_fee_address=publisher_wallet.address,
        datatoken_publish_market_order_fee_token=ZERO_ADDRESS,
        datatoken_publish_market_order_fee_amount=0,
        datatoken_bytess=[b""],
        dispenser_address=dispenser_address,
        dispenser_max_tokens=Web3.toWei(1, "ether"),
        dispenser_max_balance=Web3.toWei(1, "ether"),
        dispenser_with_mint=True,
        dispenser_allowed_swapper=ZERO_ADDRESS,
        wallet=publisher_wallet,
    )
    registered_nft_event = receipt.events["NFTCreated"]

    # Verify if the NFT was created.
    assert registered_nft_event, "Cannot find NFTCreated event."
    assert registered_nft_event["admin"] == publisher_wallet.address
    data_nft_address5 = registered_nft_event["newTokenAddress"]
    data_nft_token5 = DataNFT(config, data_nft_address5)
    assert data_nft_token5.contract.name() == "72120Bundle"
    assert data_nft_token5.symbol() == "72Bundle"

    registered_token_event = receipt.events["TokenCreated"]

    # Verify if the datatoken was created.
    assert registered_token_event, "Cannot find TokenCreated event."
    datatoken_address5 = registered_token_event["newTokenAddress"]
    datatoken5 = Datatoken(config, datatoken_address5)
    assert datatoken5.contract.name() == "DTWithPool"
    assert datatoken5.symbol() == "DTP"

    _ = Dispenser(config, dispenser_address)

    registered_dispenser_event = receipt.events["DispenserCreated"]

    # Verify if the Dispenser data token was created.
    assert registered_dispenser_event, "Cannot find DispenserCreated event."
    assert registered_dispenser_event[
        "datatokenAddress"
    ], "Invalid data token address by dispenser."

    # Create a new erc721 with metadata in one single call and get address
    receipt = data_nft_factory.create_nft_with_metadata(
        DataNFTArguments("72120Bundle", "72Bundle"),
        metadata_state=1,
        metadata_decryptor_url="http://myprovider:8030",
        metadata_decryptor_address=b"0x123",
        metadata_flags=bytes(0),
        metadata_data=Web3.toHex(text="my cool metadata."),
        metadata_data_hash=create_checksum("my cool metadata."),
        metadata_proofs=[],
        wallet=publisher_wallet,
    )
    registered_nft_event = receipt.events["NFTCreated"]
    assert registered_nft_event, "Cannot find NFTCreated event"
    assert (
        registered_nft_event["admin"] == publisher_wallet.address
    ), "Invalid NFT owner!"
    data_nft_address = registered_nft_event["newTokenAddress"]
    data_nft = DataNFT(config, data_nft_address)
    assert (
        data_nft.name() == "72120Bundle"
    ), "NFT name doesn't match with the expected one."
    metadata_info = data_nft.getMetaData()
    assert metadata_info[3] is True
    assert metadata_info[0] == "http://myprovider:8030"


@pytest.mark.unit
def test_start_multiple_order(
    config, publisher_wallet, consumer_wallet, another_consumer_wallet, data_nft_factory
):
    """Tests the utils functions."""
    data_nft = data_nft_factory.create_data_nft(
        DataNFTArguments("DT1", "DTSYMBOL"), publisher_wallet
    )
    assert data_nft.contract.name() == "DT1"
    assert data_nft.symbol() == "DTSYMBOL"
    assert data_nft_factory.check_nft(data_nft.address)

    # Tests current NFT count
    current_nft_count = data_nft_factory.getCurrentNFTCount()
    data_nft = data_nft_factory.create_data_nft(
        DataNFTArguments("DT2", "DTSYMBOL1"), publisher_wallet
    )
    assert data_nft_factory.getCurrentNFTCount() == current_nft_count + 1

    # Tests get NFT template
    nft_template_address = get_address_of_type(config, DataNFT.CONTRACT_NAME, "1")
    nft_template = data_nft_factory.getNFTTemplate(1)
    assert nft_template[0] == nft_template_address
    assert nft_template[1] is True

    # Tests creating successfully an ERC20 token
    data_nft.addToCreateERC20List(consumer_wallet.address, {"from": publisher_wallet})
    receipt = data_nft.create_datatoken(
        template_index=1,
        name="DT1",
        symbol="DT1Symbol",
        minter=publisher_wallet.address,
        fee_manager=consumer_wallet.address,
        publish_market_order_fee_address=publisher_wallet.address,
        publish_market_order_fee_token=ZERO_ADDRESS,
        publish_market_order_fee_amount=0,
        bytess=[b""],
        transaction_parameters={"from": consumer_wallet},
        wrap_as_object=False,
    )
    assert receipt, "Failed to create ERC20 token."
    registered_token_event = receipt.events["TokenCreated"]
    assert registered_token_event, "Cannot find TokenCreated event."
    datatoken_address = registered_token_event["newTokenAddress"]

    # Tests templateCount function (one of them should be the Enterprise template)
    assert data_nft_factory.templateCount() == 2

    # Tests datatoken template list
    datatoken_template_address = get_address_of_type(
        config, Datatoken.CONTRACT_NAME, "1"
    )
    template = data_nft_factory.getTokenTemplate(1)
    assert template[0] == datatoken_template_address
    assert template[1] is True

    # Tests current token template (one of them should be the Enterprise template)
    assert data_nft_factory.getCurrentTemplateCount() == 2

    # Tests datatoken can be checked as deployed by the factory
    assert data_nft_factory.check_datatoken(datatoken_address)

    # Tests starting multiple token orders successfully
    datatoken = Datatoken(config, datatoken_address)
    dt_amount = Web3.toWei("2", "ether")
    mock_dai_contract_address = get_address_of_type(config, "MockDAI")
    assert datatoken.balanceOf(consumer_wallet.address) == 0

    datatoken.addMinter(consumer_wallet.address, {"from": publisher_wallet})
    datatoken.mint(consumer_wallet.address, dt_amount, {"from": consumer_wallet})
    assert datatoken.balanceOf(consumer_wallet.address) == dt_amount

    datatoken.approve(data_nft_factory.address, dt_amount, {"from": consumer_wallet})

    datatoken.setPaymentCollector(
        another_consumer_wallet.address, {"from": publisher_wallet}
    )

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
    signed = network.web3.eth.sign(provider_fee_address, data=message)
    signature = split_signature(signed)

    order_data = OrderData(
        datatoken_address,
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

    receipt = data_nft_factory.start_multiple_token_order(
        orders, {"from": consumer_wallet}
    )

    registered_erc20_start_order_event = receipt.events["OrderStarted"]

    assert receipt, "Failed starting multiple token orders."
    assert registered_erc20_start_order_event["consumer"] == consumer_wallet.address

    assert datatoken.balanceOf(consumer_wallet.address) == 0
    assert datatoken.balanceOf(datatoken.getPaymentCollector()) == (dt_amount * 0.97)


@pytest.mark.unit
def test_fail_get_templates(data_nft_factory):
    """Tests multiple failures for getting tokens' templates."""
    # Should fail to get the Datatoken template if index = 0
    with pytest.raises(Exception, match="Template index doesnt exist"):
        data_nft_factory.getTokenTemplate(0)

    # Should fail to get the Datatoken template if index > templateCount
    with pytest.raises(Exception, match="Template index doesnt exist"):
        data_nft_factory.getTokenTemplate(3)


@pytest.mark.unit
def test_fail_create_datatoken(
    config, publisher_wallet, consumer_wallet, another_consumer_wallet, data_nft_factory
):
    """Tests multiple failures for creating ERC20 token."""
    data_nft = data_nft_factory.create_data_nft(
        DataNFTArguments("DT1", "DTSYMBOL"), publisher_wallet
    )
    data_nft.addToCreateERC20List(consumer_wallet.address, {"from": publisher_wallet})

    # Should fail to create a specific ERC20 Template if the index is ZERO
    with pytest.raises(Exception, match="Template index doesnt exist"):
        data_nft.create_datatoken(
            template_index=0,
            name="DT1",
            symbol="DT1Symbol",
            minter=publisher_wallet.address,
            fee_manager=consumer_wallet.address,
            publish_market_order_fee_address=publisher_wallet.address,
            publish_market_order_fee_token=ZERO_ADDRESS,
            publish_market_order_fee_amount=0,
            bytess=[b""],
            transaction_parameters={"from": consumer_wallet},
        )

    # Should fail to create a specific ERC20 Template if the index doesn't exist
    with pytest.raises(Exception, match="Template index doesnt exist"):
        data_nft.create_datatoken(
            template_index=3,
            name="DT1",
            symbol="DT1Symbol",
            minter=publisher_wallet.address,
            fee_manager=consumer_wallet.address,
            publish_market_order_fee_address=publisher_wallet.address,
            publish_market_order_fee_token=ZERO_ADDRESS,
            publish_market_order_fee_amount=0,
            bytess=[b""],
            transaction_parameters={"from": consumer_wallet},
        )

    # Should fail to create a specific ERC20 Template if the user is not added on the ERC20 deployers list
    assert data_nft.getPermissions(another_consumer_wallet.address)[1] is False
    with pytest.raises(Exception, match="NOT ERC20DEPLOYER_ROLE"):
        data_nft.create_datatoken(
            template_index=1,
            name="DT1",
            symbol="DT1Symbol",
            minter=publisher_wallet.address,
            fee_manager=consumer_wallet.address,
            publish_market_order_fee_address=publisher_wallet.address,
            publish_market_order_fee_token=ZERO_ADDRESS,
            publish_market_order_fee_amount=0,
            bytess=[b""],
            transaction_parameters={"from": another_consumer_wallet},
        )


@pytest.mark.unit
def test_datatoken_cap(publisher_wallet, consumer_wallet, data_nft_factory):
    # create NFT with ERC20
    with pytest.raises(Exception, match="Cap is needed for Datatoken Enterprise"):
        data_nft_factory.create_nft_with_erc20(
            DataNFTArguments("72120Bundle", "72Bundle", template_index=2),
            datatoken_template=2,
            datatoken_name="DTB1",
            datatoken_symbol="EntDT1Symbol",
            datatoken_minter=publisher_wallet.address,
            datatoken_fee_manager=consumer_wallet.address,
            datatoken_publish_market_order_fee_address=publisher_wallet.address,
            datatoken_publish_market_order_fee_token=ZERO_ADDRESS,
            datatoken_publish_market_order_fee_amount=0,
            datatoken_bytess=[b""],
            wallet=publisher_wallet,
        )

    with pytest.raises(Exception, match="Cap is needed for Datatoken Enterprise"):
        data_nft_factory.create_nft_erc20_with_fixed_rate(
            DataNFTArguments("72120Bundle", "72Bundle", template_index=2),
            datatoken_template=2,
            datatoken_name="DTWithFRE",
            datatoken_symbol="FTEFRE",
            datatoken_minter=publisher_wallet.address,
            datatoken_fee_manager=consumer_wallet.address,
            datatoken_publish_market_order_fee_address=publisher_wallet.address,
            datatoken_publish_market_order_fee_token=ZERO_ADDRESS,
            datatoken_publish_market_order_fee_amount=0,
            datatoken_bytess=[b""],
            fixed_price_address=ZERO_ADDRESS,
            fixed_price_base_token=ZERO_ADDRESS,
            fixed_price_owner=publisher_wallet.address,
            fixed_price_publish_market_swap_fee_collector=consumer_wallet.address,
            fixed_price_allowed_swapper=ZERO_ADDRESS,
            fixed_price_base_token_decimals=18,
            fixed_price_datatoken_decimals=18,
            fixed_price_rate=Web3.toWei("1", "ether"),
            fixed_price_publish_market_swap_fee_amount=Web3.toWei("0.001", "ether"),
            fixed_price_with_mint=0,
            wallet=publisher_wallet,
        )

    with pytest.raises(Exception, match="Cap is needed for Datatoken Enterprise"):
        data_nft_factory.create_nft_erc20_with_dispenser(
            DataNFTArguments("72120Bundle", "72Bundle", template_index=2),
            datatoken_template=2,
            datatoken_name="DTWithDispenser",
            datatoken_symbol="DTED",
            datatoken_minter=publisher_wallet.address,
            datatoken_fee_manager=consumer_wallet.address,
            datatoken_publish_market_order_fee_address=publisher_wallet.address,
            datatoken_publish_market_order_fee_token=ZERO_ADDRESS,
            datatoken_publish_market_order_fee_amount=0,
            datatoken_bytess=[b""],
            dispenser_address=ZERO_ADDRESS,
            dispenser_max_tokens=Web3.toWei(1, "ether"),
            dispenser_max_balance=Web3.toWei(1, "ether"),
            dispenser_with_mint=True,
            dispenser_allowed_swapper=ZERO_ADDRESS,
            wallet=publisher_wallet,
        )
