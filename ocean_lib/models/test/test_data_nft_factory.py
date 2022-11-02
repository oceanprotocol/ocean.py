#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from brownie import network
from brownie.network.transaction import TransactionReceipt
from web3.main import Web3

from ocean_lib.models.data_nft import DataNFT
from ocean_lib.models.data_nft_factory import DataNFTFactoryContract
from ocean_lib.models.datatoken import Datatoken
from ocean_lib.models.dispenser import Dispenser
from ocean_lib.ocean.util import get_address_of_type
from ocean_lib.structures.abi_tuples import OrderData
from ocean_lib.utils.utilities import create_checksum
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.currency import to_wei
from ocean_lib.web3_internal.utils import split_signature


@pytest.mark.unit
def test_main(
    config,
    publisher_wallet,
    consumer_wallet,
    another_consumer_wallet,
    provider_wallet,
):
    """Tests the utils functions."""
    data_nft_factory_address = get_address_of_type(
        config, DataNFTFactoryContract.CONTRACT_NAME
    )
    data_nft_factory = DataNFTFactoryContract(config, data_nft_factory_address)

    tx = data_nft_factory.deploy_erc721_contract(
        name="DT1",
        symbol="DTSYMBOL",
        template_index=1,
        additional_metadata_updater=ZERO_ADDRESS,
        additional_datatoken_deployer=ZERO_ADDRESS,
        token_uri="https://oceanprotocol.com/nft/",
        transferable=True,
        owner=publisher_wallet.address,
        from_wallet=publisher_wallet,
    )
    receipt = TransactionReceipt(tx)
    registered_event = receipt.events[DataNFTFactoryContract.EVENT_NFT_CREATED]

    assert registered_event["admin"] == publisher_wallet.address
    token_address = registered_event["newTokenAddress"]
    data_nft = DataNFT(config, token_address)
    assert data_nft.contract.name() == "DT1"
    assert data_nft.symbol() == "DTSYMBOL"

    # Tests current NFT count
    current_nft_count = data_nft_factory.get_current_nft_count()
    data_nft_factory.deploy_erc721_contract(
        name="DT2",
        symbol="DTSYMBOL1",
        template_index=1,
        additional_metadata_updater=ZERO_ADDRESS,
        additional_datatoken_deployer=ZERO_ADDRESS,
        token_uri="https://oceanprotocol.com/nft/",
        transferable=True,
        owner=publisher_wallet.address,
        from_wallet=publisher_wallet,
    )
    assert data_nft_factory.get_current_nft_count() == current_nft_count + 1

    # Tests get NFT template
    nft_template_address = get_address_of_type(config, DataNFT.CONTRACT_NAME, "1")
    nft_template = data_nft_factory.get_nft_template(1)
    assert nft_template[0] == nft_template_address
    assert nft_template[1] is True

    # Tests creating successfully an ERC20 token
    data_nft.add_to_create_erc20_list(consumer_wallet.address, publisher_wallet)
    tx_result = data_nft.create_erc20(
        template_index=1,
        name="DT1",
        symbol="DT1Symbol",
        minter=publisher_wallet.address,
        fee_manager=consumer_wallet.address,
        publish_market_order_fee_address=publisher_wallet.address,
        publish_market_order_fee_token=ZERO_ADDRESS,
        publish_market_order_fee_amount=0,
        bytess=[b""],
        from_wallet=consumer_wallet,
    )
    assert tx_result, "Failed to create ERC20 token."
    receipt = TransactionReceipt(tx_result)
    registered_token_event = receipt.events[DataNFTFactoryContract.EVENT_TOKEN_CREATED]
    assert registered_token_event, "Cannot find TokenCreated event."
    datatoken_address = registered_token_event["newTokenAddress"]

    # Tests templateCount function (one of them should be the Enterprise template)
    assert data_nft_factory.template_count() == 2

    # Tests datatoken template list
    datatoken_template_address = get_address_of_type(
        config, Datatoken.CONTRACT_NAME, "1"
    )
    template = data_nft_factory.get_token_template(1)
    assert template[0] == datatoken_template_address
    assert template[1] is True

    # Tests current token template (one of them should be the Enterprise template)
    assert data_nft_factory.get_current_template_count() == 2

    datatoken = Datatoken(config, datatoken_address)
    datatoken.addMinter(consumer_wallet.address, {"from": publisher_wallet})

    # Tests creating NFT with ERC20 successfully
    tx = data_nft_factory.create_nft_with_erc20(
        nft_name="72120Bundle",
        nft_symbol="72Bundle",
        nft_template=1,
        nft_token_uri="https://oceanprotocol.com/nft/",
        nft_transferable=True,
        nft_owner=publisher_wallet.address,
        datatoken_template=1,
        datatoken_name="DTB1",
        datatoken_symbol="DT1Symbol",
        datatoken_minter=publisher_wallet.address,
        datatoken_fee_manager=consumer_wallet.address,
        datatoken_publish_market_order_fee_address=publisher_wallet.address,
        datatoken_publish_market_order_fee_token=ZERO_ADDRESS,
        datatoken_publish_market_order_fee_amount=0,
        datatoken_bytess=[b""],
        from_wallet=publisher_wallet,
    )
    receipt = TransactionReceipt(tx)
    registered_nft_event = receipt.events[DataNFTFactoryContract.EVENT_NFT_CREATED]

    # Verify if the NFT was created.
    assert registered_nft_event, "Cannot find NFTCreated event."
    assert registered_nft_event["admin"] == publisher_wallet.address
    data_nft_address2 = registered_nft_event["newTokenAddress"]
    data_nft_token2 = DataNFT(config, data_nft_address2)
    assert data_nft_token2.contract.name() == "72120Bundle"
    assert data_nft_token2.symbol() == "72Bundle"

    registered_token_event = receipt.events[DataNFTFactoryContract.EVENT_TOKEN_CREATED]

    # Verify if the ERC20 token was created.
    assert registered_token_event, "Cannot find TokenCreated event."
    datatoken_address2 = registered_token_event["newTokenAddress"]
    datatoken2 = Datatoken(config, datatoken_address2)
    assert datatoken2.contract.name() == "DTB1"
    assert datatoken2.symbol() == "DT1Symbol"

    # Tests creating NFT with ERC20 and with Fixed Rate Exchange successfully.
    fixed_rate_address = get_address_of_type(config, "FixedPrice")

    # Create ERC20 data token for fees.
    tx = data_nft.create_erc20(
        template_index=1,
        name="DT1P",
        symbol="DT1SymbolP",
        minter=publisher_wallet.address,
        fee_manager=consumer_wallet.address,
        publish_market_order_fee_address=publisher_wallet.address,
        publish_market_order_fee_token=ZERO_ADDRESS,
        publish_market_order_fee_amount=to_wei("0.0005"),
        bytess=[b""],
        from_wallet=publisher_wallet,
    )
    assert tx, "Failed to create ERC20 token."
    receipt = TransactionReceipt(tx)
    registered_fee_token_event = receipt.events[
        DataNFTFactoryContract.EVENT_TOKEN_CREATED
    ]
    assert registered_fee_token_event, "Cannot find TokenCreated event."
    fee_datatoken_address = registered_fee_token_event["newTokenAddress"]

    tx = data_nft_factory.create_nft_erc20_with_fixed_rate(
        nft_name="72120Bundle",
        nft_symbol="72Bundle",
        nft_template=1,
        nft_token_uri="https://oceanprotocol.com/nft/",
        nft_transferable=True,
        nft_owner=publisher_wallet.address,
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
        fixed_price_rate=to_wei("1"),
        fixed_price_publish_market_swap_fee_amount=to_wei("0.001"),
        fixed_price_with_mint=0,
        from_wallet=publisher_wallet,
    )
    receipt = TransactionReceipt(tx)
    registered_nft_event = receipt.events[DataNFTFactoryContract.EVENT_NFT_CREATED]

    # Verify if the NFT was created.
    assert registered_nft_event, "Cannot find NFTCreated event."
    assert registered_nft_event["admin"] == publisher_wallet.address
    data_nft_address4 = registered_nft_event["newTokenAddress"]
    data_nft_token4 = DataNFT(config, data_nft_address4)
    assert data_nft_token4.contract.name() == "72120Bundle"
    assert data_nft_token4.symbol() == "72Bundle"

    registered_token_event = receipt.events[DataNFTFactoryContract.EVENT_TOKEN_CREATED]

    # Verify if the ERC20 token was created.
    assert registered_token_event, "Cannot find TokenCreated event."
    datatoken_address4 = registered_token_event["newTokenAddress"]
    datatoken4 = Datatoken(config, datatoken_address4)
    assert datatoken4.contract.name() == "DTWithPool"
    assert datatoken4.symbol() == "DTP"

    registered_fixed_rate_event = receipt.events[
        DataNFTFactoryContract.EVENT_NEW_FIXED_RATE
    ]

    # Verify if the Fixed Rate Exchange was created.
    assert registered_fixed_rate_event, "Cannot find NewFixedRate event."
    assert registered_fixed_rate_event["exchangeId"], "Invalid exchange id."

    # Tests creating NFT with ERC20 and with Dispenser successfully.
    dispenser_address = get_address_of_type(config, Dispenser.CONTRACT_NAME)

    tx = data_nft_factory.create_nft_erc20_with_dispenser(
        nft_name="72120Bundle",
        nft_symbol="72Bundle",
        nft_template=1,
        nft_token_uri="https://oceanprotocol.com/nft/",
        nft_transferable=True,
        nft_owner=publisher_wallet.address,
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
        dispenser_max_tokens=to_wei(1),
        dispenser_max_balance=to_wei(1),
        dispenser_with_mint=True,
        dispenser_allowed_swapper=ZERO_ADDRESS,
        from_wallet=publisher_wallet,
    )
    receipt = TransactionReceipt(tx)
    registered_nft_event = receipt.events[DataNFTFactoryContract.EVENT_NFT_CREATED]

    # Verify if the NFT was created.
    assert registered_nft_event, "Cannot find NFTCreated event."
    assert registered_nft_event["admin"] == publisher_wallet.address
    data_nft_address5 = registered_nft_event["newTokenAddress"]
    data_nft_token5 = DataNFT(config, data_nft_address5)
    assert data_nft_token5.contract.name() == "72120Bundle"
    assert data_nft_token5.symbol() == "72Bundle"

    registered_token_event = receipt.events[DataNFTFactoryContract.EVENT_TOKEN_CREATED]

    # Verify if the datatoken was created.
    assert registered_token_event, "Cannot find TokenCreated event."
    datatoken_address5 = registered_token_event["newTokenAddress"]
    datatoken5 = Datatoken(config, datatoken_address5)
    assert datatoken5.contract.name() == "DTWithPool"
    assert datatoken5.symbol() == "DTP"

    _ = Dispenser(config, dispenser_address)

    registered_dispenser_event = receipt.events[
        DataNFTFactoryContract.EVENT_DISPENSER_CREATED
    ]

    # Verify if the Dispenser data token was created.
    assert registered_dispenser_event, "Cannot find DispenserCreated event."
    assert registered_dispenser_event[
        "datatokenAddress"
    ], "Invalid data token address by dispenser."

    # Create a new erc721 with metadata in one single call and get address
    tx = data_nft_factory.create_nft_with_metadata(
        nft_name="72120Bundle",
        nft_symbol="72Bundle",
        nft_template=1,
        nft_token_uri="https://oceanprotocol.com/nft/",
        nft_transferable=True,
        nft_owner=publisher_wallet.address,
        metadata_state=1,
        metadata_decryptor_url="http://myprovider:8030",
        metadata_decryptor_address=b"0x123",
        metadata_flags=bytes(0),
        metadata_data=Web3.toHex(text="my cool metadata."),
        metadata_data_hash=create_checksum("my cool metadata."),
        metadata_proofs=[],
        from_wallet=publisher_wallet,
    )
    receipt = TransactionReceipt(tx)
    registered_nft_event = receipt.events[DataNFTFactoryContract.EVENT_NFT_CREATED]
    assert registered_nft_event, "Cannot find NFTCreated event"
    assert (
        registered_nft_event["admin"] == publisher_wallet.address
    ), "Invalid NFT owner!"
    data_nft_address = registered_nft_event["newTokenAddress"]
    data_nft = DataNFT(config, data_nft_address)
    assert (
        data_nft.token_name() == "72120Bundle"
    ), "NFT name doesn't match with the expected one."
    metadata_info = data_nft.get_metadata()
    assert metadata_info[3] is True
    assert metadata_info[0] == "http://myprovider:8030"


@pytest.mark.unit
def test_start_multiple_order(
    config, publisher_wallet, consumer_wallet, another_consumer_wallet
):
    """Tests the utils functions."""
    data_nft_factory_address = get_address_of_type(
        config, DataNFTFactoryContract.CONTRACT_NAME
    )
    data_nft_factory = DataNFTFactoryContract(config, data_nft_factory_address)

    tx = data_nft_factory.deploy_erc721_contract(
        name="DT1",
        symbol="DTSYMBOL",
        template_index=1,
        additional_metadata_updater=ZERO_ADDRESS,
        additional_datatoken_deployer=ZERO_ADDRESS,
        token_uri="https://oceanprotocol.com/nft/",
        transferable=True,
        owner=publisher_wallet.address,
        from_wallet=publisher_wallet,
    )
    receipt = TransactionReceipt(tx)
    registered_event = receipt.events[DataNFTFactoryContract.EVENT_NFT_CREATED]

    assert registered_event["admin"] == publisher_wallet.address
    token_address = registered_event["newTokenAddress"]
    data_nft = DataNFT(config, token_address)
    assert data_nft.contract.name() == "DT1"
    assert data_nft.symbol() == "DTSYMBOL"
    assert data_nft_factory.check_nft(token_address)

    # Tests current NFT count
    current_nft_count = data_nft_factory.get_current_nft_count()
    data_nft_factory.deploy_erc721_contract(
        name="DT2",
        symbol="DTSYMBOL1",
        template_index=1,
        additional_metadata_updater=ZERO_ADDRESS,
        additional_datatoken_deployer=ZERO_ADDRESS,
        token_uri="https://oceanprotocol.com/nft/",
        transferable=True,
        owner=publisher_wallet.address,
        from_wallet=publisher_wallet,
    )
    assert data_nft_factory.get_current_nft_count() == current_nft_count + 1

    # Tests get NFT template
    nft_template_address = get_address_of_type(config, DataNFT.CONTRACT_NAME, "1")
    nft_template = data_nft_factory.get_nft_template(1)
    assert nft_template[0] == nft_template_address
    assert nft_template[1] is True

    # Tests creating successfully an ERC20 token
    data_nft.add_to_create_erc20_list(consumer_wallet.address, publisher_wallet)
    tx_result = data_nft.create_erc20(
        template_index=1,
        name="DT1",
        symbol="DT1Symbol",
        minter=publisher_wallet.address,
        fee_manager=consumer_wallet.address,
        publish_market_order_fee_address=publisher_wallet.address,
        publish_market_order_fee_token=ZERO_ADDRESS,
        publish_market_order_fee_amount=0,
        bytess=[b""],
        from_wallet=consumer_wallet,
    )
    assert tx_result, "Failed to create ERC20 token."
    receipt = TransactionReceipt(tx_result)
    registered_token_event = receipt.events[DataNFTFactoryContract.EVENT_TOKEN_CREATED]
    assert registered_token_event, "Cannot find TokenCreated event."
    datatoken_address = registered_token_event["newTokenAddress"]

    # Tests templateCount function (one of them should be the Enterprise template)
    assert data_nft_factory.template_count() == 2

    # Tests datatoken template list
    datatoken_template_address = get_address_of_type(
        config, Datatoken.CONTRACT_NAME, "1"
    )
    template = data_nft_factory.get_token_template(1)
    assert template[0] == datatoken_template_address
    assert template[1] is True

    # Tests current token template (one of them should be the Enterprise template)
    assert data_nft_factory.get_current_template_count() == 2

    # Tests datatoken can be checked as deployed by the factory
    assert data_nft_factory.check_datatoken(datatoken_address)

    # Tests starting multiple token orders successfully
    datatoken = Datatoken(config, datatoken_address)
    dt_amount = to_wei("2")
    mock_dai_contract_address = get_address_of_type(config, "MockDAI")
    assert datatoken.balanceOf(consumer_wallet.address) == 0

    datatoken.addMinter(consumer_wallet.address, {"from": publisher_wallet})
    datatoken.mint(consumer_wallet.address, dt_amount, {"from": consumer_wallet})
    assert datatoken.balanceOf(consumer_wallet.address) == dt_amount

    datatoken.approve(data_nft_factory_address, dt_amount, consumer_wallet)

    datatoken.set_payment_collector(another_consumer_wallet.address, publisher_wallet)

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

    tx = data_nft_factory.start_multiple_token_order(orders, consumer_wallet)
    receipt = TransactionReceipt(tx)

    registered_erc20_start_order_event = receipt.events[Datatoken.EVENT_ORDER_STARTED]

    assert tx, "Failed starting multiple token orders."
    assert registered_erc20_start_order_event["consumer"] == consumer_wallet.address

    assert datatoken.balanceOf(consumer_wallet.address) == 0
    assert datatoken.balanceOf(datatoken.get_payment_collector()) == (dt_amount * 0.97)


@pytest.mark.unit
def test_fail_get_templates(config):
    """Tests multiple failures for getting tokens' templates."""
    data_nft_factory_address = get_address_of_type(
        config, DataNFTFactoryContract.CONTRACT_NAME
    )
    data_nft_factory = DataNFTFactoryContract(config, data_nft_factory_address)

    # Should fail to get the Datatoken template if index = 0
    with pytest.raises(Exception, match="Template index doesnt exist"):
        data_nft_factory.get_token_template(0)

    # Should fail to get the Datatoken template if index > templateCount
    with pytest.raises(Exception, match="Template index doesnt exist"):
        data_nft_factory.get_token_template(3)


@pytest.mark.unit
def test_fail_create_erc20(
    config, publisher_wallet, consumer_wallet, another_consumer_wallet
):
    """Tests multiple failures for creating ERC20 token."""

    data_nft_factory_address = get_address_of_type(
        config, DataNFTFactoryContract.CONTRACT_NAME
    )
    data_nft_factory = DataNFTFactoryContract(config, data_nft_factory_address)

    tx = data_nft_factory.deploy_erc721_contract(
        name="DT1",
        symbol="DTSYMBOL",
        template_index=1,
        additional_metadata_updater=ZERO_ADDRESS,
        additional_datatoken_deployer=ZERO_ADDRESS,
        token_uri="https://oceanprotocol.com/nft/",
        transferable=True,
        owner=publisher_wallet.address,
        from_wallet=publisher_wallet,
    )
    receipt = TransactionReceipt(tx)
    registered_event = receipt.events[DataNFTFactoryContract.EVENT_NFT_CREATED]
    assert registered_event["admin"] == publisher_wallet.address
    token_address = registered_event["newTokenAddress"]
    data_nft = DataNFT(config, token_address)
    data_nft.add_to_create_erc20_list(consumer_wallet.address, publisher_wallet)

    # Should fail to create a specific ERC20 Template if the index is ZERO
    with pytest.raises(Exception, match="Template index doesnt exist"):
        data_nft.create_erc20(
            template_index=0,
            name="DT1",
            symbol="DT1Symbol",
            minter=publisher_wallet.address,
            fee_manager=consumer_wallet.address,
            publish_market_order_fee_address=publisher_wallet.address,
            publish_market_order_fee_token=ZERO_ADDRESS,
            publish_market_order_fee_amount=0,
            bytess=[b""],
            from_wallet=consumer_wallet,
        )

    # Should fail to create a specific ERC20 Template if the index doesn't exist
    with pytest.raises(Exception, match="Template index doesnt exist"):
        data_nft.create_erc20(
            template_index=3,
            name="DT1",
            symbol="DT1Symbol",
            minter=publisher_wallet.address,
            fee_manager=consumer_wallet.address,
            publish_market_order_fee_address=publisher_wallet.address,
            publish_market_order_fee_token=ZERO_ADDRESS,
            publish_market_order_fee_amount=0,
            bytess=[b""],
            from_wallet=consumer_wallet,
        )

    # Should fail to create a specific ERC20 Template if the user is not added on the ERC20 deployers list
    assert data_nft.get_permissions(another_consumer_wallet.address)[1] is False
    with pytest.raises(Exception, match="NOT ERC20DEPLOYER_ROLE"):
        data_nft.create_erc20(
            template_index=1,
            name="DT1",
            symbol="DT1Symbol",
            minter=publisher_wallet.address,
            fee_manager=consumer_wallet.address,
            publish_market_order_fee_address=publisher_wallet.address,
            publish_market_order_fee_token=ZERO_ADDRESS,
            publish_market_order_fee_amount=0,
            bytess=[b""],
            from_wallet=another_consumer_wallet,
        )


@pytest.mark.unit
def test_datatoken_cap(
    config, publisher_wallet, consumer_wallet, another_consumer_wallet
):
    data_nft_factory_address = get_address_of_type(
        config, DataNFTFactoryContract.CONTRACT_NAME
    )
    data_nft_factory = DataNFTFactoryContract(config, data_nft_factory_address)

    # create NFT with ERC20
    with pytest.raises(Exception, match="Cap is needed for Datatoken Enterprise"):
        data_nft_factory.create_nft_with_erc20(
            nft_name="72120Bundle",
            nft_symbol="72Bundle",
            nft_template=1,
            nft_token_uri="https://oceanprotocol.com/nft/",
            nft_transferable=True,
            nft_owner=publisher_wallet.address,
            datatoken_template=2,
            datatoken_name="DTB1",
            datatoken_symbol="EntDT1Symbol",
            datatoken_minter=publisher_wallet.address,
            datatoken_fee_manager=consumer_wallet.address,
            datatoken_publish_market_order_fee_address=publisher_wallet.address,
            datatoken_publish_market_order_fee_token=ZERO_ADDRESS,
            datatoken_publish_market_order_fee_amount=0,
            datatoken_bytess=[b""],
            from_wallet=publisher_wallet,
        )

    with pytest.raises(Exception, match="Cap is needed for Datatoken Enterprise"):
        data_nft_factory.create_nft_erc20_with_fixed_rate(
            nft_name="72120Bundle",
            nft_symbol="72Bundle",
            nft_template=1,
            nft_token_uri="https://oceanprotocol.com/nft/",
            nft_transferable=True,
            nft_owner=publisher_wallet.address,
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
            fixed_price_rate=to_wei("1"),
            fixed_price_publish_market_swap_fee_amount=to_wei("0.001"),
            fixed_price_with_mint=0,
            from_wallet=publisher_wallet,
        )

    with pytest.raises(Exception, match="Cap is needed for Datatoken Enterprise"):
        data_nft_factory.create_nft_erc20_with_dispenser(
            nft_name="72120Bundle",
            nft_symbol="72Bundle",
            nft_template=1,
            nft_token_uri="https://oceanprotocol.com/nft/",
            nft_transferable=True,
            nft_owner=publisher_wallet.address,
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
            dispenser_max_tokens=to_wei(1),
            dispenser_max_balance=to_wei(1),
            dispenser_with_mint=True,
            dispenser_allowed_swapper=ZERO_ADDRESS,
            from_wallet=publisher_wallet,
        )
