#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""All contracts inherit from `ContractBase` class."""
import logging
from typing import Any, Optional

from brownie import network
from enforce_typing import enforce_types
from eth_typing import ChecksumAddress
from web3 import Web3

from ocean_lib.example_config import NETWORK_IDS
from ocean_lib.web3_internal.contract_utils import (
    get_contract_definition,
    load_contract,
)
from ocean_lib.web3_internal.transactions import wait_for_transaction_status
from ocean_lib.web3_internal.utils import get_gas_price
from ocean_lib.web3_internal.wallet import Wallet

logger = logging.getLogger(__name__)


class ContractBase(object):

    """Base class for all contract objects."""

    CONTRACT_NAME = None

    @enforce_types
    def __init__(self, web3: Web3, address: Optional[str]) -> None:
        """Initialises Contract Base object."""
        self.name = self.contract_name
        assert (
            self.name
        ), "contract_name property needs to be implemented in subclasses."

        self.web3 = web3

        self.network = NETWORK_IDS[web3.eth.chain_id]
        self.connect_to_network()

        self.contract = load_contract(self.web3, self.name, address)
        assert not address or (
            self.contract.address.lower() == address.lower()
            and self.address.lower() == address.lower()
        )

    def connect_to_network(self):
        if network.show_active() != self.network:
            if network.is_connected():
                network.disconnect()

            network.connect(self.network)

    def __getattribute__(self, attr):
        method = object.__getattribute__(self, attr)
        if not method:
            raise Exception("Method %s not implemented" % attr)
        if callable(method) and not method.__name__ == "connect_to_network":
            self.connect_to_network()

        return method

    @enforce_types
    def __str__(self) -> str:
        """Returns contract `name @ address.`"""
        return f"{self.contract_name} @ {self.address}"

    @property
    @enforce_types
    def contract_name(self) -> str:
        """Returns the contract name"""
        return self.CONTRACT_NAME

    @property
    @enforce_types
    def address(self) -> str:
        """Return the ethereum address of the solidity contract deployed in current network."""
        return self.contract.address

    @staticmethod
    @enforce_types
    def to_checksum_address(address: str) -> ChecksumAddress:
        """
        Validate the address provided.

        :param address: Address, hex str
        :return: address, hex str
        """
        return Web3.toChecksumAddress(address.lower())

    @enforce_types
    def send_transaction(
        self,
        fn_name: str,
        fn_args: Any,
        from_wallet: Wallet,
        transact: Optional[dict] = None,
    ) -> str:
        """Calls a smart contract function.

        :param fn_name: str the smart contract function name
        :param fn_args: tuple arguments to pass to function above
        :param from_wallet:
        :param transact: dict arguments for the transaction such as from, gas, etc.
        :return: hex str transaction hash
        """
        _transact = {
            "from": ContractBase.to_checksum_address(from_wallet.address),
            "account_key": from_wallet.key,
            # "nonce": self.web3.eth.getTransactionCount(from_wallet.address)
            # 'nonce': Wallet._get_nonce(self.web3, from_wallet.address)
        }

        gas_tx = get_gas_price(web3_object=self.web3, tx=_transact)
        _transact.update(gas_tx)

        if transact:
            _transact.update(transact)

        receipt = getattr(self.contract, fn_name)(*fn_args, _transact)
        receipt.wait(from_wallet.block_confirmations)

        txid = receipt.txid

        return wait_for_transaction_status(from_wallet, txid)

    @classmethod
    @enforce_types
    def deploy(cls, web3: Web3, deployer_wallet: Wallet, *args) -> str:
        """
        Deploy the ERCTokenTemplate contract to the current network.

        :param web3:
        :param deployer_wallet: Wallet instance

        :return: smartcontract address of this contract
        """

        _json = get_contract_definition(cls.CONTRACT_NAME)

        _contract = web3.eth.contract(abi=_json["abi"], bytecode=_json["bytecode"])
        built_tx = _contract.constructor(*args).buildTransaction(
            {"from": ContractBase.to_checksum_address(deployer_wallet.address)}
        )

        if "chainId" not in built_tx:
            built_tx["chainId"] = web3.eth.chain_id

        if "gas" not in built_tx or "gasPrice" not in built_tx:
            gas_tx = get_gas_price(web3_object=web3, tx=built_tx)
            built_tx.update(gas_tx)

        raw_tx = deployer_wallet.sign_tx(built_tx)
        logging.debug(
            f"Sending raw tx to deploy contract {cls.CONTRACT_NAME}, signed tx hash: {raw_tx.hex()}"
        )
        tx_hash = web3.eth.send_raw_transaction(raw_tx)

        return cls.get_tx_receipt(web3, tx_hash, timeout=60).contractAddress
