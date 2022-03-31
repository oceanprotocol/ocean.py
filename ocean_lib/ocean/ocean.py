#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""Ocean module."""
import json
import logging
from decimal import Decimal
from typing import Dict, List, Optional, Type, Union

from enforce_typing import enforce_types
from web3.datastructures import AttributeDict

from ocean_lib.config import Config
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.models.bpool import BPool
from ocean_lib.models.dispenser import Dispenser
from ocean_lib.models.erc20_token import ERC20Token
from ocean_lib.models.erc721_factory import ERC721FactoryContract
from ocean_lib.models.erc721_nft import ERC721NFT
from ocean_lib.models.factory_router import FactoryRouter
from ocean_lib.models.fixed_rate_exchange import FixedRateExchange
from ocean_lib.ocean.ocean_assets import OceanAssets
from ocean_lib.ocean.ocean_compute import OceanCompute
from ocean_lib.ocean.util import get_address_of_type, get_ocean_token_address, get_web3
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.currency import DECIMALS_18
from ocean_lib.web3_internal.currency import to_wei as _to_wei
from ocean_lib.web3_internal.utils import split_signature
from ocean_lib.web3_internal.wallet import Wallet

logger = logging.getLogger("ocean")


class Ocean:
    """The Ocean class is the entry point into Ocean Protocol."""

    @enforce_types
    def __init__(
        self, config: Union[Dict, Config], data_provider: Optional[Type] = None
    ) -> None:
        """Initialize Ocean class.

        Usage: Make a new Ocean instance

        `ocean = Ocean({...})`

        This class provides the main top-level functions in ocean protocol:
        1. Publish assets metadata and associated services
            - Each asset is assigned a unique DID and a DID Document (DDO)
            - The DDO contains the asset's services including the metadata
            - The DID is registered on-chain with a URL of the metadata store
              to retrieve the DDO from

            `asset = ocean.assets.create(metadata, publisher_wallet)`

        2. Discover/Search assets via the current configured metadata store (Aquarius)

            - Usage:
            `assets_list = ocean.assets.search('search text')`

        An instance of Ocean is parameterized by a `Config` instance.

        :param config: `Config` instance
        :param data_provider: `DataServiceProvider` instance
        """
        if isinstance(config, dict):
            # fallback to metadataStoreUri
            cache_key = (
                "metadataCacheUri"
                if ("metadataCacheUri" in config)
                else "metadataStoreUri"
            )
            metadata_cache_uri = config.get(
                cache_key, config.get("metadata_cache_uri", "http://172.15.0.5:5000")
            )
            config_dict = {
                "eth-network": {"network": config.get("network", "")},
                "resources": {
                    "metadata_cache_uri": metadata_cache_uri,
                    "provider.url": config.get("providerUri", "http://172.15.0.4:8030"),
                },
            }
            config = Config(options_dict=config_dict)
        self.config = config
        self.web3 = get_web3(self.config.network_url)

        if not data_provider:
            data_provider = DataServiceProvider

        self.assets = OceanAssets(self.config, self.web3, data_provider)
        self.compute = OceanCompute(self.config, data_provider)

        logger.debug("Ocean instance initialized: ")

    @property
    @enforce_types
    def OCEAN_address(self) -> str:
        return get_ocean_token_address(self.config.address_file, web3=self.web3)

    @enforce_types
    def to_wei(
        self, amount_in_ether: Union[Decimal, str, int], decimals: int = DECIMALS_18
    ):
        return _to_wei(amount_in_ether=amount_in_ether, decimals=decimals)

    @enforce_types
    def create_erc721_nft(
        self,
        name: str,
        symbol: str,
        from_wallet: Wallet,
        token_uri: Optional[str] = "https://oceanprotocol.com/nft/",
        template_index: Optional[int] = 1,
        additional_erc20_deployer: Optional[str] = None,
        additional_metadata_updater: Optional[str] = None,
        transferable: bool = True,
        owner: Optional[str] = None,
    ) -> ERC721NFT:
        """
        This method deploys a ERC721 token contract on the blockchain.
        Usage:
        ```python
            config = Config('config.ini')
            ocean = Ocean(config)
            wallet = Wallet(
                ocean.web3,
                private_key=private_key,
                block_confirmations=config.block_confirmations,
                transaction_timeout=config.transaction_timeout,
            )
            erc721_nft = ocean.create_erc721_nft("Dataset name", "dtsymbol", from_wallet=wallet)
        ```
        :param name: ERC721 token name, str
        :param symbol: ERC721 token symbol, str
        :param from_wallet: wallet instance, wallet
        :param template_index: Template type of the token, int
        :param additional_erc20_deployer: Address of another ERC20 deployer, str
        :param token_uri: URL for ERC721 token, str

        :return: `ERC721NFT` instance
        """

        if not additional_erc20_deployer:
            additional_erc20_deployer = ZERO_ADDRESS

        if not additional_metadata_updater:
            additional_metadata_updater = ZERO_ADDRESS

        nft_factory = self.get_nft_factory()

        tx_id = nft_factory.deploy_erc721_contract(
            name=name,
            symbol=symbol,
            template_index=template_index,
            additional_metadata_updater=additional_metadata_updater,
            additional_erc20_deployer=additional_erc20_deployer,
            token_uri=token_uri,
            transferable=transferable,
            owner=owner if owner is not None else from_wallet.address,
            from_wallet=from_wallet,
        )

        address = nft_factory.get_token_address(tx_id)
        assert address, "new NFT token has no address"
        token = ERC721NFT(self.web3, address)
        return token

    @enforce_types
    def get_nft_token(self, token_address: str) -> ERC721NFT:
        """
        :param token_address: Token contract address, str
        :return: `ERC721NFT` instance
        """

        return ERC721NFT(self.web3, token_address)

    @enforce_types
    def get_datatoken(self, token_address: str) -> ERC20Token:
        """
        :param token_address: Token contract address, str
        :return: `ERC20Token` instance
        """

        return ERC20Token(self.web3, token_address)

    @enforce_types
    def get_nft_factory(self, nft_factory_address: str = "") -> ERC721FactoryContract:
        """
        :param nft_factory_address: contract address, str

        :return: `ERC721FactoryContract` instance
        """
        if not nft_factory_address:
            nft_factory_address = get_address_of_type(
                self.config, ERC721FactoryContract.CONTRACT_NAME
            )

        return ERC721FactoryContract(self.web3, nft_factory_address)

    @enforce_types
    def get_user_orders(
        self, address: str, datatoken: Optional[str] = None
    ) -> List[AttributeDict]:
        """
        :return: List of orders `[Order]`
        """
        dt = ERC20Token(self.web3, datatoken)
        _orders = []
        for log in dt.get_start_order_logs(
            address, from_all_tokens=not bool(datatoken)
        ):
            a = dict(log.args.items())
            a["amount"] = int(log.args.amount)
            a["address"] = log.address
            a["transactionHash"] = log.transactionHash
            a = AttributeDict(a.items())

            _orders.append(a)

        return _orders

    @property
    @enforce_types
    def dispenser(self):
        return Dispenser(self.web3, get_address_of_type(self.config, "Dispenser"))

    @property
    @enforce_types
    def fixed_rate_exchange(self):
        return FixedRateExchange(
            self.web3, get_address_of_type(self.config, "FixedPrice")
        )

    @enforce_types
    def create_fixed_rate(
        self,
        erc20_token: ERC20Token,
        base_token: ERC20Token,
        amount: int,
        from_wallet: Wallet,
    ) -> bytes:
        fixed_price_address = get_address_of_type(self.config, "FixedPrice")
        erc20_token.approve(fixed_price_address, amount, from_wallet)

        tx = erc20_token.create_fixed_rate(
            fixed_price_address=fixed_price_address,
            base_token_address=base_token.address,
            owner=from_wallet.address,
            publish_market_swap_fee_collector=from_wallet.address,
            allowed_swapper=ZERO_ADDRESS,
            base_token_decimals=base_token.decimals(),
            datatoken_decimals=erc20_token.decimals(),
            fixed_rate=self.to_wei(1),
            publish_market_swap_fee_amount=int(1e15),
            with_mint=0,
            from_wallet=from_wallet,
        )
        tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx)
        fixed_rate_event = erc20_token.get_event_log(
            ERC721FactoryContract.EVENT_NEW_FIXED_RATE,
            tx_receipt.blockNumber,
            self.web3.eth.block_number,
            None,
        )
        exchange_id = fixed_rate_event[0].args.exchangeId

        return exchange_id

    @property
    @enforce_types
    def factory_router(self):
        return FactoryRouter(self.web3, get_address_of_type(self.config, "Router"))

    @enforce_types
    def create_pool(
        self,
        erc20_token: ERC20Token,
        base_token: ERC20Token,
        rate: int,
        vesting_amount: int,
        vesting_blocks: int,
        base_token_amount: int,
        lp_swap_fee_amount: int,
        publish_market_swap_fee_amount: int,
        from_wallet: Wallet,
    ) -> BPool:
        base_token.approve(
            get_address_of_type(self.config, "Router"), self.to_wei("2000"), from_wallet
        )

        tx = erc20_token.deploy_pool(
            rate=rate,
            base_token_decimals=base_token.decimals(),
            vesting_amount=vesting_amount,
            vesting_blocks=vesting_blocks,
            base_token_amount=base_token_amount,
            lp_swap_fee_amount=lp_swap_fee_amount,
            publish_market_swap_fee_amount=publish_market_swap_fee_amount,
            ss_contract=get_address_of_type(self.config, "Staking"),
            base_token_address=base_token.address,
            base_token_sender=from_wallet.address,
            publisher_address=from_wallet.address,
            publish_market_swap_fee_collector=get_address_of_type(
                self.config, "OPFCommunityFeeCollector"
            ),
            pool_template_address=get_address_of_type(self.config, "poolTemplate"),
            from_wallet=from_wallet,
        )
        tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx)
        pool_event = self.factory_router.get_event_log(
            ERC721FactoryContract.EVENT_NEW_POOL,
            tx_receipt.blockNumber,
            self.web3.eth.block_number,
            None,
        )

        bpool_address = pool_event[0].args.poolAddress
        bpool = BPool(self.web3, bpool_address)

        return bpool

    @enforce_types
    def build_compute_provider_fees(
        self,
        provider_data: Union[str, dict],
        provider_fee_address: str,
        provider_fee_token: str,
        provider_fee_amount: int,
        valid_until: int,
    ) -> tuple:
        if isinstance(provider_data, dict):
            provider_data = json.dumps(provider_data, separators=(",", ":"))

        message = self.web3.solidityKeccak(
            ["bytes", "address", "address", "uint256", "uint256"],
            [
                self.web3.toHex(self.web3.toBytes(text=provider_data)),
                provider_fee_address,
                provider_fee_token,
                provider_fee_amount,
                valid_until,
            ],
        )
        signed = self.web3.eth.sign(provider_fee_address, data=message)
        signature = split_signature(signed)

        return (
            signature.v,
            signature.r,
            signature.s,
            self.web3.toHex(self.web3.toBytes(text=provider_data)),
        )
