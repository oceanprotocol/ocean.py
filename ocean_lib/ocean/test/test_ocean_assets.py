#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import copy
import time
import uuid
from datetime import datetime
from unittest.mock import patch

import eth_keys
import pytest

from ocean_lib.agreements.service_types import ServiceTypes
from ocean_lib.assets.asset import Asset
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.exceptions import AquariusError, ContractNotFound, InsufficientBalance
from ocean_lib.models.erc721_factory import ERC721FactoryContract
from ocean_lib.models.erc721_nft import ERC721NFT
from ocean_lib.services.service import Service
from ocean_lib.structures.file_objects import FilesTypeFactory
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.currency import to_wei
from ocean_lib.web3_internal.wallet import Wallet
from tests.resources.ddo_helpers import (
    build_credentials_dict,
    create_asset,
    create_basics,
    get_first_service_by_type,
    get_sample_ddo,
)
from tests.resources.helper_functions import deploy_erc721_erc20, get_address_of_type


@pytest.mark.integration
def test_register_asset(publisher_ocean_instance, publisher_wallet, consumer_wallet):
    """Test various paths for asset registration.

    Happy paths are tested in the publish flow."""
    ocn = publisher_ocean_instance

    invalid_did = "did:op:0123456789"
    assert ocn.assets.resolve(invalid_did) is None


@pytest.mark.integration
def test_update_metadata(publisher_ocean_instance, publisher_wallet, config):
    """Test the update of metadata"""
    ddo = create_asset(publisher_ocean_instance, publisher_wallet, config)

    new_metadata = copy.deepcopy(ddo.metadata)

    # Update only metadata
    _description = "Updated description"
    new_metadata["description"] = _description
    new_metadata["updated"] = datetime.utcnow().isoformat()
    ddo.metadata = new_metadata

    with patch("ocean_lib.ocean.ocean_assets.ERC721FactoryContract.verify_nft") as mock:
        mock.return_value = False
        with pytest.raises(ContractNotFound):
            _asset = publisher_ocean_instance.assets.update(
                asset=ddo, publisher_wallet=publisher_wallet
            )

    _asset = publisher_ocean_instance.assets.update(
        asset=ddo, publisher_wallet=publisher_wallet
    )

    assert _asset.datatokens == ddo.datatokens
    assert len(_asset.services) == len(ddo.services)
    assert _asset.services[0].as_dictionary() == ddo.services[0].as_dictionary()
    assert _asset.credentials == ddo.credentials
    assert _asset.metadata["description"] == _description
    assert _asset.metadata["updated"] == new_metadata["updated"]


@pytest.mark.integration
def test_update_credentials(publisher_ocean_instance, publisher_wallet, config):
    """Test that the credentials can be updated."""
    ddo = create_asset(publisher_ocean_instance, publisher_wallet, config)

    # Update credentials
    _new_credentials = {
        "allow": [{"type": "address", "values": ["0x123", "0x456"]}],
        "deny": [{"type": "address", "values": ["0x2222", "0x333"]}],
    }

    ddo.credentials = _new_credentials

    _asset = publisher_ocean_instance.assets.update(
        asset=ddo, publisher_wallet=publisher_wallet
    )

    assert _asset.credentials == _new_credentials, "Credentials were not updated."


@pytest.mark.integration
def test_update_datatokens(publisher_ocean_instance, publisher_wallet, config):
    """Test the update of datatokens"""
    ddo = create_asset(publisher_ocean_instance, publisher_wallet, config)
    data_provider = DataServiceProvider
    _, erc20_token = deploy_erc721_erc20(
        publisher_ocean_instance.web3, config, publisher_wallet, publisher_wallet
    )

    file1_dict = {
        "type": "url",
        "url": "https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-abstract10.xml.gz-rss.xml",
        "method": "GET",
    }
    file1 = FilesTypeFactory(file1_dict)
    encrypted_files = publisher_ocean_instance.assets.encrypt_files([file1])

    # Add new existing datatoken with service
    old_asset = copy.deepcopy(ddo)
    access_service = Service(
        service_id="3",
        service_type=ServiceTypes.ASSET_ACCESS,
        service_endpoint=data_provider.get_url(config),
        datatoken=erc20_token.address,
        files=encrypted_files,
        timeout=0,
    )

    ddo.datatokens.append(
        {
            "address": erc20_token.address,
            "name": erc20_token.contract.caller.name(),
            "symbol": erc20_token.symbol(),
            "serviceId": access_service.id,
        }
    )

    ddo.services.append(access_service)

    _asset = publisher_ocean_instance.assets.update(
        asset=ddo, publisher_wallet=publisher_wallet
    )

    assert len(_asset.datatokens) == len(old_asset.datatokens) + 1
    assert len(_asset.services) == len(old_asset.services) + 1
    assert _asset.datatokens[1].get("address") == erc20_token.address
    assert _asset.datatokens[0].get("address") == old_asset.datatokens[0].get("address")
    assert _asset.services[0].datatoken == old_asset.datatokens[0].get("address")
    assert _asset.services[1].datatoken == erc20_token.address

    # Delete datatoken
    new_asset = new_metadata = copy.deepcopy(_asset)
    new_metadata = copy.deepcopy(_asset.metadata)
    _description = "Test delete datatoken"
    new_metadata["description"] = _description
    new_metadata["updated"] = datetime.utcnow().isoformat()

    removed_dt = new_asset.datatokens.pop()

    new_asset.services = [
        service
        for service in new_asset.services
        if service.datatoken != removed_dt.get("address")
    ]

    old_datatokens = _asset.datatokens

    _asset = publisher_ocean_instance.assets.update(
        asset=new_asset, publisher_wallet=publisher_wallet
    )

    assert _asset, "Cannot read asset after update."
    assert len(_asset.datatokens) == 1
    assert _asset.datatokens[0].get("address") == old_datatokens[0].get("address")
    assert _asset.services[0].datatoken == old_datatokens[0].get("address")


@pytest.mark.integration
def test_update_flags(publisher_ocean_instance, publisher_wallet, config):
    """Test the update of flags"""
    ddo = create_asset(publisher_ocean_instance, publisher_wallet, config)

    # Test compress & update flags
    erc721_nft = ERC721NFT(publisher_ocean_instance.web3, ddo.nft_address)

    _asset = publisher_ocean_instance.assets.update(
        asset=ddo,
        publisher_wallet=publisher_wallet,
        compress_flag=True,
        encrypt_flag=True,
    )

    registered_token_event = erc721_nft.get_event_log(
        ERC721NFT.EVENT_METADATA_UPDATED,
        _asset.event.get("block"),
        publisher_ocean_instance.web3.eth.block_number,
        None,
    )

    assert registered_token_event[0].args.get("flags") == bytes([3])


@pytest.mark.integration
def test_ocean_assets_search(publisher_ocean_instance, publisher_wallet, config):
    """Tests that a created asset can be searched successfully."""
    identifier = str(uuid.uuid1()).replace("-", "")
    metadata = {
        "created": "2020-11-15T12:27:48Z",
        "updated": "2021-05-17T21:58:02Z",
        "description": "Sample description",
        "name": identifier,
        "type": "dataset",
        "author": "OPF",
        "license": "https://market.oceanprotocol.com/terms",
    }

    assert (
        len(publisher_ocean_instance.assets.search(identifier)) == 0
    ), "Asset search failed."

    create_asset(publisher_ocean_instance, publisher_wallet, config, metadata)

    time.sleep(1)  # apparently changes are not instantaneous
    assert (
        len(publisher_ocean_instance.assets.search(identifier)) == 1
    ), "Searched for the occurrences of the identifier failed. "

    assert (
        len(
            publisher_ocean_instance.assets.query(
                {
                    "query": {
                        "query_string": {
                            "query": identifier,
                            "fields": ["metadata.name"],
                        }
                    }
                }
            )
        )
        == 1
    ), "Query failed.The identifier was not found in the name."
    assert (
        len(
            publisher_ocean_instance.assets.query(
                {
                    "query": {
                        "query_string": {
                            "query": "Gorilla",
                            "fields": ["metadata.name"],
                        }
                    }
                }
            )
        )
        == 0
    )


@pytest.mark.integration
def test_ocean_assets_validate(publisher_ocean_instance):
    """Tests that the validate function returns an error for invalid metadata."""
    ddo_dict = get_sample_ddo()
    ddo = Asset.from_dict(ddo_dict)

    assert publisher_ocean_instance.assets.validate(
        ddo
    ), "asset should be valid, unless the schema changed."

    ddo_dict = get_sample_ddo()
    ddo_dict["id"] = "something not conformant"
    ddo = Asset.from_dict(ddo_dict)

    with pytest.raises(ValueError):
        publisher_ocean_instance.assets.validate(ddo)


@pytest.mark.integration
def test_ocean_assets_algorithm(publisher_ocean_instance, publisher_wallet, config):
    """Tests the creation of an algorithm DDO."""
    metadata = {
        "created": "2020-11-15T12:27:48Z",
        "updated": "2021-05-17T21:58:02Z",
        "description": "Sample description",
        "name": "Sample algorithm asset",
        "type": "algorithm",
        "author": "OPF",
        "license": "https://market.oceanprotocol.com/terms",
        "algorithm": {
            "language": "scala",
            "format": "docker-image",
            "version": "0.1",
            "container": {
                "entrypoint": "node $ALGO",
                "image": "node",
                "tag": "10",
                "checksum": "test",
            },
        },
    }

    ddo = create_asset(publisher_ocean_instance, publisher_wallet, config, metadata)
    assert ddo, "DDO None. The ddo is not cached after the creation."


@pytest.mark.unit
def test_download_fails(publisher_ocean_instance, publisher_wallet):
    """Tests failures of assets download function."""
    with patch("ocean_lib.ocean.ocean_assets.OceanAssets.resolve") as mock:
        asset = Asset.from_dict(get_sample_ddo())
        mock.return_value = asset
        with pytest.raises(AssertionError):
            publisher_ocean_instance.assets.download_asset(
                asset, asset.services[0], publisher_wallet, "", "", index=-4
            )
        with pytest.raises(TypeError):
            publisher_ocean_instance.assets.download_asset(
                asset, asset.services[0], publisher_wallet, "", "", index="string_index"
            )


@pytest.mark.integration
def test_create_bad_metadata(publisher_ocean_instance, publisher_wallet, config):
    """Tests that we can't create the asset with plecos failure."""
    metadata = {
        "created": "2020-11-15T12:27:48Z",
        "updated": "2021-05-17T21:58:02Z",
        "description": "Sample description",
        # name missing intentionally
        "type": "dataset",
        "author": "OPF",
        "license": "https://market.oceanprotocol.com/terms",
    }
    with pytest.raises(AssertionError):
        create_asset(publisher_ocean_instance, publisher_wallet, config, metadata)

    metadata["name"] = "Sample asset"
    metadata.pop("type")
    with pytest.raises(AssertionError):
        create_asset(publisher_ocean_instance, publisher_wallet, config, metadata)


@pytest.mark.unit
def test_pay_for_service_insufficient_balance(
    publisher_ocean_instance, config, publisher_wallet
):
    """Tests if balance is lower than the purchased amount."""
    _, erc20_token = deploy_erc721_erc20(
        publisher_ocean_instance.web3, config, publisher_wallet, publisher_wallet
    )

    ddo_dict = copy.deepcopy(get_sample_ddo())
    ddo_dict["services"][0]["datatokenAddress"] = erc20_token.address
    asset = Asset.from_dict(ddo_dict)

    empty_account = publisher_ocean_instance.web3.eth.account.create()
    pk = eth_keys.KeyAPI.PrivateKey(empty_account.key)
    empty_wallet = Wallet(
        publisher_ocean_instance.web3,
        str(pk),
        block_confirmations=config.block_confirmations,
        transaction_timeout=config.transaction_timeout,
    )

    with pytest.raises(InsufficientBalance):
        publisher_ocean_instance.assets.pay_for_service(
            asset,
            get_first_service_by_type(asset, "access"),
            consume_market_fee_address=empty_wallet.address,
            consume_market_fee_token=erc20_token.address,
            consume_market_fee_amount=0,
            wallet=empty_wallet,
        )


@pytest.mark.integration
def test_plain_asset_with_one_datatoken(
    publisher_ocean_instance, publisher_wallet, config
):
    web3 = publisher_ocean_instance.web3
    data_provider = DataServiceProvider

    erc721_factory, metadata, encrypted_files = create_basics(
        config, web3, data_provider
    )

    # Publisher deploys NFT contract
    tx = erc721_factory.deploy_erc721_contract(
        name="NFT1",
        symbol="NFTSYMBOL",
        template_index=1,
        additional_metadata_updater=ZERO_ADDRESS,
        additional_erc20_deployer=ZERO_ADDRESS,
        token_uri="https://oceanprotocol.com/nft/",
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
    erc721_address = registered_event[0].args.newTokenAddress

    ddo = publisher_ocean_instance.assets.create(
        metadata=metadata,
        publisher_wallet=publisher_wallet,
        encrypted_files=encrypted_files,
        erc721_address=erc721_address,
        erc20_templates=[1],
        erc20_names=["Datatoken 1"],
        erc20_symbols=["DT1"],
        erc20_minters=[publisher_wallet.address],
        erc20_fee_managers=[publisher_wallet.address],
        erc20_publish_market_addresses=[ZERO_ADDRESS],
        erc20_publish_market_fee_tokens=[get_address_of_type(config, "Ocean")],
        erc20_caps=[to_wei("0.5")],
        erc20_publish_market_fee_amounts=[0],
        erc20_bytess=[[b""]],
    )
    assert ddo, "The asset is not created."
    assert ddo.nft["name"] == "NFT1"
    assert ddo.nft["symbol"] == "NFTSYMBOL"
    assert ddo.nft["address"] == erc721_address
    assert ddo.nft["owner"] == publisher_wallet.address
    assert ddo.datatokens[0]["name"] == "Datatoken 1"
    assert ddo.datatokens[0]["symbol"] == "DT1"
    assert ddo.credentials == build_credentials_dict()


@pytest.mark.integration
def test_plain_asset_multiple_datatokens(
    publisher_ocean_instance, publisher_wallet, config
):
    web3 = publisher_ocean_instance.web3
    data_provider = DataServiceProvider
    erc721_factory, metadata, encrypted_files = create_basics(
        config, web3, data_provider
    )

    tx = erc721_factory.deploy_erc721_contract(
        name="NFT2",
        symbol="NFT2SYMBOL",
        template_index=1,
        additional_metadata_updater=ZERO_ADDRESS,
        additional_erc20_deployer=ZERO_ADDRESS,
        token_uri="https://oceanprotocol.com/nft/",
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
    erc721_address2 = registered_event[0].args.newTokenAddress

    ddo = publisher_ocean_instance.assets.create(
        metadata=metadata,
        publisher_wallet=publisher_wallet,
        encrypted_files=encrypted_files,
        erc721_address=erc721_address2,
        erc20_templates=[1, 1],
        erc20_names=["Datatoken 2", "Datatoken 3"],
        erc20_symbols=["DT2", "DT3"],
        erc20_minters=[publisher_wallet.address, publisher_wallet.address],
        erc20_fee_managers=[publisher_wallet.address, publisher_wallet.address],
        erc20_publish_market_addresses=[ZERO_ADDRESS, ZERO_ADDRESS],
        erc20_publish_market_fee_tokens=[
            get_address_of_type(config, "Ocean"),
            get_address_of_type(config, "Ocean"),
        ],
        erc20_caps=[to_wei("0.5"), to_wei("0.5")],
        erc20_publish_market_fee_amounts=[0, 0],
        erc20_bytess=[[b""], [b""]],
    )
    assert ddo, "The asset is not created."
    assert ddo.nft["name"] == "NFT2"
    assert ddo.nft["symbol"] == "NFT2SYMBOL"
    assert ddo.nft["address"] == erc721_address2
    assert ddo.nft["owner"] == publisher_wallet.address
    assert ddo.datatokens[0]["name"] == "Datatoken 2"
    assert ddo.datatokens[0]["symbol"] == "DT2"
    assert ddo.datatokens[1]["name"] == "Datatoken 3"
    assert ddo.datatokens[1]["symbol"] == "DT3"
    assert len(ddo.services) == 2
    assert len(ddo.datatokens) == 2
    assert ddo.credentials == build_credentials_dict()

    datatoken_names = []
    for datatoken in ddo.datatokens:
        datatoken_names.append(datatoken["name"])
    assert datatoken_names[0] == "Datatoken 2"
    assert datatoken_names[1] == "Datatoken 3"


@pytest.mark.integration
def test_plain_asset_multiple_services(
    publisher_ocean_instance, publisher_wallet, config
):
    erc721_nft, erc20_token = deploy_erc721_erc20(
        publisher_ocean_instance.web3, config, publisher_wallet, publisher_wallet
    )

    web3 = publisher_ocean_instance.web3
    data_provider = DataServiceProvider
    _, metadata, encrypted_files = create_basics(config, web3, data_provider)

    access_service = Service(
        service_id="0",
        service_type=ServiceTypes.ASSET_ACCESS,
        service_endpoint=data_provider.get_url(config),
        datatoken=erc20_token.address,
        files=encrypted_files,
        timeout=0,
    )

    # Set the compute values for compute service
    compute_values = {
        "namespace": "ocean-compute",
        "cpus": 2,
        "gpus": 4,
        "gpuType": "NVIDIA Tesla V100 GPU",
        "memory": "128M",
        "volumeSize": "2G",
        "allowRawAlgorithm": False,
        "allowNetworkAccess": True,
    }
    compute_service = Service(
        service_id="1",
        service_type=ServiceTypes.CLOUD_COMPUTE,
        service_endpoint=data_provider.get_url(config),
        datatoken=erc20_token.address,
        files=encrypted_files,
        timeout=3600,
        compute_values=compute_values,
    )

    ddo = publisher_ocean_instance.assets.create(
        metadata=metadata,
        publisher_wallet=publisher_wallet,
        encrypted_files=encrypted_files,
        services=[access_service, compute_service],
        erc721_address=erc721_nft.address,
        deployed_erc20_tokens=[erc20_token],
    )
    assert ddo, "The asset is not created."
    assert ddo.nft["name"] == "NFT"
    assert ddo.nft["symbol"] == "NFTSYMBOL"
    assert ddo.nft["address"] == erc721_nft.address
    assert ddo.nft["owner"] == publisher_wallet.address
    assert ddo.datatokens[0]["name"] == "ERC20DT1"
    assert ddo.datatokens[0]["symbol"] == "ERC20DT1Symbol"
    assert ddo.datatokens[0]["address"] == erc20_token.address
    assert ddo.credentials == build_credentials_dict()
    assert ddo.services[1].compute_values == compute_values


@pytest.mark.integration
def test_encrypted_asset(publisher_ocean_instance, publisher_wallet, config):
    erc721_nft, erc20_token = deploy_erc721_erc20(
        publisher_ocean_instance.web3, config, publisher_wallet, publisher_wallet
    )

    web3 = publisher_ocean_instance.web3
    data_provider = DataServiceProvider
    _, metadata, encrypted_files = create_basics(config, web3, data_provider)

    ddo = publisher_ocean_instance.assets.create(
        metadata=metadata,
        publisher_wallet=publisher_wallet,
        encrypted_files=encrypted_files,
        erc721_address=erc721_nft.address,
        deployed_erc20_tokens=[erc20_token],
        encrypt_flag=True,
    )
    assert ddo, "The asset is not created."
    assert ddo.nft["name"] == "NFT"
    assert ddo.nft["symbol"] == "NFTSYMBOL"
    assert ddo.nft["address"] == erc721_nft.address
    assert ddo.nft["owner"] == publisher_wallet.address
    assert ddo.datatokens[0]["name"] == "ERC20DT1"
    assert ddo.datatokens[0]["symbol"] == "ERC20DT1Symbol"
    assert ddo.datatokens[0]["address"] == erc20_token.address


@pytest.mark.integration
def test_compressed_asset(publisher_ocean_instance, publisher_wallet, config):
    erc721_nft, erc20_token = deploy_erc721_erc20(
        publisher_ocean_instance.web3, config, publisher_wallet, publisher_wallet
    )

    web3 = publisher_ocean_instance.web3
    data_provider = DataServiceProvider
    _, metadata, encrypted_files = create_basics(config, web3, data_provider)

    ddo = publisher_ocean_instance.assets.create(
        metadata=metadata,
        publisher_wallet=publisher_wallet,
        encrypted_files=encrypted_files,
        erc721_address=erc721_nft.address,
        deployed_erc20_tokens=[erc20_token],
        compress_flag=True,
    )
    assert ddo, "The asset is not created."
    assert ddo.nft["name"] == "NFT"
    assert ddo.nft["symbol"] == "NFTSYMBOL"
    assert ddo.nft["address"] == erc721_nft.address
    assert ddo.nft["owner"] == publisher_wallet.address
    assert ddo.datatokens[0]["name"] == "ERC20DT1"
    assert ddo.datatokens[0]["symbol"] == "ERC20DT1Symbol"
    assert ddo.datatokens[0]["address"] == erc20_token.address


@pytest.mark.integration
def test_compressed_and_encrypted_asset(
    publisher_ocean_instance, publisher_wallet, config
):
    erc721_nft, erc20_token = deploy_erc721_erc20(
        publisher_ocean_instance.web3, config, publisher_wallet, publisher_wallet
    )

    web3 = publisher_ocean_instance.web3
    data_provider = DataServiceProvider
    _, metadata, encrypted_files = create_basics(config, web3, data_provider)

    ddo = publisher_ocean_instance.assets.create(
        metadata=metadata,
        publisher_wallet=publisher_wallet,
        encrypted_files=encrypted_files,
        erc721_address=erc721_nft.address,
        deployed_erc20_tokens=[erc20_token],
        encrypt_flag=True,
        compress_flag=True,
    )
    assert ddo, "The asset is not created."
    assert ddo.nft["name"] == "NFT"
    assert ddo.nft["symbol"] == "NFTSYMBOL"
    assert ddo.nft["owner"] == publisher_wallet.address
    assert ddo.datatokens[0]["name"] == "ERC20DT1"
    assert ddo.datatokens[0]["symbol"] == "ERC20DT1Symbol"
    assert ddo.datatokens[0]["address"] == erc20_token.address


@pytest.mark.unit
def test_asset_creation_errors(publisher_ocean_instance, publisher_wallet, config):
    erc721_nft, erc20_token = deploy_erc721_erc20(
        publisher_ocean_instance.web3, config, publisher_wallet, publisher_wallet
    )

    web3 = publisher_ocean_instance.web3
    data_provider = DataServiceProvider
    _, metadata, encrypted_files = create_basics(config, web3, data_provider)

    some_random_address = ZERO_ADDRESS
    with pytest.raises(ContractNotFound):
        publisher_ocean_instance.assets.create(
            metadata=metadata,
            publisher_wallet=publisher_wallet,
            encrypted_files=encrypted_files,
            erc721_address=some_random_address,
            deployed_erc20_tokens=[erc20_token],
            encrypt_flag=True,
        )

    with patch("ocean_lib.aquarius.aquarius.Aquarius.ddo_exists") as mock:
        mock.return_value = True
        with pytest.raises(AquariusError):
            publisher_ocean_instance.assets.create(
                metadata=metadata,
                publisher_wallet=publisher_wallet,
                encrypted_files=encrypted_files,
                erc721_address=erc721_nft.address,
                deployed_erc20_tokens=[erc20_token],
                encrypt_flag=True,
            )
