#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""Ocean module."""
import json
import logging
from typing import Dict, List, Optional, Type, Union

from enforce_typing import enforce_types
from web3.datastructures import AttributeDict

from ocean_lib.assets.ddo import DDO
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.example_config import config_defaults
from ocean_lib.models.compute_input import ComputeInput
from ocean_lib.models.data_nft import DataNFT
from ocean_lib.models.data_nft_factory import DataNFTFactoryContract
from ocean_lib.models.datatoken_base import DatatokenBase
from ocean_lib.models.df.df_rewards import DFRewards
from ocean_lib.models.df.df_strategy_v1 import DFStrategyV1
from ocean_lib.models.dispenser import Dispenser
from ocean_lib.models.factory_router import FactoryRouter
from ocean_lib.models.fixed_rate_exchange import FixedRateExchange
from ocean_lib.models.ve.smart_wallet_checker import SmartWalletChecker
from ocean_lib.models.ve.ve_allocate import VeAllocate
from ocean_lib.models.ve.ve_delegation import VeDelegation
from ocean_lib.models.ve.ve_delegation_proxy import VeDelegationProxy
from ocean_lib.models.ve.ve_fee_distributor import VeFeeDistributor
from ocean_lib.models.ve.ve_fee_estimate import VeFeeEstimate
from ocean_lib.models.ve.ve_ocean import VeOcean
from ocean_lib.ocean.ocean_assets import OceanAssets
from ocean_lib.ocean.ocean_compute import OceanCompute
from ocean_lib.ocean.util import get_address_of_type, get_ocean_token_address
from ocean_lib.services.service import Service
from ocean_lib.structures.algorithm_metadata import AlgorithmMetadata
from ocean_lib.web3_internal.utils import check_network

logger = logging.getLogger("ocean")


class Ocean:
    """The Ocean class is the entry point into Ocean Protocol."""

    @enforce_types
    def __init__(self, config_dict: Dict, data_provider: Optional[Type] = None) -> None:
        """Initialize Ocean class.

        Usage: Make a new Ocean instance

        `ocean = Ocean({...})`

        This class provides the main top-level functions in ocean protocol:
        1. Publish assets metadata and associated services
            - Each asset is assigned a unique DID and a DID Document (DDO)
            - The DDO contains the asset's services including the metadata
            - The DID is registered on-chain with a URL of the metadata store
              to retrieve the DDO from

            `ddo = ocean.assets.create(metadata, publisher_wallet)`

        2. Discover/Search ddos via the current configured metadata store (Aquarius)

            - Usage:
            `ddos_list = ocean.assets.search('search text')`

        An instance of Ocean is parameterized by a `Config` instance.

        :param config_dict: variable definitions
        :param data_provider: `DataServiceProvider` instance
        """
        config_errors = {}
        for key, value in config_defaults.items():
            if key not in config_dict:
                config_errors[key] = "required"
                continue

            if not isinstance(config_dict[key], type(value)):
                config_errors[key] = f"must be {type(value).__name__}"

        if config_errors:
            raise Exception(json.dumps(config_errors))

        self.config_dict = config_dict

        network_name = config_dict["NETWORK_NAME"]
        check_network(network_name)

        if not data_provider:
            data_provider = DataServiceProvider

        self.assets = OceanAssets(self.config_dict, data_provider)
        self.compute = OceanCompute(self.config_dict, data_provider)

        logger.debug("Ocean instance initialized: ")

    # ======================================================================
    # OCEAN
    @property
    @enforce_types
    def OCEAN_address(self) -> str:
        return get_ocean_token_address(self.config)

    @property
    @enforce_types
    def OCEAN_token(self) -> DatatokenBase:
        return DatatokenBase.get_typed(self.config, self.OCEAN_address)

    @property
    @enforce_types
    def OCEAN(self):  # alias for OCEAN_token
        return self.OCEAN_token

    # ======================================================================
    # objects for singleton smart contracts
    @property
    @enforce_types
    def data_nft_factory(self) -> DataNFTFactoryContract:
        return DataNFTFactoryContract(self.config, self._addr("ERC721Factory"))

    @property
    @enforce_types
    def dispenser(self) -> Dispenser:
        return Dispenser(self.config, self._addr("Dispenser"))

    @property
    @enforce_types
    def fixed_rate_exchange(self) -> FixedRateExchange:
        return FixedRateExchange(self.config, self._addr("FixedPrice"))

    @property
    @enforce_types
    def factory_router(self) -> FactoryRouter:
        return FactoryRouter(self.config, self._addr("Router"))

    # ======================================================================
    # token getters
    @enforce_types
    def get_nft_token(self, token_address: str) -> DataNFT:
        """
        :param token_address: Token contract address, str
        :return: `DataNFT` instance
        """
        return DataNFT(self.config, token_address)

    @enforce_types
    def get_datatoken(self, token_address: str) -> DatatokenBase:
        """
        :param token_address: Token contract address, str
        :return: `Datatoken1` or `Datatoken2` instance
        """
        return DatatokenBase.get_typed(self.config, token_address)

    # ======================================================================
    # orders
    @enforce_types
    def get_user_orders(self, address: str, datatoken: str) -> List[AttributeDict]:
        """
        :return: List of orders `[Order]`
        """
        dt = DatatokenBase.get_typed(self.config_dict, datatoken)
        _orders = []
        for log in dt.get_start_order_logs(address):
            a = dict(log.args.items())
            a["amount"] = int(log.args.amount)
            a["address"] = log.address
            a["transactionHash"] = log.transactionHash
            a = AttributeDict(a.items())

            _orders.append(a)

        return _orders

    # ======================================================================
    # provider fees
    @enforce_types
    def retrieve_provider_fees(
        self, ddo: DDO, access_service: Service, publisher_wallet
    ) -> dict:

        initialize_response = DataServiceProvider.initialize(
            ddo.did, access_service, consumer_address=publisher_wallet.address
        )
        initialize_data = initialize_response.json()
        provider_fees = initialize_data["providerFee"]

        return provider_fees

    @enforce_types
    def retrieve_provider_fees_for_compute(
        self,
        datasets: List[ComputeInput],
        algorithm_data: Union[ComputeInput, AlgorithmMetadata],
        consumer_address: str,
        compute_environment: str,
        valid_until: int,
    ) -> dict:

        initialize_compute_response = DataServiceProvider.initialize_compute(
            [x.as_dictionary() for x in datasets],
            algorithm_data.as_dictionary(),
            datasets[0].service.service_endpoint,
            consumer_address,
            compute_environment,
            valid_until,
        )

        return initialize_compute_response.json()

    # ======================================================================
    # DF/VE properties (alphabetical)
    @property
    @enforce_types
    def df_rewards(self) -> DFRewards:
        return DFRewards(self.config, self._addr("DFRewards"))

    @property
    @enforce_types
    def df_strategy_v1(self) -> DFStrategyV1:
        return DFStrategyV1(self.config, self._addr("DFStrategyV1"))

    @property
    @enforce_types
    def smart_wallet_checker(self) -> SmartWalletChecker:
        return SmartWalletChecker(self.config, self._addr("SmartWalletChecker"))

    @property
    @enforce_types
    def ve_allocate(self) -> VeAllocate:
        return VeAllocate(self.config, self._addr("veAllocate"))

    @property
    @enforce_types
    def ve_delegation(self) -> VeDelegation:
        return VeDelegation(self.config, self._addr("veDelegation"))

    @property
    @enforce_types
    def ve_delegation_proxy(self) -> VeDelegationProxy:
        return VeDelegationProxy(self.config, self._addr("veDelegationProxy"))

    @property
    @enforce_types
    def ve_fee_distributor(self) -> VeFeeDistributor:
        return VeFeeDistributor(self.config, self._addr("veFeeDistributor"))

    @property
    @enforce_types
    def ve_fee_estimate(self) -> VeFeeEstimate:
        return VeFeeEstimate(self.config, self._addr("veFeeEstimate"))

    @property
    @enforce_types
    def ve_ocean(self) -> VeOcean:
        return VeOcean(self.config, self._addr("veOCEAN"))

    @property
    @enforce_types
    def veOCEAN(self) -> VeOcean:  # alias for ve_ocean
        return self.ve_ocean

    # ======================================================================
    # helpers
    @property
    @enforce_types
    def config(self) -> dict:  # alias for config_dict
        return self.config_dict

    @enforce_types
    def _addr(self, type_str: str) -> str:
        return get_address_of_type(self.config, type_str)
