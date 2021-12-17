#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_lib.agreements.file_objects import FilesTypeFactory
from ocean_lib.agreements.service_types import ServiceTypesV4
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.models.v4.erc721_factory import ERC721FactoryContract
from ocean_lib.models.v4.models_structures import ErcCreateData
from ocean_lib.ocean.v4.ocean_assets import OceanAssetV4
from ocean_lib.services.v4.service import V4Service
from ocean_lib.utils.utilities import get_timestamp
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from tests.resources.helper_functions import get_address_of_type, deploy_erc721_erc20


def test_publish_flow(web3, config, publisher_wallet, provider_wallet):
    """Tests publish flow in different situations."""
    erc721_factory_address = get_address_of_type(
        config, ERC721FactoryContract.CONTRACT_NAME
    )
    erc721_factory = ERC721FactoryContract(web3, erc721_factory_address)

    # Publisher deploys NFT contract
    tx = erc721_factory.deploy_erc721_contract(
        "NFT1",
        "NFTSYMBOL",
        1,
        ZERO_ADDRESS,
        "https://oceanprotocol.com/nft/",
        publisher_wallet,
    )
    created = get_timestamp()
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

    data_provider = DataServiceProvider
    asset = OceanAssetV4(config, web3, data_provider)
    metadata = {
        "created": "2020-11-15T12:27:48Z",
        "updated": "2021-05-17T21:58:02Z",
        "description": "Sample description",
        "name": "Sample asset",
        "type": "dataset",
        "author": "OPF",
        "license": "https://market.oceanprotocol.com/terms",
    }
    file1_dict = {"type": "url", "url": "https://url.com/file1.csv", "method": "GET"}
    file2_dict = {"type": "url", "url": "https://url.com/file2.csv", "method": "GET"}
    file1 = FilesTypeFactory(file1_dict)
    file2 = FilesTypeFactory(file2_dict)

    # Encrypt file objects
    encrypt_response = data_provider.encrypt(
        [file1, file2], "http://localhost:8030/api/services/encrypt"
    )
    encrypted_files = encrypt_response.content.decode("utf-8")

    # Set ERC20 Data
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

    # Create a plain asset with one data token
    ddo = asset.create(
        metadata=metadata,
        publisher_wallet=publisher_wallet,
        provider_wallet=provider_wallet,
        encrypted_files=encrypted_files,
        erc721_address=erc721_address,
        created=created,
        erc20_data=[erc20_data],
    )
    assert ddo, "The asset is not created."

    # Create a plain asset with multiple data tokens
    tx = erc721_factory.deploy_erc721_contract(
        "NFT2",
        "NFT2SYMBOL",
        1,
        ZERO_ADDRESS,
        "https://oceanprotocol.com/nft/",
        publisher_wallet,
    )
    created2 = get_timestamp()
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

    ddo = asset.create(
        metadata=metadata,
        publisher_wallet=publisher_wallet,
        provider_wallet=provider_wallet,
        encrypted_files=encrypted_files,
        erc721_address=erc721_address2,
        created=created2,
        erc20_data=[erc20_data1, erc20_data2],
    )
    assert ddo, "The asset is not created."
    assert len(ddo.services) == 2
    assert len(ddo.datatokens) == 2

    data_token_names = []
    for data_token in ddo.datatokens:
        data_token_names.append(data_token["name"])
    assert data_token_names[0] == "Datatoken 2"
    assert data_token_names[1] == "Datatoken 3"

    # Create a plain asset with multiple services
    erc721_token, erc20_token = deploy_erc721_erc20(
        web3, config, publisher_wallet, publisher_wallet
    )
    created3 = get_timestamp()

    access_service = V4Service(
        service_id="1",
        service_type=ServiceTypesV4.ASSET_ACCESS,
        service_endpoint=data_provider.get_url(config),
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
    compute_service = V4Service(
        service_id="2",
        service_type=ServiceTypesV4.CLOUD_COMPUTE,
        service_endpoint=data_provider.get_url(config),
        data_token=erc20_token.address,
        files=encrypted_files,
        timeout=3600,
        compute_values=compute_values,
    )

    ddo = asset.create(
        metadata=metadata,
        publisher_wallet=publisher_wallet,
        provider_wallet=provider_wallet,
        encrypted_files=encrypted_files,
        services=[access_service, compute_service],
        erc721_address=erc721_token.address,
        created=created3,
        deployed_erc20_tokens=[erc20_token],
    )
    assert ddo

    # # Create an encrypted asset
    # erc721_token2, erc20_token2 = deploy_erc721_erc20(
    #     web3, config, publisher_wallet, publisher_wallet
    # )
    # created4 = get_timestamp()
    # ddo = asset.create(
    #     metadata=metadata,
    #     publisher_wallet=publisher_wallet,
    #     provider_wallet=provider_wallet,
    #     encrypted_files=encrypted_files,
    #     erc721_address=erc721_token2.address,
    #     created=created4,
    #     deployed_erc20_tokens=[erc20_token2],
    #     encrypt_flag=True
    # )
    # assert ddo
