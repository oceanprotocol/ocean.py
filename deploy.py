#!/usr/bin/env python

import glob
import json
import os
import shutil

import brownie
from brownie.network import accounts
from ocean_lib.web3_internal.utils import connect_to_network

ADDRESS_FILE = "~/.ocean/ocean-contracts/artifacts/address.json"
DEAD_ADDRESS = "0x000000000000000000000000000000000000dead"
INDENT = 2


def do_main():
    print("Deploy contracts: begin")

    connect_to_network("development")

    deployer = accounts.add(os.getenv("FACTORY_DEPLOYER_PRIVATE_KEY"))

    addresses = _deploy_contracts(deployer)

    _update_address_file(addresses)

    _update_ABI_files()

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
    fee_collector = B.OPFCommunityFeeCollector.deploy(owner, owner, fr)

    router = B.FactoryRouter.deploy(owner, OCEAN, DEAD_ADDRESS, fee_collector, [], fr)

    fre = B.FixedRateExchange.deploy(router, fr)
    router.addFixedRateContract(fre, fr)

    dispenser = B.Dispenser.deploy(router, fr)
    router.addDispenserContract(dispenser, fr)

    dt_temp1 = B.ERC20Template.deploy(fr)
    dt_temp2 = B.ERC20TemplateEnterprise.deploy(fr)
    dt_temp3 = B.ERC20Template3.deploy(fr)
    dnft_temp1 = B.ERC721Template.deploy(fr)

    dnft_factory = B.ERC721Factory.deploy(dnft_temp1, dt_temp1, router, fr)
    dnft_factory.addTokenTemplate(dt_temp2, fr)
    dnft_factory.addTokenTemplate(dt_temp3, fr)
    router.addFactory(dnft_factory.address)

    # code for deploying ve contracts, if needed
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

    addresses_at_network = {
        "Ocean": OCEAN.address,
        "OPFCommunityFeeCollector": fee_collector.address,
        "Router": router.address,
        "FixedPrice": fre.address,
        "ERC20Template": {
            "1": dt_temp1.address,
            "2": dt_temp2.address,
            "3": dt_temp3.address,
        },
        "ERC721Template": {
            "1": dnft_temp1.address,
        },
        "Dispenser": dispenser.address,
        "ERC721Factory": dnft_factory.address,
    }

    addresses = {"development": addresses_at_network}

    print(f"Deployed these contracts:\n{json.dumps(addresses, indent=INDENT)}")

    return addresses


def _update_address_file(addresses: dict):
    address_file = os.path.expanduser(ADDRESS_FILE)
    with open(address_file, "w") as f:
        json.dump(addresses, f, indent=INDENT)

    print()
    print(f"Updated address file: {address_file}")


def _update_ABI_files():
    """ABI (.json) files are seen the function that loads contracts:
    ocean_lib.web3_internal.contract_utils.load_contract()

    To avoid DRY violations and potentially different behavior per copy,
    we copy files one at a time and preserve target directory structure
    """
    address_file = os.path.expanduser(ADDRESS_FILE)

    from_root_dir = os.path.join(os.getcwd(), "build/contracts")
    os.chdir(from_root_dir)
    from_files = glob.glob(f"**/*.json", recursive=True)
    from_files = [os.path.join(from_root_dir, from_file) for from_file in from_files]

    to_address_dir = os.path.dirname(address_file)
    to_root_dir = os.path.join(to_address_dir, "contracts")
    os.chdir(to_root_dir)
    to_files = glob.glob(f"**/*.json", recursive=True)
    to_files = [os.path.join(to_root_dir, to_file) for to_file in to_files]

    for from_file in from_files:
        assert os.path.exists(from_file)

        if "address.json" in from_file:
            continue
        if "dependencies" in from_file:
            continue

        contract_basename = os.path.basename(from_file)

        # for the from_file, find corresponding to_file
        to_file = None
        for cand_to_file in to_files:
            if contract_basename in cand_to_file:
                to_file = cand_to_file
                assert os.path.exists(to_file)
                break

        if not to_file:  # it's new, or an error
            if contract_basename == "ERC20Template3.json":
                to_file_path = os.path.join(to_root_dir, "templates/ERC20Template3.sol")
            else:
                raise ValueError(f"Couldn't find a to_file for from_file={from_file}")

            if not os.path.exists(to_file_path):
                os.mkdir(to_file_path)
            to_file = os.path.join(to_file_path, contract_basename)

        # overwrite to_file with a copy of from_file
        shutil.copy(from_file, to_file)

    print(f"Updated ABI (.json) files in directory: {to_root_dir}")
    print()


if __name__ == "__main__":
    do_main()
