#!/usr/bin/env python
import json
import os
import sys


from examples import ExampleConfig
from ocean_lib.config_provider import ConfigProvider
from ocean_lib.models.data_token import DataToken
from ocean_lib.models.dtfactory import DTFactory
from ocean_lib.models.sfactory import SFactory
from ocean_lib.models.spool import SPool
from ocean_lib.ocean import util
from ocean_lib.ocean.util import get_web3_provider
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
    #set help message
    help = f"""
Deploy DataTokenTemplate and more to a target network. 

Usage: deploy.py NETWORK ADDRESSES_FILE_PATH
  NETWORK -- one of: {SUPPORTED_NETWORKS_STR}
  ADDRESSES_FILE_PATH -- path to json file to update the deployed contracts addresses
 """

    # ****SET INPUT ARGS****
    #got the right number of args?  If not, output help
    num_args = len(sys.argv) - 1
    num_args_needed = 2
    if num_args != num_args_needed:
        print(help)
        if num_args > 0:
            print("Got %d argument(s), need %s.\n" % (num_args, num_args_needed))
        sys.exit(0)
    
    #grab args
    network = sys.argv[1]
    print("Arguments: NETWORK=%s\n" % network)

    #corner cases
    if network not in util.SUPPORTED_NETWORK_NAMES:
        print(f"Invalid network. Supported networks: {SUPPORTED_NETWORKS_STR}")
        sys.exit(0)

    return network, sys.argv[2]


def deploy(network, addresses_file):

    config = ExampleConfig.get_config()
    ConfigProvider.set_config(config)
    Web3Provider.init_web3(provider=get_web3_provider(config.network_url))
    ContractHandler.set_artifacts_path(config.artifacts_path)

    ocean = get_publisher_ocean_instance()
    web3 = ocean.web3
    artifacts_path = ContractHandler.artifacts_path

    addresses = dict()

    # ****SET ENVT****
    #grab vars
    factory_deployer_private_key = get_ganache_wallet().private_key

    #corner cases 
    if invalidKey(factory_deployer_private_key):
        print("Need valid FACTORY_DEPLOYER_PRIVATE_KEY")
        sys.exit(0)
    
    # ****SEE FUNDS****
    print("Keys:\n%s" % Wallet(web3=get_web3(), private_key=factory_deployer_private_key).keysStr())
    print("")
        
    # ****DEPLOY****
    deployer_wallet = Wallet(web3, private_key=factory_deployer_private_key)
    minter_addr = deployer_wallet.address
    cap = 2**255

    print("****Deploy DataTokenTemplate: begin****")
    dt_address = DataToken.deploy(
        web3, minter_addr, artifacts_path,
        'Template Contract', 'TEMPLATE', minter_addr, DTFactory.CAP, DTFactory.FIRST_BLOB
    )
    addresses[DataToken.CONTRACT_NAME] = dt_address
    print("****Deploy DataTokenTemplate: done****\n")

    print("****Deploy DTFactory: begin****")
    dtfactory = DTFactory(DTFactory.deploy(web3, minter_addr, artifacts_path, dt_address))
    addresses[DTFactory.CONTRACT_NAME] = dtfactory.address
    print("****Deploy DTFactory: done****\n")

    print("****Deploy SPool: begin****")
    spool_address = SPool.deploy(web3, minter_addr, artifacts_path)
    spool_template = SPool(spool_address)
    addresses[SPool.CONTRACT_NAME] = spool_address
    print("****Deploy SPool: done****\n")
    
    print("****Deploy 'SFactory': begin****")
    sfactory_address = SFactory.deploy(web3, minter_addr, artifacts_path, spool_template.address)
    sfactory = SFactory(sfactory_address)
    addresses[SFactory.CONTRACT_NAME] = sfactory_address
    print("****Deploy 'SFactory': done****\n")

    if network == 'ganache':
        print("****Deploy fake OCEAN: begin****")
        #For simplicity, hijack DataTokenTemplate.
        minter_addr = deployer_wallet.address
        OCEAN_cap = 1410 * 10**6 #1.41B
        OCEAN_cap_base = util.toBase18(float(OCEAN_cap))
        OCEAN_token = DataToken(DataToken.deploy(
            web3, deployer_wallet.address, artifacts_path,
            'Ocean', 'OCEAN', minter_addr, OCEAN_cap_base, ''
        ))
        addresses["Ocean"] = OCEAN_token.address
        print("****Deploy fake OCEAN: done****\n")

        print("****Mint fake OCEAN: begin****")
        OCEAN_token.mint(minter_addr, OCEAN_cap_base, from_wallet=deployer_wallet)
        print("****Mint fake OCEAN: done****\n")

        print("****Distribute fake OCEAN: begin****")
        amt_distribute = 1000
        amt_distribute_base = util.toBase18(float(amt_distribute))
        for key_label in ['TEST_PRIVATE_KEY1', 'TEST_PRIVATE_KEY2']:
            key = os.environ.get(key_label)
            if not key:
                continue

            dst_address = privateKeyToAddress(key)
            OCEAN_token.transfer(dst_address, amt_distribute_base, from_wallet=deployer_wallet)

        print("****Distribute fake OCEAN: done****\n")

    if os.path.exists(addresses_file):
        with open(addresses_file) as f:
            network_addresses = json.load(f)
    else:
        network_addresses = {network: {}}

    network_addresses[network].update(addresses)

    with open(addresses_file, 'w') as f:
        json.dump(network_addresses, f, indent=2)

    return addresses


def invalidKey(private_key_str): #super basic check
    return len(private_key_str) < 10


def invalidAddr(addr_str): #super basic check
    return len(addr_str) < 10


def setenv(key, value):
    #os.putenv(key, value) #Do *not* use putenv(), it doesn't work
    os.environ[key] = value


if __name__ == '__main__':
    main()
