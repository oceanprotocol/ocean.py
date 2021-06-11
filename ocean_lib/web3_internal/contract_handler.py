#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import json
import logging
import os

from ocean_lib.web3_internal.web3_provider import Web3Provider
from web3 import Web3
from web3.contract import ConciseContract

logger = logging.getLogger(__name__)


class ContractHandler(object):

    """
    Manages loading contracts and also keeps a cache of loaded contracts.

    Example:
        `contract = ContractHandler.get('DTFactory')`

        `concise_contract = ContractHandler.get_concise_contract('DTFactory')`

    It must handle two cases:
    1. One deployment of contract, e.g. DTFactory
    2. deployments, e.g. DataTokenTemplate

    Attributes (_contracts) and methods (e.g. _load) behave accordingly.

    The _contracts dict maps:
        1. (contract_name)                   : (contract, concise_contract)
        2. (contract_name, contract_address) : (contract, concise_contract)
    """

    _contracts = dict()

    artifacts_path = None
    network_alias = {"ganache": "development"}

    @staticmethod
    def get_contracts_addresses(network, address_file):
        if not address_file or not os.path.exists(address_file):
            return None
        with open(address_file) as f:
            addresses = json.load(f)

        network_addresses = addresses.get(network, None)
        if network_addresses is None and network in ContractHandler.network_alias:
            network_addresses = addresses.get(
                ContractHandler.network_alias[network], None
            )

        return network_addresses

    @staticmethod
    def set_artifacts_path(artifacts_path):
        if artifacts_path and artifacts_path != ContractHandler.artifacts_path:
            ContractHandler.artifacts_path = artifacts_path
            ContractHandler._contracts.clear()

    @staticmethod
    def _get(name, address=None):
        """
        Return the contract & its concise version, for a given name.

        :param name: Contract name, str
        :param address: hex str -- address of contract
        :return: tuple of (contract, concise_contract)
        """
        key = (name, address) if address else (name)
        result = ContractHandler._contracts.get(key)
        if result is None:
            ContractHandler._load(name, address)
            result = ContractHandler._contracts.get(key)
            assert result is not None

        ContractHandler._verifyContractsConsistency(name)
        return result

    @staticmethod
    def get(name, address=None):
        """
        Return the Contract instance for a given name.

        :param name: Contract name, str
        :param address: hex str -- address of smart contract
        :return: Contract instance
        """
        return ContractHandler._get(name, address)[0]

    @staticmethod
    def get_concise_contract(name, address=None):
        """
        Return the Concise Contract instance for a given name.

        :param name: str -- Contract name
        :param address: hex str -- address of smart contract
        :return: Concise Contract instance
        """
        return ContractHandler._get(name, address)[1]

    @staticmethod
    def _set(name, contract):
        assert contract.address is not None

        tup = (contract, ConciseContract(contract))
        ContractHandler._contracts[(name, contract.address)] = tup
        ContractHandler._contracts[name] = tup

        ContractHandler._verifyContractsConsistency(name)

    @staticmethod
    def set(name, contract):
        """
        Set a Contract instance for a contract name.

        :param name: Contract name, str
        :param contract: Contract instance
        """
        ContractHandler._set(name, contract)

    @staticmethod
    def has(name, address=None):
        """
        Check if a contract is the ContractHandler contracts.

        :param name: Contract name, str
        :param address: hex str -- address of smart contract
        :return: True if the contract is there, bool
        """
        if address:
            return (name, address) in ContractHandler._contracts
        return name in ContractHandler._contracts

    @staticmethod
    def _load(contract_name, address=None):
        """Retrieve the contract instance for `contract_name`.

        That instance represents the smart contract in the ethereum network.

        Handles two cases:
        1. One deployment of contract, eg DTFactory. 'address' can be None, or specified
        2. 1 deployments, eg DataTokenTemplate. 'address' must be specified.

        :param contract_name: str name of the solidity smart contract.
        :param address: hex str -- address of smart contract
        """
        assert (
            ContractHandler.artifacts_path is not None
        ), "artifacts_path should be already set."
        contract_definition = ContractHandler.read_abi_from_file(
            contract_name, ContractHandler.artifacts_path
        )

        if not address and "address" in contract_definition:
            address = contract_definition.get("address")
            assert address, "Cannot find contract address in the abi file."
            address = Web3.toChecksumAddress(address)
        assert address is not None, "address shouldn't be None at this point"

        abi = contract_definition["abi"]
        bytecode = contract_definition["bytecode"]
        contract = Web3Provider.get_web3().eth.contract(
            address=address, abi=abi, bytecode=bytecode
        )
        if contract.address is None:  # if web3 drops address, fix it
            contract.address = address
        assert contract.address is not None

        ContractHandler._set(contract_name, contract)

        ContractHandler._verifyContractsConsistency(contract_name)

    @staticmethod
    def read_abi_from_file(contract_name, abi_path):
        path = None
        contract_name = contract_name + ".json"
        names = os.listdir(abi_path)
        # :HACK: temporary workaround to handle an extra folder that contain the artifact files.
        if len(names) == 1 and names[0] == "*":
            abi_path = os.path.join(abi_path, "*")

        for name in os.listdir(abi_path):
            if name.lower() == contract_name.lower():
                path = os.path.join(abi_path, contract_name)
                break

        if path:
            with open(path) as f:
                return json.loads(f.read())

        return None

    @staticmethod
    def _verifyContractsConsistency(name):
        """
        Raise an error if ContractHandler._contracts is inconsistent
        for the given contract name.

        :param name : str -- name of smart contract
        :return: None
        """
        (contract1, concise_contract1) = ContractHandler._contracts[name]
        assert contract1 is not None
        assert contract1.address is not None
        assert concise_contract1 is not None
        assert concise_contract1.address is not None

        (contract2, concise_contract2) = ContractHandler._contracts[
            (name, contract1.address)
        ]
        assert id(contract1) == id(contract2)
        assert id(concise_contract1) == id(concise_contract2)
