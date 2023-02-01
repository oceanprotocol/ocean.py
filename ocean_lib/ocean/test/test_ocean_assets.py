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
from ocean_lib.example_config import DEFAULT_PROVIDER_URL
from ocean_lib.exceptions import AquariusError, InsufficientBalance
from ocean_lib.models.data_nft_factory import DataNFTFactoryContract
from ocean_lib.models.datatoken import DatatokenArguments, TokenFeeInfo
from ocean_lib.ocean.util import get_address_of_type
from ocean_lib.services.service import Service
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from tests.resources.ddo_helpers import (
    build_credentials_dict,
    build_default_services,
    get_default_files,
    get_default_metadata,
    get_first_service_by_type,
    get_registered_asset_with_access_service,
    get_sample_ddo,
)
from tests.resources.helper_functions import deploy_erc721_erc20


@pytest.mark.integration
def test_register_asset(publisher_ocean):
    invalid_did = "did:op:0123456789"
    assert publisher_ocean.assets.resolve(invalid_did) is None


@pytest.mark.integration
def test_update_metadata(publisher_ocean, publisher_wallet):
    _, _, ddo = get_registered_asset_with_access_service(
        publisher_ocean, publisher_wallet
    )

    new_metadata = copy.deepcopy(ddo.metadata)

    # Update only metadata
    _description = "Updated description"
    new_metadata["description"] = _description
    new_metadata["updated"] = datetime.utcnow().isoformat()
    ddo.metadata = new_metadata

    ddo2 = publisher_ocean.assets.update(ddo, {"from": publisher_wallet})

    assert ddo2.datatokens == ddo.datatokens
    assert len(ddo2.services) == len(ddo.services)
    assert ddo2.services[0].as_dictionary() == ddo.services[0].as_dictionary()
    assert ddo2.credentials == ddo.credentials
    assert ddo2.metadata["description"] == _description
    assert ddo2.metadata["updated"] == new_metadata["updated"]


@pytest.mark.integration
def test_update_credentials(publisher_ocean, publisher_wallet):
    _, _, ddo = get_registered_asset_with_access_service(
        publisher_ocean, publisher_wallet
    )

    # Update credentials
    _new_credentials = {
        "allow": [{"type": "address", "values": ["0x123", "0x456"]}],
        "deny": [{"type": "address", "values": ["0x2222", "0x333"]}],
    }

    ddo.credentials = _new_credentials

    ddo2 = publisher_ocean.assets.update(ddo, {"from": publisher_wallet})

    assert ddo2.credentials == _new_credentials, "Credentials were not updated."


@pytest.mark.integration
def test_update_datatokens(publisher_ocean, publisher_wallet, config, file2):
    _, datatoken = deploy_erc721_erc20(config, publisher_wallet, publisher_wallet)
    _, _, ddo = get_registered_asset_with_access_service(
        publisher_ocean, publisher_wallet
    )

    files = [file2]

    # Add new existing datatoken with service
    ddo_orig = copy.deepcopy(ddo)
    access_service = Service(
        service_id="3",
        service_type=ServiceTypes.ASSET_ACCESS,
        service_endpoint=DEFAULT_PROVIDER_URL,
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

    ddo2 = publisher_ocean.assets.update(ddo, {"from": publisher_wallet})

    assert len(ddo2.datatokens) == len(ddo_orig.datatokens) + 1
    assert len(ddo2.services) == len(ddo_orig.services) + 1
    assert ddo2.datatokens[1].get("address") == datatoken.address
    assert ddo2.datatokens[0].get("address") == ddo_orig.datatokens[0].get("address")
    assert ddo2.services[0].datatoken == ddo_orig.datatokens[0].get("address")
    assert ddo2.services[1].datatoken == datatoken.address

    # Delete datatoken
    ddo3 = copy.deepcopy(ddo2)
    metadata3 = copy.deepcopy(ddo2.metadata)
    _description = "Test delete datatoken"
    metadata3["description"] = _description
    metadata3["updated"] = datetime.utcnow().isoformat()

    removed_dt = ddo3.datatokens.pop()

    ddo3.services = [
        service
        for service in ddo3.services
        if service.datatoken != removed_dt.get("address")
    ]

    ddo2_prev_datatokens = ddo2.datatokens

    ddo4 = publisher_ocean.assets.update(ddo3, {"from": publisher_wallet})

    assert ddo4, "Can't read ddo after update."
    assert len(ddo4.datatokens) == 1
    assert ddo4.datatokens[0].get("address") == ddo2_prev_datatokens[0].get("address")
    assert ddo4.services[0].datatoken == ddo2_prev_datatokens[0].get("address")

    nft_token = publisher_ocean.get_nft_token(ddo4.nft["address"])
    bn = network.chain[-1].number

    updated_event = nft_token.contract.events.get_sequence(bn, bn, "MetadataUpdated")[0]
    assert updated_event.args.updatedBy == publisher_wallet.address

    validation_event = nft_token.contract.events.get_sequence(
        bn, bn, "MetadataValidated"
    )[0]
    assert validation_event.args.validator.startswith("0x")
    assert updated_event.transactionHash == validation_event.transactionHash


@pytest.mark.integration
def test_update_flags(publisher_ocean, publisher_wallet):
    data_nft, _, ddo = get_registered_asset_with_access_service(
        publisher_ocean, publisher_wallet
    )

    ddo2 = publisher_ocean.assets.update(
        ddo,
        {"from": publisher_wallet},
        compress_flag=True,
        encrypt_flag=True,
    )

    registered_token_event = data_nft.contract.events.get_sequence(
        ddo2.event.get("block"),
        network.chain[-1].number,
        "MetadataUpdated",
    )

    assert registered_token_event[0].args.get("flags") == bytes([3])


@pytest.mark.integration
def test_ocean_assets_search(publisher_ocean, publisher_wallet):
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

    assert len(publisher_ocean.assets.search(identifier)) == 0, "DDO search failed."

    get_registered_asset_with_access_service(
        publisher_ocean, publisher_wallet, metadata
    )

    time.sleep(1)  # apparently changes are not instantaneous
    assert (
        len(publisher_ocean.assets.search(identifier)) == 1
    ), "Searched for the occurrences of the identifier failed. "

    assert (
        len(
            publisher_ocean.assets.query(
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
            publisher_ocean.assets.query(
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
def test_ocean_assets_validate(publisher_ocean):
    ddo_dict = get_sample_ddo()
    ddo = DDO.from_dict(ddo_dict)

    assert publisher_ocean.assets.validate(
        ddo
    ), "ddo should be valid, unless the schema changed"

    ddo_dict = get_sample_ddo()
    ddo_dict["id"] = "something not conformant"
    ddo = DDO.from_dict(ddo_dict)

    with pytest.raises(ValueError):
        publisher_ocean.assets.validate(ddo)


@pytest.mark.integration
def test_ocean_assets_algorithm(publisher_ocean, publisher_wallet):
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

    _, _, ddo = get_registered_asset_with_access_service(
        publisher_ocean, publisher_wallet, metadata
    )
    assert ddo, "DDO None. The ddo is not cached after the creation."


@pytest.mark.unit
def test_download_fails(publisher_ocean, publisher_wallet):
    with patch("ocean_lib.ocean.ocean_assets.OceanAssets.resolve") as mock:
        ddo = DDO.from_dict(get_sample_ddo())
        mock.return_value = ddo
        with pytest.raises(AssertionError):
            publisher_ocean.assets.download_asset(
                ddo,
                publisher_wallet,
                destination="",
                order_tx_id="",
                service=ddo.services[0],
                index=-4,
            )
        with pytest.raises(TypeError):
            publisher_ocean.assets.download_asset(
                ddo,
                publisher_wallet,
                destination="",
                order_tx_id="",
                service=ddo.services[0],
                index="string_index",
            )


@pytest.mark.integration
def test_create_bad_metadata(publisher_ocean, publisher_wallet):
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
        get_registered_asset_with_access_service(
            publisher_ocean, publisher_wallet, metadata
        )

    metadata["name"] = "Sample asset"
    metadata.pop("type")
    with pytest.raises(AssertionError):
        get_registered_asset_with_access_service(
            publisher_ocean, publisher_wallet, metadata
        )


@pytest.mark.unit
def test_pay_for_access_service_insufficient_balance(
    publisher_ocean, config, publisher_wallet
):
    _, datatoken = deploy_erc721_erc20(config, publisher_wallet, publisher_wallet)

    ddo_dict = copy.deepcopy(get_sample_ddo())
    ddo_dict["services"][0]["datatokenAddress"] = datatoken.address
    ddo = DDO.from_dict(ddo_dict)

    empty_wallet = accounts.add()

    with pytest.raises(InsufficientBalance):
        publisher_ocean.assets.pay_for_access_service(
            ddo,
            {"from": empty_wallet},
            get_first_service_by_type(ddo, "access"),
            TokenFeeInfo(address=empty_wallet.address, token=datatoken.address),
        )


@pytest.mark.integration
def test_create_url_asset(publisher_ocean, publisher_wallet):
    ocean = publisher_ocean

    name = "Branin dataset"
    url = "https://raw.githubusercontent.com/trentmc/branin/main/branin.arff"
    (data_nft, datatoken, ddo) = ocean.assets.create_url_asset(
        name, url, {"from": publisher_wallet}
    )

    assert ddo.nft["name"] == name  # thorough testing is below, on create() directly
    assert len(ddo.datatokens) == 1


@pytest.mark.integration
def test_plain_asset_with_one_datatoken(publisher_ocean, publisher_wallet, config):
    data_nft_factory = DataNFTFactoryContract(
        config, get_address_of_type(config, "ERC721Factory")
    )

    metadata = get_default_metadata()
    files = get_default_files()

    # Publisher deploys NFT contract
    data_nft = data_nft_factory.create({"from": publisher_wallet}, "NFT1", "NFTSYMBOL")

    _, _, ddo = publisher_ocean.assets.create(
        metadata=metadata,
        tx_dict={"from": publisher_wallet},
        data_nft_address=data_nft.address,
        datatoken_args=[DatatokenArguments(files=files)],
    )
    assert ddo, "The ddo is not created."
    assert ddo.nft["name"] == "NFT1"
    assert ddo.nft["symbol"] == "NFTSYMBOL"
    assert ddo.nft["address"] == data_nft.address
    assert ddo.nft["owner"] == publisher_wallet.address
    assert ddo.datatokens[0]["name"] == "Datatoken 1"
    assert ddo.datatokens[0]["symbol"] == "DT1"
    assert ddo.credentials == build_credentials_dict()


@pytest.mark.integration
def test_plain_asset_multiple_datatokens(publisher_ocean, publisher_wallet, config):
    data_nft_factory = DataNFTFactoryContract(
        config, get_address_of_type(config, "ERC721Factory")
    )

    metadata = get_default_metadata()
    files = get_default_files()

    data_nft = data_nft_factory.create({"from": publisher_wallet}, "NFT2", "NFT2SYMBOL")

    _, _, ddo = publisher_ocean.assets.create(
        metadata=metadata,
        tx_dict={"from": publisher_wallet},
        data_nft_address=data_nft.address,
        datatoken_args=[
            DatatokenArguments("Datatoken 2", "DT2", files=files),
            DatatokenArguments("Datatoken 3", "DT3", files=files),
        ],
    )
    assert ddo, "The ddo is not created."
    assert ddo.nft["name"] == "NFT2"
    assert ddo.nft["symbol"] == "NFT2SYMBOL"
    assert ddo.nft["address"] == data_nft.address
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
def test_plain_asset_multiple_services(publisher_ocean, publisher_wallet, config):
    data_nft, datatoken = deploy_erc721_erc20(
        config, publisher_wallet, publisher_wallet
    )

    metadata = get_default_metadata()
    files = get_default_files()

    access_service = Service(
        service_id="0",
        service_type=ServiceTypes.ASSET_ACCESS,
        service_endpoint=DEFAULT_PROVIDER_URL,
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
        service_endpoint=DEFAULT_PROVIDER_URL,
        datatoken=datatoken.address,
        files=files,
        timeout=3600,
        compute_values=compute_values,
    )

    _, _, ddo = publisher_ocean.assets.create(
        metadata=metadata,
        tx_dict={"from": publisher_wallet},
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
def test_encrypted_asset(publisher_ocean, publisher_wallet, config):
    data_nft, datatoken = deploy_erc721_erc20(
        config, publisher_wallet, publisher_wallet
    )
    metadata = get_default_metadata()
    services = build_default_services(config, datatoken)

    _, _, ddo = publisher_ocean.assets.create(
        metadata=metadata,
        tx_dict={"from": publisher_wallet},
        data_nft_address=data_nft.address,
        deployed_datatokens=[datatoken],
        services=services,
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
def test_compressed_asset(publisher_ocean, publisher_wallet, config):
    data_nft, datatoken = deploy_erc721_erc20(
        config, publisher_wallet, publisher_wallet
    )
    metadata = get_default_metadata()
    services = build_default_services(config, datatoken)

    _, _, ddo = publisher_ocean.assets.create(
        metadata=metadata,
        tx_dict={"from": publisher_wallet},
        services=services,
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
def test_compressed_and_encrypted_asset(publisher_ocean, publisher_wallet, config):
    data_nft, datatoken = deploy_erc721_erc20(
        config, publisher_wallet, publisher_wallet
    )
    metadata = get_default_metadata()
    services = build_default_services(config, datatoken)

    _, _, ddo = publisher_ocean.assets.create(
        metadata=metadata,
        tx_dict={"from": publisher_wallet},
        services=services,
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
def test_asset_creation_errors(publisher_ocean, publisher_wallet, config):
    data_nft, datatoken = deploy_erc721_erc20(
        config, publisher_wallet, publisher_wallet
    )
    metadata = get_default_metadata()

    some_random_address = ZERO_ADDRESS
    with pytest.raises(brownie.exceptions.ContractNotFound):
        publisher_ocean.assets.create(
            metadata=metadata,
            tx_dict={"from": publisher_wallet},
            services=[],
            data_nft_address=some_random_address,
            deployed_datatokens=[datatoken],
            encrypt_flag=True,
        )

    with patch("ocean_lib.aquarius.aquarius.Aquarius.ddo_exists") as mock:
        mock.return_value = True
        with pytest.raises(AquariusError):
            publisher_ocean.assets.create(
                metadata=metadata,
                tx_dict={"from": publisher_wallet},
                services=[],
                data_nft_address=data_nft.address,
                deployed_datatokens=[datatoken],
                encrypt_flag=True,
            )


@pytest.mark.integration
def test_create_algo_asset(publisher_ocean, publisher_wallet):
    ocean = publisher_ocean

    name = "Branin dataset"
    url = "https://raw.githubusercontent.com/oceanprotocol/c2d-examples/main/branin_and_gpr/gpr.py"
    (data_nft, datatoken, ddo) = ocean.assets.create_algo_asset(
        name, url, {"from": publisher_wallet}
    )

    assert ddo.nft["name"] == name  # thorough testing is below, on create() directly
    assert len(ddo.datatokens) == 1
