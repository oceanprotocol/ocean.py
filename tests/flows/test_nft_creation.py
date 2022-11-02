#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from brownie.network.transaction import TransactionReceipt
from web3.main import Web3

from ocean_lib.models.data_nft import DataNFT, DataNFTPermissions
from ocean_lib.models.data_nft_factory import DataNFTFactoryContract
from ocean_lib.models.datatoken import Datatoken
from ocean_lib.ocean.util import get_address_of_type
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from tests.resources.helper_functions import (
    deploy_erc721_erc20,
    get_non_existent_nft_template,
)


@pytest.mark.unit
def test_data_nft_roles(
    config, publisher_wallet, consumer_wallet, another_consumer_wallet
):
    """Test erc721 implicit and explicit role assignments  as well as removing them"""

    # NFT Owner is also added as manager when deploying (first time), if transferred that doesn't apply

    data_nft_factory = DataNFTFactoryContract(
        config, get_address_of_type(config, "ERC721Factory")
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

    receipt = TransactionReceipt(tx)
    assert "NFTCreated" in receipt.events
    assert receipt.events["NFTCreated"]["admin"] == publisher_wallet.address

    token_address = receipt.events["NFTCreated"]["newTokenAddress"]
    data_nft = DataNFT(config, token_address)

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
def test_nonexistent_template_index(config, publisher_wallet):
    """Test erc721 non existent template creation fail"""

    data_nft_factory = DataNFTFactoryContract(
        config, get_address_of_type(config, "ERC721Factory")
    )

    non_existent_nft_template = get_non_existent_nft_template(
        data_nft_factory, check_first=10
    )
    assert non_existent_nft_template >= 0, "Non existent NFT template not found."

    with pytest.raises(Exception, match="Template index doesnt exist"):
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


@pytest.mark.unit
def test_successful_data_nft_creation(config, publisher_wallet):
    """Test data NFT successful creation"""

    data_nft_factory = DataNFTFactoryContract(
        config, get_address_of_type(config, "ERC721Factory")
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

    receipt = TransactionReceipt(tx)
    assert "NFTCreated" in receipt.events
    assert receipt.events["NFTCreated"]["admin"] == publisher_wallet.address

    token_address = receipt.events["NFTCreated"]["newTokenAddress"]
    data_nft = DataNFT(config, token_address)
    owner_balance = data_nft.balance_of(publisher_wallet.address)
    assert data_nft.contract.name() == "NFT"
    assert data_nft.symbol() == "NFTSYMBOL"
    assert owner_balance == 1


@pytest.mark.unit
def test_nft_count(config, publisher_wallet):
    """Test  erc721 factory NFT count"""

    data_nft_factory = DataNFTFactoryContract(
        config, get_address_of_type(config, "ERC721Factory")
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
def test_nft_template(config):
    """Tests get NFT template"""

    data_nft_factory = DataNFTFactoryContract(
        config, get_address_of_type(config, "ERC721Factory")
    )
    nft_template = data_nft_factory.get_nft_template(1)
    assert nft_template[0] == get_address_of_type(config, "ERC721Template")
    assert nft_template[1] is True


@pytest.mark.unit
def test_datatoken_creation(
    config, publisher_wallet, consumer_wallet, another_consumer_wallet
):
    """Test erc20 successful creation with owner assigned as minter"""

    data_nft_factory = DataNFTFactoryContract(
        config, get_address_of_type(config, "ERC721Factory")
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

    token_address = TransactionReceipt(tx).events["NFTCreated"]["newTokenAddress"]
    data_nft = DataNFT(config, token_address)
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
    datatoken_address = TransactionReceipt(tx).events["NFTCreated"]["newTokenAddress"]

    datatoken = Datatoken(config, datatoken_address)

    permissions = datatoken.get_permissions(publisher_wallet.address)

    assert permissions[0], "Not a minter"
    assert tx_result, "Error creating datatoken."

    # Tests failed creation of datatoken
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
def test_datatoken_mint_function(config, publisher_wallet, consumer_wallet, datatoken):
    """Test datatoken failed/successful mint function"""
    datatoken.mint(publisher_wallet.address, 10, {"from": publisher_wallet})
    datatoken.mint(consumer_wallet.address, 20, {"from": publisher_wallet})

    assert datatoken.balanceOf(publisher_wallet.address) == 10
    assert datatoken.balanceOf(consumer_wallet.address) == 20

    # Tests failed mint
    with pytest.raises(Exception, match="NOT MINTER"):
        datatoken.mint(publisher_wallet.address, 10, {"from": consumer_wallet})

    # Test with another minter
    _, datatoken_2 = deploy_erc721_erc20(config, publisher_wallet, consumer_wallet)

    datatoken_2.mint(publisher_wallet.address, 10, {"from": consumer_wallet})
    datatoken_2.mint(consumer_wallet.address, 20, {"from": consumer_wallet})

    assert datatoken.balanceOf(publisher_wallet.address) == 10
    assert datatoken.balanceOf(consumer_wallet.address) == 20


@pytest.mark.unit
def test_datatoken_set_data(config, publisher_wallet, data_nft, datatoken):
    """Test erc20 data set functions"""

    """This is a special metadata, it's callable only from the erc20Token contract and
    can be done only by who has deployERC20 rights(rights to create new erc20 token contract)
    the value is stored into the 725Y standard with a predefined key which is the erc20Token address"""

    key = Web3.keccak(hexstr=datatoken.address)
    value = b"SomeData"

    assert data_nft.get_data(key) == "0x"
    datatoken.setData(value, {"from": publisher_wallet})

    assert data_nft.get_data(key).hex() == value.hex()
    """This one is the generic version of updating data into the key-value story.
    Only users with 'store' permission can do that.
    NOTE: in this function the key is chosen by the caller."""

    data_nft.set_new_data(b"arbitrary text", value, publisher_wallet)

    res = data_nft.get_data(b"arbitrary text")

    assert res.hex() == value.hex()


@pytest.mark.unit
def test_nft_owner_transfer(
    config, publisher_wallet, consumer_wallet, data_nft, datatoken
):
    """Test erc721 ownership transfer on token transfer"""

    assert data_nft.owner_of(1) == publisher_wallet.address

    with pytest.raises(Exception, match="transfer of token that is not own"):
        data_nft.transfer_from(
            consumer_wallet.address, publisher_wallet.address, 1, publisher_wallet
        )
    data_nft.transfer_from(
        publisher_wallet.address, consumer_wallet.address, 1, publisher_wallet
    )

    assert data_nft.balance_of(publisher_wallet.address) == 0
    assert data_nft.owner_of(1) == consumer_wallet.address
    # Owner is not NFT owner anymore, nor has any other role, neither older users
    with pytest.raises(Exception, match="NOT ERC20DEPLOYER_ROLE"):
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

    with pytest.raises(Exception, match="NOT MINTER"):
        datatoken.mint(publisher_wallet.address, 10, {"from": publisher_wallet})

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
    datatoken.addMinter(consumer_wallet.address, {"from": consumer_wallet})

    datatoken.mint(consumer_wallet.address, 20, {"from": consumer_wallet})

    assert datatoken.balanceOf(consumer_wallet.address) == 20
