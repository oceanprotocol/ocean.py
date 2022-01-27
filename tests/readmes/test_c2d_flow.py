#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os

from ocean_lib.agreements.file_objects import UrlFile
from ocean_lib.assets.trusted_algorithms import add_publisher_trusted_algorithm
from ocean_lib.example_config import ExampleConfig
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

    assert DATA_asset.did

    # 3. Alice publishes algorithm

    # Publish the algorithm NFT token
    ALG_nft_token = ocean.create_nft_token("NFTToken1", "NFT1", alice_wallet)
    assert ALG_nft_token.address

    # Publish the datatoken
    ALG_erc20_data = CreateErc20Data(
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
    ALG_datatoken = ALG_nft_token.create_datatoken(ALG_erc20_data, alice_wallet)

    # Specify metadata and services, using the Branin test dataset
    ALG_date_created = "2021-12-28T10:55:11Z"

    ALG_metadata = {
        "created": ALG_date_created,
        "updated": ALG_date_created,
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
    ALG_url_file = UrlFile(
        url="https://raw.githubusercontent.com/trentmc/branin/main/gpr.py"
    )

    # Encrypt file(s) using provider
    ALG_encrypted_files = ocean.assets.encrypt_files([ALG_url_file])

    # Publish asset with compute service on-chain.
    # The download (access service) is automatically created, but you can explore other options as well
    ALG_asset = ocean.assets.create(
        metadata=ALG_metadata,
        publisher_wallet=alice_wallet,
        encrypted_files=ALG_encrypted_files,
        erc721_address=ALG_nft_token.address,
        deployed_erc20_tokens=[ALG_datatoken],
    )

    assert ALG_asset.did

    # 4. Alice allows the algorithm for C2D for that data asset
    add_publisher_trusted_algorithm(
        DATA_asset, ALG_asset.did, config.metadata_cache_uri
    )
    DATA_asset = ocean.assets.update(DATA_asset, alice_wallet)

    return

    # erc20_token = ocean.get_datatoken(asset.get_service("access").datatoken)
    # OCEAN_token = ocean.get_datatoken(ocean.OCEAN_address)

    # ss_params = [
    #     ocean.to_wei(1),
    #     OCEAN_token.decimals(),
    #     ocean.to_wei(10000),
    #     2500000,
    #     ocean.to_wei(2000),
    # ]

    # swap_fees = [ocean.to_wei("0.01"), ocean.to_wei("0.01")]
    # bpool = ocean.create_pool(
    #     erc20_token, OCEAN_token, ss_params, swap_fees, alice_wallet
    # )
    # assert bpool.address

    # price_in_OCEAN = bpool.get_amount_in_exact_out(
    #     OCEAN_token.address, erc20_token.address, ocean.to_wei(1), ocean.to_wei("0.01")
    # )

    # formatted_price = pretty_ether_and_wei(price_in_OCEAN, "OCEAN")
    # assert formatted_price

    # bob_private_key = os.getenv("TEST_PRIVATE_KEY2")
    # bob_wallet = Wallet(
    #     ocean.web3,
    #     bob_private_key,
    #     config.block_confirmations,
    #     config.transaction_timeout,
    # )

    # # Verify that Bob has ganache ETH
    # assert ocean.web3.eth.get_balance(bob_wallet.address) > 0, "need ganache ETH"

    # # Verify that Bob has ganache OCEAN
    # assert OCEAN_token.balanceOf(bob_wallet.address) > 0, "need ganache OCEAN"

    # OCEAN_token.approve(bpool.address, ocean.to_wei("10000"), from_wallet=bob_wallet)

    # bpool.swap_exact_amount_out(
    #     [OCEAN_token.address, erc20_token.address, ZERO_ADDRESS],
    #     [ocean.to_wei(10), ocean.to_wei(1), ocean.to_wei(10), 0],
    #     from_wallet=bob_wallet,
    # )
    # assert erc20_token.balanceOf(bob_wallet.address) >= ocean.to_wei(
    #     1
    # ), "Bob didn't get 1.0 datatokens"

    # service = asset.get_service("access")
    # order_tx_id = ocean.assets.pay_for_service(asset, service, bob_wallet)

    # file_path = ocean.assets.download_asset(
    #     asset, service.service_endpoint, bob_wallet, str(tmp_path), order_tx_id
    # )

    # assert file_path
