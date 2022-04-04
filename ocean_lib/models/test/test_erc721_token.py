#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from web3 import exceptions

from ocean_lib.models.bpool import BPool
from ocean_lib.models.erc20_token import ERC20Token
from ocean_lib.models.erc721_factory import ERC721FactoryContract
from ocean_lib.models.erc721_nft import ERC721NFT, ERC721Permissions
from ocean_lib.models.fixed_rate_exchange import (
    FixedRateExchange,
    FixedRateExchangeDetails,
)
from ocean_lib.web3_internal.constants import BLOB, ZERO_ADDRESS
from ocean_lib.web3_internal.currency import to_wei
from tests.resources.helper_functions import deploy_erc721_erc20, get_address_of_type


@pytest.mark.unit
def test_properties(web3, config):
    """Tests the events' properties."""
    erc721_token_address = get_address_of_type(
        config=config, address_type=ERC721NFT.CONTRACT_NAME
    )
    erc721_nft = ERC721NFT(web3=web3, address=erc721_token_address)

    assert erc721_nft.event_TokenCreated.abi["name"] == ERC721NFT.EVENT_TOKEN_CREATED
    assert (
        erc721_nft.event_TokenURIUpdate.abi["name"] == ERC721NFT.EVENT_TOKEN_URI_UPDATED
    )
    assert (
        erc721_nft.event_MetadataCreated.abi["name"] == ERC721NFT.EVENT_METADATA_CREATED
    )
    assert (
        erc721_nft.event_MetadataUpdated.abi["name"] == ERC721NFT.EVENT_METADATA_UPDATED
    )
    assert (
        erc721_nft.event_MetadataValidated.abi["name"]
        == ERC721NFT.EVENT_METADATA_VALIDATED
    )


@pytest.mark.unit
def test_permissions(
    web3, config, publisher_wallet, consumer_wallet, another_consumer_wallet
):
    """Tests permissions' functions."""
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


@pytest.mark.unit
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

    tx = erc721_nft.set_metadata(
        metadata_state=1,
        metadata_decryptor_url="http://myprovider:8030",
        metadata_decryptor_address="0x123",
        flags=web3.toBytes(hexstr=BLOB),
        data=web3.toBytes(hexstr=BLOB),
        data_hash=web3.toBytes(hexstr=BLOB),
        metadata_proofs=[],
        from_wallet=consumer_wallet,
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

    tx = erc721_nft.set_metadata(
        metadata_state=1,
        metadata_decryptor_url="http://foourl",
        metadata_decryptor_address="0x123",
        flags=web3.toBytes(hexstr=BLOB),
        data=web3.toBytes(hexstr=BLOB),
        data_hash=web3.toBytes(hexstr=BLOB),
        metadata_proofs=[],
        from_wallet=consumer_wallet,
    )
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
    tx = erc721_nft.set_metadata_token_uri(
        metadata_state=1,
        metadata_decryptor_url="http://foourl",
        metadata_decryptor_address="0x123",
        flags=web3.toBytes(hexstr=BLOB),
        data=web3.toBytes(hexstr=BLOB),
        data_hash=web3.toBytes(hexstr=BLOB),
        token_id=1,
        token_uri="https://anothernewurl.com/nft/",
        metadata_proofs=[],
        from_wallet=publisher_wallet,
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

    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_nft.set_metadata(
            metadata_state=1,
            metadata_decryptor_url="http://myprovider:8030",
            metadata_decryptor_address="0x123",
            flags=web3.toBytes(hexstr=BLOB),
            data=web3.toBytes(hexstr=BLOB),
            data_hash=web3.toBytes(hexstr=BLOB),
            metadata_proofs=[],
            from_wallet=consumer_wallet,
        )

    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721Template: NOT METADATA_ROLE"
    )


@pytest.mark.unit
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

    tx = erc721_nft.create_erc20(
        template_index=1,
        name="ERC20DT1",
        symbol="ERC20DT1Symbol",
        minter=publisher_wallet.address,
        fee_manager=consumer_wallet.address,
        publish_market_order_fee_address=publisher_wallet.address,
        publish_market_order_fee_token=ZERO_ADDRESS,
        cap=to_wei("0.5"),
        publish_market_order_fee_amount=0,
        bytess=[b""],
        from_wallet=publisher_wallet,
    )
    assert tx, "Could not create ERC20."


@pytest.mark.unit
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
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_nft.create_erc20(
            template_index=1,
            name="ERC20DT1",
            symbol="ERC20DT1Symbol",
            minter=publisher_wallet.address,
            fee_manager=consumer_wallet.address,
            publish_market_order_fee_address=publisher_wallet.address,
            publish_market_order_fee_token=ZERO_ADDRESS,
            cap=to_wei("0.5"),
            publish_market_order_fee_amount=0,
            bytess=[b""],
            from_wallet=consumer_wallet,
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721Template: NOT "
        "ERC20DEPLOYER_ROLE"
    )


@pytest.mark.unit
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
        event_name=ERC721NFT.EVENT_TOKEN_URI_UPDATED,
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
    erc721_nft.create_erc20(
        template_index=1,
        name="ERC20DT1",
        symbol="ERC20DT1Symbol",
        minter=publisher_wallet.address,
        fee_manager=consumer_wallet.address,
        publish_market_order_fee_address=publisher_wallet.address,
        publish_market_order_fee_token=ZERO_ADDRESS,
        cap=to_wei("0.5"),
        publish_market_order_fee_amount=0,
        bytess=[b""],
        from_wallet=consumer_wallet,
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


@pytest.mark.unit
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


def test_transfer_nft(web3, config, publisher_wallet, consumer_wallet, factory_router):
    """Tests transferring the NFT before deploying an ERC20, a pool, a FRE."""
    erc721_factory_address = get_address_of_type(
        config, ERC721FactoryContract.CONTRACT_NAME
    )
    erc721_factory = ERC721FactoryContract(web3, erc721_factory_address)

    tx = erc721_factory.deploy_erc721_contract(
        name="NFT to TRANSFER",
        symbol="NFTtT",
        template_index=1,
        additional_metadata_updater=ZERO_ADDRESS,
        additional_erc20_deployer=consumer_wallet.address,
        token_uri="https://oceanprotocol.com/nft/",
        transferable=True,
        owner=publisher_wallet.address,
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
    assert erc721_nft.contract.caller.name() == "NFT to TRANSFER"
    assert erc721_nft.symbol() == "NFTtT"

    tx = erc721_nft.safe_transfer_from(
        publisher_wallet.address,
        consumer_wallet.address,
        token_id=1,
        from_wallet=publisher_wallet,
    )
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    transfer_event = erc721_nft.get_event_log(
        ERC721FactoryContract.EVENT_TRANSFER,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    assert transfer_event[0].event == "Transfer"
    assert transfer_event[0].args["from"] == publisher_wallet.address
    assert transfer_event[0].args.to == consumer_wallet.address
    assert erc721_nft.balance_of(consumer_wallet.address) == 1
    assert erc721_nft.balance_of(publisher_wallet.address) == 0
    assert erc721_nft.is_erc20_deployer(consumer_wallet.address) is True
    assert erc721_nft.owner_of(1) == consumer_wallet.address

    # Consumer is not the additional ERC20 deployer, but will be after the NFT transfer
    tx = erc721_factory.deploy_erc721_contract(
        name="NFT1",
        symbol="NFT",
        template_index=1,
        additional_metadata_updater=ZERO_ADDRESS,
        additional_erc20_deployer=ZERO_ADDRESS,
        token_uri="https://oceanprotocol.com/nft/",
        transferable=True,
        owner=publisher_wallet.address,
        from_wallet=publisher_wallet,
    )
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    registered_event = erc721_factory.get_event_log(
        ERC721FactoryContract.EVENT_NFT_CREATED,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    token_address = registered_event[0].args.newTokenAddress
    erc721_nft = ERC721NFT(web3, token_address)
    tx = erc721_nft.safe_transfer_from(
        publisher_wallet.address,
        consumer_wallet.address,
        token_id=1,
        from_wallet=publisher_wallet,
    )
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    transfer_event = erc721_nft.get_event_log(
        ERC721FactoryContract.EVENT_TRANSFER,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    assert transfer_event[0].event == "Transfer"
    assert transfer_event[0].args["from"] == publisher_wallet.address
    assert transfer_event[0].args.to == consumer_wallet.address
    assert erc721_nft.is_erc20_deployer(consumer_wallet.address)

    # Creates an ERC20
    tx_result = erc721_nft.create_erc20(
        template_index=1,
        name="ERC20DT1",
        symbol="ERC20DT1Symbol",
        minter=consumer_wallet.address,
        fee_manager=consumer_wallet.address,
        publish_market_order_fee_address=publisher_wallet.address,
        publish_market_order_fee_token=ZERO_ADDRESS,
        cap=to_wei(200),
        publish_market_order_fee_amount=0,
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
    erc20_token = ERC20Token(web3, erc20_address)

    assert erc20_token.is_minter(publisher_wallet.address) is False
    assert erc20_token.is_minter(consumer_wallet.address) is True
    erc20_token.add_minter(publisher_wallet.address, consumer_wallet)
    assert (
        erc20_token.get_permissions(publisher_wallet.address)[0] is True
    )  # publisher is minter now

    _, base_token = deploy_erc721_erc20(
        web3, config, consumer_wallet, consumer_wallet, cap=to_wei(250)
    )

    # Make consumer the publish_market_order_fee_address instead of publisher
    tx_result = erc20_token.set_publishing_market_fee(
        consumer_wallet.address, base_token.address, to_wei(1), publisher_wallet
    )

    assert tx_result, "Failed to set the publish fee."
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_result)
    set_publishing_fee_event = erc20_token.get_event_log(
        ERC20Token.EVENT_PUBLISH_MARKET_FEE_CHANGED,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    assert set_publishing_fee_event, "Cannot find PublishMarketFeeChanged event."
    publish_fees = erc20_token.get_publishing_market_fee()
    assert publish_fees[0] == consumer_wallet.address
    assert publish_fees[1] == base_token.address
    assert publish_fees[2] == to_wei(1)

    # The newest owner of the NFT (consumer wallet) can deploy a pool
    base_token.mint(consumer_wallet.address, to_wei(200), consumer_wallet)
    assert base_token.balanceOf(consumer_wallet.address) == to_wei(200)
    base_token.approve(factory_router.address, to_wei(10000), consumer_wallet)
    tx = erc20_token.deploy_pool(
        rate=to_wei(1),
        base_token_decimals=base_token.decimals(),
        vesting_amount=to_wei(10),
        vesting_blocks=2500000,
        base_token_amount=to_wei(100),
        lp_swap_fee_amount=to_wei("0.003"),
        publish_market_swap_fee_amount=to_wei("0.001"),
        ss_contract=get_address_of_type(config, "Staking"),
        base_token_address=base_token.address,
        base_token_sender=consumer_wallet.address,
        publisher_address=consumer_wallet.address,
        publish_market_swap_fee_collector=publisher_wallet.address,
        pool_template_address=get_address_of_type(config, "poolTemplate"),
        from_wallet=consumer_wallet,
    )
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    pool_event = factory_router.get_event_log(
        ERC721FactoryContract.EVENT_NEW_POOL,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    assert pool_event[0].event == "NewPool"
    bpool_address = pool_event[0].args.poolAddress
    bpool = BPool(web3, bpool_address)
    assert bpool.is_finalized() is True
    assert bpool.opc_fee() == to_wei("0.002")
    assert bpool.get_swap_fee() == to_wei("0.003")
    assert bpool.community_fee(base_token.address) == 0
    assert bpool.community_fee(erc20_token.address) == 0
    assert bpool.publish_market_fee(base_token.address) == 0
    assert bpool.publish_market_fee(erc20_token.address) == 0

    base_token.approve(bpool_address, to_wei(1000000), consumer_wallet)
    tx = bpool.join_swap_extern_amount_in(
        token_amount_in=to_wei(10),
        min_pool_amount_out=to_wei(1),
        from_wallet=consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    join_event = bpool.get_event_log(
        BPool.EVENT_LOG_JOIN,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    assert join_event[0].args.caller == consumer_wallet.address
    assert join_event[0].args.tokenIn == base_token.address
    assert join_event[0].args.tokenAmountIn == to_wei(10)

    bpt_event = bpool.get_event_log(
        BPool.EVENT_LOG_BPT, tx_receipt.blockNumber, web3.eth.block_number, None
    )
    assert bpt_event[0].args.bptAmount  # amount in pool shares
    assert bpool.get_balance(base_token.address) == to_wei(100) + to_wei(10)

    amount_out = bpool.get_amount_out_exact_in(
        base_token.address, erc20_token.address, to_wei(20), to_wei("0.01")
    )[0]
    tx = bpool.swap_exact_amount_in(
        token_in=base_token.address,
        token_out=erc20_token.address,
        consume_market_swap_fee_address=consumer_wallet.address,
        token_amount_in=to_wei(20),
        min_amount_out=to_wei(5),
        max_price=to_wei(1000000),
        consume_market_swap_fee_amount=to_wei("0.01"),
        from_wallet=consumer_wallet,
    )
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    swap_event = bpool.get_event_log(
        BPool.EVENT_LOG_SWAP,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert swap_event[0].args.caller == consumer_wallet.address
    assert swap_event[0].args.tokenIn == base_token.address
    assert swap_event[0].args.tokenAmountIn == to_wei(20)
    assert swap_event[0].args.tokenAmountOut == amount_out

    tx = bpool.exit_swap_pool_amount_in(
        pool_amount_in=bpt_event[0].args.bptAmount,
        min_amount_out=to_wei(10),
        from_wallet=consumer_wallet,
    )
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    exit_event = bpool.get_event_log(
        BPool.EVENT_LOG_EXIT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    assert exit_event[0].args.caller == consumer_wallet.address
    assert exit_event[0].args.tokenOut == base_token.address

    bpt_event = bpool.get_event_log(
        BPool.EVENT_LOG_BPT, tx_receipt.blockNumber, web3.eth.block_number, None
    )
    assert bpt_event[0].args.bptAmount  # amount in pool shares

    # The newest owner of the NFT (consumer wallet) has ERC20 deployer role & can deploy a FRE
    fixed_exchange = FixedRateExchange(web3, get_address_of_type(config, "FixedPrice"))
    number_of_exchanges = fixed_exchange.get_number_of_exchanges()
    tx = erc20_token.create_fixed_rate(
        fixed_price_address=fixed_exchange.address,
        base_token_address=base_token.address,
        owner=consumer_wallet.address,
        publish_market_swap_fee_collector=consumer_wallet.address,
        allowed_swapper=ZERO_ADDRESS,
        base_token_decimals=18,
        datatoken_decimals=18,
        fixed_rate=to_wei(1),
        publish_market_swap_fee_amount=to_wei("0.001"),
        with_mint=0,
        from_wallet=consumer_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    fre_event = erc20_token.get_event_log(
        event_name=ERC721FactoryContract.EVENT_NEW_FIXED_RATE,
        from_block=tx_receipt.blockNumber,
        to_block=web3.eth.block_number,
        filters=None,
    )

    assert fixed_exchange.get_number_of_exchanges() == number_of_exchanges + 1
    assert fre_event[0].args.owner == consumer_wallet.address

    exchange_id = fre_event[0].args.exchangeId

    # Exchange should have supply and fees setup
    exchange_details = fixed_exchange.get_exchange(exchange_id)
    assert (
        exchange_details[FixedRateExchangeDetails.EXCHANGE_OWNER]
        == consumer_wallet.address
    )
    assert exchange_details[FixedRateExchangeDetails.DATATOKEN] == erc20_token.address
    assert (
        exchange_details[FixedRateExchangeDetails.DT_DECIMALS] == erc20_token.decimals()
    )
    assert exchange_details[FixedRateExchangeDetails.BASE_TOKEN] == base_token.address
    assert (
        exchange_details[FixedRateExchangeDetails.BT_DECIMALS] == base_token.decimals()
    )
    assert exchange_details[FixedRateExchangeDetails.FIXED_RATE] == to_wei(1)
    assert exchange_details[FixedRateExchangeDetails.ACTIVE] is True
    assert exchange_details[FixedRateExchangeDetails.DT_SUPPLY] == 0
    assert exchange_details[FixedRateExchangeDetails.BT_SUPPLY] == 0
    assert exchange_details[FixedRateExchangeDetails.DT_BALANCE] == 0
    assert exchange_details[FixedRateExchangeDetails.BT_BALANCE] == 0
    assert exchange_details[FixedRateExchangeDetails.WITH_MINT] is False


def test_transfer_nft_with_erc20_pool_fre(
    web3, config, publisher_wallet, consumer_wallet, factory_router
):
    """Tests transferring the NFT after deploying an ERC20, a pool, a FRE."""
    erc721_factory_address = get_address_of_type(
        config, ERC721FactoryContract.CONTRACT_NAME
    )
    erc721_factory = ERC721FactoryContract(web3, erc721_factory_address)

    tx = erc721_factory.deploy_erc721_contract(
        name="NFT to TRANSFER",
        symbol="NFTtT",
        template_index=1,
        additional_metadata_updater=ZERO_ADDRESS,
        additional_erc20_deployer=consumer_wallet.address,
        token_uri="https://oceanprotocol.com/nft/",
        transferable=True,
        owner=publisher_wallet.address,
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
    assert erc721_nft.contract.caller.name() == "NFT to TRANSFER"
    assert erc721_nft.symbol() == "NFTtT"

    # Creates an ERC20
    tx_result = erc721_nft.create_erc20(
        template_index=1,
        name="ERC20DT1",
        symbol="ERC20DT1Symbol",
        minter=publisher_wallet.address,
        fee_manager=publisher_wallet.address,
        publish_market_order_fee_address=publisher_wallet.address,
        publish_market_order_fee_token=ZERO_ADDRESS,
        cap=to_wei(200),
        publish_market_order_fee_amount=0,
        bytess=[b""],
        from_wallet=publisher_wallet,
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
    erc20_token = ERC20Token(web3, erc20_address)

    assert erc20_token.is_minter(publisher_wallet.address) is True

    _, base_token = deploy_erc721_erc20(
        web3, config, publisher_wallet, publisher_wallet, cap=to_wei(250)
    )

    # The owner of the NFT (publisher wallet) has ERC20 deployer role & can deploy a pool
    base_token.mint(publisher_wallet.address, to_wei(200), publisher_wallet)
    assert base_token.balanceOf(publisher_wallet.address) == to_wei(200)
    base_token.approve(factory_router.address, to_wei(10000), publisher_wallet)
    tx = erc20_token.deploy_pool(
        rate=to_wei(1),
        base_token_decimals=base_token.decimals(),
        vesting_amount=to_wei(10),
        vesting_blocks=2500000,
        base_token_amount=to_wei(100),
        lp_swap_fee_amount=to_wei("0.003"),
        publish_market_swap_fee_amount=to_wei("0.001"),
        ss_contract=get_address_of_type(config, "Staking"),
        base_token_address=base_token.address,
        base_token_sender=publisher_wallet.address,
        publisher_address=publisher_wallet.address,
        publish_market_swap_fee_collector=publisher_wallet.address,
        pool_template_address=get_address_of_type(config, "poolTemplate"),
        from_wallet=publisher_wallet,
    )
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    pool_event = factory_router.get_event_log(
        ERC721FactoryContract.EVENT_NEW_POOL,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    assert pool_event[0].event == "NewPool"
    bpool_address = pool_event[0].args.poolAddress
    bpool = BPool(web3, bpool_address)
    assert bpool.is_finalized() is True
    assert bpool.opc_fee() == to_wei("0.002")
    assert bpool.get_swap_fee() == to_wei("0.003")
    assert bpool.community_fee(base_token.address) == 0
    assert bpool.community_fee(erc20_token.address) == 0
    assert bpool.publish_market_fee(base_token.address) == 0
    assert bpool.publish_market_fee(erc20_token.address) == 0

    base_token.approve(bpool_address, to_wei(1000000), publisher_wallet)
    tx = bpool.join_swap_extern_amount_in(
        token_amount_in=to_wei(10),
        min_pool_amount_out=to_wei(1),
        from_wallet=publisher_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    join_event = bpool.get_event_log(
        BPool.EVENT_LOG_JOIN,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    assert join_event[0].args.caller == publisher_wallet.address
    assert join_event[0].args.tokenIn == base_token.address
    assert join_event[0].args.tokenAmountIn == to_wei(10)

    bpt_event = bpool.get_event_log(
        BPool.EVENT_LOG_BPT, tx_receipt.blockNumber, web3.eth.block_number, None
    )
    assert bpt_event[0].args.bptAmount  # amount in pool shares
    assert bpool.get_balance(base_token.address) == to_wei(100) + to_wei(10)

    # The owner of the NFT (publisher wallet) has ERC20 deployer role & can deploy a FRE
    fixed_exchange = FixedRateExchange(web3, get_address_of_type(config, "FixedPrice"))
    number_of_exchanges = fixed_exchange.get_number_of_exchanges()
    tx = erc20_token.create_fixed_rate(
        fixed_price_address=fixed_exchange.address,
        base_token_address=base_token.address,
        owner=publisher_wallet.address,
        publish_market_swap_fee_collector=publisher_wallet.address,
        allowed_swapper=ZERO_ADDRESS,
        base_token_decimals=18,
        datatoken_decimals=18,
        fixed_rate=to_wei(1),
        publish_market_swap_fee_amount=to_wei("0.001"),
        with_mint=0,
        from_wallet=publisher_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)

    fre_event = erc20_token.get_event_log(
        event_name=ERC721FactoryContract.EVENT_NEW_FIXED_RATE,
        from_block=tx_receipt.blockNumber,
        to_block=web3.eth.block_number,
        filters=None,
    )

    assert fixed_exchange.get_number_of_exchanges() == number_of_exchanges + 1
    assert fre_event[0].args.owner == publisher_wallet.address

    exchange_id = fre_event[0].args.exchangeId

    exchange_details = fixed_exchange.get_exchange(exchange_id)
    assert (
        exchange_details[FixedRateExchangeDetails.EXCHANGE_OWNER]
        == publisher_wallet.address
    )
    assert exchange_details[FixedRateExchangeDetails.DATATOKEN] == erc20_token.address
    assert (
        exchange_details[FixedRateExchangeDetails.DT_DECIMALS] == erc20_token.decimals()
    )
    assert exchange_details[FixedRateExchangeDetails.BASE_TOKEN] == base_token.address
    assert (
        exchange_details[FixedRateExchangeDetails.BT_DECIMALS] == base_token.decimals()
    )
    assert exchange_details[FixedRateExchangeDetails.FIXED_RATE] == to_wei(1)
    assert exchange_details[FixedRateExchangeDetails.ACTIVE] is True
    assert exchange_details[FixedRateExchangeDetails.DT_SUPPLY] == 0
    assert exchange_details[FixedRateExchangeDetails.BT_SUPPLY] == 0
    assert exchange_details[FixedRateExchangeDetails.DT_BALANCE] == 0
    assert exchange_details[FixedRateExchangeDetails.BT_BALANCE] == 0
    assert exchange_details[FixedRateExchangeDetails.WITH_MINT] is False

    tx = erc721_nft.safe_transfer_from(
        publisher_wallet.address,
        consumer_wallet.address,
        token_id=1,
        from_wallet=publisher_wallet,
    )
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    transfer_event = erc721_nft.get_event_log(
        ERC721FactoryContract.EVENT_TRANSFER,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    assert transfer_event[0].event == "Transfer"
    assert transfer_event[0].args["from"] == publisher_wallet.address
    assert transfer_event[0].args.to == consumer_wallet.address
    assert erc721_nft.balance_of(consumer_wallet.address) == 1
    assert erc721_nft.balance_of(publisher_wallet.address) == 0
    assert erc721_nft.is_erc20_deployer(consumer_wallet.address) is True
    assert erc721_nft.owner_of(1) == consumer_wallet.address
    permissions = erc20_token.get_permissions(consumer_wallet.address)
    assert permissions[0] is False  # the newest owner is not the minter
    erc20_token.add_minter(consumer_wallet.address, consumer_wallet)
    assert erc20_token.permissions(consumer_wallet.address)[0] is True

    # Consumer wallet is not the publish market fee collector
    with pytest.raises(exceptions.ContractLogicError) as err:
        bpool.update_publish_market_fee(
            consumer_wallet.address, to_wei("0.1"), consumer_wallet
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ONLY MARKET COLLECTOR"
    )

    # Consumer wallet has not become the owner of the publisher's exchange
    exchange_details = fixed_exchange.get_exchange(exchange_id)
    assert (
        exchange_details[FixedRateExchangeDetails.EXCHANGE_OWNER]
        == publisher_wallet.address
    )
    assert exchange_details[FixedRateExchangeDetails.ACTIVE] is True
