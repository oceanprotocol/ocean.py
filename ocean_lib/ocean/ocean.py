"""Ocean module."""
#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-Lic;ense-Identifier: Apache-2.0

import logging

from ocean_lib.models.data_token import DataToken
from ocean_lib.models.fixed_rate_exchange import FixedRateExchange
from ocean_lib.ocean.ocean_exchange import OceanExchange
from ocean_lib.ocean.ocean_pool import OceanPool
from ocean_lib.web3_internal.contract_handler import ContractHandler
from ocean_lib.web3_internal.wallet import Wallet
from ocean_lib.web3_internal.web3_provider import Web3Provider
from ocean_lib.config import Config

from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.config_provider import ConfigProvider

from ocean_lib.models.dtfactory import DTFactory
from ocean_lib.ocean.ocean_assets import OceanAssets
from ocean_lib.ocean.ocean_auth import OceanAuth
from ocean_lib.ocean.ocean_compute import OceanCompute
from ocean_lib.ocean.ocean_services import OceanServices
from ocean_lib.ocean.util import get_web3_connection_provider, get_ocean_token_address, get_bfactory_address, to_base_18
from ocean_lib.web3_internal.web3helper import Web3Helper

CONFIG_FILE_ENVIRONMENT_NAME = 'CONFIG_FILE'

logger = logging.getLogger('ocean')


class Ocean:
    """The Ocean class is the entry point into Ocean Protocol."""

    def __init__(self, config=None, data_provider=None):
        """
        Initialize Ocean class.
           >> # Make a new Ocean instance
           >> ocean = Ocean({...})

        This class provides the main top-level functions in ocean protocol:
         * Publish assets metadata and associated services
            * Each asset is assigned a unique DID and a DID Document (DDO)
            * The DDO contains the asset's services including the metadata
            * The DID is registered on-chain with a URL of the metadata store
              to retrieve the DDO from

            >> asset = ocean.assets.create(metadata, publisher_wallet)

         * Discover/Search assets via the current configured metadata store (Aquarius)
            >> assets_list = ocean.assets.search('search text')

        An instance of Ocean is parameterized by a `Config` instance.

        :param config: Config instance
        """
        # Configuration information for the market is stored in the Config class
        # config = Config(filename=config_file, options_dict=config_dict)
        if not config:
            config = ConfigProvider.get_config()

        if isinstance(config, dict):

            aqua_url = config.get('metadataStoreUrl', config.get('aquarius.url', 'http://localhost:5000'))

            config_dict = {
                'eth-network': {
                    'network': config.get('network', ''),
                    'address.file': config.get('address.file', 'artifacts/addresses.json'),
                },
                'resources': {
                    'aquarius.url': aqua_url,
                    'provider.url': config.get('providerUri', 'http://localhost:8030')
                }
            }
            config = Config(options_dict=config_dict)
            ConfigProvider.set_config(config)

        self._config = config
        self._web3 = Web3Provider.get_web3(provider=get_web3_connection_provider(self._config.network_url))
        ContractHandler.set_artifacts_path(self._config.artifacts_path)

        if not data_provider:
            data_provider = DataServiceProvider

        self.assets = OceanAssets(
            self._config,
            data_provider
        )
        self.services = OceanServices()
        self.auth = OceanAuth(self._config.storage_path)
        self.compute = OceanCompute(
            self.auth,
            self._config,
            data_provider
        )
        network = Web3Helper.get_network_name()
        ocean_address = get_ocean_token_address(network)
        self.pool = OceanPool(ocean_address, get_bfactory_address(network))
        self.exchange = OceanExchange(ocean_address,
                                      FixedRateExchange.configured_address(
                                          network or Web3Helper.get_network_name(), ConfigProvider.get_config().address_file
                                      ),
                                      self.config)

        logger.debug('Ocean instance initialized: ')

    @property
    def config(self):
        return self._config

    @property
    def web3(self):
        return self._web3

    @property
    def OCEAN_address(self):
        return get_ocean_token_address(Web3Helper.get_network_name())

    def create_data_token(self, blob: str, name: str, symbol: str,
                          from_wallet: Wallet, cap: int=DataToken.DEFAULT_CAP) -> DataToken:
        dtfactory = self.get_dtfactory()
        tx_id = dtfactory.createToken(blob, name, symbol, to_base_18(cap), from_wallet=from_wallet)
        return DataToken(dtfactory.get_token_address(tx_id))

    def get_data_token(self, token_address: str) -> DataToken:
        return DataToken(token_address)

    def get_dtfactory(self, dtfactory_address: str='') -> DTFactory:
        dtf_address = dtfactory_address or DTFactory.configured_address(
            Web3Helper.get_network_name(), self._config.address_file)
        return DTFactory(dtf_address)

