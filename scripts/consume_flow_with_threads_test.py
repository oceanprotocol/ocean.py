#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os
import random
import shutil
import threading

import pytest

from ocean_lib.agreements.service_types import ServiceTypes
from ocean_lib.config import Config
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.example_config import ExampleConfig
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.structures.abi_tuples import ConsumeFees, CreateErc20Data
from ocean_lib.structures.file_objects import FilesTypeFactory
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.wallet import Wallet
from tests.resources.ddo_helpers import build_credentials_dict
from tests.resources.helper_functions import deploy_erc721_erc20, get_address_of_type


def consume_flow(ocean: Ocean, wallet: Wallet, config: Config):
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
    file1_url = "https://raw.githubusercontent.com/tbertinmahieux/MSongsDB/master/Tasks_Demos/CoverSongs/shs_dataset_test.txt"
    file1_dict = {"type": "url", "url": file1_url, "method": "GET"}
    file1 = FilesTypeFactory(file1_dict)
    file2_url = "https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-abstract10.xml.gz-rss.xml"
    file2_dict = {"type": "url", "url": file2_url, "method": "GET"}
    file2 = FilesTypeFactory(file2_dict)
    file3_url = (
        "https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-abstract10.xml.gz"
    )
    file3_dict = {"type": "url", "url": file3_url, "method": "GET"}
    file3 = FilesTypeFactory(file3_dict)
    files = [file1, file2, file3]

    for i in range(3000):
        erc721_nft, erc20_token = deploy_erc721_erc20(
            ocean.web3, config, wallet, wallet
        )
        encrypt_response = data_provider.encrypt(
            [random.choice(files)], config.provider_url
        )
        encrypted_files = encrypt_response.content.decode("utf-8")

        erc20_data = CreateErc20Data(
            template_index=1,
            strings=["Datatoken 1", "DT1"],
            addresses=[
                wallet.address,
                wallet.address,
                ZERO_ADDRESS,
                get_address_of_type(config, "Ocean"),
            ],
            uints=[ocean.to_wei("0.5"), 0],
            bytess=[b""],
        )
        ddo = ocean.assets.create(
            metadata=metadata,
            publisher_wallet=wallet,
            encrypted_files=encrypted_files,
            erc721_address=erc721_nft.address,
            erc20_tokens_data=[erc20_data],
        )
        assert ddo, "The asset is not created."
        assert ddo.nft["name"] == "NFT"
        assert ddo.nft["symbol"] == "NFTSYMBOL"
        assert ddo.nft["address"] == erc721_nft.address
        assert ddo.nft["owner"] == wallet.address
        assert ddo.datatokens[0]["name"] == "Datatoken 1"
        assert ddo.datatokens[0]["symbol"] == "DT1"
        assert ddo.credentials == build_credentials_dict()

        service = ddo.get_service(ServiceTypes.ASSET_ACCESS)

        # Initialize service
        response = data_provider.initialize(
            did=ddo.did, service=service, consumer_address=wallet.address
        )
        assert response
        assert response.status_code == 200
        assert response.json()["providerFee"]

        # Consume fees
        consume_fees = ConsumeFees(
            consumer_market_fee_address=wallet.address,
            consumer_market_fee_token=erc20_token.address,
            consumer_market_fee_amount=0,
        )

        erc20_token.mint(
            account_address=wallet.address,
            value=ocean.to_wei(i + 1),
            from_wallet=wallet,
        )
        # Start order for consumer
        tx_id = erc20_token.start_order(
            consumer=wallet.address,
            service_index=ddo.get_index_of_service(service),
            provider_fees=response.json()["providerFee"],
            consume_fees=consume_fees,
            from_wallet=wallet,
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

        ocean.assets.download_asset(
            asset=ddo,
            consumer_wallet=wallet,
            destination=destination,
            order_tx_id=tx_id,
        )

        assert (
            len(os.listdir(os.path.join(destination, os.listdir(destination)[0]))) > 0
        ), "The asset folder is empty."


def thread_function1(ocean, alice_wallet, config):
    consume_flow(ocean, wallet=alice_wallet, config=config)


def thread_function2(ocean, bob_wallet, config):
    consume_flow(ocean, wallet=bob_wallet, config=config)


def thread_function3(ocean, tristan_wallet, config):
    consume_flow(ocean, wallet=tristan_wallet, config=config)


@pytest.mark.slow
def test_consume_flow_with_threads():
    config = ExampleConfig.get_config()
    ocean = Ocean(config)

    alice_private_key = os.getenv("TEST_PRIVATE_KEY1")
    alice_wallet = Wallet(
        ocean.web3,
        alice_private_key,
        config.block_confirmations,
        config.transaction_timeout,
    )
    assert alice_wallet.address
    bob_private_key = os.getenv("TEST_PRIVATE_KEY2")
    bob_wallet = Wallet(
        ocean.web3,
        bob_private_key,
        config.block_confirmations,
        config.transaction_timeout,
    )
    assert bob_wallet.address
    tristan_private_key = os.getenv("TEST_PRIVATE_KEY3")
    tristan_wallet = Wallet(
        ocean.web3,
        tristan_private_key,
        config.block_confirmations,
        config.transaction_timeout,
    )
    assert tristan_wallet.address
    # Mint OCEAN
    mint_fake_OCEAN(config)
    assert alice_wallet.web3.eth.get_balance(alice_wallet.address) > 0, "need ETH"
    assert bob_wallet.web3.eth.get_balance(bob_wallet.address) > 0, "need ETH"
    assert tristan_wallet.web3.eth.get_balance(tristan_wallet.address) > 0, "need ETH"

    threads = list()
    t1 = threading.Thread(
        target=thread_function1,
        args=(ocean, alice_wallet, config),
    )
    threads.append(t1)
    t2 = threading.Thread(
        target=thread_function2,
        args=(ocean, bob_wallet, config),
    )
    threads.append(t2)
    t3 = threading.Thread(
        target=thread_function3,
        args=(ocean, tristan_wallet, config),
    )
    threads.append(t3)
    t1.start()
    t2.start()
    t3.start()
    for index, thread in enumerate(threads):
        print("Main    : before joining thread %d.", index)
        thread.join()
        print("Main    : thread %d done", index)
