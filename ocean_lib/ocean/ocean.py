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
                    'network': config.get('network',''),
                    'dtfactory.address': config.get('dtfactory.address',''),
                    'sfactory.address': config.get('sfactory.address',''),
                    'OCEAN.address': config.get('OCEAN.address',''),
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

    @property
    def OCEAN_address(self):
        return self.config.OCEAN_address

    @enforce.runtime_validation
    def create_data_token(self, blob:str, from_wallet: Wallet) -> DataToken:
        dtfactory = DTFactory(self._web3, self._config.dtfactory_address)
        DT_address = dtfactory.createToken(blob, from_wallet=from_wallet)
        DT = DataToken(self._web3, DT_address)
        assert DT.address == DT_address        
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

        OCEAN = BToken(self._web3, self.OCEAN_address)
        assert OCEAN.balanceOf_base(from_wallet.address) >= num_OCEAN_base, \
            "insufficient OCEAN"
        OCEAN.approve(pool_address, num_OCEAN_base, from_wallet)
        pool.bind(self.OCEAN_address, num_OCEAN_base,
                  bconstants.INIT_WEIGHT_OCEAN, from_wallet)

        return pool

    @enforce.runtime_validation
    def get_pool(self, pool_address: str) -> SPool:
        return SPool(self._web3, pool_address)

    #============================================================
    #to simplify balancer flows. These methods are here because
    # SPool doesn't know (and shouldn't know) OCEAN_address and _DT_address
    @enforce.runtime_validation     
    def addLiquidity(self, pool_address: str,
                     num_DT_base: int, num_OCEAN_base: int,
                     from_wallet: Wallet):
        DT_address = self._DT_address(pool_address)
        self._addLiquidity(pool_address, DT_address, num_DT_base,
                           bconstants.INIT_WEIGHT_DT, from_wallet)
        self._addLiquidity(pool_address, self.OCEAN_address, num_OCEAN_base,
                           bconstants.INIT_WEIGHT_OCEAN, from_wallet)

    @enforce.runtime_validation
    def _addLiquidity(self, pool_address: str, token_address: str,
                      num_add_base: int, weight_base: int, from_wallet: Wallet):
        assert num_add_base >= 0
        if num_add_base == 0: return
        
        token = BToken(self._web3, token_address)
        assert token.balanceOf_base(from_wallet.address) >= num_add_base, \
            "insufficient funds"
        
        token.approve(pool_address, num_add_base, from_wallet)

        pool = SPool(self._web3, pool_address)
        num_before_base = token.balanceOf_base(pool_address)
        num_after_base = num_before_base + num_add_base
        pool.rebind(token_address, num_after_base, weight_base, from_wallet)

    @enforce.runtime_validation
    def remove_liquidity(self, pool_address: str,
                        num_DT_base:int, num_OCEAN_base:int,
                        from_wallet: Wallet):
        DT_address = self._DT_address(pool_address)
        self._remove_liquidity(pool_address, DT_address, num_DT_base,
                               bconstants.INIT_WEIGHT_DT, from_wallet)
        self._remove_liquidity(pool_address, self.OCEAN_address, num_OCEAN_base,
                               bconstants.INIT_WEIGHT_OCEAN, from_wallet)

    @enforce.runtime_validation
    def _remove_liquidity(self, pool_address: str,
                          token_address: str, num_remove_base: int,
                          weight_base: int, from_wallet: Wallet):
        assert num_remove_base >= 0
        if num_remove_base == 0: return
        
        token = BToken(self._web3, token_address)
        num_before_base = token.balanceOf_base(pool_address)
        num_after_base = num_before_base - num_remove_base
        assert num_after_base >= 0, "tried to remove too much"
        
        pool = SPool(self._web3, pool_address)
        pool.rebind(token_address, num_after_base, weight_base, from_wallet)

    @enforce.runtime_validation
    def buy_data_tokens(self, pool_address: str,
                        num_DT_base:int, max_num_OCEAN_base:int,
                        from_wallet: Wallet):
        """
        Buy data tokens from this pool, if total spent <= max_num_OCEAN.
        -Caller is spending OCEAN, and receiving DT
        -OCEAN's going into pool, DT's going out of pool
        """
        OCEAN = BToken(self._web3, self.OCEAN_address)
        OCEAN.approve(pool_address, max_num_OCEAN_base, from_wallet)
        
        DT_address = self._DT_address(pool_address)
        pool = SPool(self._web3, pool_address)
        pool.swapExactAmountOut(
            tokenIn_address = self.OCEAN_address, #entering pool
            maxAmountIn_base = max_num_OCEAN_base, #""
            tokenOut_address = DT_address,  #leaving pool
            tokenAmountOut_base = num_DT_base, #""
            maxPrice_base = 2 ** 255, #here we limit by max_num_OCEAN, not price
            from_wallet = from_wallet,
        )

    @enforce.runtime_validation
    def sell_data_tokens(self, pool_address: str,
                       num_DT_base: int, min_num_OCEAN_base: int,
                       from_wallet: Wallet):
        """
        Sell data tokens into this pool, if total income >= min_num_OCEAN
        -Caller is spending DT, and receiving OCEAN
        -DT's going into pool, OCEAN's going out of pool
        """
        DT_address = self._DT_address(pool_address)
        DT = BToken(self._web3, DT_address)
        DT.approve(pool_address, num_DT_base, from_wallet=from_wallet)
        
        pool = SPool(self._web3, pool_address)
        pool.swapExactAmountIn(
            tokenIn_address = DT_address, #entering pool
            tokenAmountIn_base = num_DT_base, #""
            tokenOut_address = self.OCEAN_address, #leaving pool
            minAmountOut_base = min_num_OCEAN_base, # ""
            maxPrice_base = 2 ** 255, #here we limit by max_num_OCEAN, not price
            from_wallet = from_wallet,
        )

    @enforce.runtime_validation
    def get_DT_price_base(self, pool_address: str) -> int:
        DT_address = self._DT_address(pool_address)
        pool = SPool(self._web3, pool_address)
        return pool.getSpotPrice_base(
            tokenIn_address = self.OCEAN_address,
            tokenOut_address = DT_address)

    @enforce.runtime_validation
    def add_liquidity_finalized(
            self, pool_address: str, num_BPT_base: int, max_num_DT_base: int,
            max_num_OCEAN_base: int, from_wallet: Wallet):
        """Add liquidity to a pool that's been finalized.
        Buy num_BPT tokens from the pool, spending DT and OCEAN as needed"""
        assert self._is_valid_DT_OCEAN_pool(pool_address)
        DT_address = self._DT_address(pool_address)
        DT = BToken(self._web3, DT_address)
        DT.approve(pool_address, max_num_DT_base, from_wallet=from_wallet)
        
        OCEAN = BToken(self._web3, self.OCEAN_address)
        OCEAN.approve(pool_address, max_num_OCEAN_base, from_wallet=from_wallet)
        
        pool = SPool(self._web3, pool_address)
        pool.joinPool(num_BPT_base, [max_num_DT_base, max_num_OCEAN_base],
                      from_wallet=from_wallet)
        
    @enforce.runtime_validation
    def _DT_address(self, pool_address: str) -> str:
        """Returns the address of this pool's datatoken."""
        assert self._is_valid_DT_OCEAN_pool(pool_address)
        pool = SPool(self._web3, pool_address)
        return pool.getCurrentTokens()[0]

    @enforce.runtime_validation
    def _is_valid_DT_OCEAN_pool(self, pool_address) -> bool:
        pool = SPool(self._web3, pool_address)
        if pool.getNumTokens() != 2:
            return False

        #DT should be 0th token, OCEAN should be 1st token
        if pool.getCurrentTokens()[1] != self.OCEAN_address:
            return False
        return True
