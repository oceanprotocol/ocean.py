#!/usr/bin/env python

import json
import os
    
import brownie
from brownie.network import accounts
from ocean_lib.web3_internal.utils import connect_to_network

ADDRESS_FILE = "~/.ocean/ocean-contracts/artifacts/address.json"
DEAD_ADDRESS = "0x000000000000000000000000000000000000dead"
INDENT = 2

def do_main():
    print("Deploy contracts: begin")
    
    address_file = os.path.expanduser(ADDRESS_FILE)
    print(f"Will update address_file: {address_file}")

    #connect
    connect_to_network("development")

    #get account
    deployer = accounts.add(os.getenv("FACTORY_DEPLOYER_PRIVATE_KEY"))

    #deploy contracts
    # -with this trick, I can change Ocean contracts all I want, in this repo
    addresses_at_network = _deploy_contracts(deployer) # [contract_name] : address

    #update address file
    addresses = {"development" : addresses_at_network}
    with open(address_file, "w") as f:
        json.dump(addresses, f, indent=INDENT)

    #done
    print(f"Deployed these contracts:\n{json.dumps(addresses, indent=INDENT)}")
    print()
    print(f"Updated address_file: {address_file}")
    print()
    print("Deploy contracts: done")

def _deploy_contracts(owner) -> dict:
    """
    @return
      addresses_at_ganache -- dict of [contract_name_str] : contract_address

    @notes
      Inspired by deployment in contracts repo: https://github.com/oceanprotocol/contracts/blob/main/scripts/deploy-contracts.js
    """
    fr = {"from": owner}
    
    B = brownie.project.load("./", name="MyProject")
    
    OCEAN = B.OceanToken.deploy(owner, fr)
    fee_coll = B.OPFCommunityFeeCollector.deploy(owner, owner, fr)
    router = B.FactoryRouter.deploy(owner, OCEAN, DEAD_ADDRESS, fee_coll, [], fr)
    fre = B.FixedRateExchange.deploy(router, fr)
    dt_temp1 = B.ERC20Template.deploy(fr)
    dt_temp2 = B.ERC20TemplateEnterprise.deploy(fr)
    dt_temp3 = B.ERC20Template3.deploy(fr)
    dnft_temp1 = B.ERC721Template.deploy(fr)
    dispenser = B.Dispenser.deploy(router, fr)
    dnft_factory = B.ERC721Factory.deploy(dnft_temp1, dt_temp1, router, fr)

    dnft_factory.addTokenTemplate(dt_temp2, fr)
    dnft_factory.addTokenTemplate(dt_temp3, fr)
    
    #code for deploying ve contracts, if needed
    # import math
    # import time
    # timestamp = math.floor(time.time() / 1000)
    # routerOwner = owner
    # veOCEAN = B.veOCEAN.deploy(OCEAN, "veOCEAN", "veOCEAN", "0.1.0", fr)
    # veAllocate = B.veAllocate.deploy(fr)
    # veDelegation = B.veDelegation.deploy("veDelegation", "", veOCEAN, fr)
    # veFeeDistributor = B.FeeDistributor.deploy(
    #     veOCEAN, timestamp, OCEAN, routerOwner, routerOwner, fr)
    # DelegationProxy = B.DelegationProxy.deploy(veDelegation, routerOwner, fr)
    # veFeeEstimate(veOCEAN, veFeeDistributor, fr)
    # SmartWalletChecker = B.SmartWalletChecker.deploy(fr)

    return {
        "Ocean" : OCEAN.address,
        "OPFCommunityFeeCollector" : fee_coll.address,
        "Router" : router.address,
        "FixedPrice" : fre.address,
        "ERC20Template" : {
            "1" : dt_temp1.address,
            "2" : dt_temp2.address,
            "3" : dt_temp3.address,
            },
        "ERC721Template" : {
            "1" : dnft_temp1.address,
            },
        "Dispenser" : dispenser.address,
        "ERC721Factory" : dnft_factory.address,
        }

if __name__ == "__main__":
    do_main()
