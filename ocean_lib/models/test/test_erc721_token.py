#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from web3 import exceptions

from ocean_lib.models.erc721_factory import ERC721FactoryContract
from ocean_lib.models.erc721_nft import ERC721Permissions, ERC721Token
from ocean_lib.models.models_structures import (
    ChainMetadata,
    ChainMetadataWithTokenUri,
    CreateErc20Data,
)
from ocean_lib.web3_internal.constants import BLOB, ZERO_ADDRESS
from ocean_lib.web3_internal.currency import to_wei
from tests.resources.helper_functions import deploy_erc721_erc20, get_address_of_type


def test_properties(web3, config):
    """Tests the events' properties."""
    erc721_token_address = get_address_of_type(
        config=config, address_type=ERC721Token.CONTRACT_NAME
    )
    erc721_nft = ERC721Token(web3=web3, address=erc721_token_address)

    assert (
        erc721_nft.event_TokenCreated.abi["name"] == ERC721Token.EVENT_TOKEN_CREATED
    )
    assert (
        erc721_nft.event_TokenURIUpdate.abi["name"]
        == ERC721Token.EVENT_TOKEN_URI_UPDATED
    )
    assert (
        erc721_nft.event_MetadataCreated.abi["name"]
        == ERC721Token.EVENT_METADATA_CREATED
    )
    assert (
        erc721_nft.event_MetadataUpdated.abi["name"]
        == ERC721Token.EVENT_METADATA_UPDATED
    )


def test_permissions(
    web3, config, publisher_wallet, consumer_wallet, another_consumer_wallet
):
    """Tests permissions' functions."""
    erc721_factory_address = get_address_of_type(
        config=config, address_type=ERC721FactoryContract.CONTRACT_NAME
    )
    erc721_nft = deploy_erc721_erc20(
        web3=web3, config=config, erc721_publisher=publisher_wallet
    )
    assert erc721_nft.contract.caller.name() == "NFT"
    assert erc721_nft.symbol() == "NFTSYMBOL"
    assert erc721_nft.balance_of(account=publisher_wallet.address) == 1

    # Tests if the NFT was initialized
    assert erc721_nft.is_initialized() is True

    # Tests adding a manager successfully
    erc721_nft.add_manager(
        manager_address=consumer_wallet.address, from_wallet=publisher_wallet
    )
    assert (
        erc721_nft.get_permissions(user=consumer_wallet.address)[
            ERC721Permissions.MANAGER
        ]
        is True
    )

    assert erc721_nft.token_uri(1) == "https://oceanprotocol.com/nft/"

    # Tests failing to re-initialize the contract
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_nft.initialize(
            owner=publisher_wallet.address,
            name="NewName",
            symbol="NN",
            token_factory_address=erc721_factory_address,
            additional_erc20_deployer=ZERO_ADDRESS,
            token_uri="https://oceanprotocol.com/nft/",
            from_wallet=publisher_wallet,
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721Template: token instance "
        "already initialized"
    )

    # Tests failing clearing permissions
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_nft.clean_permissions(from_wallet=another_consumer_wallet)
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721Template: not NFTOwner"
    )

    # Tests clearing permissions
    erc721_nft.add_to_create_erc20_list(
        allowed_address=publisher_wallet.address, from_wallet=publisher_wallet
    )
    erc721_nft.add_to_create_erc20_list(
        allowed_address=another_consumer_wallet.address, from_wallet=publisher_wallet
    )
    assert (
        erc721_nft.get_permissions(user=publisher_wallet.address)[
            ERC721Permissions.DEPLOY_ERC20
        ]
        is True
    )
    assert (
        erc721_nft.get_permissions(user=another_consumer_wallet.address)[
            ERC721Permissions.DEPLOY_ERC20
        ]
        is True
    )
    # Still is not the NFT owner, cannot clear permissions then
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_nft.clean_permissions(from_wallet=another_consumer_wallet)
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721Template: not NFTOwner"
    )

    erc721_nft.clean_permissions(from_wallet=publisher_wallet)

    assert (
        erc721_nft.get_permissions(user=publisher_wallet.address)[
            ERC721Permissions.DEPLOY_ERC20
        ]
        is False
    )
    assert (
        erc721_nft.get_permissions(user=consumer_wallet.address)[
            ERC721Permissions.MANAGER
        ]
        is False
    )
    assert (
        erc721_nft.get_permissions(user=another_consumer_wallet.address)[
            ERC721Permissions.DEPLOY_ERC20
        ]
        is False
    )

    # Tests failing adding a new manager by another user different from the NFT owner
    erc721_nft.add_manager(
        manager_address=publisher_wallet.address, from_wallet=publisher_wallet
    )
    assert (
        erc721_nft.get_permissions(user=publisher_wallet.address)[
            ERC721Permissions.MANAGER
        ]
        is True
    )
    assert (
        erc721_nft.get_permissions(user=consumer_wallet.address)[
            ERC721Permissions.MANAGER
        ]
        is False
    )
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_nft.add_manager(
            manager_address=another_consumer_wallet.address, from_wallet=consumer_wallet
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721Template: not NFTOwner"
    )
    assert (
        erc721_nft.get_permissions(user=another_consumer_wallet.address)[
            ERC721Permissions.MANAGER
        ]
        is False
    )

    # Tests removing manager
    erc721_nft.add_manager(
        manager_address=consumer_wallet.address, from_wallet=publisher_wallet
    )
    assert (
        erc721_nft.get_permissions(user=consumer_wallet.address)[
            ERC721Permissions.MANAGER
        ]
        is True
    )
    erc721_nft.remove_manager(
        manager_address=consumer_wallet.address, from_wallet=publisher_wallet
    )
    assert (
        erc721_nft.get_permissions(user=consumer_wallet.address)[
            ERC721Permissions.MANAGER
        ]
        is False
    )

    # Tests failing removing a manager if it has not the NFT owner role
    erc721_nft.add_manager(
        manager_address=consumer_wallet.address, from_wallet=publisher_wallet
    )
    assert (
        erc721_nft.get_permissions(user=consumer_wallet.address)[
            ERC721Permissions.MANAGER
        ]
        is True
    )
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_nft.remove_manager(
            manager_address=publisher_wallet.address, from_wallet=consumer_wallet
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721Template: not NFTOwner"
    )
    assert (
        erc721_nft.get_permissions(user=publisher_wallet.address)[
            ERC721Permissions.MANAGER
        ]
        is True
    )

    # Tests removing the NFT owner from the manager role
    erc721_nft.remove_manager(
        manager_address=publisher_wallet.address, from_wallet=publisher_wallet
    )
    assert (
        erc721_nft.get_permissions(user=publisher_wallet.address)[
            ERC721Permissions.MANAGER
        ]
        is False
    )
    erc721_nft.add_manager(
        manager_address=publisher_wallet.address, from_wallet=publisher_wallet
    )
    assert (
        erc721_nft.get_permissions(user=publisher_wallet.address)[
            ERC721Permissions.MANAGER
        ]
        is True
    )

    # Tests failing calling execute_call function if the user is not manager
    assert (
        erc721_nft.get_permissions(user=another_consumer_wallet.address)[
            ERC721Permissions.MANAGER
        ]
        is False
    )
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_nft.execute_call(
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
        erc721_nft.get_permissions(user=publisher_wallet.address)[
            ERC721Permissions.MANAGER
        ]
        is True
    )
    tx = erc721_nft.execute_call(
        operation=0,
        to=consumer_wallet.address,
        value=10,
        data=web3.toHex(text="SomeData"),
        from_wallet=consumer_wallet,
    )
    assert tx, "Could not execute call to consumer."

    # Tests setting new data
    erc721_nft.add_to_725_store_list(
        allowed_address=consumer_wallet.address, from_wallet=publisher_wallet
    )
    assert (
        erc721_nft.get_permissions(user=consumer_wallet.address)[
            ERC721Permissions.STORE
        ]
        is True
    )
    erc721_nft.set_new_data(
        key=web3.keccak(text="ARBITRARY_KEY"),
        value=web3.toHex(text="SomeData"),
        from_wallet=consumer_wallet,
    )
    assert erc721_nft.get_data(key=web3.keccak(text="ARBITRARY_KEY")) == b"SomeData"

    # Tests failing setting new data if user has not STORE UPDATER role.
    assert (
        erc721_nft.get_permissions(user=another_consumer_wallet.address)[
            ERC721Permissions.STORE
        ]
        is False
    )
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_nft.set_new_data(
            key=web3.keccak(text="ARBITRARY_KEY"),
            value=web3.toHex(text="SomeData"),
            from_wallet=another_consumer_wallet,
        )

    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721Template: NOT STORE UPDATER"
    )

    # Tests failing setting ERC20 data
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_nft.set_data_erc20(
            key=web3.keccak(text="FOO_KEY"),
            value=web3.toHex(text="SomeData"),
            from_wallet=consumer_wallet,
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721Template: NOT ERC20 Contract"
    )
    assert erc721_nft.get_data(key=web3.keccak(text="FOO_KEY")) == b""


def test_success_update_metadata(web3, config, publisher_wallet, consumer_wallet):
    """Tests updating the metadata flow."""
    erc721_nft = deploy_erc721_erc20(
        web3=web3, config=config, erc721_publisher=publisher_wallet
    )
    assert (
        erc721_nft.get_permissions(user=consumer_wallet.address)[
            ERC721Permissions.UPDATE_METADATA
        ]
        is False
    )
    erc721_nft.add_to_metadata_list(
        allowed_address=consumer_wallet.address, from_wallet=publisher_wallet
    )
    metadata_info = erc721_nft.get_metadata()
    assert metadata_info[3] is False

    chain_metadata = ChainMetadata(
        metadata_state=1,
        metadata_decryptor_url="http://myprovider:8030",
        metadata_decryptor_address="0x123",
        flags=web3.toBytes(hexstr=BLOB),
        data=web3.toBytes(hexstr=BLOB),
        data_hash=web3.toBytes(hexstr=BLOB),
        data_proofs=[],
    )

    tx = erc721_nft.set_metadata(
        chain_metadata=chain_metadata, from_wallet=consumer_wallet
    )
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    create_metadata_event = erc721_nft.get_event_log(
        event_name="MetadataCreated",
        from_block=tx_receipt.blockNumber,
        to_block=web3.eth.block_number,
        filters=None,
    )
    assert create_metadata_event, "Cannot find MetadataCreated event."
    assert create_metadata_event[0].args.decryptorUrl == "http://myprovider:8030"

    metadata_info = erc721_nft.get_metadata()
    assert metadata_info[3] is True
    assert metadata_info[0] == "http://myprovider:8030"

    chain_metadata = ChainMetadata(
        metadata_state=1,
        metadata_decryptor_url="http://foourl",
        metadata_decryptor_address="0x123",
        flags=web3.toBytes(hexstr=BLOB),
        data=web3.toBytes(hexstr=BLOB),
        data_hash=web3.toBytes(hexstr=BLOB),
        data_proofs=[],
    )
    tx = erc721_nft.set_metadata(chain_metadata, from_wallet=consumer_wallet)
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    update_metadata_event = erc721_nft.get_event_log(
        event_name="MetadataUpdated",
        from_block=tx_receipt.blockNumber,
        to_block=web3.eth.block_number,
        filters=None,
    )
    assert update_metadata_event, "Cannot find MetadataUpdated event."
    assert update_metadata_event[0].args.decryptorUrl == "http://foourl"

    metadata_info = erc721_nft.get_metadata()
    assert metadata_info[3] is True
    assert metadata_info[0] == "http://foourl"

    # Update tokenURI and set metadata in one call
    metadata_with_token_uri = ChainMetadataWithTokenUri(
        metadata_state=1,
        metadata_decryptor_url="http://foourl",
        metadata_decryptor_address="0x123",
        flags=web3.toBytes(hexstr=BLOB),
        data=web3.toBytes(hexstr=BLOB),
        data_hash=web3.toBytes(hexstr=BLOB),
        data_proofs=[],
        token_id=1,
        token_uri="https://anothernewurl.com/nft/",
    )
    tx = erc721_nft.set_metadata_token_uri(
        metadata_with_token_uri, from_wallet=publisher_wallet
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    update_token_uri_event = erc721_nft.get_event_log(
        event_name="TokenURIUpdate",
        from_block=tx_receipt.blockNumber,
        to_block=web3.eth.block_number,
        filters=None,
    )
    assert update_token_uri_event, "Cannot find TokenURIUpdate event."
    assert update_token_uri_event[0].args.tokenURI == "https://anothernewurl.com/nft/"
    assert update_token_uri_event[0].args.updatedBy == publisher_wallet.address

    update_metadata_event = erc721_nft.get_event_log(
        event_name="MetadataUpdated",
        from_block=tx_receipt.blockNumber,
        to_block=web3.eth.block_number,
        filters=None,
    )

    assert update_metadata_event, "Cannot find MetadataUpdated event."
    assert update_metadata_event[0].args.decryptorUrl == "http://foourl"

    metadata_info = erc721_nft.get_metadata()
    assert metadata_info[3] is True
    assert metadata_info[0] == "http://foourl"


def test_fails_update_metadata(web3, config, publisher_wallet, consumer_wallet):
    """Tests failure of calling update metadata function when the role of the user is not METADATA UPDATER."""
    erc721_nft = deploy_erc721_erc20(
        web3=web3, config=config, erc721_publisher=publisher_wallet
    )
    assert (
        erc721_nft.get_permissions(user=consumer_wallet.address)[
            ERC721Permissions.UPDATE_METADATA
        ]
        is False
    )

    wrong_chain_metadata = ChainMetadata(
        metadata_state=1,
        metadata_decryptor_url="http://myprovider:8030",
        metadata_decryptor_address="0x123",
        flags=web3.toBytes(hexstr=BLOB),
        data=web3.toBytes(hexstr=BLOB),
        data_hash=web3.toBytes(hexstr=BLOB),
        data_proofs=[],
    )

    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_nft.set_metadata(
            chain_metadata=wrong_chain_metadata, from_wallet=consumer_wallet
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721Template: NOT METADATA_ROLE"
    )


def test_create_erc20(web3, config, publisher_wallet, consumer_wallet):
    """Tests calling create an ERC20 by the owner."""
    erc721_nft = deploy_erc721_erc20(
        web3=web3, config=config, erc721_publisher=publisher_wallet
    )
    assert (
        erc721_nft.get_permissions(user=publisher_wallet.address)[
            ERC721Permissions.DEPLOY_ERC20
        ]
        is True
    )

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
    tx = erc721_nft.create_erc20(
        erc_create_data=erc_create_data, from_wallet=publisher_wallet
    )
    assert tx, "Could not create ERC20."


def test_fail_creating_erc20(web3, config, publisher_wallet, consumer_wallet):
    """Tests failure for creating ERC20 token."""
    erc721_nft = deploy_erc721_erc20(
        web3=web3, config=config, erc721_publisher=publisher_wallet
    )
    assert (
        erc721_nft.get_permissions(consumer_wallet.address)[
            ERC721Permissions.DEPLOY_ERC20
        ]
        is False
    )
    erc_create_data = CreateErc20Data(
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
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_nft.create_erc20(
            erc_create_data=erc_create_data, from_wallet=consumer_wallet
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721Template: NOT "
        "ERC20DEPLOYER_ROLE"
    )


def test_erc721_datatoken_functions(web3, config, publisher_wallet, consumer_wallet):
    """Tests ERC721 Template functions for ERC20 tokens."""
    erc721_nft, erc20_token = deploy_erc721_erc20(
        web3=web3,
        config=config,
        erc721_publisher=publisher_wallet,
        erc20_minter=publisher_wallet,
    )
    assert len(erc721_nft.get_tokens_list()) == 1
    assert erc721_nft.is_deployed(datatoken=erc20_token.address) is True

    erc721_token_v2 = deploy_erc721_erc20(
        web3=web3, config=config, erc721_publisher=publisher_wallet
    )
    assert erc721_token_v2.is_deployed(datatoken=consumer_wallet.address) is False
    tx = erc721_nft.set_token_uri(
        token_id=1,
        new_token_uri="https://newurl.com/nft/",
        from_wallet=publisher_wallet,
    )
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    assert tx_receipt.status == 1
    registered_event = erc721_nft.get_event_log(
        event_name=ERC721Token.EVENT_TOKEN_URI_UPDATED,
        from_block=tx_receipt.blockNumber,
        to_block=web3.eth.block_number,
        filters=None,
    )
    assert registered_event, "Cannot find TokenURIUpdate event."
    assert registered_event[0].args.updatedBy == publisher_wallet.address
    assert registered_event[0].args.tokenID == 1
    assert registered_event[0].args.blockNumber == tx_receipt.blockNumber
    assert erc721_nft.token_uri(token_id=1) == "https://newurl.com/nft/"
    assert erc721_nft.token_uri(token_id=1) == registered_event[0].args.tokenURI

    # Tests failing setting token URI by another user
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_nft.set_token_uri(
            token_id=1,
            new_token_uri="https://foourl.com/nft/",
            from_wallet=consumer_wallet,
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721Template: not NFTOwner"
    )

    # Tests transfer functions
    erc20_token.mint(
        account_address=consumer_wallet.address,
        value=to_wei("0.2"),
        from_wallet=publisher_wallet,
    )
    assert erc20_token.balanceOf(account=consumer_wallet.address) == to_wei("0.2")
    assert erc721_nft.owner_of(token_id=1) == publisher_wallet.address

    erc721_nft.transfer_from(
        from_address=publisher_wallet.address,
        to_address=consumer_wallet.address,
        token_id=1,
        from_wallet=publisher_wallet,
    )
    assert erc721_nft.balance_of(account=publisher_wallet.address) == 0
    assert erc721_nft.owner_of(token_id=1) == consumer_wallet.address
    assert (
        erc721_nft.get_permissions(user=consumer_wallet.address)[
            ERC721Permissions.DEPLOY_ERC20
        ]
        is True
    )
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
    erc721_nft.create_erc20(
        erc_create_data=erc_create_data, from_wallet=consumer_wallet
    )
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc20_token.mint(
            account_address=consumer_wallet.address,
            value=to_wei("1"),
            from_wallet=consumer_wallet,
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC20Template: NOT MINTER"
    )

    erc20_token.add_minter(
        minter_address=consumer_wallet.address, from_wallet=consumer_wallet
    )
    erc20_token.mint(
        account_address=consumer_wallet.address,
        value=to_wei("0.2"),
        from_wallet=consumer_wallet,
    )
    assert erc20_token.balanceOf(account=consumer_wallet.address) == to_wei("0.4")


def test_fail_transfer_function(web3, config, publisher_wallet, consumer_wallet):
    """Tests failure of using the transfer functions."""
    erc721_nft = deploy_erc721_erc20(
        web3=web3, config=config, erc721_publisher=publisher_wallet
    )
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_nft.transfer_from(
            from_address=publisher_wallet.address,
            to_address=consumer_wallet.address,
            token_id=1,
            from_wallet=consumer_wallet,
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721: transfer caller is not "
        "owner nor approved"
    )

    # Tests for safe transfer as well
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_nft.safe_transfer_from(
            from_address=publisher_wallet.address,
            to_address=consumer_wallet.address,
            token_id=1,
            from_wallet=consumer_wallet,
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721: transfer caller is not "
        "owner nor approved"
    )
