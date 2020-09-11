#!/usr/bin/env python
import json
import os
import sys
from pathlib import Path

from examples import ExampleConfig
from ocean_lib.config_provider import ConfigProvider
from ocean_lib.models.data_token import DataToken
from ocean_lib.models.ddo import DDOContract
from ocean_lib.models.dtfactory import DTFactory
from ocean_lib.models.fixed_rate_exchange import FixedRateExchange
from ocean_lib.models.bfactory import BFactory
from ocean_lib.models.bpool import BPool
from ocean_lib.ocean import util
from ocean_lib.ocean.util import get_web3_connection_provider
from ocean_lib.web3_internal.contract_handler import ContractHandler
from ocean_lib.web3_internal.utils import privateKeyToAddress
from ocean_lib.web3_internal.wallet import Wallet
from ocean_lib.web3_internal.web3_provider import Web3Provider
from tests.resources.helper_functions import get_web3, get_ganache_wallet, \
    get_publisher_ocean_instance

SUPPORTED_NETWORKS_STR = str(util.SUPPORTED_NETWORK_NAMES)[1:-1]


def main():
    network, address_file = processArgs()
    addresses = deploy(network, address_file)
    _s = json.dumps(addresses, indent=4)
    s = '**** deployed contracts with the following addresses ****\n' + _s
    print(s)


def processArgs():
    # set help message
    help = f"""
Deploy DataTokenTemplate and more to a target network. 

Usage: deploy.py NETWORK ADDRESSES_FILE_PATH
  NETWORK -- one of: {SUPPORTED_NETWORKS_STR}
  ADDRESSES_FILE_PATH -- path to json file to update the deployed contracts addresses
 """

    # ****SET INPUT ARGS****
    # got the right number of args?  If not, output help
    num_args = len(sys.argv) - 1
    num_args_needed = 1
    if num_args != num_args_needed:
        print(help)
        if num_args > 0:
            print("Got %d argument(s), need %s.\n" % (num_args, num_args_needed))
        sys.exit(0)

    # grab args
    network = sys.argv[1]
    print("Arguments: NETWORK=%s\n" % network)

    # corner cases
    if network not in util.SUPPORTED_NETWORK_NAMES:
        print(f"Invalid network. Supported networks: {SUPPORTED_NETWORKS_STR}")
        sys.exit(0)

    return network, sys.argv[2] if len(sys.argv) > 2 else ''


def deploy(network, addresses_file):
    config = ExampleConfig.get_config()
    ConfigProvider.set_config(config)
    Web3Provider.init_web3(provider=get_web3_connection_provider(config.network_url))
    ContractHandler.set_artifacts_path(config.artifacts_path)

    artifacts_path = ContractHandler.artifacts_path
    if not addresses_file:
        addresses_file = config.address_file
    else:
        addresses_file = Path(addresses_file).expanduser().resolve()

    ocean = get_publisher_ocean_instance()
    web3 = ocean.web3

    addresses = dict()

    if os.path.exists(addresses_file):
        with open(addresses_file) as f:
            network_addresses = json.load(f)
    else:
        network_addresses = {network: {}}

    _addresses = network_addresses[network]

    # ****SET ENVT****
    # grab vars
    factory_deployer_private_key = get_ganache_wallet().private_key

    # corner cases
    if invalidKey(factory_deployer_private_key):
        print("Need valid FACTORY_DEPLOYER_PRIVATE_KEY")
        sys.exit(0)

    # ****SEE FUNDS****
    print("Keys:\n%s" % Wallet(web3=get_web3(), private_key=factory_deployer_private_key).keysStr())
    print("")

    # ****DEPLOY****
    deployer_wallet = Wallet(web3, private_key=factory_deployer_private_key)
    minter_addr = deployer_wallet.address
    cap = 2 ** 255

    if DTFactory.CONTRACT_NAME not in _addresses:
        print("****Deploy DataTokenTemplate: begin****")
        dt_address = DataToken.deploy(
            web3, deployer_wallet, artifacts_path,
            'Template Contract', 'TEMPLATE',
            minter_addr, DataToken.DEFAULT_CAP_BASE,
            DTFactory.FIRST_BLOB, minter_addr
        )
        addresses[DataToken.CONTRACT_NAME] = dt_address
        print("****Deploy DataTokenTemplate: done****\n")

        print("****Deploy DTFactory: begin****")
        dtfactory = DTFactory(DTFactory.deploy(
            web3, deployer_wallet, artifacts_path, dt_address, minter_addr))
        addresses[DTFactory.CONTRACT_NAME] = dtfactory.address
        print("****Deploy DTFactory: done****\n")

    if BFactory.CONTRACT_NAME not in _addresses:
        print("****Deploy BPool: begin****")
        bpool_address = BPool.deploy(web3, deployer_wallet, artifacts_path)
        bpool_template = BPool(bpool_address)
        addresses[BPool.CONTRACT_NAME] = bpool_address
        print("****Deploy BPool: done****\n")

        print("****Deploy 'BFactory': begin****")
        bfactory_address = BFactory.deploy(web3, deployer_wallet, artifacts_path, bpool_template.address)
        bfactory = BFactory(bfactory_address)
        addresses[BFactory.CONTRACT_NAME] = bfactory_address
        print("****Deploy 'BFactory': done****\n")

    if FixedRateExchange.CONTRACT_NAME not in _addresses:
        print("****Deploy 'FixedRateExchange': begin****")
        addresses[FixedRateExchange.CONTRACT_NAME] = FixedRateExchange.deploy(web3, deployer_wallet, artifacts_path)
        print("****Deploy 'FixedRateExchange': done****\n")

    if DDOContract.CONTRACT_NAME not in _addresses:
        print("****Deploy 'DDO': begin****")
        addresses[DDOContract.CONTRACT_NAME] = DDOContract.deploy(web3, deployer_wallet, artifacts_path)
        print("****Deploy 'DDO': done****\n")

    if network == 'ganache' and 'Ocean' not in _addresses:
        print("****Deploy fake OCEAN: begin****")
        # For simplicity, hijack DataTokenTemplate.
        minter_addr = deployer_wallet.address
        OCEAN_cap = 1410 * 10 ** 6  # 1.41B
        OCEAN_cap_base = util.to_base_18(float(OCEAN_cap))
        OCEAN_token = DataToken(DataToken.deploy(
            web3, deployer_wallet, artifacts_path,
            'Ocean', 'OCEAN', minter_addr, OCEAN_cap_base, '', minter_addr
        ))
        addresses["Ocean"] = OCEAN_token.address
        print("****Deploy fake OCEAN: done****\n")

        print("****Mint fake OCEAN: begin****")
        OCEAN_token.mint(minter_addr, OCEAN_cap_base, from_wallet=deployer_wallet)
        print("****Mint fake OCEAN: done****\n")

        print("****Distribute fake OCEAN: begin****")
        amt_distribute = 1000
        amt_distribute_base = util.to_base_18(float(amt_distribute))
        for key_label in ['TEST_PRIVATE_KEY1', 'TEST_PRIVATE_KEY2']:
            key = os.environ.get(key_label)
            if not key:
                continue

            dst_address = privateKeyToAddress(key)
            OCEAN_token.transfer(dst_address, amt_distribute_base, from_wallet=deployer_wallet)

        print("****Distribute fake OCEAN: done****\n")

    network_addresses[network].update(addresses)

    with open(addresses_file, 'w') as f:
        json.dump(network_addresses, f, indent=2)

    return addresses


def invalidKey(private_key_str):  # super basic check
    return len(private_key_str) < 10


def invalidAddr(addr_str):  # super basic check
    return len(addr_str) < 10


def setenv(key, value):
    # os.putenv(key, value) #Do *not* use putenv(), it doesn't work
    os.environ[key] = value


if __name__ == '__main__':
    main()
