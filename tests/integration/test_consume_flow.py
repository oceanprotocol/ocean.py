#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import json

import ecies

from ocean_lib.agreements.file_objects import FilesTypeFactory
from ocean_lib.agreements.service_types import ServiceTypesV4
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.models.v4.erc20_token import ERC20Token
from ocean_lib.models.v4.erc721_factory import ERC721FactoryContract
from ocean_lib.models.v4.models_structures import ErcCreateData
from ocean_lib.ocean.v4.ocean_assets import OceanAssetV4
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.currency import to_wei
from tests.resources.helper_functions import get_address_of_type, get_provider_fees


def test_consume_flow(web3, config, publisher_wallet, consumer_wallet, provider_wallet):
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
        [file1, file2], "http://172.15.0.4:8030/api/services/encrypt"
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
        uints=[web3.toWei("100", "ether"), 0],
        bytess=[b""],
    )

    # Publish a plain asset with one data token on chain
    ddo = asset.create(
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

    service = ddo.get_service(ServiceTypesV4.ASSET_ACCESS)
    erc20_token = ERC20Token(web3, ddo.datatokens[0]["address"])

    # Mint 50 ERC20 tokens in consumer wallet from publisher. Max cap = 100
    erc20_token.mint(
        account_address=consumer_wallet.address,
        value=to_wei(50),
        from_wallet=publisher_wallet,
    )

    # Start order for consumer
    tx_id = erc20_token.start_order(
        consumer=consumer_wallet.address,
        service_id=int(service.id),
        provider_fees=get_provider_fees(),
        from_wallet=consumer_wallet,
    )
    response = data_provider.download(
        did=ddo.did,
        service_id=service.id,
        tx_id=tx_id,
        file_index=0,
        consumer_wallet=consumer_wallet,
        download_endpoint="http://172.15.0.4:8030/api/services/download",
    )
    assert response
