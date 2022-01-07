#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import time
import uuid
from unittest.mock import patch

import pytest
from ocean_lib.agreements.file_objects import FilesTypeFactory
from ocean_lib.agreements.service_types import ServiceTypes
from ocean_lib.assets.asset import Asset
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.exceptions import InsufficientBalance
from ocean_lib.models.erc721_factory import ERC721FactoryContract
from ocean_lib.models.models_structures import ErcCreateData
from ocean_lib.services.service import Service
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from tests.resources.ddo_helpers import (
    build_credentials_dict,
    get_resource_path,
    get_sample_ddo,
    wait_for_update,
)
from tests.resources.helper_functions import (
    deploy_erc721_erc20,
    get_address_of_type,
    create_basics,
)


def create_asset(ocean, publisher, config, metadata=None):
    """Helper function for asset creation based on ddo_sa_sample.json."""
    erc20_data = ErcCreateData(
        template_index=1,
        strings=["Datatoken 1", "DT1"],
        addresses=[
            publisher.address,
            publisher.address,
            ZERO_ADDRESS,
            get_address_of_type(config, "Ocean"),
        ],
        uints=[ocean.web3.toWei("0.5", "ether"), 0],
        bytess=[b""],
    )

    if not metadata:
        metadata = {
            "created": "2020-11-15T12:27:48Z",
            "updated": "2021-05-17T21:58:02Z",
            "description": "Sample description",
            "name": "Sample asset",
            "type": "dataset",
            "author": "OPF",
            "license": "https://market.oceanprotocol.com/terms",
        }
    data_provider = DataServiceProvider
    file1_dict = {"type": "url", "url": "https://url.com/file1.csv", "method": "GET"}
    file1 = FilesTypeFactory(file1_dict)
    encrypt_response = data_provider.encrypt(
        [file1], "http://172.15.0.4:8030/api/services/encrypt"
    )
    encrypted_files = encrypt_response.content.decode("utf-8")

    ddo = ocean.assets.create(
        metadata, publisher, encrypted_files, erc20_tokens_data=[erc20_data]
    )

    return ddo


def test_register_asset(publisher_ocean_instance, publisher_wallet, consumer_wallet):
    """Test various paths for asset registration.

    Happy paths are tested in the publish flow."""
    ocn = publisher_ocean_instance

    invalid_did = "did:op:0123456789"
    assert ocn.assets.resolve(invalid_did) is None


@pytest.mark.skip(reason="TODO: update function on OceanAssets class")
def test_update(publisher_ocean_instance, publisher_wallet, consumer_wallet, config):
    ocn = publisher_ocean_instance
    block = ocn.web3.eth.block_number
    alice = publisher_wallet
    bob = consumer_wallet

    ddo = create_asset(ocn, alice, config)

    # Publish the metadata
    _name = "updated name"
    ddo.metadata["name"] = _name
    assert ddo.metadata["name"] == _name, "Asset's name was not updated."

    with pytest.raises(ValueError):
        ocn.assets.update(ddo, bob)

    _ = ocn.assets.update(ddo, alice)
    block_confirmations = ocn.config.block_confirmations.value

    log = ddo_reg.get_event_log(
        ddo_reg.EVENT_METADATA_UPDATED, block - block_confirmations, asset_id, 30
    )
    assert log, "no ddo updated event"
    _asset = wait_for_update(ocn, ddo.did, "name", _name)
    assert _asset, "Cannot read asset after update."
    assert (
        _asset.metadata["main"]["name"] == _name
    ), "updated asset does not have the new updated name !!!"

    assert (
        ocn.assets.owner(ddo.did) == alice.address
    ), "asset owner does not seem correct."

    assert (
        _get_num_assets(alice.address) == num_assets_owned + 1
    ), "The new asset was not published in Alice wallet."


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


def test_ocean_assets_validate(publisher_ocean_instance):
    """Tests that the validate function returns an error for invalid metadata."""
    ddo_dict = get_sample_ddo()
    ddo = Asset.from_dict(ddo_dict)

    assert publisher_ocean_instance.assets.validate(
        ddo
    ), "asset should be valid, unless the schema changed."


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


def test_download_fails(publisher_ocean_instance, publisher_wallet):
    """Tests failures of assets download function."""
    with patch("ocean_lib.ocean.ocean_assets.OceanAssets.resolve") as mock:
        mock.return_value = Asset.from_dict(get_sample_ddo())
        asset = mock.return_value
        with pytest.raises(AssertionError):
            publisher_ocean_instance.assets.download_asset(
                asset, "", publisher_wallet, "", "", DataServiceProvider, [], index=-4
            )
        with pytest.raises(TypeError):
            publisher_ocean_instance.assets.download_asset(
                asset,
                "",
                publisher_wallet,
                "",
                "",
                DataServiceProvider,
                [],
                index="string_index",
            )


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


@pytest.mark.skip(reason="TODO: pay_for_service function on OceanAssets class")
def test_pay_for_service_insufficient_balance(
    publisher_ocean_instance, publisher_wallet
):
    """Tests if balance is lower than the purchased amount."""
    #  FIXME: this test still has v3 structure, please adapt
    ocn = publisher_ocean_instance
    alice = publisher_wallet

    sample_ddo_path = get_resource_path("ddo", "ddo_sa_sample.json")
    asset = Asset(json_filename=sample_ddo_path)
    asset.metadata["main"]["files"][0]["checksum"] = str(uuid.uuid4())

    token = ocn.create_data_token(
        "DataToken1", "DT1", from_wallet=alice, blob="foo_blob"
    )

    with pytest.raises(InsufficientBalance):
        ocn.assets.pay_for_service(
            ocn.web3,
            10000000000000,
            token.address,
            asset.did,
            0,
            ZERO_ADDRESS,
            alice,
            alice.address,
        )


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
        "NFT1",
        "NFTSYMBOL",
        1,
        ZERO_ADDRESS,
        "https://oceanprotocol.com/nft/",
        publisher_wallet,
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

    erc20_data = ErcCreateData(
        template_index=1,
        strings=["Datatoken 1", "DT1"],
        addresses=[
            publisher_wallet.address,
            publisher_wallet.address,
            ZERO_ADDRESS,
            get_address_of_type(config, "Ocean"),
        ],
        uints=[web3.toWei("0.5", "ether"), 0],
        bytess=[b""],
    )

    ddo = publisher_ocean_instance.assets.create(
        metadata=metadata,
        publisher_wallet=publisher_wallet,
        encrypted_files=encrypted_files,
        erc721_address=erc721_address,
        erc20_tokens_data=[erc20_data],
    )
    assert ddo, "The asset is not created."
    assert ddo.nft["name"] == "NFT1"
    assert ddo.nft["symbol"] == "NFTSYMBOL"
    assert ddo.nft["address"] == erc721_address
    assert ddo.nft["owner"] == publisher_wallet.address
    assert ddo.datatokens[0]["name"] == "Datatoken 1"
    assert ddo.datatokens[0]["symbol"] == "DT1"
    assert ddo.credentials == build_credentials_dict()


def test_plain_asset_multiple_datatokens(
    publisher_ocean_instance, publisher_wallet, config
):
    web3 = publisher_ocean_instance.web3
    data_provider = DataServiceProvider
    erc721_factory, metadata, encrypted_files = create_basics(
        config, web3, data_provider
    )

    tx = erc721_factory.deploy_erc721_contract(
        "NFT2",
        "NFT2SYMBOL",
        1,
        ZERO_ADDRESS,
        "https://oceanprotocol.com/nft/",
        publisher_wallet,
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

    erc20_data1 = ErcCreateData(
        template_index=1,
        strings=["Datatoken 2", "DT2"],
        addresses=[
            publisher_wallet.address,
            publisher_wallet.address,
            ZERO_ADDRESS,
            get_address_of_type(config, "Ocean"),
        ],
        uints=[web3.toWei("0.5", "ether"), 0],
        bytess=[b""],
    )
    erc20_data2 = ErcCreateData(
        template_index=1,
        strings=["Datatoken 3", "DT3"],
        addresses=[
            publisher_wallet.address,
            publisher_wallet.address,
            ZERO_ADDRESS,
            get_address_of_type(config, "Ocean"),
        ],
        uints=[web3.toWei("0.5", "ether"), 0],
        bytess=[b""],
    )

    ddo = publisher_ocean_instance.assets.create(
        metadata=metadata,
        publisher_wallet=publisher_wallet,
        encrypted_files=encrypted_files,
        erc721_address=erc721_address2,
        erc20_tokens_data=[erc20_data1, erc20_data2],
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

    data_token_names = []
    for data_token in ddo.datatokens:
        data_token_names.append(data_token["name"])
    assert data_token_names[0] == "Datatoken 2"
    assert data_token_names[1] == "Datatoken 3"


def test_plain_asset_multiple_services(
    publisher_ocean_instance, publisher_wallet, config
):
    erc721_token, erc20_token = deploy_erc721_erc20(
        publisher_ocean_instance.web3, config, publisher_wallet, publisher_wallet
    )

    web3 = publisher_ocean_instance.web3
    data_provider = DataServiceProvider
    _, metadata, encrypted_files = create_basics(config, web3, data_provider)

    access_service = Service(
        service_id="0",
        service_type=ServiceTypes.ASSET_ACCESS,
        service_endpoint=f"{data_provider.get_url(config)}/api/services/download",
        data_token=erc20_token.address,
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
        service_endpoint=f"{data_provider.get_url(config)}/api/services/compute",
        data_token=erc20_token.address,
        files=encrypted_files,
        timeout=3600,
        compute_values=compute_values,
    )

    ddo = publisher_ocean_instance.assets.create(
        metadata=metadata,
        publisher_wallet=publisher_wallet,
        encrypted_files=encrypted_files,
        services=[access_service, compute_service],
        erc721_address=erc721_token.address,
        deployed_erc20_tokens=[erc20_token],
    )
    assert ddo, "The asset is not created."
    assert ddo.nft["name"] == "NFT"
    assert ddo.nft["symbol"] == "NFTSYMBOL"
    assert ddo.nft["address"] == erc721_token.address
    assert ddo.nft["owner"] == publisher_wallet.address
    assert ddo.datatokens[0]["name"] == "ERC20DT1"
    assert ddo.datatokens[0]["symbol"] == "ERC20DT1Symbol"
    assert ddo.datatokens[0]["address"] == erc20_token.address
    assert ddo.credentials == build_credentials_dict()
    assert ddo.services[1].compute_values == compute_values


def test_encrypted_asset(publisher_ocean_instance, publisher_wallet, config):
    erc721_token, erc20_token = deploy_erc721_erc20(
        publisher_ocean_instance.web3, config, publisher_wallet, publisher_wallet
    )

    web3 = publisher_ocean_instance.web3
    data_provider = DataServiceProvider
    _, metadata, encrypted_files = create_basics(config, web3, data_provider)

    ddo = publisher_ocean_instance.assets.create(
        metadata=metadata,
        publisher_wallet=publisher_wallet,
        encrypted_files=encrypted_files,
        erc721_address=erc721_token.address,
        deployed_erc20_tokens=[erc20_token],
        encrypt_flag=True,
    )
    assert ddo, "The asset is not created."
    assert ddo.nft["name"] == "NFT"
    assert ddo.nft["symbol"] == "NFTSYMBOL"
    assert ddo.nft["address"] == erc721_token.address
    assert ddo.nft["owner"] == publisher_wallet.address
    assert ddo.datatokens[0]["name"] == "ERC20DT1"
    assert ddo.datatokens[0]["symbol"] == "ERC20DT1Symbol"
    assert ddo.datatokens[0]["address"] == erc20_token.address


def test_compressed_asset(publisher_ocean_instance, publisher_wallet, config):
    erc721_token, erc20_token = deploy_erc721_erc20(
        publisher_ocean_instance.web3, config, publisher_wallet, publisher_wallet
    )

    web3 = publisher_ocean_instance.web3
    data_provider = DataServiceProvider
    _, metadata, encrypted_files = create_basics(config, web3, data_provider)

    ddo = publisher_ocean_instance.assets.create(
        metadata=metadata,
        publisher_wallet=publisher_wallet,
        encrypted_files=encrypted_files,
        erc721_address=erc721_token.address,
        deployed_erc20_tokens=[erc20_token],
        compress_flag=True,
    )
    assert ddo, "The asset is not created."
    assert ddo.nft["name"] == "NFT"
    assert ddo.nft["symbol"] == "NFTSYMBOL"
    assert ddo.nft["address"] == erc721_token.address
    assert ddo.nft["owner"] == publisher_wallet.address
    assert ddo.datatokens[0]["name"] == "ERC20DT1"
    assert ddo.datatokens[0]["symbol"] == "ERC20DT1Symbol"
    assert ddo.datatokens[0]["address"] == erc20_token.address


def test_compressed_and_encrypted_asset(
    publisher_ocean_instance, publisher_wallet, config
):
    erc721_token, erc20_token = deploy_erc721_erc20(
        publisher_ocean_instance.web3, config, publisher_wallet, publisher_wallet
    )

    web3 = publisher_ocean_instance.web3
    data_provider = DataServiceProvider
    _, metadata, encrypted_files = create_basics(config, web3, data_provider)

    ddo = publisher_ocean_instance.assets.create(
        metadata=metadata,
        publisher_wallet=publisher_wallet,
        encrypted_files=encrypted_files,
        erc721_address=erc721_token.address,
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

    # owner can view file urls for his asset
    asset_urls = DataServiceProvider.get_asset_urls(
        ddo.did, ddo.services[0].id, "http://172.15.0.4:8030", publisher_wallet
    )
    file1_dict = {"type": "url", "url": "https://url.com/file1.csv", "method": "GET"}
    file2_dict = {"type": "url", "url": "https://url.com/file2.csv", "method": "GET"}
    assert file1_dict in asset_urls
    assert file2_dict in asset_urls
