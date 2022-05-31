#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import json
import logging
import logging.config
import os
import secrets
from typing import Any, Dict, Optional, Tuple, Union

import coloredlogs
import yaml
from enforce_typing import enforce_types
from eth_keys import KeyAPI
from eth_keys.backends import NativeECCBackend
from pytest import approx
from web3 import Web3

from ocean_lib.config import Config
from ocean_lib.example_config import ExampleConfig
from ocean_lib.models.bpool import BPool
from ocean_lib.models.data_nft import DataNFT
from ocean_lib.models.data_nft_factory import DataNFTFactoryContract
from ocean_lib.models.datatoken import Datatoken
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.ocean.util import get_contracts_addresses
from ocean_lib.ocean.util import get_web3 as util_get_web3
from ocean_lib.structures.file_objects import FilesTypeFactory
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.currency import DECIMALS_18, format_units, from_wei, to_wei
from ocean_lib.web3_internal.transactions import send_ether
from ocean_lib.web3_internal.wallet import Wallet
from tests.resources.mocks.data_provider_mock import DataProviderMock

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
    address = (
        addresses[address_type]
        if not isinstance(addresses[address_type], dict)
        else addresses[address_type].get(key, addresses[address_type]["1"])
    )
    return Web3.toChecksumAddress(address)


@enforce_types
def get_wallet(index: int) -> Wallet:
    config = get_example_config()
    return Wallet(
        get_web3(),
        private_key=os.getenv(f"TEST_PRIVATE_KEY{index}"),
        block_confirmations=config.block_confirmations,
        transaction_timeout=config.transaction_timeout,
    )


@enforce_types
def get_publisher_wallet() -> Wallet:
    return get_wallet(1)


@enforce_types
def get_consumer_wallet() -> Wallet:
    return get_wallet(2)


@enforce_types
def get_another_consumer_wallet() -> Wallet:
    return get_wallet(3)


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
def generate_wallet() -> Wallet:
    """Generates wallets on the fly with funds."""
    web3 = get_web3()
    config = get_example_config()
    secret = secrets.token_hex(32)
    private_key = "0x" + secret

    generated_wallet = Wallet(
        web3,
        private_key=private_key,
        block_confirmations=config.block_confirmations,
        transaction_timeout=config.transaction_timeout,
    )
    assert generated_wallet.private_key == private_key
    deployer_wallet = get_factory_deployer_wallet("ganache")
    send_ether(deployer_wallet, generated_wallet.address, to_wei(3))

    ocn = Ocean(config)
    OCEAN_token = ocn.OCEAN_token
    OCEAN_token.transfer(
        generated_wallet.address, to_wei(50), from_wallet=deployer_wallet
    )
    return generated_wallet


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
def deploy_erc721_erc20(
    web3: Web3,
    config: Config,
    data_nft_publisher: Wallet,
    datatoken_minter: Optional[Wallet] = None,
    template_index: Optional[int] = 1,
) -> Union[DataNFT, Tuple[DataNFT, Datatoken]]:
    """Helper function to deploy an DataNFT using data_nft_publisher Wallet
    and an Datatoken data token with the newly DataNFT using datatoken_minter Wallet
    if the wallet is provided.
    :rtype: Union[DataNFT, Tuple[DataNFT, Datatoken]]
    """

    data_nft_factory = DataNFTFactoryContract(
        web3, get_address_of_type(config, "ERC721Factory")
    )
    tx = data_nft_factory.deploy_erc721_contract(
        name="NFT",
        symbol="NFTSYMBOL",
        template_index=1,
        additional_metadata_updater=ZERO_ADDRESS,
        additional_datatoken_deployer=ZERO_ADDRESS,
        token_uri="https://oceanprotocol.com/nft/",
        transferable=True,
        owner=data_nft_publisher.address,
        from_wallet=data_nft_publisher,
    )
    token_address = data_nft_factory.get_token_address(tx)
    data_nft = DataNFT(web3, token_address)
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
    tx_receipt2 = web3.eth.wait_for_transaction_receipt(tx_result)

    registered_event2 = data_nft_factory.get_event_log(
        DataNFTFactoryContract.EVENT_TOKEN_CREATED,
        tx_receipt2.blockNumber,
        web3.eth.block_number,
        None,
    )

    datatoken_address = registered_event2[0].args.newTokenAddress

    datatoken = Datatoken(web3, datatoken_address)

    return data_nft, datatoken


@enforce_types
def get_non_existent_nft_template(
    data_nft_factory: DataNFTFactoryContract, check_first=20
) -> int:
    """Helper function to find a non existent ERC721 template among the first *check_first* templates
    of an Data NFT Factory contract. Returns -1 if template was found.
    """
    for template_nbr in range(check_first):
        [address, _] = data_nft_factory.get_nft_template(template_nbr)
        if address == ZERO_ADDRESS:
            return template_nbr

    return -1


@enforce_types
def send_mock_usdc_to_address(
    web3: Web3, config: Config, recipient: str, amount: int
) -> int:
    """Helper function to send mock usdc to an arbitrary recipient address if factory_deployer has enough balance
    to send. Returns the transferred balance.
    """
    factory_deployer = get_factory_deployer_wallet(config.network_name)

    mock_usdc = Datatoken(web3, get_address_of_type(config, "MockUSDC"))
    initial_recipient_balance = mock_usdc.balanceOf(recipient)

    if mock_usdc.balanceOf(factory_deployer.address) >= amount:
        mock_usdc.transfer(recipient, amount, factory_deployer)

    return mock_usdc.balanceOf(recipient) - initial_recipient_balance


@enforce_types
def transfer_base_token_if_balance_lte(
    web3: Web3,
    base_token_address: str,
    from_wallet: Wallet,
    recipient: str,
    min_balance: int,
    amount_to_transfer: int,
) -> int:
    """Helper function to send an arbitrary amount of ocean to recipient address if recipient's ocean balance
    is less or equal to min_balance and from_wallet has enough ocean balance to send.
    Returns the transferred ocean amount.
    """
    base_token = Datatoken(web3, base_token_address)
    initial_recipient_balance = base_token.balanceOf(recipient)
    if (
        initial_recipient_balance <= min_balance
        and base_token.balanceOf(from_wallet.address) >= amount_to_transfer
    ):
        base_token.transfer(recipient, amount_to_transfer, from_wallet)

    return base_token.balanceOf(recipient) - initial_recipient_balance


@enforce_types
def get_provider_fees(
    web3: Web3,
    provider_wallet: Wallet,
    provider_fee_token: str,
    provider_fee_amount: int,
    valid_until: int,
    compute_env: str = None,
) -> Dict[str, Any]:
    """Copied and adapted from
    https://github.com/oceanprotocol/provider/blob/b9eb303c3470817d11b3bba01a49f220953ed963/ocean_provider/utils/provider_fees.py#L22-L74

    Keep this in sync with the corresponding provider fee logic when it changes!
    """
    provider_fee_address = provider_wallet.address

    provider_data = json.dumps({"environment": compute_env}, separators=(",", ":"))
    message_hash = web3.solidityKeccak(
        ["bytes", "address", "address", "uint256", "uint256"],
        [
            web3.toHex(web3.toBytes(text=provider_data)),
            provider_fee_address,
            provider_fee_token,
            provider_fee_amount,
            valid_until,
        ],
    )

    keys = KeyAPI(NativeECCBackend)
    pk = keys.PrivateKey(Web3.toBytes(hexstr=provider_wallet.key))
    prefix = "\x19Ethereum Signed Message:\n32"
    signable_hash = web3.solidityKeccak(
        ["bytes", "bytes"], [web3.toBytes(text=prefix), web3.toBytes(message_hash)]
    )
    signed = keys.ecdsa_sign(message_hash=signable_hash, private_key=pk)

    provider_fee = {
        "providerFeeAddress": provider_fee_address,
        "providerFeeToken": provider_fee_token,
        "providerFeeAmount": provider_fee_amount,
        "providerData": web3.toHex(web3.toBytes(text=provider_data)),
        # make it compatible with last openzepellin https://github.com/OpenZeppelin/openzeppelin-contracts/pull/1622
        "v": (signed.v + 27) if signed.v <= 1 else signed.v,
        "r": web3.toHex(web3.toBytes(signed.r).rjust(32, b"\0")),
        "s": web3.toHex(web3.toBytes(signed.s).rjust(32, b"\0")),
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


def create_nft_erc20_with_pool(
    web3,
    config,
    publisher_wallet,
    base_token,
    swap_fee=to_wei("0.0001"),
    swap_market_fee=to_wei("0.0001"),
    initial_pool_liquidity=to_wei("100"),
    pool_initial_rate=to_wei("1"),
):
    data_nft_factory_address = get_address_of_type(
        config, DataNFTFactoryContract.CONTRACT_NAME
    )
    data_nft_factory = DataNFTFactoryContract(web3, data_nft_factory_address)
    side_staking_address = get_address_of_type(config, "Staking")
    pool_template_address = get_address_of_type(config, "poolTemplate")

    base_token.approve(
        data_nft_factory_address, initial_pool_liquidity, publisher_wallet
    )

    tx = data_nft_factory.create_nft_erc20_with_pool(
        nft_name="72120Bundle",
        nft_symbol="72Bundle",
        nft_template=1,
        nft_token_uri="https://oceanprotocol.com/nft/",
        datatoken_template=1,
        datatoken_name="DTWithPool",
        datatoken_symbol="DTP",
        datatoken_minter=publisher_wallet.address,
        datatoken_fee_manager=publisher_wallet.address,
        datatoken_publish_market_order_fee_address=publisher_wallet.address,
        datatoken_publish_market_order_fee_token=ZERO_ADDRESS,
        datatoken_publish_market_order_fee_amount=0,
        datatoken_bytess=[b""],
        pool_rate=pool_initial_rate,
        pool_base_token_decimals=base_token.decimals(),
        pool_base_token_amount=initial_pool_liquidity,
        pool_lp_swap_fee_amount=swap_fee,
        pool_publish_market_swap_fee_amount=swap_market_fee,
        pool_side_staking=side_staking_address,
        pool_base_token=base_token.address,
        pool_base_token_sender=get_address_of_type(
            config, DataNFTFactoryContract.CONTRACT_NAME
        ),
        pool_publisher=publisher_wallet.address,
        pool_publish_market_swap_fee_collector=publisher_wallet.address,
        pool_template_address=pool_template_address,
        nft_transferable=True,
        nft_owner=publisher_wallet.address,
        from_wallet=publisher_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    registered_nft_event = data_nft_factory.get_event_log(
        DataNFTFactoryContract.EVENT_NFT_CREATED,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    data_nft_token_address = registered_nft_event[0].args.newTokenAddress
    data_nft_token = DataNFT(web3, data_nft_token_address)

    registered_token_event = data_nft_factory.get_event_log(
        DataNFTFactoryContract.EVENT_TOKEN_CREATED,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    datatoken_address = registered_token_event[0].args.newTokenAddress
    datatoken = Datatoken(web3, datatoken_address)

    registered_pool_event = datatoken.get_event_log(
        DataNFTFactoryContract.EVENT_NEW_POOL,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    pool_address = registered_pool_event[0].args.poolAddress
    bpool = BPool(web3, pool_address)
    pool_token = Datatoken(web3, pool_address)

    return bpool, datatoken, data_nft_token, pool_token


def join_pool_with_max_base_token(bpool, web3, base_token, wallet, amt: int = 0):
    """
    Join pool with max base token if amt is 0. Otherwise join pool with amt base token.
    """
    pool_token_out_balance = bpool.get_balance(
        base_token.address
    )  # pool base token balance
    max_out_ratio = bpool.get_max_out_ratio()  # max ratio

    max_out_ratio_limit = int(from_wei(max_out_ratio) * pool_token_out_balance)

    web3.eth.wait_for_transaction_receipt(
        bpool.join_swap_extern_amount_in(
            amt if amt else max_out_ratio_limit,
            to_wei("0"),
            wallet,
        )
    )


def wallet_exit_pool_one_side(
    web3, bpool, base_token, pool_token, wallet, amt: int = 0
):
    """
    Exit pool with one side with amt, if amt is 0, exit pool with max amount.
    """
    pool_token_out_balance = bpool.get_balance(
        base_token.address
    )  # pool base token balance
    max_out_ratio = bpool.get_max_out_ratio()  # max ratio

    max_out_ratio_limit = int(from_wei(max_out_ratio) * pool_token_out_balance)

    web3.eth.wait_for_transaction_receipt(
        bpool.exit_swap_pool_amount_in(
            amt
            if amt
            else min(max_out_ratio_limit, pool_token.balanceOf(wallet.address)),
            0,
            wallet,
        )
    )


def join_pool_one_side(web3, bpool, base_token, wallet, amt: int = 0):
    """
    Join 1ss pool with amt, if amt is 0, join pool with max amount.
    """
    pool_token_out_balance = bpool.get_balance(
        base_token.address
    )  # pool base token balance
    max_in_ratio = bpool.get_max_in_ratio()  # max ratio

    max_in_ratio_limit = int(from_wei(max_in_ratio) * pool_token_out_balance)

    web3.eth.wait_for_transaction_receipt(
        bpool.join_swap_extern_amount_in(
            amt if amt else max_in_ratio_limit,
            to_wei("0"),
            wallet,
        )
    )


def swap_exact_amount_in_datatoken(bpool, datatoken, base_token, wallet, amt: int = 0):
    bpool.swap_exact_amount_in(
        datatoken.address,
        base_token.address,
        wallet.address,
        amt,
        to_wei("0"),
        to_wei("100000"),
        to_wei("0"),
        wallet,
    )


def swap_exact_amount_in_base_token(bpool, datatoken, base_token, wallet, amt: int = 0):
    pool_token_out_balance = bpool.get_balance(
        base_token.address
    )  # pool base token balance
    max_out_ratio = bpool.get_max_out_ratio()  # max ratio

    max_out_ratio_limit = int(from_wei(max_out_ratio) * pool_token_out_balance)

    bpool.swap_exact_amount_in(
        base_token.address,
        datatoken.address,
        wallet.address,
        amt if amt else max_out_ratio_limit,
        to_wei("0"),
        to_wei("100000"),
        to_wei("0"),
        wallet,
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
