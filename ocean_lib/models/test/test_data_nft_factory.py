#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from brownie import network
from web3.main import Web3

from ocean_lib.models.data_nft import DataNFT, DataNFTArguments
from ocean_lib.models.datatoken import Datatoken, DatatokenArguments, TokenFeeInfo
from ocean_lib.models.dispenser import Dispenser
from ocean_lib.ocean.util import create_checksum, get_address_of_type, to_wei
from ocean_lib.structures.abi_tuples import OrderData
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.utils import split_signature
from tests.resources.helper_functions import get_non_existent_nft_template


@pytest.mark.unit
def test_nft_creation(
    config,
    publisher_wallet,
    consumer_wallet,
    data_nft_factory,
):
    """Tests the utils functions."""
    data_nft = data_nft_factory.create(
        DataNFTArguments("DT1", "DTSYMBOL"), {"from": publisher_wallet}
    )
    assert data_nft.contract.name() == "DT1"
    assert data_nft.symbol() == "DTSYMBOL"

    # Tests current NFT count
    current_nft_count = data_nft_factory.getCurrentNFTCount()
    data_nft = data_nft_factory.create(
        DataNFTArguments("DT2", "DTSYMBOL1"), {"from": publisher_wallet}
    )
    assert data_nft_factory.getCurrentNFTCount() == current_nft_count + 1

    # Tests get NFT template
    nft_template_address = get_address_of_type(config, DataNFT.CONTRACT_NAME, "1")
    nft_template = data_nft_factory.getNFTTemplate(1)
    assert nft_template[0] == nft_template_address
    assert nft_template[1] is True

    # Tests creating successfully an ERC20 token
    data_nft.addToCreateERC20List(consumer_wallet.address, {"from": publisher_wallet})
    datatoken = data_nft.create_datatoken(
        {"from": publisher_wallet},
        DatatokenArguments(
            "DT1P",
            "DT1Symbol",
            fee_manager=consumer_wallet.address,
        ),
    )
    assert datatoken, "Failed to create ERC20 token."

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


@pytest.mark.unit
def test_combo_functions(
    config,
    publisher_wallet,
    consumer_wallet,
    data_nft_factory,
):
    """Tests the utils functions."""
    # Tests creating NFT with ERC20 successfully
    data_nft_token2, datatoken2 = data_nft_factory.create_with_erc20(
        DataNFTArguments("72120Bundle", "72Bundle"),
        DatatokenArguments(
            "DTB1",
            "DT1Symbol",
            fee_manager=consumer_wallet.address,
        ),
        {"from": publisher_wallet},
    )
    assert data_nft_token2.contract.name() == "72120Bundle"
    assert data_nft_token2.symbol() == "72Bundle"
    assert datatoken2.contract.name() == "DTB1"
    assert datatoken2.symbol() == "DT1Symbol"

    # Tests creating NFT with ERC20 and with Fixed Rate Exchange successfully.
    fixed_rate_address = get_address_of_type(config, "FixedPrice")

    # Create ERC20 data token for fees.
    datatoken = data_nft_token2.create_datatoken(
        {"from": publisher_wallet},
        DatatokenArguments(
            "DT1P",
            "DT1SymbolP",
            fee_manager=consumer_wallet.address,
            publish_market_order_fees=TokenFeeInfo(
                address=publisher_wallet.address,
                token=ZERO_ADDRESS,
                amount=to_wei(0.0005),
            ),
        ),
    )
    assert datatoken, "Failed to create ERC20 token."
    fee_datatoken_address = datatoken.address

    (
        data_nft_token4,
        datatoken4,
        one_fixed_rate,
    ) = data_nft_factory.create_with_erc20_and_fixed_rate(
        DataNFTArguments("72120Bundle", "72Bundle"),
        DatatokenArguments(
            "DTWithPool",
            "DTP",
            fee_manager=consumer_wallet.address,
        ),
        fixed_price_base_token=fee_datatoken_address,
        fixed_price_owner=publisher_wallet.address,
        fixed_price_publish_market_swap_fee_collector=consumer_wallet.address,
        fixed_price_allowed_swapper=ZERO_ADDRESS,
        fixed_price_base_token_decimals=18,
        fixed_price_datatoken_decimals=18,
        fixed_price_rate=to_wei(1),
        fixed_price_publish_market_swap_fee_amount=to_wei(0.001),
        fixed_price_with_mint=0,
        tx_dict={"from": publisher_wallet},
    )

    assert data_nft_token4.contract.name() == "72120Bundle"
    assert data_nft_token4.symbol() == "72Bundle"
    assert datatoken4.contract.name() == "DTWithPool"
    assert datatoken4.symbol() == "DTP"
    assert one_fixed_rate.address == fixed_rate_address

    # Tests creating NFT with ERC20 and with Dispenser successfully.
    dispenser_address = get_address_of_type(config, Dispenser.CONTRACT_NAME)

    data_nft_token5, datatoken5 = data_nft_factory.create_with_erc20_and_dispenser(
        DataNFTArguments("72120Bundle", "72Bundle"),
        DatatokenArguments(
            "DTWithPool",
            "DTP",
            fee_manager=consumer_wallet.address,
        ),
        dispenser_max_tokens=to_wei(1),
        dispenser_max_balance=to_wei(1),
        dispenser_with_mint=True,
        dispenser_allowed_swapper=ZERO_ADDRESS,
        tx_dict={"from": publisher_wallet},
    )
    assert data_nft_token5.contract.name() == "72120Bundle"
    assert data_nft_token5.symbol() == "72Bundle"
    assert datatoken5.contract.name() == "DTWithPool"
    assert datatoken5.symbol() == "DTP"

    _ = Dispenser(config, dispenser_address)

    # Create a new erc721 with metadata in one single call and get address
    data_nft = data_nft_factory.create_with_metadata(
        DataNFTArguments("72120Bundle", "72Bundle"),
        metadata_state=1,
        metadata_decryptor_url="http://myprovider:8030",
        metadata_decryptor_address=b"0x123",
        metadata_flags=bytes(0),
        metadata_data=Web3.toHex(text="my cool metadata."),
        metadata_data_hash=create_checksum("my cool metadata."),
        metadata_proofs=[],
        tx_dict={"from": publisher_wallet},
    )
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
    data_nft = data_nft_factory.create(
        DataNFTArguments("DT1", "DTSYMBOL"), {"from": publisher_wallet}
    )
    assert data_nft.contract.name() == "DT1"
    assert data_nft.symbol() == "DTSYMBOL"
    assert data_nft_factory.check_nft(data_nft.address)

    # Tests current NFT count
    current_nft_count = data_nft_factory.getCurrentNFTCount()
    data_nft = data_nft_factory.create(
        DataNFTArguments("DT2", "DTSYMBOL1"), {"from": publisher_wallet}
    )
    assert data_nft_factory.getCurrentNFTCount() == current_nft_count + 1

    # Tests get NFT template
    nft_template_address = get_address_of_type(config, DataNFT.CONTRACT_NAME, "1")
    nft_template = data_nft_factory.getNFTTemplate(1)
    assert nft_template[0] == nft_template_address
    assert nft_template[1] is True

    # Tests creating successfully an ERC20 token
    data_nft.addToCreateERC20List(consumer_wallet.address, {"from": publisher_wallet})
    datatoken = data_nft.create_datatoken(
        {"from": consumer_wallet},
        DatatokenArguments(
            name="DT1",
            symbol="DT1Symbol",
            minter=publisher_wallet.address,
        ),
    )
    assert datatoken, "Failed to create ERC20 token."

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
    assert data_nft_factory.check_datatoken(datatoken.address)

    # Tests starting multiple token orders successfully
    datatoken = Datatoken(config, datatoken.address)
    dt_amount = to_wei(2)
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
        datatoken.address,
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
def test_nonexistent_template_index(data_nft_factory, publisher_wallet):
    """Test erc721 non existent template creation fail"""
    non_existent_nft_template = get_non_existent_nft_template(
        data_nft_factory, check_first=10
    )
    assert non_existent_nft_template >= 0, "Non existent NFT template not found."

    with pytest.raises(Exception, match="Missing NFTCreated event"):
        data_nft_factory.create(
            DataNFTArguments(
                "DT1", "DTSYMBOL", template_index=non_existent_nft_template
            ),
            {"from": publisher_wallet, "required_confs": 0},
        )
