#  Copyright 2021 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

from ocean_lib.config_provider import ConfigProvider
from ocean_lib.web3_internal.contract_handler import ContractHandler

_NETWORK = "ganache"

def test1():
    config = ConfigProvider.get_config()
    contracts_addresses = ContractHandler.get_contracts_addresses(
        _NETWORK, config.address_file)
