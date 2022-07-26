#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""Ocean module."""
import logging
from decimal import Decimal
from typing import Dict, List, Optional, Type, Union

from enforce_typing import enforce_types
from web3.datastructures import AttributeDict

from ocean_lib.assets.asset import Asset
from ocean_lib.config import Config
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.models.compute_input import ComputeInput
from ocean_lib.models.data_nft import DataNFT
from ocean_lib.models.data_nft_factory import DataNFTFactoryContract
from ocean_lib.models.datatoken import Datatoken
from ocean_lib.models.dispenser import Dispenser
from ocean_lib.models.factory_router import FactoryRouter
from ocean_lib.models.fixed_rate_exchange import FixedRateExchange
from ocean_lib.models.side_staking import SideStaking
from ocean_lib.ocean.ocean_assets import OceanAssets
from ocean_lib.ocean.ocean_compute import OceanCompute
from ocean_lib.ocean.util import get_address_of_type, get_ocean_token_address, get_web3
from ocean_lib.services.service import Service
from ocean_lib.structures.algorithm_metadata import AlgorithmMetadata
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.currency import DECIMALS_18
from ocean_lib.web3_internal.currency import format_units as _format_units
from ocean_lib.web3_internal.currency import from_wei as _from_wei
from ocean_lib.web3_internal.currency import parse_units as _parse_units
from ocean_lib.web3_internal.currency import to_wei as _to_wei
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

    @property
    @enforce_types
    def OCEAN_token(self) -> Datatoken:
        return Datatoken(self.web3, self.OCEAN_address)

    @enforce_types
    def to_wei(self, amount_in_ether: Union[Decimal, str, int]):
        return _to_wei(amount_in_ether)

    @enforce_types
    def from_wei(self, amount_in_wei: int):
        return _from_wei(amount_in_wei)

    @enforce_types
    def parse_units(self, amount: Union[Decimal, str, int], units: int = DECIMALS_18):
        return _parse_units(amount, units)

    @enforce_types
    def format_units(self, amount: Union[Decimal, str, int], units: int = DECIMALS_18):
        return _format_units(amount, units)

    @enforce_types
    def create_data_nft(
        self,
        name: str,
        symbol: str,
        from_wallet: Wallet,
        token_uri: Optional[str] = "https://oceanprotocol.com/nft/",
        template_index: Optional[int] = 1,
        additional_datatoken_deployer: Optional[str] = None,
        additional_metadata_updater: Optional[str] = None,
        transferable: bool = True,
        owner: Optional[str] = None,
    ) -> DataNFT:
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
            data_nft = ocean.create_data_nft("Dataset name", "dtsymbol", from_wallet=wallet)
        ```
        :param name: data NFT token name, str
        :param symbol: data NFT token symbol, str
        :param from_wallet: wallet instance, wallet
        :param template_index: Template type of the token, int
        :param additional_datatoken_deployer: Address of another ERC20 deployer, str
        :param token_uri: URL for the data NFT token, str

        :return: `DataNFT` instance
        """

        if not additional_datatoken_deployer:
            additional_datatoken_deployer = ZERO_ADDRESS

        if not additional_metadata_updater:
            additional_metadata_updater = ZERO_ADDRESS

        nft_factory = self.get_nft_factory()

        tx_id = nft_factory.deploy_erc721_contract(
            name=name,
            symbol=symbol,
            template_index=template_index,
            additional_metadata_updater=additional_metadata_updater,
            additional_datatoken_deployer=additional_datatoken_deployer,
            token_uri=token_uri,
            transferable=transferable,
            owner=owner if owner is not None else from_wallet.address,
            from_wallet=from_wallet,
        )

        address = nft_factory.get_token_address(tx_id)
        assert address, "new NFT token has no address"
        token = DataNFT(self.web3, address)
        return token

    @enforce_types
    def get_nft_token(self, token_address: str) -> DataNFT:
        """
        :param token_address: Token contract address, str
        :return: `DataNFT` instance
        """

        return DataNFT(self.web3, token_address)

    @enforce_types
    def get_datatoken(self, token_address: str) -> Datatoken:
        """
        :param token_address: Token contract address, str
        :return: `Datatoken` instance
        """

        return Datatoken(self.web3, token_address)

    @enforce_types
    def get_nft_factory(self, nft_factory_address: str = "") -> DataNFTFactoryContract:
        """
        :param nft_factory_address: contract address, str

        :return: `DataNFTFactoryContract` instance
        """
        if not nft_factory_address:
            nft_factory_address = get_address_of_type(
                self.config, DataNFTFactoryContract.CONTRACT_NAME
            )

        return DataNFTFactoryContract(self.web3, nft_factory_address)

    @enforce_types
    def get_user_orders(
        self, address: str, datatoken: Optional[str] = None
    ) -> List[AttributeDict]:
        """
        :return: List of orders `[Order]`
        """
        dt = Datatoken(self.web3, datatoken)
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

    @property
    @enforce_types
    def side_staking(self):
        return SideStaking(self.web3, get_address_of_type(self.config, "Staking"))

    @enforce_types
    def create_fixed_rate(
        self,
        datatoken: Datatoken,
        base_token: Datatoken,
        amount: int,
        fixed_rate: int,
        from_wallet: Wallet,
    ) -> bytes:
        fixed_price_address = get_address_of_type(self.config, "FixedPrice")
        datatoken.approve(fixed_price_address, amount, from_wallet)

        tx = datatoken.create_fixed_rate(
            fixed_price_address=fixed_price_address,
            base_token_address=base_token.address,
            owner=from_wallet.address,
            publish_market_swap_fee_collector=from_wallet.address,
            allowed_swapper=ZERO_ADDRESS,
            base_token_decimals=base_token.decimals(),
            datatoken_decimals=datatoken.decimals(),
            fixed_rate=fixed_rate,
            publish_market_swap_fee_amount=int(1e15),
            with_mint=0,
            from_wallet=from_wallet,
        )
        tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx)
        fixed_rate_event = datatoken.get_event_log(
            DataNFTFactoryContract.EVENT_NEW_FIXED_RATE,
            tx_receipt.blockNumber,
            self.web3.eth.block_number,
            None,
        )
        exchange_id = fixed_rate_event[0].args.exchangeId

        return exchange_id

    @property
    @enforce_types
    def factory_router(self) -> FactoryRouter:
        return FactoryRouter(self.web3, get_address_of_type(self.config, "Router"))

    @enforce_types
    def retrieve_provider_fees(
        self, asset: Asset, access_service: Service, publisher_wallet: Wallet
    ) -> tuple:

        initialize_response = DataServiceProvider.initialize(
            asset.did, access_service, consumer_address=publisher_wallet.address
        )
        initialize_data = initialize_response.json()
        provider_fees = initialize_data["providerFee"]

        return (
            provider_fees["providerFeeAddress"],
            provider_fees["providerFeeToken"],
            provider_fees["providerFeeAmount"],
            provider_fees["v"],
            provider_fees["r"],
            provider_fees["s"],
            provider_fees["validUntil"],
            provider_fees["providerData"],
        )

    @enforce_types
    def retrieve_provider_fees_for_compute(
        self,
        datasets: List[ComputeInput],
        algorithm_data: Union[ComputeInput, AlgorithmMetadata],
        consumer_address: str,
        compute_environment: str,
        valid_until: int,
    ) -> tuple:

        initialize_compute_response = DataServiceProvider.initialize_compute(
            [x.as_dictionary() for x in datasets],
            algorithm_data.as_dictionary(),
            datasets[0].service.service_endpoint,
            consumer_address,
            compute_environment,
            valid_until,
        )

        return initialize_compute_response.json()
