#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

"""All contracts inherit from `ContractBase` class."""
import logging
import os
from typing import Any, Dict, List, Optional

import requests
from eth_typing import BlockIdentifier
from hexbytes import HexBytes
from ocean_lib.enforce_typing_shim import enforce_types_shim
from ocean_lib.web3_internal.constants import ENV_GAS_PRICE
from ocean_lib.web3_internal.contract_handler import ContractHandler
from ocean_lib.web3_internal.wallet import Wallet
from ocean_lib.web3_internal.web3_overrides.contract import CustomContractFunction
from ocean_lib.web3_internal.web3_provider import Web3Provider
from web3 import Web3
from web3.exceptions import MismatchedABI, ValidationError
from web3.utils.events import get_event_data
from web3.utils.filters import construct_event_filter_params
from web3.utils.threads import Timeout
from websockets import ConnectionClosed

logger = logging.getLogger(__name__)


@enforce_types_shim
class ContractBase(object):

    """Base class for all contract objects."""

    CONTRACT_NAME = None

    def __init__(self, address: Optional[str], abi_path=None):
        """Initialises Contract Base object.

        The contract name attribute and `abi_path` are required.
        """
        self.name = self.contract_name
        assert (
            self.name
        ), "contract_name property needs to be implemented in subclasses."
        if not abi_path:
            abi_path = ContractHandler.artifacts_path

        assert abi_path, f"abi_path is required, got {abi_path}"

        self.contract_concise = ContractHandler.get_concise_contract(self.name, address)
        self.contract = ContractHandler.get(self.name, address)

        assert not address or (
            self.contract.address == address and self.address == address
        )
        assert self.contract_concise is not None

    def __str__(self):
        """Returns contract `name @ address.`"""
        return f"{self.contract_name} @ {self.address}"

    @classmethod
    def configured_address(cls, network, address_file):
        """Returns the contract addresses"""
        addresses = ContractHandler.get_contracts_addresses(network, address_file)
        return addresses.get(cls.CONTRACT_NAME) if addresses else None

    @property
    def contract_name(self) -> str:
        """Returns the contract name"""
        return self.CONTRACT_NAME

    @property
    def address(self) -> str:
        """Return the ethereum address of the solidity contract deployed in current network."""
        return self.contract.address

    @property
    def events(self):
        """Expose the underlying contract's events."""
        return self.contract.events

    @property
    def function_names(self) -> List[str]:
        """Returns the list of functions in the contract"""
        return list(self.contract.functions)

    @staticmethod
    def to_checksum_address(address: str):
        """
        Validate the address provided.

        :param address: Address, hex str
        :return: address, hex str
        """
        return Web3.toChecksumAddress(address)

    @staticmethod
    def get_tx_receipt(tx_hash: str, timeout=20):
        """
        Get the receipt of a tx.

        :param tx_hash: hash of the transaction
        :param timeout: int in seconds to wait for transaction receipt
        :return: Tx receipt
        """
        try:
            Web3Provider.get_web3().eth.waitForTransactionReceipt(
                tx_hash, timeout=timeout
            )
        except ValueError as e:
            logger.error(f"Waiting for transaction receipt failed: {e}")
            return None
        except Timeout as e:
            logger.info(f"Waiting for transaction receipt may have timed out: {e}.")
            return None
        except ConnectionClosed as e:
            logger.info(
                f"ConnectionClosed error waiting for transaction receipt failed: {e}."
            )
            raise
        except Exception as e:
            logger.info(f"Unknown error waiting for transaction receipt: {e}.")
            raise

        return Web3Provider.get_web3().eth.getTransactionReceipt(tx_hash)

    def is_tx_successful(self, tx_hash: str) -> bool:
        """Check if the transaction is successful.

        :param tx_hash: hash of the transaction
        :return: bool
        """
        receipt = self.get_tx_receipt(tx_hash)
        return bool(receipt and receipt.status == 1)

    def get_event_signature(self, event_name):
        """
        Return signature of event definition to use in the call to eth_getLogs.

        The event signature is used as topic0 (first topic) in the eth_getLogs arguments
        The signature reflects the event name and argument types.

        :param event_name:
        :return:
        """
        try:
            e = getattr(self.events, event_name)
        except MismatchedABI:
            e = None

        if not e:
            raise ValueError(
                f"Event {event_name} not found in {self.CONTRACT_NAME} contract."
            )

        abi = e().abi
        types = [param["type"] for param in abi["inputs"]]
        sig_str = f'{event_name}({",".join(types)})'
        return Web3.sha3(text=sig_str).hex()

    def subscribe_to_event(
        self,
        event_name: str,
        timeout,
        event_filter,
        callback=None,
        timeout_callback=None,
        args=None,
        wait=False,
        from_block="latest",
        to_block="latest",
    ):
        """
        Create a listener for the event `event_name` on this contract.

        :param event_name: name of the event to subscribe, str
        :param timeout:
        :param event_filter:
        :param callback:
        :param timeout_callback:
        :param args:
        :param wait: if true block the listener until get the event, bool
        :param from_block: int or None
        :param to_block: int or None
        :return: event if blocking is True and an event is received, otherwise returns None
        """
        from ocean_lib.web3_internal.event_listener import EventListener

        return EventListener(
            self.CONTRACT_NAME,
            event_name,
            args,
            filters=event_filter,
            from_block=from_block,
            to_block=to_block,
        ).listen_once(
            callback, timeout_callback=timeout_callback, timeout=timeout, blocking=wait
        )

    def send_transaction(
        self, fn_name: str, fn_args, from_wallet: Wallet, transact: dict = None
    ) -> str:
        """Calls a smart contract function.

        Uses either `personal_sendTransaction` (if passphrase is available) or `ether_sendTransaction`.

        :param fn_name: str the smart contract function name
        :param fn_args: tuple arguments to pass to function above
        :param from_wallet:
        :param transact: dict arguments for the transaction such as from, gas, etc.
        :return: hex str transaction hash
        """
        contract_fn = getattr(self.contract.functions, fn_name)(*fn_args)
        contract_function = CustomContractFunction(contract_fn)
        _transact = {
            "from": from_wallet.address,
            "passphrase": from_wallet.password,
            "account_key": from_wallet.key,
            # 'gas': GAS_LIMIT_DEFAULT
        }

        gas_price = os.environ.get(ENV_GAS_PRICE, None)
        if gas_price:
            _transact["gasPrice"] = gas_price

        if transact:
            _transact.update(transact)

        return contract_function.transact(_transact).hex()

    def get_event_argument_names(self, event_name: str):
        """Finds the event arguments by `event_name`.

        :param event_name: str Name of the event to search in the `contract`.
        :return: `event.argument_names` if event is found or None
        """
        event = getattr(self.contract.events, event_name, None)
        if event:
            return event().argument_names

    @classmethod
    def deploy(cls, web3, deployer_wallet: Wallet, abi_path: str = "", *args):
        """
        Deploy the DataTokenTemplate and DTFactory contracts to the current network.

        :param web3:
        :param abi_path:
        :param deployer_wallet: Wallet instance

        :return: smartcontract address of this contract
        """
        if not abi_path:
            abi_path = ContractHandler.artifacts_path

        assert abi_path, f"abi_path is required, got {abi_path}"

        w3 = web3
        _json = ContractHandler.read_abi_from_file(cls.CONTRACT_NAME, abi_path)

        _contract = w3.eth.contract(abi=_json["abi"], bytecode=_json["bytecode"])
        built_tx = _contract.constructor(*args).buildTransaction(
            {"from": deployer_wallet.address}
        )

        if "gas" not in built_tx:
            built_tx["gas"] = web3.eth.estimateGas(built_tx)

        raw_tx = deployer_wallet.sign_tx(built_tx)
        logging.debug(
            f"Sending raw tx to deploy contract {cls.CONTRACT_NAME}, signed tx hash: {raw_tx.hex()}"
        )
        tx_hash = web3.eth.sendRawTransaction(raw_tx)

        return cls.get_tx_receipt(tx_hash, timeout=60).contractAddress

    def get_event_logs(
        self, event_name, from_block, to_block, filters, web3=None, chunk_size=1000
    ):
        """
        Fetches the list of event logs between the given block numbers.

        :param event_name: str
        :param from_block: int
        :param to_block: int
        :param filters:
        :param web3: Wallet instance
        :param chunk_size: int

        :return: List of event logs. List will have the structure as below.
        ```Python
            [AttributeDict({
                'args': AttributeDict({}),
                'event': 'LogNoArguments',
                'logIndex': 0,
                'transactionIndex': 0,
                'transactionHash': HexBytes('...'),
                'address': '0xF2E246BB76DF876Cef8b38ae84130F4F55De395b',
                'blockHash': HexBytes('...'),
                'blockNumber': 3
                }),
            AttributeDict(...),
            ...
            ]
        ```
        """
        event = getattr(self.events, event_name)
        if not web3:
            web3 = Web3Provider.get_web3()

        chunk = chunk_size
        _from = from_block
        _to = _from + chunk - 1

        all_logs = []
        error_count = 0
        _to = min(_to, to_block)
        while _from <= to_block:
            try:
                logs = self.getLogs(
                    event, web3, argument_filters=filters, fromBlock=_from, toBlock=_to
                )
                all_logs.extend(logs)
                _from = _to + 1
                _to = min(_from + chunk - 1, to_block)
                error_count = 0
                if (_from - from_block) % 1000 == 0:
                    print(
                        f"    So far processed {len(all_logs)} Transfer events from {_from-from_block} blocks."
                    )
            except requests.exceptions.ReadTimeout as err:
                print(f"ReadTimeout ({_from}, {_to}): {err}")
                error_count += 1

            if error_count > 1:
                break

        return all_logs

    def getLogs(
        self,
        event,
        web3,
        argument_filters: Optional[Dict[str, Any]] = None,
        fromBlock: Optional[BlockIdentifier] = None,
        toBlock: Optional[BlockIdentifier] = None,
        blockHash: Optional[HexBytes] = None,
    ):
        """Get events for this contract instance using eth_getLogs API.

        This is a stateless method, as opposed to createFilter.
        It can be safely called against nodes which do not provide
        eth_newFilter API, like Infura nodes.
        If there are many events,
        like ``Transfer`` events for a popular token,
        the Ethereum node might be overloaded and timeout
        on the underlying JSON-RPC call.
        Example - how to get all ERC-20 token transactions
        for the latest 10 blocks:

        ```python
            from = max(mycontract.web3.eth.blockNumber - 10, 1)
            to = mycontract.web3.eth.blockNumber
            events = mycontract.events.Transfer.getLogs(fromBlock=from, toBlock=to)
            for e in events:
                print(e["args"]["from"],
                    e["args"]["to"],
                    e["args"]["value"])
        ```
        The returned processed log values will look like:

        ```python
            (
                AttributeDict({
                 'args': AttributeDict({}),
                 'event': 'LogNoArguments',
                 'logIndex': 0,
                 'transactionIndex': 0,
                 'transactionHash': HexBytes('...'),
                 'address': '0xF2E246BB76DF876Cef8b38ae84130F4F55De395b',
                 'blockHash': HexBytes('...'),
                 'blockNumber': 3
                }),
                AttributeDict(...),
                ...
            )
        ```

        See also: :func:`web3.middleware.filter.local_filter_middleware`.
        :param argument_filters:
        :param fromBlock: block number or "latest", defaults to "latest"
        :param toBlock: block number or "latest". Defaults to "latest"
        :param blockHash: block hash. blockHash cannot be set at the
          same time as fromBlock or toBlock
        :yield: Tuple of :class:`AttributeDict` instances
        """
        if not self.address:
            raise TypeError(
                "This method can be only called on "
                "an instated contract with an address"
            )

        abi = event._get_event_abi()

        if argument_filters is None:
            argument_filters = dict()

        _filters = dict(**argument_filters)

        blkhash_set = blockHash is not None
        blknum_set = fromBlock is not None or toBlock is not None
        if blkhash_set and blknum_set:
            raise ValidationError(
                "blockHash cannot be set at the same" " time as fromBlock or toBlock"
            )

        # Construct JSON-RPC raw filter presentation based on human readable Python descriptions
        # Namely, convert event names to their keccak signatures
        _, event_filter_params = construct_event_filter_params(
            abi,
            contract_address=self.address,
            argument_filters=_filters,
            fromBlock=fromBlock,
            toBlock=toBlock,
        )

        if blockHash is not None:
            event_filter_params["blockHash"] = blockHash

        # Call JSON-RPC API
        logs = web3.eth.getLogs(event_filter_params)

        # Convert raw binary data to Python proxy objects as described by ABI
        return tuple(get_event_data(abi, entry) for entry in logs)
