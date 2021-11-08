#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from web3 import exceptions

from ocean_lib.models.v4.erc721_factory import ERC721FactoryContract
from ocean_lib.models.v4.erc721_token import ERC721Permissions, ERC721Token
from ocean_lib.models.v4.models_structures import ErcCreateData
from ocean_lib.web3_internal.constants import BLOB, ZERO_ADDRESS
from tests.resources.helper_functions import deploy_erc721_erc20, get_address_of_type


def test_properties(web3, config):
    """Tests the events' properties."""
    erc721_token_address = get_address_of_type(config, ERC721Token.CONTRACT_NAME)
    erc721_token = ERC721Token(web3, erc721_token_address)

    assert (
        erc721_token.event_TokenCreated.abi["name"] == ERC721Token.EVENT_TOKEN_CREATED
    )
    assert (
        erc721_token.event_MetadataCreated.abi["name"]
        == ERC721Token.EVENT_METADATA_CREATED
    )
    assert (
        erc721_token.event_MetadataUpdated.abi["name"]
        == ERC721Token.EVENT_METADATA_UPDATED
    )


def test_permissions(
    web3, config, publisher_wallet, consumer_wallet, another_consumer_wallet
):
    """Tests permissions' functions."""
    erc721_factory_address = get_address_of_type(
        config, ERC721FactoryContract.CONTRACT_NAME
    )
    erc721_token = deploy_erc721_erc20(web3, config, publisher_wallet)
    assert erc721_token.contract.caller.name() == "NFT"
    assert erc721_token.symbol() == "NFTSYMBOL"
    assert erc721_token.balance_of(publisher_wallet.address) == 1

    # Tests if the NFT was initialized
    assert erc721_token.is_initialized() is True

    # Tests adding a manager successfully
    erc721_token.add_manager(consumer_wallet.address, publisher_wallet)
    assert erc721_token.get_permissions(consumer_wallet.address)[
        ERC721Permissions.MANAGER
    ]

    assert erc721_token.token_uri(1) == "https://oceanprotocol.com/nft/1"

    # Tests failing to re-initialize the contract
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_token.initialize(
            publisher_wallet.address,
            "NewName",
            "NN",
            erc721_factory_address,
            ZERO_ADDRESS,
            "https://oceanprotocol.com/nft/",
            publisher_wallet,
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721Template: token instance "
        "already initialized"
    )

    # Tests failing clearing permissions
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_token.clean_permissions(another_consumer_wallet)
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721Template: not NFTOwner"
    )

    # Tests clearing permissions
    erc721_token.add_to_create_erc20_list(publisher_wallet.address, publisher_wallet)
    erc721_token.add_to_create_erc20_list(
        another_consumer_wallet.address, publisher_wallet
    )
    assert (
        erc721_token.get_permissions(publisher_wallet.address)[
            ERC721Permissions.DEPLOY_ERC20
        ]
        is True
    )
    assert (
        erc721_token.get_permissions(another_consumer_wallet.address)[
            ERC721Permissions.DEPLOY_ERC20
        ]
        is True
    )
    # Still is not the NFT owner, cannot clear permissions then
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_token.clean_permissions(another_consumer_wallet)
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721Template: not NFTOwner"
    )

    erc721_token.clean_permissions(publisher_wallet)

    assert (
        erc721_token.get_permissions(publisher_wallet.address)[
            ERC721Permissions.DEPLOY_ERC20
        ]
        is False
    )
    assert (
        erc721_token.get_permissions(consumer_wallet.address)[ERC721Permissions.MANAGER]
        is False
    )
    assert (
        erc721_token.get_permissions(another_consumer_wallet.address)[
            ERC721Permissions.DEPLOY_ERC20
        ]
        is False
    )

    # Tests failing adding a new manager by another user different from the NFT owner
    erc721_token.add_manager(publisher_wallet.address, publisher_wallet)
    assert (
        erc721_token.get_permissions(publisher_wallet.address)[
            ERC721Permissions.MANAGER
        ]
        is True
    )
    assert (
        erc721_token.get_permissions(consumer_wallet.address)[ERC721Permissions.MANAGER]
        is False
    )
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_token.add_manager(another_consumer_wallet.address, consumer_wallet)
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721Template: not NFTOwner"
    )
    assert (
        erc721_token.get_permissions(another_consumer_wallet.address)[
            ERC721Permissions.MANAGER
        ]
        is False
    )

    # Tests removing manager
    erc721_token.add_manager(consumer_wallet.address, publisher_wallet)
    assert (
        erc721_token.get_permissions(consumer_wallet.address)[ERC721Permissions.MANAGER]
        is True
    )
    erc721_token.remove_manager(consumer_wallet.address, publisher_wallet)
    assert (
        erc721_token.get_permissions(consumer_wallet.address)[ERC721Permissions.MANAGER]
        is False
    )

    # Tests failing removing a manager if it has not the NFT owner role
    erc721_token.add_manager(consumer_wallet.address, publisher_wallet)
    assert (
        erc721_token.get_permissions(consumer_wallet.address)[ERC721Permissions.MANAGER]
        is True
    )
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_token.remove_manager(publisher_wallet.address, consumer_wallet)
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721Template: not NFTOwner"
    )
    assert (
        erc721_token.get_permissions(publisher_wallet.address)[
            ERC721Permissions.MANAGER
        ]
        is True
    )

    # Tests removing the NFT owner from the manager role
    erc721_token.remove_manager(publisher_wallet.address, publisher_wallet)
    assert (
        erc721_token.get_permissions(publisher_wallet.address)[
            ERC721Permissions.MANAGER
        ]
        is False
    )
    erc721_token.add_manager(publisher_wallet.address, publisher_wallet)
    assert (
        erc721_token.get_permissions(publisher_wallet.address)[
            ERC721Permissions.MANAGER
        ]
        is True
    )

    # Tests failing calling execute_call function if the user is not manager
    assert (
        erc721_token.get_permissions(another_consumer_wallet.address)[
            ERC721Permissions.MANAGER
        ]
        is False
    )
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_token.execute_call(
            operation=0,
            to=consumer_wallet.address,
            value=10,
            data=web3.toHex(text="SomeData"),
            from_wallet=another_consumer_wallet,
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721RolesAddress: NOT MANAGER"
    )

    # Tests calling execute_call with a manager role
    assert (
        erc721_token.get_permissions(publisher_wallet.address)[
            ERC721Permissions.MANAGER
        ]
        is True
    )
    tx = erc721_token.execute_call(
        operation=0,
        to=consumer_wallet.address,
        value=10,
        data=web3.toHex(text="SomeData"),
        from_wallet=consumer_wallet,
    )
    assert tx, "Could not execute call to consumer."

    # Tests setting new data
    erc721_token.add_to_725_store_list(consumer_wallet.address, publisher_wallet)
    assert (
        erc721_token.get_permissions(consumer_wallet.address)[ERC721Permissions.STORE]
        is True
    )
    erc721_token.set_new_data(
        web3.keccak(text="ARBITRARY_KEY"), web3.toHex(text="SomeData"), consumer_wallet
    )
    assert erc721_token.get_data(web3.keccak(text="ARBITRARY_KEY")) == b"SomeData"

    # Tests failing setting new data if user has not STORE UPDATER role.
    assert (
        erc721_token.get_permissions(another_consumer_wallet.address)[
            ERC721Permissions.STORE
        ]
        is False
    )
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_token.set_new_data(
            web3.keccak(text="ARBITRARY_KEY"),
            web3.toHex(text="SomeData"),
            another_consumer_wallet,
        )

    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721Template: NOT STORE UPDATER"
    )

    # Tests failing setting ERC20 data
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_token.set_data_erc20(
            web3.keccak(text="FOO_KEY"),
            web3.toHex(text="SomeData"),
            consumer_wallet,
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721Template: NOT ERC20 Contract"
    )
    assert erc721_token.get_data(key=web3.keccak(text="FOO_KEY")) == b""


def test_success_update_metadata(web3, config, publisher_wallet, consumer_wallet):
    """Tests updating the metadata flow."""
    erc721_token = deploy_erc721_erc20(web3, config, publisher_wallet)
    assert (
        erc721_token.get_permissions(consumer_wallet.address)[
            ERC721Permissions.UPDATE_METADATA
        ]
        is False
    )
    erc721_token.add_to_metadata_list(consumer_wallet.address, publisher_wallet)
    metadata_info = erc721_token.get_metadata()
    assert metadata_info[3] is False
    tx = erc721_token.set_metadata(
        1,
        "http://myprovider:8030",
        "0x123",
        flags=web3.toBytes(hexstr=BLOB),
        data=web3.toBytes(hexstr=BLOB),
        data_hash=web3.toBytes(hexstr=BLOB),
        from_wallet=consumer_wallet,
    )
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    create_metadata_event = erc721_token.get_event_log(
        "MetadataCreated", tx_receipt.blockNumber, web3.eth.block_number, None
    )
    assert create_metadata_event, "Cannot find MetadataCreated event."
    assert create_metadata_event[0].args.decryptorUrl == "http://myprovider:8030"

    metadata_info = erc721_token.get_metadata()
    assert metadata_info[3] is True
    assert metadata_info[0] == "http://myprovider:8030"

    tx = erc721_token.set_metadata(
        1,
        "http://foourl",
        "0x123",
        flags=web3.toBytes(hexstr=BLOB),
        data=web3.toBytes(hexstr=BLOB),
        data_hash=web3.toBytes(hexstr=BLOB),
        from_wallet=consumer_wallet,
    )
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    update_metadata_event = erc721_token.get_event_log(
        "MetadataUpdated", tx_receipt.blockNumber, web3.eth.block_number, None
    )
    assert update_metadata_event, "Cannot find MetadataUpdated event."
    assert update_metadata_event[0].args.decryptorUrl == "http://foourl"

    metadata_info = erc721_token.get_metadata()
    assert metadata_info[3] is True
    assert metadata_info[0] == "http://foourl"


def test_fails_update_metadata(web3, config, publisher_wallet, consumer_wallet):
    """Tests failure of calling update metadata function when the role of the user is not METADATA UPDATER."""
    erc721_token = deploy_erc721_erc20(web3, config, publisher_wallet)
    assert (
        erc721_token.get_permissions(consumer_wallet.address)[
            ERC721Permissions.UPDATE_METADATA
        ]
        is False
    )
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_token.set_metadata(
            1,
            "http://myprovider:8030",
            "0x123",
            flags=web3.toBytes(hexstr=BLOB),
            data=web3.toBytes(hexstr=BLOB),
            data_hash=web3.toBytes(hexstr=BLOB),
            from_wallet=consumer_wallet,
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721Template: NOT METADATA_ROLE"
    )


def test_create_erc20(web3, config, publisher_wallet, consumer_wallet):
    """Tests calling create an ERC20 by the owner."""
    erc721_token = deploy_erc721_erc20(web3, config, publisher_wallet)
    assert (
        erc721_token.get_permissions(publisher_wallet.address)[
            ERC721Permissions.DEPLOY_ERC20
        ]
        is True
    )

    erc_create_data = ErcCreateData(
        template_index=1,
        strings=["ERC20DT1", "ERC20DT1Symbol"],
        addresses=[
            publisher_wallet.address,
            consumer_wallet.address,
            publisher_wallet.address,
            ZERO_ADDRESS,
        ],
        uints=[web3.toWei("0.5", "ether"), 0],
        bytess=[b""],
    )
    tx = erc721_token.create_erc20(erc_create_data, publisher_wallet)
    assert tx, "Could not create ERC20."


def test_fail_creating_erc20(web3, config, publisher_wallet, consumer_wallet):
    """Tests failure for creating ERC20 token."""
    erc721_token = deploy_erc721_erc20(web3, config, publisher_wallet)
    assert (
        erc721_token.get_permissions(consumer_wallet.address)[
            ERC721Permissions.DEPLOY_ERC20
        ]
        is False
    )
    erc_create_data = ErcCreateData(
        template_index=1,
        strings=["ERC20DT1", "ERC20DT1Symbol"],
        addresses=[
            consumer_wallet.address,
            consumer_wallet.address,
            consumer_wallet.address,
            ZERO_ADDRESS,
        ],
        uints=[web3.toWei("0.5", "ether"), 0],
        bytess=[b""],
    )
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_token.create_erc20(erc_create_data, consumer_wallet)
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721Template: NOT "
        "ERC20DEPLOYER_ROLE"
    )


def test_erc721_data_token_functions(web3, config, publisher_wallet, consumer_wallet):
    """Tests ERC721 Template functions for ERC20 tokens."""
    erc721_token, erc20_token = deploy_erc721_erc20(
        web3, config, publisher_wallet, publisher_wallet
    )
    assert len(erc721_token.get_tokens_list()) == 1
    assert erc721_token.is_deployed(erc20_token.address) is True

    erc721_token_v2 = deploy_erc721_erc20(web3, config, publisher_wallet)
    assert erc721_token_v2.is_deployed(consumer_wallet.address) is False

    erc721_token.set_base_uri("https://newurl.com/nft/", publisher_wallet)
    assert erc721_token.token_uri(1) == "https://newurl.com/nft/1"

    # Tests failing setting token URI by another user
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_token.set_base_uri("https://foourl.com/nft/", consumer_wallet)
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721Template: not NFTOwner"
    )

    # Tests transfer functions
    erc20_token.mint(
        consumer_wallet.address, web3.toWei("0.2", "ether"), publisher_wallet
    )
    assert erc20_token.balanceOf(consumer_wallet.address) == web3.toWei("0.2", "ether")
    assert erc721_token.owner_of(1) == publisher_wallet.address

    erc721_token.transfer_from(
        publisher_wallet.address, consumer_wallet.address, 1, publisher_wallet
    )
    assert erc721_token.balance_of(publisher_wallet.address) == 0
    assert erc721_token.owner_of(1) == consumer_wallet.address
    assert (
        erc721_token.get_permissions(consumer_wallet.address)[
            ERC721Permissions.DEPLOY_ERC20
        ]
        is True
    )
    erc_create_data = ErcCreateData(
        template_index=1,
        strings=["ERC20DT1", "ERC20DT1Symbol"],
        addresses=[
            publisher_wallet.address,
            consumer_wallet.address,
            publisher_wallet.address,
            ZERO_ADDRESS,
        ],
        uints=[web3.toWei("0.5", "ether"), 0],
        bytess=[b""],
    )
    erc721_token.create_erc20(erc_create_data, consumer_wallet)
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc20_token.mint(
            consumer_wallet.address, web3.toWei(1, "ether"), consumer_wallet
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC20Template: NOT MINTER"
    )

    erc20_token.add_minter(consumer_wallet.address, consumer_wallet)
    erc20_token.mint(
        consumer_wallet.address, web3.toWei("0.2", "ether"), consumer_wallet
    )
    assert erc20_token.balanceOf(consumer_wallet.address) == web3.toWei("0.4", "ether")


def test_fail_transfer_function(web3, config, publisher_wallet, consumer_wallet):
    """Tests failure of using the transfer functions."""
    erc721_token = deploy_erc721_erc20(web3, config, publisher_wallet)
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_token.transfer_from(
            publisher_wallet.address, consumer_wallet.address, 1, consumer_wallet
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721: transfer caller is not "
        "owner nor approved"
    )

    # Tests for safe transfer as well
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_token.safe_transfer_from(
            publisher_wallet.address, consumer_wallet.address, 1, consumer_wallet
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721: transfer caller is not "
        "owner nor approved"
    )
