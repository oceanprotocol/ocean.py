#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""Ocean module."""
import logging
from typing import Dict, List, Optional, Type, Union

from enforce_typing import enforce_types
from eth_utils import remove_0x_prefix
from ocean_lib.config import Config
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.models.data_token import DataToken
from ocean_lib.models.erc20_token import ERC20Token
from ocean_lib.models.erc721_factory import ERC721FactoryContract
from ocean_lib.models.erc721_token import ERC721Token
from ocean_lib.models.fixed_rate_exchange import FixedRateExchange
from ocean_lib.models.models_structures import ErcCreateData
from ocean_lib.models.order import Order
from ocean_lib.ocean.ocean_assets import OceanAssets
from ocean_lib.ocean.ocean_compute import OceanCompute
from ocean_lib.ocean.ocean_exchange import OceanExchange
from ocean_lib.ocean.ocean_pool import OceanPool
from ocean_lib.ocean.util import (
    get_address_of_type,
    get_bfactory_address,
    get_ocean_token_address,
    get_web3,
)
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.utils import get_network_name
from ocean_lib.web3_internal.wallet import Wallet
from web3.datastructures import AttributeDict

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
                cache_key, config.get("metadata_cache_uri", "http://localhost:5000")
            )
            config_dict = {
                "eth-network": {"network": config.get("network", "")},
                "resources": {
                    "metadata_cache_uri": metadata_cache_uri,
                    "provider.url": config.get("providerUri", "http://localhost:8030"),
                },
            }
            config = Config(options_dict=config_dict)
        self.config = config
        self.web3 = get_web3(self.config.network_url)

        if not data_provider:
            data_provider = DataServiceProvider

        network = get_network_name(web3=self.web3)
        self.assets = OceanAssets(self.config, self.web3, data_provider)
        self.compute = OceanCompute(self.config, data_provider)

        ocean_address = get_ocean_token_address(self.config.address_file, network)
        # FIXME: reinstate after figuring out bfactory and dtfactory
        # self.pool = OceanPool(
        #    self.web3,
        #    ocean_address,
        #    get_bfactory_address(self.config.address_file, network),
        #    get_dtfactory_address(self.config.address_file, network),
        # )
        # self.exchange = OceanExchange(
        #    self.web3,
        #    ocean_address,
        #    FixedRateExchange.configured_address(network, self.config.address_file),
        #    self.config,
        # )

        logger.debug("Ocean instance initialized: ")

    @property
    @enforce_types
    def OCEAN_address(self) -> str:
        return get_ocean_token_address(self.config.address_file, web3=self.web3)

    @enforce_types
    def create_nft_token(
        self,
        name: str,
        symbol: str,
        from_wallet: Wallet,
        token_uri: Optional[str] = "https://oceanprotocol.com/nft/",
        template_index: Optional[int] = 1,
        additional_erc20_deployer: Optional[str] = None,
    ) -> ERC721Token:
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
            datatoken = ocean.create_data_token("Dataset name", "dtsymbol", from_wallet=wallet)
        ```
        :param name: ERC721 token name, str
        :param symbol: ERC721 token symbol, str
        :param from_wallet: wallet instance, wallet
        :param template_index: Template type of the token, int
        :param additional_erc20_deployer: Address of another ERC20 deployer, str
        :param token_uri: URL for ERC721 token, str

        :return: `ERC721Token` instance
        """

        if not additional_erc20_deployer:
            additional_erc20_deployer = ZERO_ADDRESS

        nft_factory = self.get_nft_factory()
        tx_id = nft_factory.deploy_erc721_contract(
            name=name,
            symbol=symbol,
            template_index=template_index,
            additional_erc20_deployer=additional_erc20_deployer,
            token_uri=token_uri,
            from_wallet=from_wallet,
        )

        address = nft_factory.get_token_address(tx_id)
        assert address, "new NFT token has no address"
        token = ERC721Token(self.web3, address)
        return token

    def create_data_token(
        self,
        erc20_data: ErcCreateData,
        erc721_token: ERC721Token,
        from_wallet: Wallet,
    ) -> ERC20Token:
        nft_factory = self.get_nft_factory()
        tx_id = erc721_token.create_erc20(erc20_data, from_wallet)
        address = nft_factory.get_data_token_address(tx_id)
        assert address, "new data token has no address"
        token = ERC20Token(self.web3, address)
        return token

    @enforce_types
    def get_nft_token(self, token_address: str) -> ERC721Token:
        """
        :param token_address: Token contract address, str
        :return: `ERC721Token` instance
        """

        return ERC721Token(self.web3, token_address)

    @enforce_types
    def get_data_token(self, token_address: str) -> ERC20Token:
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

    # TODO: adapt for v4
    @enforce_types
    def get_user_orders(
        self,
        address: str,
        datatoken: Optional[str] = None,
        service_id: Optional[int] = None,
    ) -> List[Order]:
        """
        :return: List of orders `[Order]`
        """
        dt = DataToken(self.web3, datatoken)
        _orders = []
        for log in dt.get_start_order_logs(
            address, from_all_tokens=not bool(datatoken)
        ):
            a = dict(log.args.items())
            a["amount"] = int(log.args.amount)
            a["marketFee"] = int(log.args.marketFee)
            a = AttributeDict(a.items())

            # 'datatoken', 'amount', 'timestamp', 'transactionId', 'did', 'payer', 'consumer', 'serviceId', 'serviceType'
            order = Order(
                log.address,
                a.amount,
                a.timestamp,
                log.transactionHash,
                f"did:op:{remove_0x_prefix(log.address)}",
                a.payer,
                a.consumer,
                a.serviceId,
                None,
            )
            if service_id is None or order.serviceId == service_id:
                _orders.append(order)

        return _orders
