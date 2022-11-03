#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import json
import logging
import logging.config
import os
import secrets
from datetime import datetime
from typing import Any, Dict, Optional, Tuple, Union

import coloredlogs
import yaml
from brownie.network import accounts
from brownie.network.transaction import TransactionReceipt
from enforce_typing import enforce_types
from pytest import approx
from web3 import Web3

from ocean_lib.example_config import ExampleConfig
from ocean_lib.models.data_nft import DataNFT
from ocean_lib.models.data_nft_factory import DataNFTFactoryContract
from ocean_lib.models.datatoken import Datatoken
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.ocean.util import get_address_of_type
from ocean_lib.structures.file_objects import FilesTypeFactory
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.currency import DECIMALS_18, format_units, from_wei, to_wei
from ocean_lib.web3_internal.transactions import send_ether, sign_with_key
from tests.resources.mocks.data_provider_mock import DataProviderMock

_NETWORK = "ganache"


def get_example_config():
    return ExampleConfig.get_config()


@enforce_types
def get_wallet(index: int):
    return accounts.add(os.getenv(f"TEST_PRIVATE_KEY{index}"))


@enforce_types
def get_publisher_wallet():
    return get_wallet(1)


@enforce_types
def get_consumer_wallet():
    return get_wallet(2)


@enforce_types
def get_another_consumer_wallet():
    return get_wallet(3)


@enforce_types
def get_provider_wallet():
    return accounts.add(os.getenv("PROVIDER_PRIVATE_KEY"))


def get_factory_deployer_wallet(config):
    if config["NETWORK_NAME"] == "development":
        return get_ganache_wallet()

    private_key = os.environ.get("FACTORY_DEPLOYER_PRIVATE_KEY")
    if not private_key:
        return None

    config = get_example_config()
    return accounts.add(private_key)


def get_ganache_wallet():
    return accounts.add(
        "0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58"
    )


@enforce_types
def generate_wallet():
    """Generates wallets on the fly with funds."""
    config = get_example_config()
    secret = secrets.token_hex(32)
    private_key = "0x" + secret

    generated_wallet = accounts.add(private_key)
    assert generated_wallet.private_key == private_key
    deployer_wallet = get_factory_deployer_wallet(config)
    send_ether(config, deployer_wallet, generated_wallet.address, "3 ether")

    ocn = Ocean(config)
    OCEAN_token = ocn.OCEAN_token
    OCEAN_token.transfer(
        generated_wallet.address, to_wei(50), {"from": deployer_wallet}
    )
    return generated_wallet


@enforce_types
def get_publisher_ocean_instance(use_provider_mock=False) -> Ocean:
    config_dict = ExampleConfig.get_config()
    data_provider = DataProviderMock if use_provider_mock else None
    ocn = Ocean(config_dict, data_provider=data_provider)
    account = get_publisher_wallet()
    ocn.main_account = account
    return ocn


@enforce_types
def get_consumer_ocean_instance(use_provider_mock: bool = False) -> Ocean:
    config = ExampleConfig.get_config()
    data_provider = DataProviderMock if use_provider_mock else None
    ocn = Ocean(config, data_provider=data_provider)
    account = get_consumer_wallet()
    ocn.main_account = account
    return ocn


@enforce_types
def get_another_consumer_ocean_instance(use_provider_mock: bool = False) -> Ocean:
    config = ExampleConfig.get_config()
    data_provider = DataProviderMock if use_provider_mock else None
    ocn = Ocean(config, data_provider=data_provider)
    account = get_another_consumer_wallet()
    ocn.main_account = account
    return ocn


@enforce_types
def setup_logging(
    default_path: str = "logging.yaml",
    default_level=logging.INFO,
    env_key: str = "LOG_CFG",
):
    """Logging setup."""
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, "rt") as file:
            try:
                config = yaml.safe_load(file.read())
                logging.config.dictConfig(config)
                coloredlogs.install()
                logging.info(f"Logging configuration loaded from file: {path}")
            except Exception as ex:
                print(ex)
                print("Error in Logging Configuration. Using default configs")
                logging.basicConfig(level=default_level)
                coloredlogs.install(level=default_level)
    else:
        logging.basicConfig(level=default_level)
        coloredlogs.install(level=default_level)


@enforce_types
def deploy_erc721_erc20(
    config_dict: dict,
    data_nft_publisher,
    datatoken_minter: Optional = None,
    template_index: Optional[int] = 1,
) -> Union[DataNFT, Tuple[DataNFT, Datatoken]]:
    """Helper function to deploy an DataNFT using data_nft_publisher Wallet
    and an Datatoken data token with the newly DataNFT using datatoken_minter Wallet
    if the wallet is provided.
    :rtype: Union[DataNFT, Tuple[DataNFT, Datatoken]]
    """

    data_nft_factory = DataNFTFactoryContract(
        config_dict, get_address_of_type(config_dict, "ERC721Factory")
    )
    receipt = data_nft_factory.deployERC721Contract(
        "NFT",
        "NFTSYMBOL",
        1,
        ZERO_ADDRESS,
        ZERO_ADDRESS,
        "https://oceanprotocol.com/nft/",
        True,
        data_nft_publisher.address,
        {"from": data_nft_publisher},
    )
    token_address = data_nft_factory.get_token_address(receipt)
    data_nft = DataNFT(config_dict, token_address)
    if not datatoken_minter:
        return data_nft

    tx_result = data_nft.create_erc20(
        template_index=template_index,
        name="DT1",
        symbol="DT1Symbol",
        minter=datatoken_minter.address,
        fee_manager=data_nft_publisher.address,
        publish_market_order_fee_address=data_nft_publisher.address,
        publish_market_order_fee_token=ZERO_ADDRESS,
        publish_market_order_fee_amount=0,
        bytess=[b""],
        from_wallet=data_nft_publisher,
    )
    tx_receipt2 = TransactionReceipt(tx_result)

    registered_event2 = tx_receipt2.events[DataNFTFactoryContract.EVENT_TOKEN_CREATED]
    datatoken_address = registered_event2["newTokenAddress"]

    datatoken = Datatoken(config_dict, datatoken_address)

    return data_nft, datatoken


@enforce_types
def get_non_existent_nft_template(
    data_nft_factory: DataNFTFactoryContract, check_first=20
) -> int:
    """Helper function to find a non existent ERC721 template among the first *check_first* templates
    of an Data NFT Factory contract. Returns -1 if template was found.
    """
    for template_nbr in range(check_first):
        [address, _] = data_nft_factory.getNFTTemplate(template_nbr)
        if address == ZERO_ADDRESS:
            return template_nbr

    return -1


@enforce_types
def send_mock_usdc_to_address(config: dict, recipient: str, amount: int) -> int:
    """Helper function to send mock usdc to an arbitrary recipient address if factory_deployer has enough balance
    to send. Returns the transferred balance.
    """
    factory_deployer = get_factory_deployer_wallet(config)

    mock_usdc = Datatoken(config, get_address_of_type(config, "MockUSDC"))
    initial_recipient_balance = mock_usdc.balanceOf(recipient)

    if mock_usdc.balanceOf(factory_deployer.address) >= amount:
        mock_usdc.transfer(recipient, amount, factory_deployer)

    return mock_usdc.balanceOf(recipient) - initial_recipient_balance


@enforce_types
def transfer_base_token_if_balance_lte(
    config: dict,
    base_token_address: str,
    from_wallet,
    recipient: str,
    min_balance: int,
    amount_to_transfer: int,
) -> int:
    """Helper function to send an arbitrary amount of ocean to recipient address if recipient's ocean balance
    is less or equal to min_balance and from_wallet has enough ocean balance to send.
    Returns the transferred ocean amount.
    """
    base_token = Datatoken(config, base_token_address)
    initial_recipient_balance = base_token.balanceOf(recipient)
    if (
        initial_recipient_balance <= min_balance
        and base_token.balanceOf(from_wallet.address) >= amount_to_transfer
    ):
        base_token.transfer(recipient, amount_to_transfer, {"from": from_wallet})

    return base_token.balanceOf(recipient) - initial_recipient_balance


@enforce_types
def get_provider_fees(
    provider_wallet,
    provider_fee_token: str,
    provider_fee_amount: int,
    valid_until: int,
    compute_env: str = None,
    timestamp: int = None,
) -> Dict[str, Any]:
    """Copied and adapted from
    https://github.com/oceanprotocol/provider/blob/b9eb303c3470817d11b3bba01a49f220953ed963/ocean_provider/utils/provider_fees.py#L22-L74

    Keep this in sync with the corresponding provider fee logic when it changes!
    """
    provider_fee_address = provider_wallet.address

    provider_data = json.dumps(
        {"environment": compute_env, "timestamp": datetime.utcnow().timestamp()},
        separators=(",", ":"),
    )
    message_hash = Web3.solidityKeccak(
        ["bytes", "address", "address", "uint256", "uint256"],
        [
            Web3.toHex(Web3.toBytes(text=provider_data)),
            provider_fee_address,
            provider_fee_token,
            provider_fee_amount,
            valid_until,
        ],
    )

    signed = sign_with_key(message_hash, os.getenv("PROVIDER_PRIVATE_KEY"))

    provider_fee = {
        "providerFeeAddress": provider_fee_address,
        "providerFeeToken": provider_fee_token,
        "providerFeeAmount": str(provider_fee_amount),
        "providerData": Web3.toHex(Web3.toBytes(text=provider_data)),
        # make it compatible with last openzepellin https://github.com/OpenZeppelin/openzeppelin-contracts/pull/1622
        "v": (signed.v + 27) if signed.v <= 1 else signed.v,
        "r": Web3.toHex(Web3.toBytes(signed.r).rjust(32, b"\0")),
        "s": Web3.toHex(Web3.toBytes(signed.s).rjust(32, b"\0")),
        "validUntil": valid_until,
    }
    return provider_fee


def base_token_to_datatoken(
    base_token_amount: int,
    base_token_decimals: int,
    datatokens_per_base_token: int,
) -> int:
    """Convert base tokens to equivalent datatokens, accounting for differences
    in decimals and exchange rate.

    When creating a pool, the "rate" argument is the datatokens per base token,
    and can be passed directly into this function.

    When creating an exchange, the "rate" argument is the base tokens per datatoken,
    so it needs to be inverted before passing into this function.

    Datatokens always have 18 decimals, even when the base tokens don't.
    """
    return to_wei(
        format_units(base_token_amount, base_token_decimals)
        * from_wei(datatokens_per_base_token)
    )


def approx_from_wei(amount_a, amount_b) -> float:
    """Helper function to compare token amounts in wei
    with pytest approx function with a relative tolerance of 1e-6."""
    return approx_format_units(amount_a, DECIMALS_18, amount_b, DECIMALS_18)


def approx_format_units(
    amount_a, unit_name_a, amount_b, unit_name_b, rel=1e-6
) -> float:
    """Helper function to compare token amounts where decimals != 18
    with pytest approx function with a relative tolerance of 1e-6."""
    return float(format_units(amount_a, unit_name_a)) == approx(
        float(format_units(amount_b, unit_name_b)),
        rel=rel,
    )


def get_file1():
    file1_dict = {
        "type": "url",
        "url": "https://raw.githubusercontent.com/tbertinmahieux/MSongsDB/master/Tasks_Demos/CoverSongs/shs_dataset_test.txt",
        "method": "GET",
    }

    return FilesTypeFactory(file1_dict)


def get_file2():
    file2_dict = {
        "type": "url",
        "url": "https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-abstract10.xml.gz-rss.xml",
        "method": "GET",
    }

    return FilesTypeFactory(file2_dict)


def get_file3():
    file3_dict = {
        "type": "url",
        "url": "https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-abstract10.xml.gz",
        "method": "GET",
    }

    return FilesTypeFactory(file3_dict)
