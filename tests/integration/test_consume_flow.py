#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os
import shutil

import pytest

from ocean_lib.agreements.service_types import ServiceTypes
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.models.erc20_token import ERC20Token
from ocean_lib.models.erc721_factory import ERC721FactoryContract
from ocean_lib.ocean.ocean_assets import OceanAssets
from ocean_lib.structures.file_objects import FilesTypeFactory
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.currency import to_wei
from tests.resources.ddo_helpers import get_first_service_by_type
from tests.resources.helper_functions import get_address_of_type


@pytest.mark.integration
def test_consume_flow(web3, config, publisher_wallet, consumer_wallet):
    erc721_factory_address = get_address_of_type(
        config, ERC721FactoryContract.CONTRACT_NAME
    )
    erc721_factory = ERC721FactoryContract(web3, erc721_factory_address)

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

    data_provider = DataServiceProvider
    asset = OceanAssets(config, web3, data_provider)
    metadata = {
        "created": "2020-11-15T12:27:48Z",
        "updated": "2021-05-17T21:58:02Z",
        "description": "Sample description",
        "name": "Sample asset",
        "type": "dataset",
        "author": "OPF",
        "license": "https://market.oceanprotocol.com/terms",
    }
    file_url = "https://raw.githubusercontent.com/tbertinmahieux/MSongsDB/master/Tasks_Demos/CoverSongs/shs_dataset_test.txt"
    file_dict = {"type": "url", "url": file_url, "method": "GET"}
    file = FilesTypeFactory(file_dict)
    files = [file]

    # Encrypt file objects
    encrypt_response = data_provider.encrypt(files, config.provider_url)
    encrypted_files = encrypt_response.content.decode("utf-8")

    # Publish a plain asset with one data token on chain
    ddo = asset.create(
        metadata=metadata,
        publisher_wallet=publisher_wallet,
        encrypted_files=encrypted_files,
        erc721_address=erc721_address,
        erc20_templates=[1],
        erc20_names=["Datatoken 1"],
        erc20_symbols=["DT1"],
        erc20_minters=[publisher_wallet.address],
        erc20_fee_managers=[publisher_wallet.address],
        erc20_publishing_market_addresses=[ZERO_ADDRESS],
        fee_token_addresses=[get_address_of_type(config, "Ocean")],
        erc20_cap_values=[to_wei(100)],
        publishing_fee_amounts=[0],
        erc20_bytess=[[b""]],
    )

    assert ddo, "The asset is not created."
    assert ddo.nft["name"] == "NFT1"
    assert ddo.nft["symbol"] == "NFTSYMBOL"
    assert ddo.nft["address"] == erc721_address
    assert ddo.nft["owner"] == publisher_wallet.address
    assert ddo.datatokens[0]["name"] == "Datatoken 1"
    assert ddo.datatokens[0]["symbol"] == "DT1"

    service = get_first_service_by_type(ddo, ServiceTypes.ASSET_ACCESS)
    erc20_token = ERC20Token(web3, ddo.datatokens[0]["address"])

    # Mint 50 ERC20 tokens in consumer wallet from publisher. Max cap = 100
    erc20_token.mint(
        account_address=consumer_wallet.address,
        value=to_wei("50"),
        from_wallet=publisher_wallet,
    )

    # Initialize service
    response = data_provider.initialize(
        did=ddo.did, service=service, consumer_address=consumer_wallet.address
    )
    assert response
    assert response.status_code == 200
    assert response.json()["providerFee"]
    provider_fees = response.json()["providerFee"]

    # Start order for consumer
    tx_id = erc20_token.start_order(
        consumer=consumer_wallet.address,
        service_index=ddo.get_index_of_service(service),
        provider_fee_address=provider_fees["providerFeeAddress"],
        provider_fee_token=provider_fees["providerFeeToken"],
        provider_fee_amount=provider_fees["providerFeeAmount"],
        v=provider_fees["v"],
        r=provider_fees["r"],
        s=provider_fees["s"],
        valid_until=provider_fees["validUntil"],
        provider_data=provider_fees["providerData"],
        consumer_market_fee_address=consumer_wallet.address,
        consumer_market_fee_token=erc20_token.address,
        consumer_market_fee_amount=0,
        from_wallet=consumer_wallet,
    )

    # Download file
    destination = config.downloads_path
    if not os.path.isabs(destination):
        destination = os.path.abspath(destination)

    if os.path.exists(destination) and len(os.listdir(destination)) > 0:
        list(
            map(
                lambda d: shutil.rmtree(os.path.join(destination, d)),
                os.listdir(destination),
            )
        )

    if not os.path.exists(destination):
        os.mkdir(destination)

    assert len(os.listdir(destination)) == 0

    asset.download_asset(
        asset=ddo,
        service=service,
        consumer_wallet=consumer_wallet,
        destination=destination,
        order_tx_id=tx_id,
    )

    assert len(
        os.listdir(os.path.join(destination, os.listdir(destination)[0]))
    ) == len(files), "The asset folder is empty."
