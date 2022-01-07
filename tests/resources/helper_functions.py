#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import json
import logging
import logging.config
import os
import time
from typing import Optional, Dict, Any

import coloredlogs
import yaml
from enforce_typing import enforce_types

from ocean_lib.agreements.file_objects import FilesTypeFactory
from ocean_lib.config import Config
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.example_config import ExampleConfig
from ocean_lib.models.data_token import DataToken
from ocean_lib.models.erc20_token import ERC20Token
from ocean_lib.models.erc721_factory import ERC721FactoryContract
from ocean_lib.models.erc721_token import ERC721Token
from ocean_lib.models.models_structures import ErcCreateData
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.ocean.util import get_contracts_addresses
from ocean_lib.ocean.util import get_web3 as util_get_web3
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.currency import to_wei
from ocean_lib.web3_internal.utils import split_signature
from ocean_lib.web3_internal.wallet import Wallet
from tests.resources.mocks.data_provider_mock import DataProviderMock
from web3 import Web3

_NETWORK = "ganache"


def get_web3():
    return util_get_web3(get_example_config().network_url)


def get_example_config():
    return ExampleConfig.get_config()


@enforce_types
def get_address_of_type(
    config: Config, address_type: str, key: Optional[str] = None
) -> str:
    addresses = get_contracts_addresses(config.address_file, _NETWORK)
    if address_type not in addresses.keys():
        raise KeyError(f"{address_type} address is not set in the config file")
    return (
        addresses[address_type]
        if not isinstance(addresses[address_type], dict)
        else addresses[address_type].get(key, addresses[address_type]["1"])
    )


@enforce_types
def get_publisher_wallet() -> Wallet:
    config = get_example_config()
    return Wallet(
        get_web3(),
        private_key=os.environ.get("TEST_PRIVATE_KEY1"),
        block_confirmations=config.block_confirmations,
        transaction_timeout=config.transaction_timeout,
    )


@enforce_types
def get_consumer_wallet() -> Wallet:
    config = get_example_config()
    return Wallet(
        get_web3(),
        private_key=os.environ.get("TEST_PRIVATE_KEY2"),
        block_confirmations=config.block_confirmations,
        transaction_timeout=config.transaction_timeout,
    )


@enforce_types
def get_another_consumer_wallet() -> Wallet:
    config = get_example_config()
    return Wallet(
        get_web3(),
        private_key=os.environ.get("TEST_PRIVATE_KEY3"),
        block_confirmations=config.block_confirmations,
        transaction_timeout=config.transaction_timeout,
    )


@enforce_types
def get_provider_wallet() -> Wallet:
    config = get_example_config()
    return Wallet(
        get_web3(),
        private_key=os.environ.get("PROVIDER_PRIVATE_KEY"),
        block_confirmations=config.block_confirmations,
        transaction_timeout=config.transaction_timeout,
    )


def get_factory_deployer_wallet(network):
    if network == "ganache":
        return get_ganache_wallet()

    private_key = os.environ.get("FACTORY_DEPLOYER_PRIVATE_KEY")
    if not private_key:
        return None

    config = get_example_config()
    return Wallet(
        get_web3(),
        private_key=private_key,
        block_confirmations=config.block_confirmations,
        transaction_timeout=config.transaction_timeout,
    )


def get_ganache_wallet():
    web3 = get_web3()
    if (
        web3.eth.accounts
        and web3.eth.accounts[0].lower()
        == "0xe2DD09d719Da89e5a3D0F2549c7E24566e947260".lower()
    ):
        config = get_example_config()
        return Wallet(
            web3,
            private_key="0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58",
            block_confirmations=config.block_confirmations,
            transaction_timeout=config.transaction_timeout,
        )

    return None


@enforce_types
def get_publisher_ocean_instance(use_provider_mock=False) -> Ocean:
    config = ExampleConfig.get_config()
    data_provider = DataProviderMock if use_provider_mock else None
    ocn = Ocean(config, data_provider=data_provider)
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
def log_event(event_name: str):
    def _process_event(event):
        print(f"Received event {event_name}: {event}")

    return _process_event


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
def mint_tokens_and_wait(
    data_token_contract: DataToken, receiver_address: str, minter_wallet: Wallet
):
    dtc = data_token_contract
    tx_id = dtc.mint(receiver_address, to_wei(50), minter_wallet)
    dtc.get_tx_receipt(dtc.web3, tx_id)
    time.sleep(2)

    def verify_supply(mint_amount=to_wei(50)):
        supply = dtc.contract.caller.totalSupply()
        if supply <= 0:
            _tx_id = dtc.mint(receiver_address, mint_amount, minter_wallet)
            dtc.get_tx_receipt(dtc.web3, _tx_id)
            supply = dtc.contract.caller.totalSupply()
        return supply

    while True:
        try:
            s = verify_supply()
            if s > 0:
                break
        except (ValueError, Exception):
            pass


def deploy_erc721_erc20(
    web3: Web3,
    config: Config,
    erc721_publisher: Wallet,
    erc20_minter: Optional[Wallet] = None,
    cap: int = Web3.toWei("0.5", "ether"),
    template_index: Optional[int] = 1,
):
    """Helper function to deploy an ERC721Token using erc721_publisher Wallet
    and an ERC20Token data token with the newly ERC721Token using erc20_minter Wallet
    if the wallet is provided.
    :rtype: Union[ERC721Token, Tuple[ERC721Token, ERC20Token]]
    """

    erc721_factory = ERC721FactoryContract(
        web3, get_address_of_type(config, "ERC721Factory")
    )
    tx = erc721_factory.deploy_erc721_contract(
        name="NFT",
        symbol="NFTSYMBOL",
        template_index=1,
        additional_erc20_deployer=ZERO_ADDRESS,
        token_uri="https://oceanprotocol.com/nft/",
        from_wallet=erc721_publisher,
    )
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    registered_event = erc721_factory.get_event_log(
        event_name=ERC721FactoryContract.EVENT_NFT_CREATED,
        from_block=tx_receipt.blockNumber,
        to_block=web3.eth.block_number,
        filters=None,
    )
    token_address = registered_event[0].args.newTokenAddress
    erc721_token = ERC721Token(web3, token_address)
    if not erc20_minter:
        return erc721_token

    erc_create_data = ErcCreateData(
        template_index=template_index,
        strings=["ERC20DT1", "ERC20DT1Symbol"],
        addresses=[
            erc20_minter.address,
            erc721_publisher.address,
            erc721_publisher.address,
            ZERO_ADDRESS,
        ],
        uints=[cap, 0],
        bytess=[b""],
    )
    tx_result = erc721_token.create_erc20(erc_create_data, erc721_publisher)
    tx_receipt2 = web3.eth.wait_for_transaction_receipt(tx_result)

    registered_event2 = erc721_factory.get_event_log(
        ERC721FactoryContract.EVENT_TOKEN_CREATED,
        tx_receipt2.blockNumber,
        web3.eth.block_number,
        None,
    )

    erc20_address = registered_event2[0].args.newTokenAddress

    erc20_token = ERC20Token(web3, erc20_address)

    return erc721_token, erc20_token


def get_non_existent_nft_template(
    erc721_factory: ERC721FactoryContract, check_first=20
) -> int:
    """Helper function to find a non existent ERC721 template among the first *check_first* templates
    of an ERC721 Factory contract. Returns -1 if template was found.
    """
    for template_nbr in range(check_first):
        [address, _] = erc721_factory.get_nft_template(template_nbr)
        if address == ZERO_ADDRESS:
            return template_nbr

    return -1


def send_mock_usdc_to_address(
    web3: Web3, config: Config, recipient: str, amount: int
) -> int:
    """Helper function to send mock usdc to an arbitrary recipient address if factory_deployer has enough balance
    to send. Returns the transferred balance.
    """
    factory_deployer = get_factory_deployer_wallet(config.network_name)

    mock_usdc = ERC20Token(web3, get_address_of_type(config, "MockUSDC"))
    initial_recipient_balance = mock_usdc.balanceOf(recipient)

    if mock_usdc.balanceOf(factory_deployer) >= amount:
        mock_usdc.transfer(recipient, amount, factory_deployer)

    return mock_usdc.balanceOf(recipient) - initial_recipient_balance


def transfer_ocean_if_balance_lte(
    web3: Web3,
    config: Config,
    factory_deployer_wallet: Wallet,
    recipient: str,
    min_balance: int,
    amount_to_transfer: int,
) -> int:
    """Helper function to send an arbitrary amount of ocean to recipient address if recipient's ocean balance
    is less or equal to min_balance and factory_deployer_wallet has enough ocean balance to send.
    Returns the transferred ocean amount.
    """
    ocean_token = ERC20Token(web3, get_address_of_type(config, "Ocean"))
    initial_recipient_balance = ocean_token.balanceOf(recipient)
    if (
        initial_recipient_balance
        <= min_balance & ocean_token.balanceOf(factory_deployer_wallet.address)
        >= amount_to_transfer
    ):
        ocean_token.transfer(
            recipient, web3.toWei("20000", "ether"), factory_deployer_wallet
        )

    return ocean_token.balanceOf(recipient) - initial_recipient_balance


def get_provider_fees() -> Dict[str, Any]:
    provider_wallet = get_provider_wallet()
    web3 = get_web3()
    provider_fee_amount = 0
    provider_data = json.dumps({"timeout": 0}, separators=(",", ":"))
    provider_fee_address = provider_wallet.address
    provider_fee_token = os.environ.get("PROVIDER_FEE_TOKEN", ZERO_ADDRESS)

    message = Web3.solidityKeccak(
        ["bytes", "address", "address", "uint256"],
        [
            Web3.toHex(Web3.toBytes(text=provider_data)),
            provider_fee_address,
            provider_fee_token,
            provider_fee_amount,
        ],
    )
    signed = web3.eth.sign(provider_fee_address, data=message)
    signature = split_signature(signed)

    provider_fee = {
        "providerFeeAddress": provider_fee_address,
        "providerFeeToken": provider_fee_token,
        "providerFeeAmount": provider_fee_amount,
        "providerData": Web3.toHex(Web3.toBytes(text=provider_data)),
        # make it compatible with last openzepellin https://github.com/OpenZeppelin/openzeppelin-contracts/pull/1622
        "v": signature.v,
        "r": signature.r,
        "s": signature.s,
    }

    return provider_fee


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


def create_basics(config, web3, data_provider):
    erc721_factory_address = get_address_of_type(
        config, ERC721FactoryContract.CONTRACT_NAME
    )
    erc721_factory = ERC721FactoryContract(web3, erc721_factory_address)

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

    return erc721_factory, metadata, encrypted_files
