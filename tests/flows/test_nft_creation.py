#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from ocean_lib.models.erc20_token import ERC20Token
from ocean_lib.models.erc721_factory import ERC721FactoryContract
from ocean_lib.models.erc721_token import ERC721Permissions, ERC721Token
from ocean_lib.models.models_structures import CreateErc20Data, CreateERC721Data
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.currency import to_wei
from tests.resources.helper_functions import (
    deploy_erc721_erc20,
    get_address_of_type,
    get_non_existent_nft_template,
)
from web3 import Web3, exceptions


def test_erc721_roles(
    web3, config, publisher_wallet, consumer_wallet, another_consumer_wallet
):
    """Test erc721 implicit and explicit role assignments  as well as removing them"""

    # NFT Owner is also added as manager when deploying (first time), if transferred that doesn't apply

    erc721_factory = ERC721FactoryContract(
        web3, get_address_of_type(config, "ERC721Factory")
    )
    erc721_data = CreateERC721Data(
        name="NFT",
        symbol="NFTSYMBOL",
        template_index=1,
        additional_erc20_deployer=ZERO_ADDRESS,
        token_uri="https://oceanprotocol.com/nft/",
    )
    tx = erc721_factory.deploy_erc721_contract(
        erc721_data, from_wallet=publisher_wallet
    )
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    registered_event = erc721_factory.get_event_log(
        event_name=ERC721FactoryContract.EVENT_NFT_CREATED,
        from_block=tx_receipt.blockNumber,
        to_block=web3.eth.block_number,
        filters=None,
    )
    assert registered_event[0].event == ERC721FactoryContract.EVENT_NFT_CREATED
    assert registered_event[0].args.admin == publisher_wallet.address
    token_address = registered_event[0].args.newTokenAddress
    erc721_token = ERC721Token(web3, token_address)

    # Publisher should be a manager
    assert erc721_token.get_permissions(publisher_wallet.address)[
        ERC721Permissions.MANAGER
    ]

    # Consumer address should't be manager
    assert not erc721_token.get_permissions(consumer_wallet.address)[
        ERC721Permissions.MANAGER
    ]

    erc721_token.add_manager(consumer_wallet.address, publisher_wallet)

    # Consumer now should be manager
    assert erc721_token.get_permissions(consumer_wallet.address)[
        ERC721Permissions.MANAGER
    ]

    # Check the rest of roles for another_consumer_wallet
    assert not erc721_token.get_permissions(another_consumer_wallet.address)[
        ERC721Permissions.MANAGER
    ]
    assert not erc721_token.get_permissions(another_consumer_wallet.address)[
        ERC721Permissions.DEPLOY_ERC20
    ]
    assert not erc721_token.get_permissions(another_consumer_wallet.address)[
        ERC721Permissions.UPDATE_METADATA
    ]
    assert not erc721_token.get_permissions(another_consumer_wallet.address)[
        ERC721Permissions.STORE
    ]

    erc721_token.add_to_create_erc20_list(
        another_consumer_wallet.address, consumer_wallet
    )
    erc721_token.add_to_725_store_list(another_consumer_wallet.address, consumer_wallet)
    erc721_token.add_to_metadata_list(another_consumer_wallet.address, consumer_wallet)

    # Test rest of add roles functions with newly added manager
    assert erc721_token.get_permissions(another_consumer_wallet.address)[
        ERC721Permissions.DEPLOY_ERC20
    ]
    assert erc721_token.get_permissions(another_consumer_wallet.address)[
        ERC721Permissions.UPDATE_METADATA
    ]
    assert erc721_token.get_permissions(another_consumer_wallet.address)[
        ERC721Permissions.STORE
    ]

    # Remove the manager
    erc721_token.remove_manager(consumer_wallet.address, publisher_wallet)

    assert not erc721_token.get_permissions(consumer_wallet.address)[
        ERC721Permissions.MANAGER
    ]


def test_properties(web3, config):
    """Tests the events' properties."""

    erc721_factory = ERC721FactoryContract(
        web3, get_address_of_type(config, "ERC721Factory")
    )
    assert (
        erc721_factory.event_NFTCreated.abi["name"]
        == ERC721FactoryContract.EVENT_NFT_CREATED
    )
    assert (
        erc721_factory.event_TokenCreated.abi["name"]
        == ERC721FactoryContract.EVENT_TOKEN_CREATED
    )
    assert (
        erc721_factory.event_NewPool.abi["name"] == ERC721FactoryContract.EVENT_NEW_POOL
    )
    assert (
        erc721_factory.event_NewFixedRate.abi["name"]
        == ERC721FactoryContract.EVENT_NEW_FIXED_RATE
    )


def test_fail_create_erc20(web3, config, publisher_wallet):
    """Test erc20 creation fail"""

    erc721_factory = ERC721FactoryContract(
        web3, get_address_of_type(config, "ERC721Factory")
    )

    wrong_erc20_data = CreateErc20Data(
        template_index=1,
        strings=["ERC20DT1", "ERC20DT1Symbol"],
        addresses=[
            publisher_wallet.address,
            publisher_wallet.address,
            publisher_wallet.address,
            ZERO_ADDRESS,
        ],
        uints=[to_wei("1.0"), 0],
        bytess=[b""],
    )

    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_factory.create_token(wrong_erc20_data, from_wallet=publisher_wallet)
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721Factory: ONLY ERC721 "
        "INSTANCE FROM ERC721FACTORY"
    )


def test_nonexistent_template_index(web3, config, publisher_wallet):
    """Test erc721 non existent template creation fail"""

    erc721_factory = ERC721FactoryContract(
        web3, get_address_of_type(config, "ERC721Factory")
    )

    non_existent_nft_template = get_non_existent_nft_template(
        erc721_factory, check_first=10
    )
    assert non_existent_nft_template >= 0, "Non existent NFT template not found."

    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_factory.deploy_erc721_contract(
            (
                "DT1",
                "DTSYMBOL",
                non_existent_nft_template,
                ZERO_ADDRESS,
                "https://oceanprotocol.com/nft/",
            ),
            from_wallet=publisher_wallet,
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721DTFactory: Template index "
        "doesnt exist"
    )


def test_successful_erc721_creation(web3, config, publisher_wallet):
    """Test erc721 successful creation"""

    erc721_factory = ERC721FactoryContract(
        web3, get_address_of_type(config, "ERC721Factory")
    )
    erc721_data = CreateERC721Data(
        name="NFT",
        symbol="NFTSYMBOL",
        template_index=1,
        additional_erc20_deployer=ZERO_ADDRESS,
        token_uri="https://oceanprotocol.com/nft/",
    )
    tx = erc721_factory.deploy_erc721_contract(
        erc721_data, from_wallet=publisher_wallet
    )
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    registered_event = erc721_factory.get_event_log(
        event_name=ERC721FactoryContract.EVENT_NFT_CREATED,
        from_block=tx_receipt.blockNumber,
        to_block=web3.eth.block_number,
        filters=None,
    )
    assert registered_event[0].event == ERC721FactoryContract.EVENT_NFT_CREATED
    assert registered_event[0].args.admin == publisher_wallet.address
    token_address = registered_event[0].args.newTokenAddress
    erc721_token = ERC721Token(web3, token_address)
    owner_balance = erc721_token.balance_of(publisher_wallet.address)
    assert erc721_token.contract.caller.name() == "NFT"
    assert erc721_token.symbol() == "NFTSYMBOL"
    assert owner_balance == 1


def test_nft_count(web3, config, publisher_wallet):
    """Test  erc721 factory NFT count"""

    erc721_factory = ERC721FactoryContract(
        web3, get_address_of_type(config, "ERC721Factory")
    )
    erc721_data = CreateERC721Data(
        name="NFT",
        symbol="NFTSYMBOL",
        template_index=1,
        additional_erc20_deployer=ZERO_ADDRESS,
        token_uri="https://oceanprotocol.com/nft/",
    )
    current_nft_count = erc721_factory.get_current_nft_count()
    erc721_factory.deploy_erc721_contract(erc721_data, from_wallet=publisher_wallet)
    assert erc721_factory.get_current_nft_count() == current_nft_count + 1


def test_nft_template(web3, config):
    """Tests get NFT template"""

    erc721_factory = ERC721FactoryContract(
        web3, get_address_of_type(config, "ERC721Factory")
    )
    nft_template = erc721_factory.get_nft_template(1)
    assert nft_template[0] == get_address_of_type(config, "ERC721Template")
    assert nft_template[1] is True


def test_erc20_creation(
    web3, config, publisher_wallet, consumer_wallet, another_consumer_wallet
):
    """Test erc20 successful creation with owner assigned as minter"""

    erc721_factory = ERC721FactoryContract(
        web3, get_address_of_type(config, "ERC721Factory")
    )
    erc721_data = CreateERC721Data(
        name="NFT",
        symbol="NFTSYMBOL",
        template_index=1,
        additional_erc20_deployer=ZERO_ADDRESS,
        token_uri="https://oceanprotocol.com/nft/",
    )

    tx = erc721_factory.deploy_erc721_contract(
        erc721_data, from_wallet=publisher_wallet
    )
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    registered_event = erc721_factory.get_event_log(
        event_name=ERC721FactoryContract.EVENT_NFT_CREATED,
        from_block=tx_receipt.blockNumber,
        to_block=web3.eth.block_number,
        filters=None,
    )
    token_address = registered_event[0].args.newTokenAddress
    erc721_token = ERC721Token(web3, token_address)
    erc721_token.add_to_create_erc20_list(consumer_wallet.address, publisher_wallet)
    erc_create_data = CreateErc20Data(
        template_index=1,
        strings=["ERC20DT1", "ERC20DT1Symbol"],
        addresses=[
            publisher_wallet.address,
            consumer_wallet.address,
            publisher_wallet.address,
            ZERO_ADDRESS,
        ],
        uints=[to_wei("0.5"), 0],
        bytess=[b""],
    )
    tx_result = erc721_token.create_erc20(erc_create_data, consumer_wallet)
    tx_receipt2 = web3.eth.wait_for_transaction_receipt(tx_result)

    registered_event2 = erc721_factory.get_event_log(
        event_name=ERC721FactoryContract.EVENT_TOKEN_CREATED,
        from_block=tx_receipt2.blockNumber,
        to_block=web3.eth.block_number,
        filters=None,
    )

    erc20_address = registered_event2[0].args.newTokenAddress

    erc20_token = ERC20Token(web3, erc20_address)

    permissions = erc20_token.get_permissions(publisher_wallet.address)

    assert permissions[0], "Not a minter"
    assert tx_result, "Error creating ERC20 token."

    # Tests failed creation of ERC20
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_token.create_erc20(erc_create_data, another_consumer_wallet)
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721Template: NOT "
        "ERC20DEPLOYER_ROLE"
    )


def test_erc20_mint_function(web3, config, publisher_wallet, consumer_wallet):
    """Test erc20 failed/successful mint function"""

    _, erc20 = deploy_erc721_erc20(
        web3=web3,
        config=config,
        erc721_publisher=publisher_wallet,
        erc20_minter=publisher_wallet,
    )

    erc20.mint(publisher_wallet.address, 10, publisher_wallet)
    erc20.mint(consumer_wallet.address, 20, publisher_wallet)

    assert erc20.balanceOf(publisher_wallet.address) == 10
    assert erc20.balanceOf(consumer_wallet.address) == 20

    # Tests failed mint
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc20.mint(publisher_wallet.address, 10, consumer_wallet)
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC20Template: NOT MINTER"
    )

    # Test with another minter
    _, erc20_2 = deploy_erc721_erc20(web3, config, publisher_wallet, consumer_wallet)

    erc20_2.mint(publisher_wallet.address, 10, consumer_wallet)
    erc20_2.mint(consumer_wallet.address, 20, consumer_wallet)

    assert erc20.balanceOf(publisher_wallet.address) == 10
    assert erc20.balanceOf(consumer_wallet.address) == 20


def test_erc20_set_data(web3, config, publisher_wallet):
    """Test erc20 data set functions"""

    erc721, erc20 = deploy_erc721_erc20(
        web3, config, publisher_wallet, publisher_wallet
    )

    """This is a special metadata, it's callable only from the erc20Token contract and
    can be done only by who has deployERC20 rights(rights to create new erc20 token contract)
    the value is stored into the 725Y standard with a predefined key which is the erc20Token address"""

    key = Web3.keccak(hexstr=erc20.address)

    value = Web3.toHex(text="SomeData")

    assert Web3.toHex(erc721.get_data(key)) == "0x"
    erc20.set_data(value, publisher_wallet)

    assert Web3.toHex(erc721.get_data(key)) == value
    """This one is the generic version of updating data into the key-value story.
    Only users with 'store' permission can do that.
    NOTE: in this function the key is chosen by the caller."""

    erc721.set_new_data(Web3.keccak(text="arbitrary text"), value, publisher_wallet)

    res = erc721.get_data(Web3.keccak(text="arbitrary text"))

    assert Web3.toHex(res) == value


def test_nft_owner_transfer(web3, config, publisher_wallet, consumer_wallet):
    """Test erc721 ownership transfer on token transfer"""

    erc721, erc20 = deploy_erc721_erc20(
        web3, config, publisher_wallet, publisher_wallet
    )

    assert erc721.owner_of(1) == publisher_wallet.address

    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721.transfer_from(
            consumer_wallet.address, publisher_wallet.address, 1, publisher_wallet
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721: transfer of token that is not own"
    )
    erc721.transfer_from(
        publisher_wallet.address, consumer_wallet.address, 1, publisher_wallet
    )

    assert erc721.balance_of(publisher_wallet.address) == 0
    assert erc721.owner_of(1) == consumer_wallet.address
    # Owner is not NFT owner anymore, nor has any other role, neither older users
    erc_create_data = CreateErc20Data(
        template_index=1,
        strings=["ERC20DT1", "ERC20DT1Symbol"],
        addresses=[
            publisher_wallet.address,
            publisher_wallet.address,
            publisher_wallet.address,
            ZERO_ADDRESS,
        ],
        uints=[to_wei("0.5"), 0],
        bytess=[b""],
    )
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721.create_erc20(erc_create_data, publisher_wallet)
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721Template: NOT ERC20DEPLOYER_ROLE"
    )
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc20.mint(publisher_wallet.address, 10, publisher_wallet)
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC20Template: NOT MINTER"
    )

    # NewOwner now owns the NFT, is already Manager by default and has all roles
    erc_create_data_new_manager = CreateErc20Data(
        template_index=1,
        strings=["ERC20DT1", "ERC20DT1Symbol"],
        addresses=[
            consumer_wallet.address,
            consumer_wallet.address,
            consumer_wallet.address,
            ZERO_ADDRESS,
        ],
        uints=[to_wei("0.5"), 0],
        bytess=[b""],
    )

    erc721.create_erc20(erc_create_data_new_manager, consumer_wallet)
    erc20.add_minter(consumer_wallet.address, consumer_wallet)

    erc20.mint(consumer_wallet.address, 20, consumer_wallet)

    assert erc20.balanceOf(consumer_wallet.address) == 20
