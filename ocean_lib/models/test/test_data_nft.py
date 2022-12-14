#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from web3 import Web3

from ocean_lib.models.data_nft import DataNFT, DataNFTPermissions
from ocean_lib.models.data_nft_factory import DataNFTFactoryContract
from ocean_lib.models.datatoken import Datatoken
from ocean_lib.ocean.util import get_address_of_type, to_wei, from_wei
from ocean_lib.web3_internal.constants import MAX_UINT256, ZERO_ADDRESS
from tests.resources.helper_functions import deploy_erc721_erc20

BLOB = "f8929916089218bdb4aa78c3ecd16633afd44b8aef89299160"


@pytest.mark.unit
def test_permissions(
    publisher_wallet,
    consumer_wallet,
    another_consumer_wallet,
    config,
    data_nft,
):
    """Tests permissions' functions."""
    assert data_nft.contract.name() == "NFT"
    assert data_nft.symbol() == "NFTSYMBOL"
    assert data_nft.balanceOf(publisher_wallet.address) == 1
    # Tests if the NFT was initialized
    assert data_nft.isInitialized()

    # Tests adding a manager successfully
    data_nft.addManager(consumer_wallet.address, {"from": publisher_wallet})
    assert data_nft.getPermissions(consumer_wallet.address)[DataNFTPermissions.MANAGER]

    assert data_nft.tokenURI(1) == "https://oceanprotocol.com/nft/"

    # Tests failing clearing permissions
    with pytest.raises(Exception, match="not NFTOwner"):
        data_nft.cleanPermissions({"from": another_consumer_wallet})

    # Tests clearing permissions
    data_nft.addToCreateERC20List(publisher_wallet.address, {"from": publisher_wallet})
    data_nft.addToCreateERC20List(
        another_consumer_wallet.address, {"from": publisher_wallet}
    )
    assert data_nft.getPermissions(publisher_wallet.address)[
        DataNFTPermissions.DEPLOY_DATATOKEN
    ]
    assert data_nft.getPermissions(another_consumer_wallet.address)[
        DataNFTPermissions.DEPLOY_DATATOKEN
    ]
    # Still is not the NFT owner, cannot clear permissions then
    with pytest.raises(Exception, match="not NFTOwner"):
        data_nft.cleanPermissions({"from": another_consumer_wallet})

    data_nft.cleanPermissions({"from": publisher_wallet})

    assert not (
        data_nft.getPermissions(publisher_wallet.address)[
            DataNFTPermissions.DEPLOY_DATATOKEN
        ]
    )
    assert not (
        data_nft.getPermissions(consumer_wallet.address)[DataNFTPermissions.MANAGER]
    )
    assert not (
        data_nft.getPermissions(another_consumer_wallet.address)[
            DataNFTPermissions.DEPLOY_DATATOKEN
        ]
    )

    # Tests failing adding a new manager by another user different from the NFT owner
    data_nft.addManager(publisher_wallet.address, {"from": publisher_wallet})
    assert data_nft.getPermissions(publisher_wallet.address)[DataNFTPermissions.MANAGER]
    assert not (
        data_nft.getPermissions(consumer_wallet.address)[DataNFTPermissions.MANAGER]
    )
    with pytest.raises(Exception, match="not NFTOwner"):
        data_nft.addManager(another_consumer_wallet.address, {"from": consumer_wallet})
    assert not (
        data_nft.getPermissions(another_consumer_wallet.address)[
            DataNFTPermissions.MANAGER
        ]
    )

    # Tests removing manager
    data_nft.addManager(consumer_wallet.address, {"from": publisher_wallet})
    assert data_nft.getPermissions(consumer_wallet.address)[DataNFTPermissions.MANAGER]
    data_nft.removeManager(consumer_wallet.address, {"from": publisher_wallet})
    assert not (
        data_nft.getPermissions(consumer_wallet.address)[DataNFTPermissions.MANAGER]
    )

    # Tests failing removing a manager if it has not the NFT owner role
    data_nft.addManager(consumer_wallet.address, {"from": publisher_wallet})
    assert data_nft.getPermissions(consumer_wallet.address)[DataNFTPermissions.MANAGER]
    with pytest.raises(Exception, match="not NFTOwner"):
        data_nft.removeManager(publisher_wallet.address, {"from": consumer_wallet})
    assert data_nft.getPermissions(publisher_wallet.address)[DataNFTPermissions.MANAGER]

    # Tests removing the NFT owner from the manager role
    data_nft.removeManager(publisher_wallet.address, {"from": publisher_wallet})
    assert not (
        data_nft.getPermissions(publisher_wallet.address)[DataNFTPermissions.MANAGER]
    )
    data_nft.addManager(publisher_wallet.address, {"from": publisher_wallet})
    assert data_nft.getPermissions(publisher_wallet.address)[DataNFTPermissions.MANAGER]

    # Tests failing calling execute_call function if the user is not manager
    assert not (
        data_nft.getPermissions(another_consumer_wallet.address)[
            DataNFTPermissions.MANAGER
        ]
    )
    with pytest.raises(Exception, match="NOT MANAGER"):
        data_nft.executeCall(
            0,
            consumer_wallet.address,
            10,
            Web3.toHex(text="SomeData"),
            {"from": another_consumer_wallet},
        )

    # Tests calling execute_call with a manager role
    assert data_nft.getPermissions(publisher_wallet.address)[DataNFTPermissions.MANAGER]
    tx = data_nft.executeCall(
        0,
        consumer_wallet.address,
        10,
        Web3.toHex(text="SomeData"),
        {"from": consumer_wallet},
    )
    assert tx, "Could not execute call to consumer."

    # Tests setting new data
    data_nft.addTo725StoreList(consumer_wallet.address, {"from": publisher_wallet})
    assert data_nft.getPermissions(consumer_wallet.address)[DataNFTPermissions.STORE]
    data_nft.setNewData(
        b"ARBITRARY_KEY",
        b"SomeData",
        {"from": consumer_wallet},
    )
    assert data_nft.getData(b"ARBITRARY_KEY").hex() == b"SomeData".hex()

    # Tests failing setting new data if user has not STORE UPDATER role.
    assert not (
        data_nft.getPermissions(another_consumer_wallet.address)[
            DataNFTPermissions.STORE
        ]
    )
    with pytest.raises(Exception, match="NOT STORE UPDATER"):
        data_nft.setNewData(
            b"ARBITRARY_KEY",
            b"SomeData",
            {"from": another_consumer_wallet},
        )

    # Tests failing setting ERC20 data
    with pytest.raises(Exception, match="NOT ERC20 Contract"):
        data_nft.setDataERC20(
            b"FOO_KEY",
            b"SomeData",
            {"from": consumer_wallet},
        )
    assert data_nft.getData(b"FOO_KEY").hex() == b"".hex()


def test_add_and_remove_permissions(
    publisher_wallet, consumer_wallet, config, data_nft
):

    # Assert consumer has no permissions
    permissions = data_nft.getPermissions(consumer_wallet.address)
    assert not permissions[DataNFTPermissions.MANAGER]
    assert not permissions[DataNFTPermissions.DEPLOY_DATATOKEN]
    assert not permissions[DataNFTPermissions.UPDATE_METADATA]
    assert not permissions[DataNFTPermissions.STORE]

    # Grant consumer all permissions, one by one
    data_nft.addManager(consumer_wallet.address, {"from": publisher_wallet})
    data_nft.addToCreateERC20List(consumer_wallet.address, {"from": publisher_wallet})
    data_nft.addToMetadataList(consumer_wallet.address, {"from": publisher_wallet})
    data_nft.addTo725StoreList(consumer_wallet.address, {"from": publisher_wallet})

    # Assert consumer has all permissions
    permissions = data_nft.getPermissions(consumer_wallet.address)
    assert permissions[DataNFTPermissions.MANAGER]
    assert permissions[DataNFTPermissions.DEPLOY_DATATOKEN]
    assert permissions[DataNFTPermissions.UPDATE_METADATA]
    assert permissions[DataNFTPermissions.STORE]

    # Revoke all consumer permissions, one by one
    data_nft.removeManager(consumer_wallet.address, {"from": publisher_wallet})
    data_nft.removeFromCreateERC20List(
        consumer_wallet.address, {"from": publisher_wallet}
    )
    data_nft.removeFromMetadataList(consumer_wallet.address, {"from": publisher_wallet})
    data_nft.removeFrom725StoreList(consumer_wallet.address, {"from": publisher_wallet})

    # Assert consumer has no permissions
    permissions = data_nft.getPermissions(consumer_wallet.address)
    assert not permissions[DataNFTPermissions.MANAGER]
    assert not permissions[DataNFTPermissions.DEPLOY_DATATOKEN]
    assert not permissions[DataNFTPermissions.UPDATE_METADATA]
    assert not permissions[DataNFTPermissions.STORE]


@pytest.mark.unit
def test_success_update_metadata(publisher_wallet, consumer_wallet, config, data_nft):
    """Tests updating the metadata flow."""
    assert not (
        data_nft.getPermissions(consumer_wallet.address)[
            DataNFTPermissions.UPDATE_METADATA
        ]
    )
    data_nft.addToMetadataList(consumer_wallet.address, {"from": publisher_wallet})
    metadata_info = data_nft.getMetaData()
    assert not metadata_info[3]

    receipt = data_nft.setMetaData(
        1,
        "http://myprovider:8030",
        b"0x123",
        Web3.toBytes(hexstr=BLOB),
        Web3.toBytes(hexstr=BLOB),
        Web3.toBytes(hexstr=BLOB),
        [],
        {"from": consumer_wallet},
    )
    assert receipt.events["MetadataCreated"]["decryptorUrl"] == "http://myprovider:8030"

    metadata_info = data_nft.getMetaData()
    assert metadata_info[3]
    assert metadata_info[0] == "http://myprovider:8030"

    receipt = data_nft.setMetaData(
        1,
        "http://foourl",
        b"0x123",
        Web3.toBytes(hexstr=BLOB),
        Web3.toBytes(hexstr=BLOB),
        Web3.toBytes(hexstr=BLOB),
        [],
        {"from": consumer_wallet},
    )
    assert receipt.events["MetadataUpdated"]["decryptorUrl"] == "http://foourl"

    metadata_info = data_nft.getMetaData()
    assert metadata_info[3]
    assert metadata_info[0] == "http://foourl"

    # Update tokenURI and set metadata in one call
    receipt = data_nft.setMetaDataAndTokenURI(
        (
            1,
            "http://foourl",
            b"0x123",
            Web3.toBytes(hexstr=BLOB),
            Web3.toBytes(hexstr=BLOB),
            Web3.toBytes(hexstr=BLOB),
            1,
            "https://anothernewurl.com/nft/",
            [],
        ),
        {"from": publisher_wallet},
    )

    assert (
        receipt.events["TokenURIUpdate"]["tokenURI"] == "https://anothernewurl.com/nft/"
    )
    assert receipt.events["TokenURIUpdate"]["updatedBy"] == publisher_wallet.address

    assert receipt.events["MetadataUpdated"]["decryptorUrl"] == "http://foourl"

    metadata_info = data_nft.getMetaData()
    assert metadata_info[3]
    assert metadata_info[0] == "http://foourl"

    # Consumer self-revokes permission to update metadata
    data_nft.removeFromMetadataList(consumer_wallet.address, {"from": consumer_wallet})
    assert not data_nft.getPermissions(consumer_wallet.address)[
        DataNFTPermissions.UPDATE_METADATA
    ]


def test_fails_update_metadata(consumer_wallet, publisher_wallet, config, data_nft):
    """Tests failure of calling update metadata function when the role of the user is not METADATA UPDATER."""
    assert not (
        data_nft.getPermissions(consumer_wallet.address)[
            DataNFTPermissions.UPDATE_METADATA
        ]
    )

    with pytest.raises(Exception, match="NOT METADATA_ROLE"):
        data_nft.setMetaData(
            1,
            "http://myprovider:8030",
            b"0x123",
            BLOB.encode("utf-8"),
            BLOB,
            BLOB,
            [],
            {"from": consumer_wallet},
        )


@pytest.mark.unit
def test_create_datatoken(
    publisher_wallet,
    consumer_wallet,
    config,
    data_nft_factory: DataNFTFactoryContract,
    data_nft,
):
    """Tests calling create an ERC20 by the owner."""
    assert data_nft.getPermissions(publisher_wallet.address)[
        DataNFTPermissions.DEPLOY_DATATOKEN
    ]

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
        transaction_parameters={"from": publisher_wallet},
        wrap_as_object=False,
    )
    assert receipt, "Could not create ERC20."

    assert receipt.events["TokenCreated"], "Cannot find TokenCreated event."

    with pytest.raises(Exception, match="Cap is needed for Datatoken Enterprise"):
        data_nft.create_datatoken(
            template_index=2,
            name="DatatokenEnterpriseDT1",
            symbol="DatatokenEnterpriseDT1Symbol",
            minter=publisher_wallet.address,
            fee_manager=consumer_wallet.address,
            publish_market_order_fee_address=publisher_wallet.address,
            publish_market_order_fee_token=ZERO_ADDRESS,
            publish_market_order_fee_amount=0,
            bytess=[b""],
            transaction_parameters={"from": publisher_wallet},
        )

    with pytest.raises(Exception, match="Cap is needed for Datatoken Enterprise"):
        data_nft.create_datatoken(
            template_index=2,
            name="DatatokenEnterpriseDT1",
            symbol="DatattokenEnterpriseDT1Symbol",
            transaction_parameters={"from": publisher_wallet},
        )

    tx = data_nft.create_datatoken(
        template_index=2,
        name="DatatokenEnterpriseDT1",
        symbol="DatatokenEnterpriseDT1Symbol",
        minter=publisher_wallet.address,
        fee_manager=consumer_wallet.address,
        publish_market_order_fee_address=publisher_wallet.address,
        publish_market_order_fee_token=ZERO_ADDRESS,
        publish_market_order_fee_amount=0,
        bytess=[b""],
        transaction_parameters={"from": publisher_wallet},
        datatoken_cap=Web3.toWei("0.1", "ether"),
        wrap_as_object=False,
    )
    assert tx, "Could not create datatoken Enterprise with explicit parameters"

    tx = data_nft.create_datatoken(
        template_index=2,
        name="DatatokenEnterpriseDT1",
        symbol="DatatokenEnterpriseDT1Symbol",
        datatoken_cap=Web3.toWei("0.1", "ether"),
        transaction_parameters={"from": publisher_wallet},
    )
    assert tx, "Could not create datatoken Enterprise with implicit parameters."


def test_create_datatoken_with_usdc_order_fee(
    config: dict, publisher_wallet, data_nft_factory: DataNFTFactoryContract, data_nft
):
    """Create an ERC20 with order fees ( 5 USDC, going to publishMarketAddress)"""
    usdc = Datatoken(config, get_address_of_type(config, "MockUSDC"))
    publish_market_order_fee_amount_in_wei = Web3.toWei(5, "ether")
    dt = data_nft.create_datatoken(
        template_index=1,
        name="DT1",
        symbol="DT1Symbol",
        minter=publisher_wallet.address,
        fee_manager=publisher_wallet.address,
        publish_market_order_fee_address=publisher_wallet.address,
        publish_market_order_fee_token=usdc.address,
        publish_market_order_fee_amount=publish_market_order_fee_amount_in_wei,
        bytess=[b""],
        transaction_parameters={"from": publisher_wallet},
    )

    # Check publish fee info
    (
        publish_market_order_fee_address,
        publish_market_order_fee_token,
        publish_market_order_fee_amount,
    ) = dt.getPublishingMarketFee()
    assert publish_market_order_fee_address == publisher_wallet.address
    assert publish_market_order_fee_token == usdc.address
    assert publish_market_order_fee_amount == publish_market_order_fee_amount_in_wei


@pytest.mark.unit
def test_create_datatoken_with_non_owner(
    publisher_wallet,
    consumer_wallet,
    data_nft_factory: DataNFTFactoryContract,
    config,
    data_nft,
):
    """Tests creating an ERC20 token by wallet other than nft owner"""
    # Assert consumer cannot create ERC20
    assert not data_nft.getPermissions(consumer_wallet.address)[
        DataNFTPermissions.DEPLOY_DATATOKEN
    ]

    # Grant consumer permission to create ERC20
    data_nft.addToCreateERC20List(consumer_wallet.address, {"from": publisher_wallet})
    assert data_nft.getPermissions(consumer_wallet.address)[
        DataNFTPermissions.DEPLOY_DATATOKEN
    ]

    # Consumer creates ERC20
    receipt = data_nft.create_datatoken(
        template_index=1,
        name="DT1",
        symbol="DT1Symbol",
        minter=publisher_wallet.address,
        fee_manager=publisher_wallet.address,
        publish_market_order_fee_address=publisher_wallet.address,
        publish_market_order_fee_token=ZERO_ADDRESS,
        publish_market_order_fee_amount=0,
        bytess=[b""],
        transaction_parameters={"from": consumer_wallet},
        wrap_as_object=False,
    )
    assert receipt, "Failed to create ERC20 token."

    assert receipt.events["TokenCreated"], "Cannot find TokenCreated event."

    # Consumer self-revokes permission to create ERC20
    data_nft.removeFromCreateERC20List(
        consumer_wallet.address, {"from": consumer_wallet}
    )
    assert not data_nft.getPermissions(consumer_wallet.address)[
        DataNFTPermissions.DEPLOY_DATATOKEN
    ]


@pytest.mark.unit
def test_fail_creating_erc20(
    consumer_wallet,
    publisher_wallet,
    config,
    data_nft,
):
    """Tests failure for creating ERC20 token."""
    assert not (
        data_nft.getPermissions(consumer_wallet.address)[
            DataNFTPermissions.DEPLOY_DATATOKEN
        ]
    )
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
            transaction_parameters={"from": consumer_wallet},
        )


@pytest.mark.unit
def test_erc721_datatoken_functions(
    publisher_wallet,
    consumer_wallet,
    config,
    data_NFT_and_DT,
):
    """Tests ERC721 Template functions for ERC20 tokens."""
    data_nft, datatoken = data_NFT_and_DT
    assert len(data_nft.getTokensList()) == 1
    assert data_nft.isDeployed(datatoken.address)

    assert not data_nft.isDeployed(consumer_wallet.address)
    receipt = data_nft.setTokenURI(
        1,
        "https://newurl.com/nft/",
        {"from": publisher_wallet},
    )
    registered_event = receipt.events["TokenURIUpdate"]

    assert registered_event, "Cannot find TokenURIUpdate event."
    assert registered_event["updatedBy"] == publisher_wallet.address
    assert registered_event["tokenID"] == 1
    assert registered_event["blockNumber"] == receipt.block_number
    assert data_nft.tokenURI(1) == "https://newurl.com/nft/"
    assert data_nft.tokenURI(1) == registered_event["tokenURI"]

    # Tests failing setting token URI by another user
    with pytest.raises(Exception, match="not NFTOwner"):
        data_nft.setTokenURI(
            1,
            "https://foourl.com/nft/",
            {"from": consumer_wallet},
        )

    # Tests transfer functions
    datatoken.mint(
        consumer_wallet.address,
        Web3.toWei("0.2", "ether"),
        {"from": publisher_wallet},
    )
    assert datatoken.balanceOf(consumer_wallet.address) == Web3.toWei("0.2", "ether")
    assert data_nft.ownerOf(1) == publisher_wallet.address

    data_nft.transferFrom(
        publisher_wallet.address,
        consumer_wallet.address,
        1,
        {"from": publisher_wallet},
    )
    assert data_nft.balanceOf(publisher_wallet.address) == 0
    assert data_nft.ownerOf(1) == consumer_wallet.address
    assert data_nft.getPermissions(consumer_wallet.address)[
        DataNFTPermissions.DEPLOY_DATATOKEN
    ]
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
        transaction_parameters={"from": consumer_wallet},
        wrap_as_object=False,
    )
    with pytest.raises(Exception, match="NOT MINTER"):
        datatoken.mint(
            consumer_wallet.address,
            Web3.toWei("1", "ether"),
            {"from": consumer_wallet},
        )

    datatoken.addMinter(consumer_wallet.address, {"from": consumer_wallet})
    datatoken.mint(
        consumer_wallet.address,
        Web3.toWei("0.2", "ether"),
        {"from": consumer_wallet},
    )
    assert datatoken.balanceOf(consumer_wallet.address) == Web3.toWei("0.4", "ether")


@pytest.mark.unit
def test_fail_transfer_function(consumer_wallet, publisher_wallet, config, data_nft):
    """Tests failure of using the transfer functions."""
    with pytest.raises(
        Exception,
        match="transfer caller is not owner nor approved",
    ):
        data_nft.transferFrom(
            publisher_wallet.address,
            consumer_wallet.address,
            1,
            {"from": consumer_wallet},
        )

    # Tests for safe transfer as well
    with pytest.raises(
        Exception,
        match="transfer caller is not owner nor approved",
    ):
        data_nft.safeTransferFrom(
            publisher_wallet.address,
            consumer_wallet.address,
            1,
            {"from": consumer_wallet},
        )


def test_transfer_nft(
    config,
    publisher_wallet,
    consumer_wallet,
    factory_router,
    data_nft_factory,
    publisher_ocean,
):
    """Tests transferring the NFT before deploying an ERC20, a pool, a FRE."""

    receipt = data_nft_factory.deployERC721Contract(
        "NFT to TRANSFER",
        "NFTtT",
        1,
        ZERO_ADDRESS,
        consumer_wallet.address,
        "https://oceanprotocol.com/nft/",
        True,
        publisher_wallet.address,
        {"from": publisher_wallet},
    )
    registered_event = receipt.events["NFTCreated"]
    assert registered_event["admin"] == publisher_wallet.address
    token_address = registered_event["newTokenAddress"]
    data_nft = DataNFT(config, token_address)
    assert data_nft.contract.name() == "NFT to TRANSFER"
    assert data_nft.symbol() == "NFTtT"

    receipt = data_nft.safeTransferFrom(
        publisher_wallet.address,
        consumer_wallet.address,
        1,
        {"from": publisher_wallet},
    )
    transfer_event = receipt.events["Transfer"]

    assert transfer_event["from"] == publisher_wallet.address
    assert transfer_event["to"] == consumer_wallet.address
    assert data_nft.balanceOf(consumer_wallet.address) == 1
    assert data_nft.balanceOf(publisher_wallet.address) == 0
    assert data_nft.isERC20Deployer(consumer_wallet.address)
    assert data_nft.ownerOf(1) == consumer_wallet.address

    # Consumer is not the additional ERC20 deployer, but will be after the NFT transfer
    receipt = data_nft_factory.deployERC721Contract(
        "NFT1",
        "NFT",
        1,
        ZERO_ADDRESS,
        ZERO_ADDRESS,
        "https://oceanprotocol.com/nft/",
        True,
        publisher_wallet.address,
        {"from": publisher_wallet},
    )
    registered_event = receipt.events["NFTCreated"]

    token_address = registered_event["newTokenAddress"]
    data_nft = DataNFT(config, token_address)
    receipt = data_nft.safeTransferFrom(
        publisher_wallet.address,
        consumer_wallet.address,
        1,
        {"from": publisher_wallet},
    )
    transfer_event = receipt.events["Transfer"]

    assert transfer_event["from"] == publisher_wallet.address
    assert transfer_event["to"] == consumer_wallet.address
    assert data_nft.isERC20Deployer(consumer_wallet.address)

    # Creates an ERC20
    receipt = data_nft.create_datatoken(
        template_index=1,
        name="DT1",
        symbol="DT1Symbol",
        minter=consumer_wallet.address,
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
    datatoken = Datatoken(config, datatoken_address)

    assert not datatoken.isMinter(publisher_wallet.address)
    assert datatoken.isMinter(consumer_wallet.address)
    datatoken.addMinter(publisher_wallet.address, {"from": consumer_wallet})
    assert datatoken.getPermissions(publisher_wallet.address)[
        0
    ]  # publisher is minter now

    OCEAN = publisher_ocean.OCEAN_token
    OCEAN.approve(factory_router.address, to_wei(10000), {"from": consumer_wallet})

    # Make consumer the publish_market_order_fee_address instead of publisher
    receipt = datatoken.setPublishingMarketFee(
        consumer_wallet.address,
        OCEAN.address,
        to_wei(1),
        {"from": publisher_wallet},
    )

    set_publishing_fee_event = receipt.events["PublishMarketFeeChanged"]
    assert set_publishing_fee_event, "Cannot find PublishMarketFeeChanged event."

    publish_fees = datatoken.getPublishingMarketFee()
    assert publish_fees[0] == consumer_wallet.address
    assert publish_fees[1] == OCEAN.address
    assert publish_fees[2] == to_wei(1)


def test_nft_transfer_with_fre(
    config,
    OCEAN,
    publisher_wallet,
    consumer_wallet,
    data_NFT_and_DT,
):
    """Tests transferring the NFT before deploying an ERC20, a FRE."""
    data_nft, datatoken = data_NFT_and_DT

    receipt = data_nft.safeTransferFrom(
        publisher_wallet.address,
        consumer_wallet.address,
        1,
        {"from": publisher_wallet},
    )
    transfer_event = receipt.events["Transfer"]

    assert transfer_event["from"] == publisher_wallet.address
    assert transfer_event["to"] == consumer_wallet.address
    assert data_nft.balanceOf(consumer_wallet.address) == 1
    assert data_nft.balanceOf(publisher_wallet.address) == 0
    assert data_nft.isERC20Deployer(consumer_wallet.address) is True
    assert data_nft.ownerOf(1) == consumer_wallet.address

    # The newest owner of the NFT (consumer wallet) has ERC20 deployer role & can deploy an exchange
    (exchange, tx) = datatoken.create_exchange(
        rate=to_wei(1),
        base_token_addr=OCEAN.address,
        publish_market_fee_amount=to_wei(0.01),
        with_mint=True,
        tx_dict={"from": consumer_wallet},
    )

    # Exchange should have supply and fees setup
    # (Don't test thoroughly here, since exchange has its own unit tests)
    details = exchange.details
    details.owner == consumer_wallet.address
    assert details.datatoken == datatoken.address
    assert details.fixed_rate == to_wei(1)

    # Can this new NFT owner buy, sell, and collect like we'd expect?
    datatoken.approve(exchange.address, to_wei(100), {"from": consumer_wallet})
    OCEAN.approve(exchange.address, to_wei(100), {"from": consumer_wallet})

    DT_supply1 = exchange.details.dt_supply
    DT_bought = to_wei(2)
    exchange.buy_DT(DT_bought, {"from": consumer_wallet})
    assert exchange.details.dt_supply == DT_supply1 - DT_bought
    assert datatoken.balanceOf(consumer_wallet) == DT_bought

    DT_supply1 = exchange.details.dt_supply
    exchange.sell_DT(DT_bought, {"from": consumer_wallet})
    assert exchange.details.dt_supply == DT_supply1 + DT_bought
    assert datatoken.balanceOf(consumer_wallet) == 0

    exchange.collect_DT(to_wei(1), {"from": consumer_wallet})
    assert datatoken.balanceOf(consumer_wallet) == to_wei(1)


def test_nft_transfer_with_fre(
    config,
    OCEAN,
    publisher_wallet,
    consumer_wallet,
    data_nft_factory: DataNFTFactoryContract,
):
    """Tests transferring the NFT after deploying an ERC20, a pool, a FRE."""
    receipt = data_nft_factory.deployERC721Contract(
        "NFT to TRANSFER",
        "NFTtT",
        1,
        ZERO_ADDRESS,
        consumer_wallet.address,
        "https://oceanprotocol.com/nft/",
        True,
        publisher_wallet.address,
        {"from": publisher_wallet},
    )
    registered_event = receipt.events["NFTCreated"]
    assert registered_event["admin"] == publisher_wallet.address
    token_address = registered_event["newTokenAddress"]
    data_nft = DataNFT(config, token_address)
    assert data_nft.contract.name() == "NFT to TRANSFER"
    assert data_nft.symbol() == "NFTtT"

    # Creates an ERC20
    receipt = data_nft.create_datatoken(
        template_index=1,
        name="DT1",
        symbol="DT1Symbol",
        minter=publisher_wallet.address,
        fee_manager=publisher_wallet.address,
        publish_market_order_fee_address=publisher_wallet.address,
        publish_market_order_fee_token=ZERO_ADDRESS,
        publish_market_order_fee_amount=0,
        bytess=[b""],
        transaction_parameters={"from": publisher_wallet},
        wrap_as_object=False,
    )
    assert receipt, "Failed to create ERC20 token."
    registered_token_event = receipt.events["TokenCreated"]
    assert registered_token_event, "Cannot find TokenCreated event."
    datatoken_address = registered_token_event["newTokenAddress"]
    datatoken = Datatoken(config, datatoken_address)
    assert datatoken.isMinter(publisher_wallet.address)

    # The NFT owner (publisher) has ERC20 deployer role & can deploy an exchange
    (exchange, tx) = datatoken.create_exchange(
        rate=to_wei(1),
        base_token_addr=OCEAN.address,
        publish_market_fee=to_wei(0.01),
        tx_dict={"from": publisher_wallet},
    )

    # Exchange should have supply and fees setup
    # (Don't test thoroughly here, since exchange has its own unit tests)
    details = exchange.details
    assert details.owner == publisher_wallet.address
    assert details.datatoken == datatoken.address
    assert details.fixed_rate == to_wei(1)

    # Now do a transfer
    receipt = data_nft.safeTransferFrom(
        publisher_wallet.address,
        consumer_wallet.address,
        1,
        {"from": publisher_wallet},
    )
    transfer_event = receipt.events["Transfer"]

    assert transfer_event["from"] == publisher_wallet.address
    assert transfer_event["to"] == consumer_wallet.address
    assert data_nft.balanceOf(consumer_wallet) == 1
    assert data_nft.balanceOf(publisher_wallet) == 0
    assert data_nft.isERC20Deployer(consumer_wallet)
    assert data_nft.ownerOf(1) == consumer_wallet
    permissions = datatoken.getPermissions(consumer_wallet)
    assert not permissions[0]  # the newest owner is not the minter
    datatoken.addMinter(consumer_wallet, {"from": consumer_wallet})
    assert datatoken.permissions(consumer_wallet)[0]

    # Consumer wallet has not become the owner of the publisher's exchange
    details = exchange.details
    assert details.owner == publisher_wallet.address
    assert details.active
