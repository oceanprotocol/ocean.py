#!/usr/bin/myenv

import os
import sys

import brownie
import pdb; pdb.set_trace()
from brownie import ERC20Template, Factory
import os

from ocean_lib import Ocean

ALLOWED_NETWORKS = ["development", "mainnet", "rinkeby"] #see 'brownie network lists'
    
if __name__ == '__main__':

    #set help message
    help = f"""
Deploy ERC20Template and Factory to a target network. 

Usage: deploy.py NETWORK
  NETWORK -- one of: {ALLOWED_NETWORKS}

Notes:
 -'development' means ganache 
 -It gets OPF_PRIVATE_KEY and OCEAN_COMMUNITY_ADDRESS from the enviroment, 
  e.g. from ~/.ocean_vars
 """

    # ****SET INPUT ARGS****
    #got the right number of args?  If not, output help
    num_args = len(sys.argv) - 1
    num_args_needed = [1]
    if num_args not in num_args_needed:
        print(help)
        if num_args > 0:
            print("Got %d argument(s), need %s.\n" % (num_args, num_args_needed))
        sys.exit(0)
    
    #input args: get them
    network = eval(sys.argv[1])

    print("Arguments: NETWORK=%s\n" % network)

    #input args: handle corner cases
    if network not in ALLOWED_NETWORKS:
        print(f"Invalid network. Allowed networks: {ALLOWED_NETWORKS}")
        sys.exit(0)

    # ****SET ENVT****
    #grab from env't
    opf_private_key = os.getenv('OPF_PRIVATE_KEY')
    community_addr = os.getenv('OCEAN_COMMUNITY_ADDRESS')

    #sanity check envt
    if opf_private_key is None:
        print("Need environmental var OPF_PRIVATE_KEY")
        sys.exit(0)
    if community_addr is None:
        print("Need environmental var OCEAN_COMMUNITY_ADDRESS")
        sys.exit(0)
    
    # ****DEPLOY****
    if not brownie.network.is_connected():
        brownie.network.connect(network)

    print("Deploy ERC20Template...")
    ERC20_template = ERC20Template.deploy(
        'Template', 'TEMPLATE', opf_account.address,
        community_addr, {'from': alice_account})
    print("... deployed.")
        
    print("Deploy Factory...")
    factory = Factory.deploy(
        ERC20_template.address, community_addr, {'from': opf_account})
    print("... deployed.")
        
