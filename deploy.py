#! ./myenv/bin/python3

import brownie
import os
import sys

from ocean_lib import constants
from ocean_lib.Ocean import confFileValue

ALLOWED_NETWORKS = ['ganache', 'rinkeby', 'mainnet']
ALLOWED_NETWORKS_STR = str(ALLOWED_NETWORKS)[1:-1]

def brownieAccount(private_key):
    assert brownie.network.is_connected()
    return brownie.network.accounts.add(priv_key=private_key)

def invalidKey(private_key_str): #super basic check
    return len(private_key_str) < 10

def invalidAddr(addr_str): #super basic check
    return len(addr_str) < 10
    
if __name__ == '__main__':

    #set help message
    help = f"""
Deploy DataTokenTemplate and Factory to a target network. 

Usage: deploy.py NETWORK
  NETWORK -- one of: {ALLOWED_NETWORKS_STR}

Notes:
 -It gets FACTORY_DEPLOYER_PRIVATE_KEY and FEE_MANAGER_ADDRESS from {constants.CONF_FILE_PATH}
 """

    # ****SET INPUT ARGS****
    #got the right number of args?  If not, output help
    num_args = len(sys.argv) - 1
    num_args_needed = 1
    if num_args != num_args_needed:
        print(help)
        if num_args > 0:
            print("Got %d argument(s), need %s.\n" % (num_args, num_args_needed))
        sys.exit(0)
    
    #grab args
    network = sys.argv[1]
    print("Arguments: NETWORK=%s\n" % network)

    #corner cases
    if network not in ALLOWED_NETWORKS:
        print(f"Invalid network. Allowed networks: {ALLOWED_NETWORKS_STR}")
        sys.exit(0)

    # ****SET ENVT****
    #grab vars
    factory_deployer_private_key = confFileValue(network, 'FACTORY_DEPLOYER_PRIVATE_KEY')
    fee_manager_addr = confFileValue(network, 'FEE_MANAGER_ADDRESS')

    #corner cases 
    if invalidKey(factory_deployer_private_key):
        print("Need valid FACTORY_DEPLOYER_PRIVATE_KEY")
        sys.exit(0)
    if invalidAddr(fee_manager_addr):
        print("Need valid OCEAN_FEE_MANAGER_ADDRESS")
        sys.exit(0)

    
    # ****CONNECT TO EXISTING RUNNING CHAIN****
    assert not brownie.network.is_connected()
    assert network != 'development', "can't have network='development' because brownie reverts that"
    brownie.network.connect(network)
        
    # ****DEPLOY****
    if network == 'ganache': #past deployments cause errors, so delete them
        os.system('rm -rf ./build/deployments/1234')
        
    factory_deployer_account = brownieAccount(factory_deployer_private_key)

    print("****Deploy DataTokenTemplate: begin****")
    p = brownie.project.load('./', name='DataTokenTemplate')
    name, symbol = 'Template', 'TEMPLATE'
    minter_addr = factory_deployer_account.address
    cap = constants.DEFAULT_MINTING_CAP
    blob = 'blob_string'
    # args to deploy = args for DataTokenTemplate constructor & {'from':addr}
    ERC20_template = p.DataTokenTemplate.deploy(
        name, symbol, minter_addr, cap, blob, fee_manager_addr, 
        {'from': factory_deployer_account})
    print(ERC20_template.tx)
    print("****Deploy DataTokenTemplate: done****")
        
    print("****Deploy Factory: begin****")
    factory = p.Factory.deploy(
        ERC20_template.address, fee_manager_addr, {'from': factory_deployer_account})
    print(factory.tx)
    print("****Deploy Factory: done****")
