#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""All contracts inherit from `ContractBase` class."""
import logging
from typing import List, Optional

from enforce_typing import enforce_types
from eth_typing import ChecksumAddress
from web3.exceptions import MismatchedABI
from web3.logs import DISCARD
from web3.main import Web3

from ocean_lib.web3_internal.contract_utils import load_contract

logger = logging.getLogger(__name__)


def function_wrapper(contract, web3, contract_functions, func_name):
    # direct function calls
    if hasattr(contract, func_name):
        return getattr(contract, func_name)

    # contract functions
    def wrap(*args, **kwargs):
        args2 = list(args)

        tx_dict = None

        # retrieve tx dict from either args or kwargs
        if args and isinstance(args[-1], dict):
            tx_dict = args[-1] if args[-1].get("from") else None
            args2 = list(args[:-1])

        if "tx_dict" in kwargs:
            tx_dict = kwargs["tx_dict"] if kwargs["tx_dict"].get("from") else None
            del kwargs["tx_dict"]

        # use addresses instead of wallets when doing the call
        for arg in args2:
            if hasattr(arg, "address"):
                args2 = list(args2)
                args2[args2.index(arg)] = arg.address

        func = getattr(contract_functions, func_name)
        result = func(*args2, **kwargs)

        # view/pure functions don't need "from" key in tx_dict
        if not tx_dict and result.abi["stateMutability"] not in ["view", "pure"]:
            raise Exception("Needs tx_dict with 'from' key.")

        # if it's a view/pure function, just call it
        if result.abi["stateMutability"] in ["view", "pure"]:
            return result.call()
        else:
            # if it's a transaction, build and send it
            wallet = tx_dict["from"]
            tx_dict2 = tx_dict.copy()
            tx_dict2["nonce"] = web3.eth.get_transaction_count(wallet.address)
            tx_dict2["from"] = tx_dict["from"].address

            result = result.build_transaction(tx_dict2)

            # sign with wallet private key and send transaction
            signed_tx = web3.eth.account.sign_transaction(result, wallet._private_key)
            receipt = web3.eth.send_raw_transaction(signed_tx.rawTransaction)

            return web3.eth.wait_for_transaction_receipt(receipt)

    return wrap


class ContractBase(object):

    """Base class for all contract objects."""

    CONTRACT_NAME = None

    @enforce_types
    def __init__(self, config_dict: dict, address: Optional[str]) -> None:
        """Initialises Contract Base object."""
        assert (
            self.contract_name
        ), "contract_name property needs to be implemented in subclasses."

        self.config_dict = config_dict

        self.contract = load_contract(
            config_dict["web3_instance"], self.contract_name, address
        )
        assert not address or (self.contract.address.lower() == address.lower())

        transferable = [
            x for x in dir(self.contract.functions) if not x.startswith("_")
        ]

        # transfer contract functions to ContractBase object
        for function in transferable:
            setattr(
                self,
                function,
                function_wrapper(
                    self.contract,
                    config_dict["web3_instance"],
                    self.contract.functions,
                    function,
                ),
            )

    @enforce_types
    def __str__(self) -> str:
        """Returns contract `name @ address.`"""
        return f"{self.contract_name} @ {self.address}"

    @property
    @enforce_types
    def contract_name(self) -> str:
        """Returns the contract name"""
        return self.CONTRACT_NAME

    @staticmethod
    @enforce_types
    def to_checksum_address(address: str) -> ChecksumAddress:
        """
        Validate the address provided.

        :param address: Address, hex str
        :return: address, hex str
        """
        return Web3.to_checksum_address(address.lower())

    @enforce_types
    def get_event_signature(self, event_name: str) -> str:
        try:
            e = getattr(self.contract.events, event_name)
        except MismatchedABI:
            raise ValueError(
                f"Event {event_name} not found in {self.CONTRACT_NAME} contract."
            )

        abi = e().abi
        types = [param["type"] for param in abi["inputs"]]
        sig_str = f'{event_name}({",".join(types)})'

        return Web3.keccak(text=sig_str).hex()

    @enforce_types
    def get_logs(
        self,
        event_name: str,
        from_block: Optional[int] = 0,
        to_block: Optional[int] = "latest",
    ) -> List:
        topic = self.get_event_signature(event_name)
        web3 = self.config_dict["web3_instance"]

        event_filter = web3.eth.filter(
            {
                "topics": [topic],
                "toBlock": to_block,
                "fromBlock": from_block,
            }
        )

        events = []

        for log in event_filter.get_all_entries():
            receipt = web3.eth.wait_for_transaction_receipt(log.transactionHash)
            fn = getattr(self.contract.events, event_name)
            processed_events = fn().process_receipt(receipt, errors=DISCARD)
            for processed_event in processed_events:
                events.append(processed_event)

        return events
