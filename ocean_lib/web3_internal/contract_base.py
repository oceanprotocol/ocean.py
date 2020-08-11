"""All contracts inherit from this base class"""
#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0
import logging
import os
import typing

from web3 import Web3
from web3.utils.threads import Timeout

from ocean_lib.web3_internal.constants import GAS_LIMIT_DEFAULT
from ocean_lib.web3_internal.contract_handler import ContractHandler
from ocean_lib.web3_internal.wallet import Wallet
from ocean_lib.web3_internal.web3_overrides.contract import CustomContractFunction
from ocean_lib.web3_internal.web3_provider import Web3Provider

logger = logging.getLogger(__name__)


class ContractBase(object):
    """Base class for all contract objects."""
    CONTRACT_NAME = None

    def __init__(self, address: [str, None], abi_path=None):
        self.name = self.contract_name
        assert self.name, 'contract_name property needs to be implemented in subclasses.'
        if not abi_path:
            abi_path = ContractHandler.artifacts_path

        assert abi_path, f'abi_path is required, got {abi_path}'

        self.contract_concise = ContractHandler.get_concise_contract(self.name, address)
        self.contract = ContractHandler.get(self.name, address)

        assert not address or (self.contract.address == address and self.address == address)
        assert self.contract_concise is not None

    def __str__(self):
        return f'{self.contract_name} @ {self.address}'

    @classmethod
    def configured_address(cls, network, address_file):
        addresses = ContractHandler.get_contracts_addresses(
            network, address_file)
        return addresses.get(cls.CONTRACT_NAME) if addresses else None

    @property
    def contract_name(self) -> str:
        return self.CONTRACT_NAME

    @property
    def address(self) -> str:
        """Return the ethereum address of the solidity contract deployed
        in current network.
        """
        return self.contract.address

    @property
    def events(self):
        """Expose the underlying contract's events.

        :return:
        """
        return self.contract.events

    @property
    def function_names(self) -> typing.List[str]:
        return list(self.contract.function_names)

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
            Web3Provider.get_web3().eth.waitForTransactionReceipt(tx_hash, timeout=timeout)
        except ValueError as e:
            logger.error(f'Waiting for transaction receipt failed: {e}')
            return None
        except (Timeout, Exception) as e:
            logger.info(f'Waiting for transaction receipt may have timed out: {e}.')
            return None

        return Web3Provider.get_web3().eth.getTransactionReceipt(tx_hash)

    def is_tx_successful(self, tx_hash: str) -> bool:
        receipt = self.get_tx_receipt(tx_hash)
        return bool(receipt and receipt.status == 1)

    def subscribe_to_event(self, event_name: str, timeout, event_filter, callback=None,
                           timeout_callback=None, args=None, wait=False,
                           from_block='latest', to_block='latest'):
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
            to_block=to_block
        ).listen_once(
            callback,
            timeout_callback=timeout_callback,
            timeout=timeout,
            blocking=wait
        )

    def send_transaction(self, fn_name: str, fn_args, from_wallet: Wallet, transact: dict =None) -> str:
        """Calls a smart contract function using either `personal_sendTransaction` (if
        passphrase is available) or `ether_sendTransaction`.

        :param fn_name: str the smart contract function name
        :param fn_args: tuple arguments to pass to function above
        :param from_wallet:
        :param transact: dict arguments for the transaction such as from, gas, etc.
        :return:
        """
        contract_fn = getattr(self.contract.functions, fn_name)(*fn_args)
        contract_function = CustomContractFunction(
            contract_fn
        )
        _transact = {
            'from': from_wallet.address,
            'passphrase': from_wallet.password,
            'account_key': from_wallet.key,
            # 'gas': GAS_LIMIT_DEFAULT
        }

        gas_price = os.environ.get('GAS_PRICE', None)
        if gas_price:
            _transact['gasPrice'] = gas_price

        if transact:
            _transact.update(transact)

        return contract_function.transact(_transact).hex()

    def get_event_argument_names(self, event_name: str):
        event = getattr(self.contract.events, event_name, None)
        if event:
            return event().argument_names

    @classmethod
    def deploy(cls, web3, deployer_wallet: Wallet, abi_path: str= '', *args):
        """
        Deploy the DataTokenTemplate and DTFactory contracts to the current network.

        :param web3:
        :param abi_path:
        :param deployer_wallet: Wallet instance

        :return: smartcontract address of this contract
        """
        if not abi_path:
            abi_path = ContractHandler.artifacts_path

        assert abi_path, f'abi_path is required, got {abi_path}'

        w3 = web3
        _json = ContractHandler.read_abi_from_file(
            cls.CONTRACT_NAME,
            abi_path
        )

        _contract = w3.eth.contract(abi=_json['abi'], bytecode=_json['bytecode'])
        built_tx = _contract.constructor(*args)\
            .buildTransaction({'from': deployer_wallet.address})

        if 'gas' not in built_tx:
            built_tx['gas'] = web3.eth.estimateGas(built_tx)

        raw_tx = deployer_wallet.sign_tx(built_tx)
        logging.debug(f'Sending raw tx to deploy contract {cls.CONTRACT_NAME}, signed tx hash: {raw_tx.hex()}')
        tx_hash = web3.eth.sendRawTransaction(raw_tx)

        return cls.get_tx_receipt(tx_hash, timeout=60).contractAddress
