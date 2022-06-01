#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from web3 import Web3, exceptions

from ocean_lib.models.data_nft import DataNFT, DataNFTPermissions
from ocean_lib.models.data_nft_factory import DataNFTFactoryContract
from ocean_lib.models.datatoken import Datatoken
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from tests.resources.helper_functions import (
    deploy_erc721_erc20,
    get_address_of_type,
    get_non_existent_nft_template,
)


@pytest.mark.unit
def test_data_nft_roles(
    web3, config, publisher_wallet, consumer_wallet, another_consumer_wallet
):
    """Test erc721 implicit and explicit role assignments  as well as removing them"""

    # NFT Owner is also added as manager when deploying (first time), if transferred that doesn't apply

    data_nft_factory = DataNFTFactoryContract(
        web3, get_address_of_type(config, "ERC721Factory")
    )
    tx = data_nft_factory.deploy_erc721_contract(
        name="NFT",
        symbol="NFTSYMBOL",
        template_index=1,
        additional_datatoken_deployer=ZERO_ADDRESS,
        additional_metadata_updater=ZERO_ADDRESS,
        token_uri="https://oceanprotocol.com/nft/",
        transferable=True,
        owner=publisher_wallet.address,
        from_wallet=publisher_wallet,
    )
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    registered_event = data_nft_factory.get_event_log(
        event_name=DataNFTFactoryContract.EVENT_NFT_CREATED,
        from_block=tx_receipt.blockNumber,
        to_block=web3.eth.block_number,
        filters=None,
    )
    assert registered_event[0].event == DataNFTFactoryContract.EVENT_NFT_CREATED
    assert registered_event[0].args.admin == publisher_wallet.address
    token_address = registered_event[0].args.newTokenAddress
    data_nft = DataNFT(web3, token_address)

    # Publisher should be a manager
    assert data_nft.get_permissions(publisher_wallet.address)[
        DataNFTPermissions.MANAGER
    ]

    # Consumer address should't be manager
    assert not data_nft.get_permissions(consumer_wallet.address)[
        DataNFTPermissions.MANAGER
    ]

    data_nft.add_manager(consumer_wallet.address, publisher_wallet)

    # Consumer now should be manager
    assert data_nft.get_permissions(consumer_wallet.address)[DataNFTPermissions.MANAGER]

    # Check the rest of roles for another_consumer_wallet
    assert not data_nft.get_permissions(another_consumer_wallet.address)[
        DataNFTPermissions.MANAGER
    ]
    assert not data_nft.get_permissions(another_consumer_wallet.address)[
        DataNFTPermissions.DEPLOY_DATATOKEN
    ]
    assert not data_nft.get_permissions(another_consumer_wallet.address)[
        DataNFTPermissions.UPDATE_METADATA
    ]
    assert not data_nft.get_permissions(another_consumer_wallet.address)[
        DataNFTPermissions.STORE
    ]

    data_nft.add_to_create_erc20_list(another_consumer_wallet.address, consumer_wallet)
    data_nft.add_to_725_store_list(another_consumer_wallet.address, consumer_wallet)
    data_nft.add_to_metadata_list(another_consumer_wallet.address, consumer_wallet)

    # Test rest of add roles functions with newly added manager
    assert data_nft.get_permissions(another_consumer_wallet.address)[
        DataNFTPermissions.DEPLOY_DATATOKEN
    ]
    assert data_nft.get_permissions(another_consumer_wallet.address)[
        DataNFTPermissions.UPDATE_METADATA
    ]
    assert data_nft.get_permissions(another_consumer_wallet.address)[
        DataNFTPermissions.STORE
    ]

    # Remove the manager
    data_nft.remove_manager(consumer_wallet.address, publisher_wallet)

    assert not data_nft.get_permissions(consumer_wallet.address)[
        DataNFTPermissions.MANAGER
    ]


@pytest.mark.unit
def test_properties(web3, config):
    """Tests the events' properties."""

    data_nft_factory = DataNFTFactoryContract(
        web3, get_address_of_type(config, "ERC721Factory")
    )
    assert (
        data_nft_factory.event_NFTCreated.abi["name"]
        == DataNFTFactoryContract.EVENT_NFT_CREATED
    )
    assert (
        data_nft_factory.event_TokenCreated.abi["name"]
        == DataNFTFactoryContract.EVENT_TOKEN_CREATED
    )
    assert (
        data_nft_factory.event_NewPool.abi["name"]
        == DataNFTFactoryContract.EVENT_NEW_POOL
    )
    assert (
        data_nft_factory.event_NewFixedRate.abi["name"]
        == DataNFTFactoryContract.EVENT_NEW_FIXED_RATE
    )


@pytest.mark.unit
def test_nonexistent_template_index(web3, config, publisher_wallet):
    """Test erc721 non existent template creation fail"""

    data_nft_factory = DataNFTFactoryContract(
        web3, get_address_of_type(config, "ERC721Factory")
    )

    non_existent_nft_template = get_non_existent_nft_template(
        data_nft_factory, check_first=10
    )
    assert non_existent_nft_template >= 0, "Non existent NFT template not found."

    with pytest.raises(exceptions.ContractLogicError) as err:
        data_nft_factory.deploy_erc721_contract(
            name="DT1",
            symbol="DTSYMBOL",
            template_index=non_existent_nft_template,
            additional_datatoken_deployer=ZERO_ADDRESS,
            additional_metadata_updater=ZERO_ADDRESS,
            token_uri="https://oceanprotocol.com/nft/",
            transferable=True,
            owner=publisher_wallet.address,
            from_wallet=publisher_wallet,
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721DTFactory: Template index "
        "doesnt exist"
    )


@pytest.mark.unit
def test_successful_data_nft_creation(web3, config, publisher_wallet):
    """Test data NFT successful creation"""

    data_nft_factory = DataNFTFactoryContract(
        web3, get_address_of_type(config, "ERC721Factory")
    )
    tx = data_nft_factory.deploy_erc721_contract(
        name="NFT",
        symbol="NFTSYMBOL",
        template_index=1,
        additional_datatoken_deployer=ZERO_ADDRESS,
        additional_metadata_updater=ZERO_ADDRESS,
        token_uri="https://oceanprotocol.com/nft/",
        transferable=True,
        owner=publisher_wallet.address,
        from_wallet=publisher_wallet,
    )
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    registered_event = data_nft_factory.get_event_log(
        event_name=DataNFTFactoryContract.EVENT_NFT_CREATED,
        from_block=tx_receipt.blockNumber,
        to_block=web3.eth.block_number,
        filters=None,
    )
    assert registered_event[0].event == DataNFTFactoryContract.EVENT_NFT_CREATED
    assert registered_event[0].args.admin == publisher_wallet.address
    token_address = registered_event[0].args.newTokenAddress
    data_nft = DataNFT(web3, token_address)
    owner_balance = data_nft.balance_of(publisher_wallet.address)
    assert data_nft.contract.caller.name() == "NFT"
    assert data_nft.symbol() == "NFTSYMBOL"
    assert owner_balance == 1


@pytest.mark.unit
def test_nft_count(web3, config, publisher_wallet):
    """Test  erc721 factory NFT count"""

    data_nft_factory = DataNFTFactoryContract(
        web3, get_address_of_type(config, "ERC721Factory")
    )
    current_nft_count = data_nft_factory.get_current_nft_count()
    data_nft_factory.deploy_erc721_contract(
        name="NFT",
        symbol="NFTSYMBOL",
        template_index=1,
        additional_datatoken_deployer=ZERO_ADDRESS,
        additional_metadata_updater=ZERO_ADDRESS,
        token_uri="https://oceanprotocol.com/nft/",
        transferable=True,
        owner=publisher_wallet.address,
        from_wallet=publisher_wallet,
    )
    assert data_nft_factory.get_current_nft_count() == current_nft_count + 1


@pytest.mark.unit
def test_nft_template(web3, config):
    """Tests get NFT template"""

    data_nft_factory = DataNFTFactoryContract(
        web3, get_address_of_type(config, "ERC721Factory")
    )
    nft_template = data_nft_factory.get_nft_template(1)
    assert nft_template[0] == get_address_of_type(config, "ERC721Template")
    assert nft_template[1] is True


@pytest.mark.unit
def test_datatoken_creation(
    web3, config, publisher_wallet, consumer_wallet, another_consumer_wallet
):
    """Test erc20 successful creation with owner assigned as minter"""

    data_nft_factory = DataNFTFactoryContract(
        web3, get_address_of_type(config, "ERC721Factory")
    )
    tx = data_nft_factory.deploy_erc721_contract(
        name="NFT",
        symbol="NFTSYMBOL",
        template_index=1,
        additional_datatoken_deployer=ZERO_ADDRESS,
        additional_metadata_updater=ZERO_ADDRESS,
        token_uri="https://oceanprotocol.com/nft/",
        transferable=True,
        owner=publisher_wallet.address,
        from_wallet=publisher_wallet,
    )
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    registered_event = data_nft_factory.get_event_log(
        event_name=DataNFTFactoryContract.EVENT_NFT_CREATED,
        from_block=tx_receipt.blockNumber,
        to_block=web3.eth.block_number,
        filters=None,
    )
    token_address = registered_event[0].args.newTokenAddress
    data_nft = DataNFT(web3, token_address)
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
    tx_receipt2 = web3.eth.wait_for_transaction_receipt(tx_result)

    registered_event2 = data_nft_factory.get_event_log(
        event_name=DataNFTFactoryContract.EVENT_TOKEN_CREATED,
        from_block=tx_receipt2.blockNumber,
        to_block=web3.eth.block_number,
        filters=None,
    )

    datatoken_address = registered_event2[0].args.newTokenAddress

    datatoken = Datatoken(web3, datatoken_address)

    permissions = datatoken.get_permissions(publisher_wallet.address)

    assert permissions[0], "Not a minter"
    assert tx_result, "Error creating datatoken."

    # Tests failed creation of datatoken
    with pytest.raises(exceptions.ContractLogicError) as err:
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
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721Template: NOT "
        "ERC20DEPLOYER_ROLE"
    )


@pytest.mark.unit
def test_datatoken_mint_function(
    web3, config, publisher_wallet, consumer_wallet, datatoken
):
    """Test datatoken failed/successful mint function"""
    datatoken.mint(publisher_wallet.address, 10, publisher_wallet)
    datatoken.mint(consumer_wallet.address, 20, publisher_wallet)

    assert datatoken.balanceOf(publisher_wallet.address) == 10
    assert datatoken.balanceOf(consumer_wallet.address) == 20

    # Tests failed mint
    with pytest.raises(exceptions.ContractLogicError) as err:
        datatoken.mint(publisher_wallet.address, 10, consumer_wallet)
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC20Template: NOT MINTER"
    )

    # Test with another minter
    _, datatoken_2 = deploy_erc721_erc20(
        web3, config, publisher_wallet, consumer_wallet
    )

    datatoken_2.mint(publisher_wallet.address, 10, consumer_wallet)
    datatoken_2.mint(consumer_wallet.address, 20, consumer_wallet)

    assert datatoken.balanceOf(publisher_wallet.address) == 10
    assert datatoken.balanceOf(consumer_wallet.address) == 20


@pytest.mark.unit
def test_datatoken_set_data(web3, config, publisher_wallet, data_nft, datatoken):
    """Test erc20 data set functions"""

    """This is a special metadata, it's callable only from the erc20Token contract and
    can be done only by who has deployERC20 rights(rights to create new erc20 token contract)
    the value is stored into the 725Y standard with a predefined key which is the erc20Token address"""

    key = Web3.keccak(hexstr=datatoken.address)

    value = Web3.toHex(text="SomeData")

    assert Web3.toHex(data_nft.get_data(key)) == "0x"
    datatoken.set_data(value, publisher_wallet)

    assert Web3.toHex(data_nft.get_data(key)) == value
    """This one is the generic version of updating data into the key-value story.
    Only users with 'store' permission can do that.
    NOTE: in this function the key is chosen by the caller."""

    data_nft.set_new_data(Web3.keccak(text="arbitrary text"), value, publisher_wallet)

    res = data_nft.get_data(Web3.keccak(text="arbitrary text"))

    assert Web3.toHex(res) == value


@pytest.mark.unit
def test_nft_owner_transfer(
    web3, config, publisher_wallet, consumer_wallet, data_nft, datatoken
):
    """Test erc721 ownership transfer on token transfer"""

    assert data_nft.owner_of(1) == publisher_wallet.address

    with pytest.raises(exceptions.ContractLogicError) as err:
        data_nft.transfer_from(
            consumer_wallet.address, publisher_wallet.address, 1, publisher_wallet
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721: transfer of token that is not own"
    )
    data_nft.transfer_from(
        publisher_wallet.address, consumer_wallet.address, 1, publisher_wallet
    )

    assert data_nft.balance_of(publisher_wallet.address) == 0
    assert data_nft.owner_of(1) == consumer_wallet.address
    # Owner is not NFT owner anymore, nor has any other role, neither older users
    with pytest.raises(exceptions.ContractLogicError) as err:
        data_nft.create_erc20(
            template_index=1,
            name="DT1",
            symbol="DT1Symbol",
            minter=publisher_wallet.address,
            fee_manager=publisher_wallet.address,
            publish_market_order_fee_address=publisher_wallet.address,
            publish_market_order_fee_token=ZERO_ADDRESS,
            publish_market_order_fee_amount=0,
            bytess=[b""],
            from_wallet=publisher_wallet,
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721Template: NOT ERC20DEPLOYER_ROLE"
    )
    with pytest.raises(exceptions.ContractLogicError) as err:
        datatoken.mint(publisher_wallet.address, 10, publisher_wallet)
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC20Template: NOT MINTER"
    )

    # NewOwner now owns the NFT, is already Manager by default and has all roles
    data_nft.create_erc20(
        template_index=1,
        name="DT1",
        symbol="DT1Symbol",
        minter=consumer_wallet.address,
        fee_manager=consumer_wallet.address,
        publish_market_order_fee_address=consumer_wallet.address,
        publish_market_order_fee_token=ZERO_ADDRESS,
        publish_market_order_fee_amount=0,
        bytess=[b""],
        from_wallet=consumer_wallet,
    )
    datatoken.add_minter(consumer_wallet.address, consumer_wallet)

    datatoken.mint(consumer_wallet.address, 20, consumer_wallet)

    assert datatoken.balanceOf(consumer_wallet.address) == 20
