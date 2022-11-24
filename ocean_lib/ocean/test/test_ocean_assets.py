#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import copy
import time
import uuid
from datetime import datetime
from unittest.mock import patch

import brownie
import pytest
from brownie import network
from brownie.network import accounts

from ocean_lib.agreements.service_types import ServiceTypes
from ocean_lib.assets.ddo import DDO
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.exceptions import AquariusError, InsufficientBalance
from ocean_lib.models.data_nft import DataNFT
from ocean_lib.ocean.util import get_address_of_type
from ocean_lib.services.service import Service
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from tests.resources.ddo_helpers import (
    build_credentials_dict,
    create_asset,
    create_basics,
    get_first_service_by_type,
    get_sample_ddo,
)


@pytest.mark.integration
def test_register_asset(publisher_ocean_instance, publisher_wallet, consumer_wallet):
    """Test various paths for asset registration.

    Happy paths are tested in the publish flow."""
    ocean = publisher_ocean_instance

    invalid_did = "did:op:0123456789"
    assert ocean.assets.resolve(invalid_did) is None


@pytest.mark.integration
def test_update_metadata(publisher_ocean_instance, publisher_wallet):
    """Test the update of metadata"""
    ddo = create_asset(publisher_ocean_instance, publisher_wallet)

    new_metadata = copy.deepcopy(ddo.metadata)

    # Update only metadata
    _description = "Updated description"
    new_metadata["description"] = _description
    new_metadata["updated"] = datetime.utcnow().isoformat()
    ddo.metadata = new_metadata

    _ddo = publisher_ocean_instance.assets.update(
        ddo=ddo, publisher_wallet=publisher_wallet
    )

    assert _ddo.datatokens == ddo.datatokens
    assert len(_ddo.services) == len(ddo.services)
    assert _ddo.services[0].as_dictionary() == ddo.services[0].as_dictionary()
    assert _ddo.credentials == ddo.credentials
    assert _ddo.metadata["description"] == _description
    assert _ddo.metadata["updated"] == new_metadata["updated"]


@pytest.mark.integration
def test_update_credentials(publisher_ocean_instance, publisher_wallet):
    """Test that the credentials can be updated."""
    ddo = create_asset(publisher_ocean_instance, publisher_wallet)

    # Update credentials
    _new_credentials = {
        "allow": [{"type": "address", "values": ["0x123", "0x456"]}],
        "deny": [{"type": "address", "values": ["0x2222", "0x333"]}],
    }

    ddo.credentials = _new_credentials

    _ddo = publisher_ocean_instance.assets.update(
        ddo=ddo, publisher_wallet=publisher_wallet
    )

    assert _ddo.credentials == _new_credentials, "Credentials were not updated."


@pytest.mark.integration
def test_update_datatokens(
    publisher_ocean_instance, publisher_wallet, config, datatoken, file2
):
    """Test the update of datatokens"""
    ddo = create_asset(publisher_ocean_instance, publisher_wallet)
    data_provider = DataServiceProvider

    files = [file2]

    # Add new existing datatoken with service
    old_ddo = copy.deepcopy(ddo)
    access_service = Service(
        service_id="3",
        service_type=ServiceTypes.ASSET_ACCESS,
        service_endpoint=data_provider.get_url(config),
        datatoken=datatoken.address,
        files=files,
        timeout=0,
    )

    ddo.datatokens.append(
        {
            "address": datatoken.address,
            "name": datatoken.contract.name(),
            "symbol": datatoken.symbol(),
            "serviceId": access_service.id,
        }
    )

    ddo.services.append(access_service)

    _ddo = publisher_ocean_instance.assets.update(
        ddo=ddo, publisher_wallet=publisher_wallet
    )

    assert len(_ddo.datatokens) == len(old_ddo.datatokens) + 1
    assert len(_ddo.services) == len(old_ddo.services) + 1
    assert _ddo.datatokens[1].get("address") == datatoken.address
    assert _ddo.datatokens[0].get("address") == old_ddo.datatokens[0].get("address")
    assert _ddo.services[0].datatoken == old_ddo.datatokens[0].get("address")
    assert _ddo.services[1].datatoken == datatoken.address

    # Delete datatoken
    new_ddo = copy.deepcopy(_ddo)
    new_metadata = copy.deepcopy(_ddo.metadata)
    _description = "Test delete datatoken"
    new_metadata["description"] = _description
    new_metadata["updated"] = datetime.utcnow().isoformat()

    removed_dt = new_ddo.datatokens.pop()

    new_ddo.services = [
        service
        for service in new_ddo.services
        if service.datatoken != removed_dt.get("address")
    ]

    old_datatokens = _ddo.datatokens

    _ddo = publisher_ocean_instance.assets.update(
        ddo=new_ddo, publisher_wallet=publisher_wallet
    )

    assert _ddo, "Cannot read ddo after update."
    assert len(_ddo.datatokens) == 1
    assert _ddo.datatokens[0].get("address") == old_datatokens[0].get("address")
    assert _ddo.services[0].datatoken == old_datatokens[0].get("address")

    nft_token = publisher_ocean_instance.get_nft_token(_ddo.nft["address"])
    bn = network.chain[-1].number

    updated_event = nft_token.contract.events.get_sequence(bn, bn, "MetadataUpdated")[0]
    assert updated_event.args.updatedBy == publisher_wallet.address

    validation_event = nft_token.contract.events.get_sequence(
        bn, bn, "MetadataValidated"
    )[0]
    assert validation_event.args.validator.startswith("0x")
    assert updated_event.transactionHash == validation_event.transactionHash


@pytest.mark.integration
def test_update_flags(publisher_ocean_instance, publisher_wallet):
    """Test the update of flags"""
    ddo = create_asset(publisher_ocean_instance, publisher_wallet)

    # Test compress & update flags
    data_nft = DataNFT(publisher_ocean_instance.config_dict, ddo.nft_address)

    _ddo = publisher_ocean_instance.assets.update(
        ddo=ddo,
        publisher_wallet=publisher_wallet,
        compress_flag=True,
        encrypt_flag=True,
    )

    registered_token_event = data_nft.contract.events.get_sequence(
        _ddo.event.get("block"),
        network.chain[-1].number,
        "MetadataUpdated",
    )

    assert registered_token_event[0].args.get("flags") == bytes([3])


@pytest.mark.integration
def test_ocean_assets_search(publisher_ocean_instance, publisher_wallet):
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
    ), "DDO search failed."

    create_asset(publisher_ocean_instance, publisher_wallet, metadata)

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
    ddo = DDO.from_dict(ddo_dict)

    assert publisher_ocean_instance.assets.validate(
        ddo
    ), "ddo should be valid, unless the schema changed."

    ddo_dict = get_sample_ddo()
    ddo_dict["id"] = "something not conformant"
    ddo = DDO.from_dict(ddo_dict)

    with pytest.raises(ValueError):
        publisher_ocean_instance.assets.validate(ddo)


@pytest.mark.integration
def test_ocean_assets_algorithm(publisher_ocean_instance, publisher_wallet):
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

    ddo = create_asset(publisher_ocean_instance, publisher_wallet, metadata)
    assert ddo, "DDO None. The ddo is not cached after the creation."


@pytest.mark.unit
def test_download_fails(publisher_ocean_instance, publisher_wallet):
    """Tests failures of assets download function."""
    with patch("ocean_lib.ocean.ocean_assets.OceanAssets.resolve") as mock:
        ddo = DDO.from_dict(get_sample_ddo())
        mock.return_value = ddo
        with pytest.raises(AssertionError):
            publisher_ocean_instance.assets.download_asset(
                ddo,
                publisher_wallet,
                destination="",
                order_tx_id="",
                service=ddo.services[0],
                index=-4,
            )
        with pytest.raises(TypeError):
            publisher_ocean_instance.assets.download_asset(
                ddo,
                publisher_wallet,
                destination="",
                order_tx_id="",
                service=ddo.services[0],
                index="string_index",
            )


@pytest.mark.integration
def test_create_bad_metadata(publisher_ocean_instance, publisher_wallet):
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
        create_asset(publisher_ocean_instance, publisher_wallet, metadata)

    metadata["name"] = "Sample asset"
    metadata.pop("type")
    with pytest.raises(AssertionError):
        create_asset(publisher_ocean_instance, publisher_wallet, metadata)


@pytest.mark.unit
def test_pay_for_access_service_insufficient_balance(
    publisher_ocean_instance, config, publisher_wallet, datatoken
):
    """Tests if balance is lower than the purchased amount."""
    ddo_dict = copy.deepcopy(get_sample_ddo())
    ddo_dict["services"][0]["datatokenAddress"] = datatoken.address
    ddo = DDO.from_dict(ddo_dict)

    empty_wallet = accounts.add()

    with pytest.raises(InsufficientBalance):
        publisher_ocean_instance.assets.pay_for_access_service(
            ddo,
            empty_wallet,
            get_first_service_by_type(ddo, "access"),
            consume_market_order_fee_address=empty_wallet.address,
            consume_market_order_fee_token=datatoken.address,
            consume_market_order_fee_amount=0,
        )


@pytest.mark.integration
def test_create_url_asset(publisher_ocean_instance, publisher_wallet):
    ocean = publisher_ocean_instance

    name = "Branin dataset"
    url = "https://raw.githubusercontent.com/trentmc/branin/main/branin.arff"
    (data_nft, datatoken, ddo) = ocean.assets.create_url_asset(
        name, url, publisher_wallet
    )

    assert ddo.nft["name"] == name  # thorough testing is below, on create() directly
    assert len(ddo.datatokens) == 1


@pytest.mark.integration
def test_create_graphql_asset(publisher_ocean_instance, publisher_wallet):
    ocean = publisher_ocean_instance

    name = "Data NFTs in Ocean"
    url = "https://v4.subgraph.goerli.oceanprotocol.com/subgraphs/name/oceanprotocol/ocean-subgraph"
    query = """query{
                   nfts(orderBy: createdTimestamp,orderDirection:desc){
                        id
                        symbol
                        createdTimestamp
                        }
                   }
    """
    (data_nft, datatoken, ddo) = ocean.assets.create_graphql_asset(
        name, url, query, publisher_wallet
    )

    assert ddo.nft["name"] == name  # thorough testing is below, on create() directly
    assert len(ddo.datatokens) == 1


@pytest.mark.integration
def test_create_onchain_asset(publisher_ocean_instance, publisher_wallet, config):
    ocean = publisher_ocean_instance

    name = "swapOceanFee function call"
    contract_address = get_address_of_type(config, "Router")
    contract_abi = {
        "inputs": [],
        "name": "swapOceanFee",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    }

    (data_nft, datatoken, ddo) = ocean.assets.create_onchain_asset(
        name, contract_address, contract_abi, publisher_wallet
    )

    assert ddo.nft["name"] == name  # thorough testing is below, on create() directly
    assert len(ddo.datatokens) == 1


@pytest.mark.integration
def test_plain_asset_with_one_datatoken(
    publisher_ocean_instance, publisher_wallet, config
):
    data_provider = DataServiceProvider

    data_nft_factory, metadata, files = create_basics(config, data_provider)

    # Publisher deploys NFT contract
    tx_receipt = data_nft_factory.deployERC721Contract(
        "NFT1",
        "NFTSYMBOL",
        1,
        ZERO_ADDRESS,
        ZERO_ADDRESS,
        "https://oceanprotocol.com/nft/",
        True,
        publisher_wallet.address,
        {"from": publisher_wallet},
    )
    registered_event = tx_receipt.events["NFTCreated"]
    assert registered_event["admin"] == publisher_wallet.address
    data_nft_address = registered_event["newTokenAddress"]

    ddo = publisher_ocean_instance.assets.create(
        metadata=metadata,
        publisher_wallet=publisher_wallet,
        files=files,
        data_nft_address=data_nft_address,
        datatoken_templates=[1],
        datatoken_names=["Datatoken 1"],
        datatoken_symbols=["DT1"],
        datatoken_minters=[publisher_wallet.address],
        datatoken_fee_managers=[publisher_wallet.address],
        datatoken_publish_market_order_fee_addresses=[ZERO_ADDRESS],
        datatoken_publish_market_order_fee_tokens=[
            publisher_ocean_instance.OCEAN_address
        ],
        datatoken_publish_market_order_fee_amounts=[0],
        datatoken_bytess=[[b""]],
    )
    assert ddo, "The ddo is not created."
    assert ddo.nft["name"] == "NFT1"
    assert ddo.nft["symbol"] == "NFTSYMBOL"
    assert ddo.nft["address"] == data_nft_address
    assert ddo.nft["owner"] == publisher_wallet.address
    assert ddo.datatokens[0]["name"] == "Datatoken 1"
    assert ddo.datatokens[0]["symbol"] == "DT1"
    assert ddo.credentials == build_credentials_dict()


@pytest.mark.integration
def test_plain_asset_multiple_datatokens(
    publisher_ocean_instance, publisher_wallet, config
):
    data_provider = DataServiceProvider
    data_nft_factory, metadata, files = create_basics(config, data_provider)

    tx_receipt = data_nft_factory.deployERC721Contract(
        "NFT2",
        "NFT2SYMBOL",
        1,
        ZERO_ADDRESS,
        ZERO_ADDRESS,
        "https://oceanprotocol.com/nft/",
        True,
        publisher_wallet.address,
        {"from": publisher_wallet},
    )
    registered_event = tx_receipt.events["NFTCreated"]

    assert registered_event["admin"] == publisher_wallet.address
    data_nft_address2 = registered_event["newTokenAddress"]

    ddo = publisher_ocean_instance.assets.create(
        metadata=metadata,
        publisher_wallet=publisher_wallet,
        files=[files, files],
        data_nft_address=data_nft_address2,
        datatoken_templates=[1, 1],
        datatoken_names=["Datatoken 2", "Datatoken 3"],
        datatoken_symbols=["DT2", "DT3"],
        datatoken_minters=[publisher_wallet.address, publisher_wallet.address],
        datatoken_fee_managers=[publisher_wallet.address, publisher_wallet.address],
        datatoken_publish_market_order_fee_addresses=[ZERO_ADDRESS, ZERO_ADDRESS],
        datatoken_publish_market_order_fee_tokens=[
            publisher_ocean_instance.OCEAN_address,
            publisher_ocean_instance.OCEAN_address,
        ],
        datatoken_publish_market_order_fee_amounts=[0, 0],
        datatoken_bytess=[[b""], [b""]],
    )
    assert ddo, "The ddo is not created."
    assert ddo.nft["name"] == "NFT2"
    assert ddo.nft["symbol"] == "NFT2SYMBOL"
    assert ddo.nft["address"] == data_nft_address2
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
    publisher_ocean_instance, publisher_wallet, config, data_nft, datatoken
):
    data_provider = DataServiceProvider
    _, metadata, files = create_basics(config, data_provider)

    access_service = Service(
        service_id="0",
        service_type=ServiceTypes.ASSET_ACCESS,
        service_endpoint=data_provider.get_url(config),
        datatoken=datatoken.address,
        files=files,
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
        datatoken=datatoken.address,
        files=files,
        timeout=3600,
        compute_values=compute_values,
    )

    ddo = publisher_ocean_instance.assets.create(
        metadata=metadata,
        publisher_wallet=publisher_wallet,
        files=files,
        services=[access_service, compute_service],
        data_nft_address=data_nft.address,
        deployed_datatokens=[datatoken],
    )
    assert ddo, "The ddo is not created."
    assert ddo.nft["name"] == "NFT"
    assert ddo.nft["symbol"] == "NFTSYMBOL"
    assert ddo.nft["address"] == data_nft.address
    assert ddo.nft["owner"] == publisher_wallet.address
    assert ddo.datatokens[0]["name"] == "DT1"
    assert ddo.datatokens[0]["symbol"] == "DT1Symbol"
    assert ddo.datatokens[0]["address"] == datatoken.address
    assert ddo.credentials == build_credentials_dict()
    assert ddo.services[1].compute_values == compute_values


@pytest.mark.integration
def test_encrypted_asset(
    publisher_ocean_instance, publisher_wallet, config, data_nft, datatoken
):
    data_provider = DataServiceProvider
    _, metadata, files = create_basics(config, data_provider)

    ddo = publisher_ocean_instance.assets.create(
        metadata=metadata,
        publisher_wallet=publisher_wallet,
        files=files,
        data_nft_address=data_nft.address,
        deployed_datatokens=[datatoken],
        encrypt_flag=True,
    )
    assert ddo, "The ddo is not created."
    assert ddo.nft["name"] == "NFT"
    assert ddo.nft["symbol"] == "NFTSYMBOL"
    assert ddo.nft["address"] == data_nft.address
    assert ddo.nft["owner"] == publisher_wallet.address
    assert ddo.datatokens[0]["name"] == "DT1"
    assert ddo.datatokens[0]["symbol"] == "DT1Symbol"
    assert ddo.datatokens[0]["address"] == datatoken.address


@pytest.mark.integration
def test_compressed_asset(
    publisher_ocean_instance, publisher_wallet, config, data_nft, datatoken
):
    data_provider = DataServiceProvider
    _, metadata, files = create_basics(config, data_provider)

    ddo = publisher_ocean_instance.assets.create(
        metadata=metadata,
        publisher_wallet=publisher_wallet,
        files=files,
        data_nft_address=data_nft.address,
        deployed_datatokens=[datatoken],
        compress_flag=True,
    )
    assert ddo, "The ddo is not created."
    assert ddo.nft["name"] == "NFT"
    assert ddo.nft["symbol"] == "NFTSYMBOL"
    assert ddo.nft["address"] == data_nft.address
    assert ddo.nft["owner"] == publisher_wallet.address
    assert ddo.datatokens[0]["name"] == "DT1"
    assert ddo.datatokens[0]["symbol"] == "DT1Symbol"
    assert ddo.datatokens[0]["address"] == datatoken.address


@pytest.mark.integration
def test_compressed_and_encrypted_asset(
    publisher_ocean_instance, publisher_wallet, config, data_nft, datatoken
):
    data_provider = DataServiceProvider
    _, metadata, files = create_basics(config, data_provider)

    ddo = publisher_ocean_instance.assets.create(
        metadata=metadata,
        publisher_wallet=publisher_wallet,
        files=files,
        data_nft_address=data_nft.address,
        deployed_datatokens=[datatoken],
        encrypt_flag=True,
        compress_flag=True,
    )
    assert ddo, "The ddo is not created."
    assert ddo.nft["name"] == "NFT"
    assert ddo.nft["symbol"] == "NFTSYMBOL"
    assert ddo.nft["owner"] == publisher_wallet.address
    assert ddo.datatokens[0]["name"] == "DT1"
    assert ddo.datatokens[0]["symbol"] == "DT1Symbol"
    assert ddo.datatokens[0]["address"] == datatoken.address


@pytest.mark.unit
def test_asset_creation_errors(
    publisher_ocean_instance, publisher_wallet, config, data_nft, datatoken
):
    data_provider = DataServiceProvider
    _, metadata, files = create_basics(config, data_provider)

    some_random_address = ZERO_ADDRESS
    with pytest.raises(brownie.exceptions.ContractNotFound):
        publisher_ocean_instance.assets.create(
            metadata=metadata,
            publisher_wallet=publisher_wallet,
            files=files,
            data_nft_address=some_random_address,
            deployed_datatokens=[datatoken],
            encrypt_flag=True,
        )

    with patch("ocean_lib.aquarius.aquarius.Aquarius.ddo_exists") as mock:
        mock.return_value = True
        with pytest.raises(AquariusError):
            publisher_ocean_instance.assets.create(
                metadata=metadata,
                publisher_wallet=publisher_wallet,
                files=files,
                data_nft_address=data_nft.address,
                deployed_datatokens=[datatoken],
                encrypt_flag=True,
            )
