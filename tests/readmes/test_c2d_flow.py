#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os
import time
from datetime import datetime, timedelta

from ocean_lib.agreements.file_objects import UrlFile
from ocean_lib.assets.trusted_algorithms import add_publisher_trusted_algorithm
from ocean_lib.example_config import ExampleConfig
from ocean_lib.models.compute_input import ComputeInput
from ocean_lib.models.models_structures import CreateErc20Data
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.services.service import Service
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.wallet import Wallet


def test_c2d_flow():
    """This test mirrors the c2d-flow.md README."""

    # 2. Alice publishes data asset with compute service
    config = ExampleConfig.get_config()
    ocean = Ocean(config)

    # Create Alice's wallet
    alice_private_key = os.getenv("TEST_PRIVATE_KEY1")
    alice_wallet = Wallet(
        ocean.web3,
        alice_private_key,
        config.block_confirmations,
        config.transaction_timeout,
    )
    assert alice_wallet.address

    # Mint OCEAN
    mint_fake_OCEAN(config)
    assert alice_wallet.web3.eth.get_balance(alice_wallet.address) > 0, "need ETH"

    # Publish the data NFT token
    DATA_nft_token = ocean.create_nft_token("NFTToken1", "NFT1", alice_wallet)
    assert DATA_nft_token.address

    # Publish the datatoken
    DATA_erc20_data = CreateErc20Data(
        template_index=1,
        strings=["Datatoken 1", "DT1"],
        addresses=[
            alice_wallet.address,
            alice_wallet.address,
            ZERO_ADDRESS,
            ocean.OCEAN_address,
        ],
        uints=[ocean.to_wei(100000), 0],
        bytess=[b""],
    )
    DATA_datatoken = DATA_nft_token.create_datatoken(DATA_erc20_data, alice_wallet)
    assert DATA_datatoken.address

    # Specify metadata and services, using the Branin test dataset
    DATA_date_created = "2021-12-28T10:55:11Z"

    DATA_metadata = {
        "created": DATA_date_created,
        "updated": DATA_date_created,
        "description": "Branin dataset",
        "name": "Branin dataset",
        "type": "dataset",
        "author": "Trent",
        "license": "CC0: PublicDomain",
    }

    # ocean.py offers multiple file types, but a simple url file should be enough for this example
    DATA_url_file = UrlFile(
        url="https://raw.githubusercontent.com/trentmc/branin/main/branin.arff"
    )

    # Encrypt file(s) using provider
    DATA_encrypted_files = ocean.assets.encrypt_files([DATA_url_file])

    # Set the compute values for compute service
    DATA_compute_values = {
        "allowRawAlgorithm": False,
        "allowNetworkAccess": True,
        "publisherTrustedAlgorithms": [],
        "publisherTrustedAlgorithmPublishers": [],
    }

    # Create the Service
    DATA_compute_service = Service(
        service_id="2",
        service_type="compute",
        service_endpoint=f"{ocean.config.provider_url}/api/services/compute",
        datatoken=DATA_datatoken.address,
        files=DATA_encrypted_files,
        timeout=3600,
        compute_values=DATA_compute_values,
    )

    # Publish asset with compute service on-chain.
    DATA_asset = ocean.assets.create(
        metadata=DATA_metadata,
        publisher_wallet=alice_wallet,
        encrypted_files=DATA_encrypted_files,
        services=[DATA_compute_service],
        erc721_address=DATA_nft_token.address,
        deployed_erc20_tokens=[DATA_datatoken],
    )

    assert DATA_asset.did, "create dataset with compute service unsuccessful"

    # 3. Alice publishes algorithm

    # Publish the algorithm NFT token
    ALGO_nft_token = ocean.create_nft_token("NFTToken1", "NFT1", alice_wallet)
    assert ALGO_nft_token.address

    # Publish the datatoken
    ALGO_erc20_data = CreateErc20Data(
        template_index=1,
        strings=["Datatoken 1", "DT1"],
        addresses=[
            alice_wallet.address,
            alice_wallet.address,
            ZERO_ADDRESS,
            ocean.OCEAN_address,
        ],
        uints=[ocean.to_wei(100000), 0],
        bytess=[b""],
    )
    ALGO_datatoken = ALGO_nft_token.create_datatoken(ALGO_erc20_data, alice_wallet)

    # Specify metadata and services, using the Branin test dataset
    ALGO_date_created = "2021-12-28T10:55:11Z"

    ALGO_metadata = {
        "created": ALGO_date_created,
        "updated": ALGO_date_created,
        "description": "gpr",
        "name": "gpr",
        "type": "algorithm",
        "author": "Trent",
        "license": "CC0: PublicDomain",
        "algorithm": {
            "language": "python",
            "format": "docker-image",
            "version": "0.1",
            "container": {
                "entrypoint": "python $ALGO",
                "image": "oceanprotocol/algo_dockers",
                "tag": "python-branin",
                # TODO: fix checksum
                "checksum": "44e10daa6637893f4276bb8d7301eb35306ece50f61ca34dcab550",
            },
        },
    }

    # ocean.py offers multiple file types, but a simple url file should be enough for this example
    ALGO_url_file = UrlFile(
        url="https://raw.githubusercontent.com/trentmc/branin/main/gpr.py"
    )

    # Encrypt file(s) using provider
    ALGO_encrypted_files = ocean.assets.encrypt_files([ALGO_url_file])

    # Publish asset with compute service on-chain.
    # The download (access service) is automatically created, but you can explore other options as well
    ALGO_asset = ocean.assets.create(
        metadata=ALGO_metadata,
        publisher_wallet=alice_wallet,
        encrypted_files=ALGO_encrypted_files,
        erc721_address=ALGO_nft_token.address,
        deployed_erc20_tokens=[ALGO_datatoken],
    )

    assert ALGO_asset.did, "create algorithm unsuccessful"

    # 4. Alice allows the algorithm for C2D for that data asset
    add_publisher_trusted_algorithm(
        DATA_asset, ALGO_asset.did, config.metadata_cache_uri
    )
    DATA_asset = ocean.assets.update(DATA_asset, alice_wallet)

    # 5. Bob acquires datatokens for data and algorithm
    bob_wallet = Wallet(
        ocean.web3,
        os.getenv("TEST_PRIVATE_KEY2"),
        config.block_confirmations,
        config.transaction_timeout,
    )
    print(f"bob_wallet.address = '{bob_wallet.address}'")

    # Alice mints DATA datatokens and ALGO datatokens to Bob.
    # Alternatively, Bob might have bought these in a market.
    DATA_datatoken.mint(bob_wallet.address, ocean.to_wei(5), alice_wallet)
    ALGO_datatoken.mint(bob_wallet.address, ocean.to_wei(5), alice_wallet)

    # 6. Bob starts a compute job

    # Convenience variables
    DATA_did = DATA_asset.did
    ALGO_did = ALGO_asset.did

    # Operate on updated and indexed assets
    DATA_asset = ocean.assets.resolve(DATA_did)
    ALGO_asset = ocean.assets.resolve(ALGO_did)

    compute_service = DATA_asset.get_service("compute")
    algo_service = ALGO_asset.get_service("access")

    # Pay for dataset
    DATA_order_tx_id = ocean.assets.pay_for_service(
        asset=DATA_asset,
        service=compute_service,
        wallet=bob_wallet,
        initialize_args={
            "compute_environment": "unused",
            "valid_until": int((datetime.now() + timedelta(days=1)).timestamp()),
        },
    )
    assert DATA_order_tx_id, "pay for dataset unsuccessful"

    # Pay for algorithm
    ALGO_order_tx_id = ocean.assets.pay_for_service(
        asset=ALGO_asset,
        service=algo_service,
        wallet=bob_wallet,
        initialize_args={
            "valid_until": int((datetime.now() + timedelta(days=1)).timestamp())
        },
    )
    assert ALGO_order_tx_id, "pay for algorithm unsuccessful"

    # Start compute job
    DATA_compute_input = ComputeInput(DATA_did, DATA_order_tx_id, compute_service.id)
    ALGO_compute_input = ComputeInput(ALGO_did, ALGO_order_tx_id, algo_service.id)
    job_id = ocean.compute.start(
        consumer_wallet=bob_wallet,
        dataset=DATA_compute_input,
        # TODO: Update once compute environment implemented in provider
        compute_environment="unused",
        algorithm=ALGO_compute_input,
    )
    assert job_id, "start compute unsuccessful"

    # Wait until job is done
    succeeded = False
    for _ in range(0, 200):
        status = ocean.compute.status(DATA_did, job_id, bob_wallet)
        if status["status"] > 60:
            succeeded = True
            break
        time.sleep(5)
    assert succeeded, "compute job unsuccessful"

    # Retrieve result
    # 0 index, means we retrieve the results from the first dataset index
    result = ocean.compute.result_file(DATA_did, job_id, 0, bob_wallet)
    assert result, "result retrieval unsuccessful"
