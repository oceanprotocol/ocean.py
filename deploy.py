#! ./myenv/bin/python3

import brownie
import configparser
import os
import sys


ALLOWED_NETWORKS = ["development", "mainnet", "rinkeby"] #see 'brownie network lists'
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
Deploy ERC20Template and Factory to a target network. 

Usage: deploy.py NETWORK
  NETWORK -- one of: {ALLOWED_NETWORKS_STR}

Notes:
 -'development' means ganache 
 -It gets OPF_PRIVATE_KEY and OCEAN_COMMUNITY_ADDRESS from the enviroment, 
  e.g. from ~/.ocean_vars
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
    cp = configparser.ConfigParser()
    cp.read(os.path.expanduser('~/ocean.conf'))
    opf_private_key = cp[network]['OPF_PRIVATE_KEY']
    community_addr = cp[network]['OCEAN_COMMUNITY_ADDRESS']

    #corner cases 
    if invalidKey(opf_private_key):
        print("Need valid OPF_PRIVATE_KEY")
        sys.exit(0)
    if invalidAddr(community_addr):
        print("Need valid OCEAN_COMMUNITY_ADDRESS")
        sys.exit(0)

    # ****DEPLOY****
    if not brownie.network.is_connected():
        brownie.network.connect(network)
    opf_account = brownieAccount(opf_private_key)

    print("****Deploy ERC20Template: begin****")
    p = brownie.project.load('./', name='FooProject')
    ERC20_template = p.ERC20Template.deploy(
        'Template', 'TEMPLATE', opf_account.address,
        community_addr, {'from': opf_account})
    print(ERC20_template.tx)
    print("****Deploy ERC20Template: done****")
        
    print("****Deploy Factory: begin****")
    factory = p.Factory.deploy(
        ERC20_template.address, community_addr, {'from': opf_account})
    print(factory.tx)
    print("****Deploy Factory: done****")
