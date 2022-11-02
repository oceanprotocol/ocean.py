#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from brownie.network.transaction import TransactionReceipt
from web3 import Web3

from ocean_lib.models.data_nft import DataNFT, DataNFTPermissions
from ocean_lib.models.data_nft_factory import DataNFTFactoryContract
from ocean_lib.models.datatoken import Datatoken
from ocean_lib.models.fixed_rate_exchange import (
    FixedRateExchange,
    FixedRateExchangeDetails,
)
from ocean_lib.ocean.util import get_address_of_type
from ocean_lib.web3_internal.constants import BLOB, MAX_UINT256, ZERO_ADDRESS
from ocean_lib.web3_internal.currency import to_wei


@pytest.mark.unit
def test_permissions(
    publisher_wallet,
    consumer_wallet,
    another_consumer_wallet,
    publisher_addr,
    consumer_addr,
    another_consumer_addr,
    data_nft,
):
    """Tests permissions' functions."""
    assert data_nft.contract.name() == "NFT"
    assert data_nft.symbol() == "NFTSYMBOL"
    assert data_nft.balance_of(account=publisher_addr) == 1

    # Tests if the NFT was initialized
    assert data_nft.is_initialized()

    # Tests adding a manager successfully
    data_nft.add_manager(manager_address=consumer_addr, from_wallet=publisher_wallet)
    assert data_nft.get_permissions(user=consumer_addr)[DataNFTPermissions.MANAGER]

    assert data_nft.token_uri(1) == "https://oceanprotocol.com/nft/"

    # Tests failing clearing permissions
    with pytest.raises(Exception, match="not NFTOwner"):
        data_nft.clean_permissions(from_wallet=another_consumer_wallet)

    # Tests clearing permissions
    data_nft.add_to_create_erc20_list(
        allowed_address=publisher_addr, from_wallet=publisher_wallet
    )
    data_nft.add_to_create_erc20_list(
        allowed_address=another_consumer_addr, from_wallet=publisher_wallet
    )
    assert data_nft.get_permissions(user=publisher_addr)[
        DataNFTPermissions.DEPLOY_DATATOKEN
    ]
    assert data_nft.get_permissions(user=another_consumer_addr)[
        DataNFTPermissions.DEPLOY_DATATOKEN
    ]
    # Still is not the NFT owner, cannot clear permissions then
    with pytest.raises(Exception, match="not NFTOwner"):
        data_nft.clean_permissions(from_wallet=another_consumer_wallet)

    data_nft.clean_permissions(from_wallet=publisher_wallet)

    assert not (
        data_nft.get_permissions(user=publisher_addr)[
            DataNFTPermissions.DEPLOY_DATATOKEN
        ]
    )
    assert not (
        data_nft.get_permissions(user=consumer_addr)[DataNFTPermissions.MANAGER]
    )
    assert not (
        data_nft.get_permissions(user=another_consumer_addr)[
            DataNFTPermissions.DEPLOY_DATATOKEN
        ]
    )

    # Tests failing adding a new manager by another user different from the NFT owner
    data_nft.add_manager(manager_address=publisher_addr, from_wallet=publisher_wallet)
    assert data_nft.get_permissions(user=publisher_addr)[DataNFTPermissions.MANAGER]
    assert not (
        data_nft.get_permissions(user=consumer_addr)[DataNFTPermissions.MANAGER]
    )
    with pytest.raises(Exception, match="not NFTOwner"):
        data_nft.add_manager(
            manager_address=another_consumer_addr, from_wallet=consumer_wallet
        )
    assert not (
        data_nft.get_permissions(user=another_consumer_addr)[DataNFTPermissions.MANAGER]
    )

    # Tests removing manager
    data_nft.add_manager(manager_address=consumer_addr, from_wallet=publisher_wallet)
    assert data_nft.get_permissions(user=consumer_addr)[DataNFTPermissions.MANAGER]
    data_nft.remove_manager(manager_address=consumer_addr, from_wallet=publisher_wallet)
    assert not (
        data_nft.get_permissions(user=consumer_addr)[DataNFTPermissions.MANAGER]
    )

    # Tests failing removing a manager if it has not the NFT owner role
    data_nft.add_manager(manager_address=consumer_addr, from_wallet=publisher_wallet)
    assert data_nft.get_permissions(user=consumer_addr)[DataNFTPermissions.MANAGER]
    with pytest.raises(Exception, match="not NFTOwner"):
        data_nft.remove_manager(
            manager_address=publisher_addr, from_wallet=consumer_wallet
        )
    assert data_nft.get_permissions(user=publisher_addr)[DataNFTPermissions.MANAGER]

    # Tests removing the NFT owner from the manager role
    data_nft.remove_manager(
        manager_address=publisher_addr, from_wallet=publisher_wallet
    )
    assert not (
        data_nft.get_permissions(user=publisher_addr)[DataNFTPermissions.MANAGER]
    )
    data_nft.add_manager(manager_address=publisher_addr, from_wallet=publisher_wallet)
    assert data_nft.get_permissions(user=publisher_addr)[DataNFTPermissions.MANAGER]

    # Tests failing calling execute_call function if the user is not manager
    assert not (
        data_nft.get_permissions(user=another_consumer_addr)[DataNFTPermissions.MANAGER]
    )
    with pytest.raises(Exception, match="NOT MANAGER"):
        data_nft.execute_call(
            operation=0,
            to=consumer_addr,
            value=10,
            data=Web3.toHex(text="SomeData"),
            from_wallet=another_consumer_wallet,
        )

    # Tests calling execute_call with a manager role
    assert data_nft.get_permissions(user=publisher_addr)[DataNFTPermissions.MANAGER]
    tx = data_nft.execute_call(
        operation=0,
        to=consumer_addr,
        value=10,
        data=Web3.toHex(text="SomeData"),
        from_wallet=consumer_wallet,
    )
    assert tx, "Could not execute call to consumer."

    # Tests setting new data
    data_nft.add_to_725_store_list(
        allowed_address=consumer_addr, from_wallet=publisher_wallet
    )
    assert data_nft.get_permissions(user=consumer_addr)[DataNFTPermissions.STORE]
    data_nft.set_new_data(
        key=b"ARBITRARY_KEY",
        value=b"SomeData",
        from_wallet=consumer_wallet,
    )
    assert data_nft.get_data(key=b"ARBITRARY_KEY").hex() == b"SomeData".hex()

    # Tests failing setting new data if user has not STORE UPDATER role.
    assert not (
        data_nft.get_permissions(user=another_consumer_addr)[DataNFTPermissions.STORE]
    )
    with pytest.raises(Exception, match="NOT STORE UPDATER"):
        data_nft.set_new_data(
            key=b"ARBITRARY_KEY",
            value=b"SomeData",
            from_wallet=another_consumer_wallet,
        )

    # Tests failing setting ERC20 data
    with pytest.raises(Exception, match="NOT ERC20 Contract"):
        data_nft.set_data_erc20(
            key=b"FOO_KEY",
            value=b"SomeData",
            from_wallet=consumer_wallet,
        )
    assert data_nft.get_data(key=b"FOO_KEY").hex() == b"".hex()


def test_add_and_remove_permissions(
    publisher_wallet, consumer_wallet, data_nft: DataNFT
):
    # Assert consumer has no permissions
    permissions = data_nft.get_permissions(consumer_wallet.address)
    assert not permissions[DataNFTPermissions.MANAGER]
    assert not permissions[DataNFTPermissions.DEPLOY_DATATOKEN]
    assert not permissions[DataNFTPermissions.UPDATE_METADATA]
    assert not permissions[DataNFTPermissions.STORE]

    # Grant consumer all permissions, one by one
    data_nft.add_manager(consumer_wallet.address, publisher_wallet)
    data_nft.add_to_create_erc20_list(consumer_wallet.address, publisher_wallet)
    data_nft.add_to_metadata_list(consumer_wallet.address, publisher_wallet)
    data_nft.add_to_725_store_list(consumer_wallet.address, publisher_wallet)

    # Assert consumer has all permissions
    permissions = data_nft.get_permissions(consumer_wallet.address)
    assert permissions[DataNFTPermissions.MANAGER]
    assert permissions[DataNFTPermissions.DEPLOY_DATATOKEN]
    assert permissions[DataNFTPermissions.UPDATE_METADATA]
    assert permissions[DataNFTPermissions.STORE]

    # Revoke all consumer permissions, one by one
    data_nft.remove_manager(consumer_wallet.address, publisher_wallet)
    data_nft.remove_from_create_erc20_list(consumer_wallet.address, publisher_wallet)
    data_nft.remove_from_metadata_list(consumer_wallet.address, publisher_wallet)
    data_nft.remove_from_725_store_list(consumer_wallet.address, publisher_wallet)

    # Assert consumer has no permissions
    permissions = data_nft.get_permissions(consumer_wallet.address)
    assert not permissions[DataNFTPermissions.MANAGER]
    assert not permissions[DataNFTPermissions.DEPLOY_DATATOKEN]
    assert not permissions[DataNFTPermissions.UPDATE_METADATA]
    assert not permissions[DataNFTPermissions.STORE]


@pytest.mark.unit
def test_success_update_metadata(
    publisher_wallet,
    consumer_wallet,
    publisher_addr: str,
    consumer_addr: str,
    data_nft: DataNFT,
):
    """Tests updating the metadata flow."""
    assert not (
        data_nft.get_permissions(user=consumer_addr)[DataNFTPermissions.UPDATE_METADATA]
    )
    data_nft.add_to_metadata_list(
        allowed_address=consumer_addr, from_wallet=publisher_wallet
    )
    metadata_info = data_nft.get_metadata()
    assert not metadata_info[3]

    tx = data_nft.set_metadata(
        metadata_state=1,
        metadata_decryptor_url="http://myprovider:8030",
        metadata_decryptor_address=b"0x123",
        flags=Web3.toBytes(hexstr=BLOB),
        data=Web3.toBytes(hexstr=BLOB),
        data_hash=Web3.toBytes(hexstr=BLOB),
        metadata_proofs=[],
        from_wallet=consumer_wallet,
    )
    receipt = TransactionReceipt(tx)
    assert receipt.events["MetadataCreated"]["decryptorUrl"] == "http://myprovider:8030"

    metadata_info = data_nft.get_metadata()
    assert metadata_info[3]
    assert metadata_info[0] == "http://myprovider:8030"

    tx = data_nft.set_metadata(
        metadata_state=1,
        metadata_decryptor_url="http://foourl",
        metadata_decryptor_address=b"0x123",
        flags=Web3.toBytes(hexstr=BLOB),
        data=Web3.toBytes(hexstr=BLOB),
        data_hash=Web3.toBytes(hexstr=BLOB),
        metadata_proofs=[],
        from_wallet=consumer_wallet,
    )
    receipt = TransactionReceipt(tx)
    assert receipt.events["MetadataUpdated"]["decryptorUrl"] == "http://foourl"

    metadata_info = data_nft.get_metadata()
    assert metadata_info[3]
    assert metadata_info[0] == "http://foourl"

    # Update tokenURI and set metadata in one call
    tx = data_nft.set_metadata_token_uri(
        metadata_state=1,
        metadata_decryptor_url="http://foourl",
        metadata_decryptor_address=b"0x123",
        flags=Web3.toBytes(hexstr=BLOB),
        data=Web3.toBytes(hexstr=BLOB),
        data_hash=Web3.toBytes(hexstr=BLOB),
        token_id=1,
        token_uri="https://anothernewurl.com/nft/",
        metadata_proofs=[],
        from_wallet=publisher_wallet,
    )

    receipt = TransactionReceipt(tx)
    assert (
        receipt.events["TokenURIUpdate"]["tokenURI"] == "https://anothernewurl.com/nft/"
    )
    assert receipt.events["TokenURIUpdate"]["updatedBy"] == publisher_addr

    assert receipt.events["MetadataUpdated"]["decryptorUrl"] == "http://foourl"

    metadata_info = data_nft.get_metadata()
    assert metadata_info[3]
    assert metadata_info[0] == "http://foourl"

    # Consumer self-revokes permission to update metadata
    data_nft.remove_from_metadata_list(consumer_wallet.address, consumer_wallet)
    assert not data_nft.get_permissions(consumer_wallet.address)[
        DataNFTPermissions.UPDATE_METADATA
    ]


def test_fails_update_metadata(consumer_wallet, consumer_addr, data_nft):
    """Tests failure of calling update metadata function when the role of the user is not METADATA UPDATER."""
    assert not (
        data_nft.get_permissions(user=consumer_addr)[DataNFTPermissions.UPDATE_METADATA]
    )

    with pytest.raises(Exception, match="NOT METADATA_ROLE"):
        data_nft.set_metadata(
            metadata_state=1,
            metadata_decryptor_url="http://myprovider:8030",
            metadata_decryptor_address=b"0x123",
            flags=BLOB.encode("utf-8"),
            data=BLOB,
            data_hash=BLOB,
            metadata_proofs=[],
            from_wallet=consumer_wallet,
        )


@pytest.mark.unit
def test_create_erc20(
    publisher_wallet,
    publisher_addr,
    consumer_addr,
    data_nft: DataNFT,
    data_nft_factory: DataNFTFactoryContract,
):
    """Tests calling create an ERC20 by the owner."""
    assert data_nft.get_permissions(user=publisher_addr)[
        DataNFTPermissions.DEPLOY_DATATOKEN
    ]

    tx = data_nft.create_erc20(
        template_index=1,
        name="DT1",
        symbol="DT1Symbol",
        minter=publisher_addr,
        fee_manager=consumer_addr,
        publish_market_order_fee_address=publisher_addr,
        publish_market_order_fee_token=ZERO_ADDRESS,
        publish_market_order_fee_amount=0,
        bytess=[b""],
        from_wallet=publisher_wallet,
    )
    assert tx, "Could not create ERC20."

    receipt = TransactionReceipt(tx)
    assert receipt.events[
        DataNFTFactoryContract.EVENT_TOKEN_CREATED
    ], "Cannot find TokenCreated event."

    with pytest.raises(Exception, match="Cap is needed for Datatoken Enterprise"):
        data_nft.create_erc20(
            template_index=2,
            name="DatatokenEnterpriseDT1",
            symbol="DatatokenEnterpriseDT1Symbol",
            minter=publisher_addr,
            fee_manager=consumer_addr,
            publish_market_order_fee_address=publisher_addr,
            publish_market_order_fee_token=ZERO_ADDRESS,
            publish_market_order_fee_amount=0,
            bytess=[b""],
            from_wallet=publisher_wallet,
        )

    with pytest.raises(Exception, match="Cap is needed for Datatoken Enterprise"):
        data_nft.create_datatoken(
            template_index=2,
            name="DatatokenEnterpriseDT1",
            symbol="DatattokenEnterpriseDT1Symbol",
            from_wallet=publisher_wallet,
        )

    tx = data_nft.create_erc20(
        template_index=2,
        name="DatatokenEnterpriseDT1",
        symbol="DatatokenEnterpriseDT1Symbol",
        minter=publisher_addr,
        fee_manager=consumer_addr,
        publish_market_order_fee_address=publisher_addr,
        publish_market_order_fee_token=ZERO_ADDRESS,
        publish_market_order_fee_amount=0,
        bytess=[b""],
        from_wallet=publisher_wallet,
        datatoken_cap=to_wei("0.1"),
    )
    assert tx, "Could not create datatoken Enterprise."

    tx = data_nft.create_datatoken(
        template_index=2,
        name="DatatokenEnterpriseDT1",
        symbol="DatatokenEnterpriseDT1Symbol",
        datatoken_cap=to_wei("0.1"),
        from_wallet=publisher_wallet,
    )
    assert tx, "Could not create datatoken Enterprise using create_datatoken."


def test_create_datatoken_with_usdc_order_fee(
    config: dict,
    publisher_wallet,
    data_nft: DataNFT,
    data_nft_factory: DataNFTFactoryContract,
):
    """Create an ERC20 with order fees ( 5 USDC, going to publishMarketAddress)"""
    usdc = Datatoken(config, get_address_of_type(config, "MockUSDC"))
    publish_market_order_fee_amount_in_wei = to_wei(5)
    tx = data_nft.create_erc20(
        template_index=1,
        name="DT1",
        symbol="DT1Symbol",
        minter=publisher_wallet.address,
        fee_manager=publisher_wallet.address,
        publish_market_order_fee_address=publisher_wallet.address,
        publish_market_order_fee_token=usdc.address,
        publish_market_order_fee_amount=publish_market_order_fee_amount_in_wei,
        bytess=[b""],
        from_wallet=publisher_wallet,
    )
    receipt = TransactionReceipt(tx)
    dt_address = receipt.events[DataNFTFactoryContract.EVENT_TOKEN_CREATED][
        "newTokenAddress"
    ]

    dt = Datatoken(config, dt_address)

    # Check publish fee info
    (
        publish_market_order_fee_address,
        publish_market_order_fee_token,
        publish_market_order_fee_amount,
    ) = dt.get_publishing_market_fee()
    assert publish_market_order_fee_address == publisher_wallet.address
    assert publish_market_order_fee_token == usdc.address
    assert publish_market_order_fee_amount == publish_market_order_fee_amount_in_wei


@pytest.mark.unit
def test_create_datatoken_with_non_owner(
    publisher_wallet,
    consumer_wallet,
    data_nft: DataNFT,
    data_nft_factory: DataNFTFactoryContract,
):
    """Tests creating an ERC20 token by wallet other than nft owner"""

    # Assert consumer cannot create ERC20
    assert not data_nft.get_permissions(consumer_wallet.address)[
        DataNFTPermissions.DEPLOY_DATATOKEN
    ]

    # Grant consumer permission to create ERC20
    data_nft.add_to_create_erc20_list(consumer_wallet.address, publisher_wallet)
    assert data_nft.get_permissions(consumer_wallet.address)[
        DataNFTPermissions.DEPLOY_DATATOKEN
    ]

    # Consumer creates ERC20
    tx = data_nft.create_erc20(
        template_index=1,
        name="DT1",
        symbol="DT1Symbol",
        minter=publisher_wallet.address,
        fee_manager=publisher_wallet.address,
        publish_market_order_fee_address=publisher_wallet.address,
        publish_market_order_fee_token=ZERO_ADDRESS,
        publish_market_order_fee_amount=0,
        bytess=[b""],
        from_wallet=consumer_wallet,
    )
    assert tx, "Failed to create ERC20 token."

    receipt = TransactionReceipt(tx)
    assert receipt.events[
        DataNFTFactoryContract.EVENT_TOKEN_CREATED
    ], "Cannot find TokenCreated event."

    # Consumer self-revokes permission to create ERC20
    data_nft.remove_from_create_erc20_list(consumer_wallet.address, consumer_wallet)
    assert not data_nft.get_permissions(consumer_wallet.address)[
        DataNFTPermissions.DEPLOY_DATATOKEN
    ]


@pytest.mark.unit
def test_fail_creating_erc20(consumer_wallet, publisher_addr, consumer_addr, data_nft):
    """Tests failure for creating ERC20 token."""
    assert not (
        data_nft.get_permissions(consumer_addr)[DataNFTPermissions.DEPLOY_DATATOKEN]
    )
    with pytest.raises(Exception, match="NOT ERC20DEPLOYER_ROLE"):
        data_nft.create_erc20(
            template_index=1,
            name="DT1",
            symbol="DT1Symbol",
            minter=publisher_addr,
            fee_manager=consumer_addr,
            publish_market_order_fee_address=publisher_addr,
            publish_market_order_fee_token=ZERO_ADDRESS,
            publish_market_order_fee_amount=0,
            bytess=[b""],
            from_wallet=consumer_wallet,
        )


@pytest.mark.unit
def test_erc721_datatoken_functions(
    publisher_wallet,
    consumer_wallet,
    publisher_addr,
    consumer_addr,
    data_nft,
    datatoken,
):
    """Tests ERC721 Template functions for ERC20 tokens."""
    assert len(data_nft.get_tokens_list()) == 1
    assert data_nft.is_deployed(datatoken=datatoken.address)

    assert not data_nft.is_deployed(datatoken=consumer_addr)
    tx = data_nft.set_token_uri(
        token_id=1,
        new_token_uri="https://newurl.com/nft/",
        from_wallet=publisher_wallet,
    )
    receipt = TransactionReceipt(tx)
    registered_event = receipt.events[DataNFT.EVENT_TOKEN_URI_UPDATED]

    assert registered_event, "Cannot find TokenURIUpdate event."
    assert registered_event["updatedBy"] == publisher_addr
    assert registered_event["tokenID"] == 1
    assert registered_event["blockNumber"] == receipt.block_number
    assert data_nft.token_uri(token_id=1) == "https://newurl.com/nft/"
    assert data_nft.token_uri(token_id=1) == registered_event["tokenURI"]

    # Tests failing setting token URI by another user
    with pytest.raises(Exception, match="not NFTOwner"):
        data_nft.set_token_uri(
            token_id=1,
            new_token_uri="https://foourl.com/nft/",
            from_wallet=consumer_wallet,
        )

    # Tests transfer functions
    datatoken.mint(
        consumer_addr,
        to_wei("0.2"),
        {"from": publisher_wallet},
    )
    assert datatoken.balanceOf(account=consumer_addr) == to_wei("0.2")
    assert data_nft.owner_of(token_id=1) == publisher_addr

    data_nft.transfer_from(
        from_address=publisher_addr,
        to_address=consumer_addr,
        token_id=1,
        from_wallet=publisher_wallet,
    )
    assert data_nft.balance_of(account=publisher_addr) == 0
    assert data_nft.owner_of(token_id=1) == consumer_addr
    assert data_nft.get_permissions(user=consumer_addr)[
        DataNFTPermissions.DEPLOY_DATATOKEN
    ]
    data_nft.create_erc20(
        template_index=1,
        name="DT1",
        symbol="DT1Symbol",
        minter=publisher_addr,
        fee_manager=consumer_addr,
        publish_market_order_fee_address=publisher_addr,
        publish_market_order_fee_token=ZERO_ADDRESS,
        publish_market_order_fee_amount=0,
        bytess=[b""],
        from_wallet=consumer_wallet,
    )
    with pytest.raises(Exception, match="NOT MINTER"):
        datatoken.mint(
            consumer_addr,
            to_wei("1"),
            {"from": consumer_wallet},
        )

    datatoken.addMinter(consumer_addr, {"from": consumer_wallet})
    datatoken.mint(
        consumer_addr,
        to_wei("0.2"),
        {"from": consumer_wallet},
    )
    assert datatoken.balanceOf(account=consumer_addr) == to_wei("0.4")


@pytest.mark.unit
def test_fail_transfer_function(
    consumer_wallet, publisher_addr, consumer_addr, data_nft
):
    """Tests failure of using the transfer functions."""
    with pytest.raises(
        Exception,
        match="transfer caller is not owner nor approved",
    ):
        data_nft.transfer_from(
            from_address=publisher_addr,
            to_address=consumer_addr,
            token_id=1,
            from_wallet=consumer_wallet,
        )

    # Tests for safe transfer as well
    with pytest.raises(
        Exception,
        match="transfer caller is not owner nor approved",
    ):
        data_nft.safe_transfer_from(
            from_address=publisher_addr,
            to_address=consumer_addr,
            token_id=1,
            from_wallet=consumer_wallet,
        )


def test_transfer_nft(
    config,
    publisher_wallet,
    consumer_wallet,
    publisher_addr,
    consumer_addr,
    factory_router,
    data_nft_factory,
    publisher_ocean_instance,
):
    """Tests transferring the NFT before deploying an ERC20, a pool, a FRE."""

    tx = data_nft_factory.deploy_erc721_contract(
        name="NFT to TRANSFER",
        symbol="NFTtT",
        template_index=1,
        additional_metadata_updater=ZERO_ADDRESS,
        additional_datatoken_deployer=consumer_addr,
        token_uri="https://oceanprotocol.com/nft/",
        transferable=True,
        owner=publisher_addr,
        from_wallet=publisher_wallet,
    )
    receipt = TransactionReceipt(tx)
    registered_event = receipt.events[DataNFTFactoryContract.EVENT_NFT_CREATED]
    assert registered_event["admin"] == publisher_wallet.address
    token_address = registered_event["newTokenAddress"]
    data_nft = DataNFT(config, token_address)
    assert data_nft.contract.name() == "NFT to TRANSFER"
    assert data_nft.symbol() == "NFTtT"

    tx = data_nft.safe_transfer_from(
        publisher_addr,
        consumer_addr,
        token_id=1,
        from_wallet=publisher_wallet,
    )
    receipt = TransactionReceipt(tx)
    transfer_event = receipt.events[DataNFTFactoryContract.EVENT_TRANSFER]

    assert transfer_event["from"] == publisher_addr
    assert transfer_event["to"] == consumer_addr
    assert data_nft.balance_of(consumer_addr) == 1
    assert data_nft.balance_of(publisher_addr) == 0
    assert data_nft.is_erc20_deployer(consumer_addr)
    assert data_nft.owner_of(1) == consumer_addr

    # Consumer is not the additional ERC20 deployer, but will be after the NFT transfer
    tx = data_nft_factory.deploy_erc721_contract(
        name="NFT1",
        symbol="NFT",
        template_index=1,
        additional_metadata_updater=ZERO_ADDRESS,
        additional_datatoken_deployer=ZERO_ADDRESS,
        token_uri="https://oceanprotocol.com/nft/",
        transferable=True,
        owner=publisher_addr,
        from_wallet=publisher_wallet,
    )
    receipt = TransactionReceipt(tx)
    registered_event = receipt.events[DataNFTFactoryContract.EVENT_NFT_CREATED]

    token_address = registered_event["newTokenAddress"]
    data_nft = DataNFT(config, token_address)
    tx = data_nft.safe_transfer_from(
        publisher_addr,
        consumer_addr,
        token_id=1,
        from_wallet=publisher_wallet,
    )
    receipt = TransactionReceipt(tx)
    transfer_event = receipt.events[DataNFTFactoryContract.EVENT_TRANSFER]

    assert transfer_event["from"] == publisher_addr
    assert transfer_event["to"] == consumer_addr
    assert data_nft.is_erc20_deployer(consumer_addr)

    # Creates an ERC20
    tx_result = data_nft.create_erc20(
        template_index=1,
        name="DT1",
        symbol="DT1Symbol",
        minter=consumer_addr,
        fee_manager=consumer_addr,
        publish_market_order_fee_address=publisher_addr,
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
    datatoken = Datatoken(config, datatoken_address)

    assert not datatoken.isMinter(publisher_addr)
    assert datatoken.isMinter(consumer_addr)
    datatoken.addMinter(publisher_addr, {"from": consumer_wallet})
    assert datatoken.get_permissions(publisher_addr)[0]  # publisher is minter now

    ocean_token = publisher_ocean_instance.OCEAN_token
    ocean_token.approve(factory_router.address, to_wei(10000), consumer_wallet)

    # Make consumer the publish_market_order_fee_address instead of publisher
    tx_result = datatoken.set_publishing_market_fee(
        consumer_addr, ocean_token.address, to_wei(1), publisher_wallet
    )

    assert tx_result, "Failed to set the publish fee."
    receipt = TransactionReceipt(tx_result)
    set_publishing_fee_event = receipt.events[
        Datatoken.EVENT_PUBLISH_MARKET_FEE_CHANGED
    ]
    assert set_publishing_fee_event, "Cannot find PublishMarketFeeChanged event."

    publish_fees = datatoken.get_publishing_market_fee()
    assert publish_fees[0] == consumer_addr
    assert publish_fees[1] == ocean_token.address
    assert publish_fees[2] == to_wei(1)


def test_nft_transfer_with_fre(
    config,
    ocean_token,
    publisher_wallet,
    consumer_wallet,
    data_nft,
    datatoken,
    consumer_addr,
):
    """Tests transferring the NFT before deploying an ERC20, a FRE."""

    tx = data_nft.safe_transfer_from(
        publisher_wallet.address,
        consumer_wallet.address,
        token_id=1,
        from_wallet=publisher_wallet,
    )
    receipt = TransactionReceipt(tx)
    transfer_event = receipt.events[DataNFTFactoryContract.EVENT_TRANSFER]

    assert transfer_event["from"] == publisher_wallet.address
    assert transfer_event["to"] == consumer_wallet.address
    assert data_nft.balance_of(consumer_wallet.address) == 1
    assert data_nft.balance_of(publisher_wallet.address) == 0
    assert data_nft.is_erc20_deployer(consumer_wallet.address) is True
    assert data_nft.owner_of(1) == consumer_wallet.address

    # The newest owner of the NFT (consumer wallet) has ERC20 deployer role & can deploy a FRE
    fixed_exchange = FixedRateExchange(
        config, get_address_of_type(config, "FixedPrice")
    )
    number_of_exchanges = fixed_exchange.get_number_of_exchanges()
    tx = datatoken.create_fixed_rate(
        fixed_price_address=fixed_exchange.address,
        base_token_address=ocean_token.address,
        owner=consumer_wallet.address,
        publish_market_swap_fee_collector=consumer_wallet.address,
        allowed_swapper=ZERO_ADDRESS,
        base_token_decimals=ocean_token.decimals(),
        datatoken_decimals=datatoken.decimals(),
        fixed_rate=to_wei(1),
        publish_market_swap_fee_amount=to_wei("0.001"),
        with_mint=1,
        from_wallet=consumer_wallet,
    )

    receipt = TransactionReceipt(tx)
    fre_event = receipt.events[DataNFTFactoryContract.EVENT_NEW_FIXED_RATE]

    assert fixed_exchange.get_number_of_exchanges() == number_of_exchanges + 1
    assert fre_event["owner"] == consumer_addr

    exchange_id = fre_event["exchangeId"]

    # Exchange should have supply and fees setup
    exchange_details = fixed_exchange.get_exchange(exchange_id)
    assert exchange_details[FixedRateExchangeDetails.EXCHANGE_OWNER] == consumer_addr
    assert exchange_details[FixedRateExchangeDetails.DATATOKEN] == datatoken.address
    assert (
        exchange_details[FixedRateExchangeDetails.DT_DECIMALS] == datatoken.decimals()
    )
    assert exchange_details[FixedRateExchangeDetails.BASE_TOKEN] == ocean_token.address
    assert (
        exchange_details[FixedRateExchangeDetails.BT_DECIMALS] == ocean_token.decimals()
    )
    assert exchange_details[FixedRateExchangeDetails.FIXED_RATE] == to_wei(1)
    assert exchange_details[FixedRateExchangeDetails.ACTIVE]
    assert exchange_details[FixedRateExchangeDetails.DT_SUPPLY] == MAX_UINT256
    assert exchange_details[FixedRateExchangeDetails.DT_BALANCE] == 0
    assert exchange_details[FixedRateExchangeDetails.BT_BALANCE] == 0
    assert exchange_details[FixedRateExchangeDetails.WITH_MINT]

    datatoken.approve(fixed_exchange.address, to_wei(100), consumer_wallet)
    ocean_token.approve(fixed_exchange.address, to_wei(100), consumer_wallet)
    amount_dt_bought = to_wei(2)
    fixed_exchange.buy_dt(
        exchange_id=exchange_id,
        datatoken_amount=amount_dt_bought,
        max_base_token_amount=to_wei(5),
        consume_market_swap_fee_address=ZERO_ADDRESS,
        consume_market_swap_fee_amount=0,
        from_wallet=consumer_wallet,
    )
    assert (
        fixed_exchange.get_dt_supply(exchange_id)
        == exchange_details[FixedRateExchangeDetails.DT_SUPPLY] - amount_dt_bought
    )
    assert datatoken.balanceOf(consumer_addr) == amount_dt_bought
    fixed_exchange.sell_dt(
        exchange_id=exchange_id,
        datatoken_amount=to_wei(2),
        min_base_token_amount=to_wei(1),
        consume_market_swap_fee_address=ZERO_ADDRESS,
        consume_market_swap_fee_amount=0,
        from_wallet=consumer_wallet,
    )
    assert (
        fixed_exchange.get_dt_supply(exchange_id)
        == exchange_details[FixedRateExchangeDetails.DT_SUPPLY] - amount_dt_bought
    )
    assert datatoken.balanceOf(consumer_addr) == 0
    fixed_exchange.collect_dt(
        exchange_id=exchange_id, amount=to_wei(1), from_wallet=consumer_wallet
    )
    assert datatoken.balanceOf(consumer_addr) == to_wei(1)


def test_transfer_nft_with_erc20_pool_fre(
    config,
    publisher_wallet,
    consumer_wallet,
    publisher_addr,
    consumer_addr,
    factory_router,
    publisher_ocean_instance,
    data_nft_factory,
):
    """Tests transferring the NFT after deploying an ERC20, a pool, a FRE."""

    tx = data_nft_factory.deploy_erc721_contract(
        name="NFT to TRANSFER",
        symbol="NFTtT",
        template_index=1,
        additional_metadata_updater=ZERO_ADDRESS,
        additional_datatoken_deployer=consumer_addr,
        token_uri="https://oceanprotocol.com/nft/",
        transferable=True,
        owner=publisher_addr,
        from_wallet=publisher_wallet,
    )
    receipt = TransactionReceipt(tx)
    registered_event = receipt.events[DataNFTFactoryContract.EVENT_NFT_CREATED]
    assert registered_event["admin"] == publisher_addr
    token_address = registered_event["newTokenAddress"]
    data_nft = DataNFT(config, token_address)
    assert data_nft.contract.name() == "NFT to TRANSFER"
    assert data_nft.symbol() == "NFTtT"

    # Creates an ERC20
    tx_result = data_nft.create_erc20(
        template_index=1,
        name="DT1",
        symbol="DT1Symbol",
        minter=publisher_addr,
        fee_manager=publisher_addr,
        publish_market_order_fee_address=publisher_addr,
        publish_market_order_fee_token=ZERO_ADDRESS,
        publish_market_order_fee_amount=0,
        bytess=[b""],
        from_wallet=publisher_wallet,
    )
    assert tx_result, "Failed to create ERC20 token."
    receipt = TransactionReceipt(tx_result)
    registered_token_event = receipt.events[DataNFTFactoryContract.EVENT_TOKEN_CREATED]
    assert registered_token_event, "Cannot find TokenCreated event."
    datatoken_address = registered_token_event["newTokenAddress"]
    datatoken = Datatoken(config, datatoken_address)

    assert datatoken.isMinter(publisher_addr)

    ocean_token = publisher_ocean_instance.OCEAN_token

    # The owner of the NFT (publisher wallet) has ERC20 deployer role & can deploy a FRE
    fixed_exchange = FixedRateExchange(
        config, get_address_of_type(config, "FixedPrice")
    )
    number_of_exchanges = fixed_exchange.get_number_of_exchanges()
    tx = datatoken.create_fixed_rate(
        fixed_price_address=fixed_exchange.address,
        base_token_address=ocean_token.address,
        owner=publisher_addr,
        publish_market_swap_fee_collector=publisher_addr,
        allowed_swapper=ZERO_ADDRESS,
        base_token_decimals=ocean_token.decimals(),
        datatoken_decimals=datatoken.decimals(),
        fixed_rate=to_wei(1),
        publish_market_swap_fee_amount=to_wei("0.001"),
        with_mint=0,
        from_wallet=publisher_wallet,
    )

    receipt = TransactionReceipt(tx)
    fre_event = receipt.events[DataNFTFactoryContract.EVENT_NEW_FIXED_RATE]
    assert fixed_exchange.get_number_of_exchanges() == number_of_exchanges + 1
    assert fre_event["owner"] == publisher_addr

    exchange_id = fre_event["exchangeId"]

    exchange_details = fixed_exchange.get_exchange(exchange_id)
    assert exchange_details[FixedRateExchangeDetails.EXCHANGE_OWNER] == publisher_addr
    assert exchange_details[FixedRateExchangeDetails.DATATOKEN] == datatoken.address
    assert (
        exchange_details[FixedRateExchangeDetails.DT_DECIMALS] == datatoken.decimals()
    )
    assert exchange_details[FixedRateExchangeDetails.BASE_TOKEN] == ocean_token.address
    assert (
        exchange_details[FixedRateExchangeDetails.BT_DECIMALS] == ocean_token.decimals()
    )
    assert exchange_details[FixedRateExchangeDetails.FIXED_RATE] == to_wei(1)
    assert exchange_details[FixedRateExchangeDetails.ACTIVE]
    assert exchange_details[FixedRateExchangeDetails.DT_SUPPLY] == 0
    assert exchange_details[FixedRateExchangeDetails.BT_SUPPLY] == 0
    assert exchange_details[FixedRateExchangeDetails.DT_BALANCE] == 0
    assert exchange_details[FixedRateExchangeDetails.BT_BALANCE] == 0
    assert not exchange_details[FixedRateExchangeDetails.WITH_MINT]

    tx = data_nft.safe_transfer_from(
        publisher_addr,
        consumer_addr,
        token_id=1,
        from_wallet=publisher_wallet,
    )
    receipt = TransactionReceipt(tx)
    transfer_event = receipt.events[DataNFTFactoryContract.EVENT_TRANSFER]

    assert transfer_event["from"] == publisher_addr
    assert transfer_event["to"] == consumer_addr
    assert data_nft.balance_of(consumer_addr) == 1
    assert data_nft.balance_of(publisher_addr) == 0
    assert data_nft.is_erc20_deployer(consumer_addr)
    assert data_nft.owner_of(1) == consumer_addr
    permissions = datatoken.get_permissions(consumer_addr)
    assert not permissions[0]  # the newest owner is not the minter
    datatoken.addMinter(consumer_addr, {"from": consumer_wallet})
    assert datatoken.permissions(consumer_addr)[0]

    # Consumer wallet has not become the owner of the publisher's exchange
    exchange_details = fixed_exchange.get_exchange(exchange_id)
    assert exchange_details[FixedRateExchangeDetails.EXCHANGE_OWNER] == publisher_addr
    assert exchange_details[FixedRateExchangeDetails.ACTIVE]
