"""Ocean module."""
#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import enforce
import eth_account
import logging
import os

from ocean_lib.ocean import constants #import here to toggle type-checking

from ocean_lib.ocean.ocean_market import OceanMarket
from ocean_lib.web3_internal.contract_handler import ContractHandler
from ocean_lib.web3_internal.wallet import Wallet
from ocean_lib.web3_internal.web3_provider import Web3Provider
from ocean_lib import Config

from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.config_provider import ConfigProvider
from ocean_lib.models import bconstants
from ocean_lib.models.btoken import BToken
from ocean_lib.models.datatoken import DataToken
from ocean_lib.models.dtfactory import DTFactory
from ocean_lib.models.sfactory import SFactory
from ocean_lib.models.spool import SPool
from ocean_lib.ocean.ocean_assets import OceanAssets
from ocean_lib.ocean.ocean_auth import OceanAuth
from ocean_lib.ocean.ocean_compute import OceanCompute
from ocean_lib.ocean.ocean_services import OceanServices
from ocean_lib.ocean.util import get_web3_provider

CONFIG_FILE_ENVIRONMENT_NAME = 'CONFIG_FILE'

logger = logging.getLogger('ocean')

class Ocean:
    """The Ocean class is the entry point into Ocean Protocol."""

    def __init__(self, config=None, data_provider=None):
        # Configuration information for the market is stored in the Config class
        # config = Config(filename=config_file, options_dict=config_dict)
        if not config:
            config = ConfigProvider.get_config()

        if isinstance(config, dict):

            private_key = config.get('privateKey', None)
            if private_key:
                account = eth_account.Account.from_key(private_key)
                os.environ['PARITY_KEY'] = private_key
                os.environ['PARITY_ADDRESS'] = account.address

            aqua_url = config.get('metadataStoreUri', config.get('aquarius.url', 'http://localhost:5000'))
            config_dict = {
                'eth-network': {
                    'network': config['network'],
                    'dtfactory.address': config.get('dtfactory.address'),
                    'sfactory.address': config.get('sfactory.address'),
                    'OCEAN.address': config.get('OCEAN.address'),
                },
                'resources': {
                    'aquarius.url': aqua_url,
                    'provider.url': config.get('providerUri', 'http://localhost:8030')
                }
            }
            config = Config(options_dict=config_dict)
            ConfigProvider.set_config(config)

        self._config = config
        self._web3 = Web3Provider.get_web3(provider=get_web3_provider(self._config.network_url))
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
        self.ocean_market = OceanMarket(self._config, data_provider)

        logger.debug('Ocean instance initialized: ')

    @property
    def config(self):
        return self._config
    
    @property
    def web3(self):
        return self._web3

    @enforce.runtime_validation
    def create_data_token(self, blob:str, from_wallet: Wallet) -> DataToken:
        dtfactory = DTFactory(self._web3, self._config.dtfactory_address)
        DT_address = dtfactory.createToken(blob, from_wallet=from_wallet)
        DT = DataToken(self._web3, DT_address)
        assert dt.address == DT_address        
        return DT

    @enforce.runtime_validation
    def get_data_token(self, token_address: str) -> DataToken:
        return DataToken(self._web3, token_address)

    @enforce.runtime_validation
    def create_pool(self,
                    DT_address: str,
                    num_DT_base: int,
                    num_OCEAN_base:int,
                    from_wallet: Wallet) -> SPool:
        sfactory_address = self._config.sfactory_address
        OCEAN_address = self._config.OCEAN_address
        
        sfactory = SFactory(self._web3, sfactory_address)

        pool_address = sfactory.newSPool(from_wallet)
        pool = SPool(self._web3, pool_address)
        pool.setPublicSwap(True, from_wallet=from_wallet)
        pool.setSwapFee(bconstants.DEFAULT_SWAP_FEE, from_wallet) 

        DT = BToken(self._web3, DT_address)
        assert DT.balanceOf_base(from_wallet.address) >= num_DT_base, \
            "insufficient DT"
        DT.approve(pool_address, num_DT_base, from_wallet=from_wallet)
        pool.bind(DT_address, num_DT_base, bconstants.INIT_WEIGHT_DT,
                  from_wallet)

        OCEAN = BToken(self._web3, OCEAN_address)
        assert OCEAN.balanceOf_base(from_wallet.address) >= num_OCEAN_base, \
            "insufficient OCEAN"
        OCEAN.approve(pool_address, num_OCEAN_base, from_wallet)
        pool.bind(OCEAN_address, num_OCEAN_base, bconstants.INIT_WEIGHT_OCEAN,
                  from_wallet)

        return pool
