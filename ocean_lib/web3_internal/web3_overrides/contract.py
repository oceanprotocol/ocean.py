#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging

from ocean_lib.web3_internal.utils import get_network_timeout
from ocean_lib.web3_internal.wallet import Wallet
from web3._utils.threads import Timeout
from web3.contract import prepare_transaction


class CustomContractFunction:
    def __init__(self, contract_function):
        """Initializes CustomContractFunction."""
        self._contract_function = contract_function

    def transact(self, transaction):
        """Customize calling smart contract transaction functions.
        This function is copied from web3 ContractFunction with a few additions:

        1. Use personal_sendTransaction (local node) if `passphrase` is in the `transaction` dict
        2. Else, use eth_sendTransaction (hosted node)
        3. Estimate gas limit if `gas` is not in the `transaction` dict
        4. Retry failed transactions until the network-dependent timeout is reached

        :param transaction: dict which has the required transaction arguments per
            `personal_sendTransaction` requirements.
        :return: hex str transaction hash
        """
        transact_transaction = dict(**transaction)

        if "data" in transact_transaction:
            raise ValueError("Cannot set data in transact transaction")

        cf = self._contract_function
        if cf.address is not None:
            transact_transaction.setdefault("to", cf.address)

        if "to" not in transact_transaction:
            if isinstance(self, type):
                raise ValueError(
                    "When using `Contract.transact` from a contract factory you "
                    "must provide a `to` address with the transaction"
                )
            else:
                raise ValueError(
                    "Please ensure that this contract instance has an address."
                )
        if "chainId" not in transact_transaction:
            transact_transaction["chainId"] = cf.web3.eth.chain_id

        if "gas" not in transact_transaction:
            tx = transaction.copy()
            if "passphrase" in tx:
                tx.pop("passphrase")
            if "account_key" in tx:
                tx.pop("account_key")
            gas = cf.estimateGas(tx)
            transact_transaction["gas"] = gas

        return transact_with_contract_function(
            cf.address,
            cf.web3,
            cf.function_identifier,
            transact_transaction,
            cf.contract_abi,
            cf.abi,
            *cf.args,
            **cf.kwargs,
        )


def transact_with_contract_function(
    address,
    web3,
    function_name=None,
    transaction=None,
    contract_abi=None,
    fn_abi=None,
    *args,
    **kwargs,
):
    """
    Helper function for interacting with a contract function by sending a
    transaction. This is copied from web3 `transact_with_contract_function`
    so we can use `personal_sendTransaction` when possible.
    """
    transact_transaction = prepare_transaction(
        address,
        web3,
        fn_identifier=function_name,
        contract_abi=contract_abi,
        transaction=transaction,
        fn_abi=fn_abi,
        fn_args=args,
        fn_kwargs=kwargs,
    )

    passphrase = None
    account_key = None
    if transaction and "passphrase" in transaction:
        passphrase = transaction["passphrase"]
        transact_transaction.pop("passphrase")
    if transaction and "account_key" in transaction:
        account_key = transaction["account_key"]
        transact_transaction.pop("account_key")

    with Timeout(get_network_timeout()) as _timeout:
        while True:
            if account_key:
                raw_tx = Wallet(web3, private_key=account_key).sign_tx(
                    transact_transaction
                )
                logging.debug(
                    f"sending raw tx: function: {function_name}, tx hash: {raw_tx.hex()}"
                )
                txn_hash = web3.eth.send_raw_transaction(raw_tx)
            elif passphrase:
                txn_hash = web3.personal.sendTransaction(
                    transact_transaction, passphrase
                )
            else:
                txn_hash = web3.eth.send_transaction(transact_transaction)

            txn_receipt = web3.eth.wait_for_transaction_receipt(
                txn_hash, get_network_timeout()
            )
            if bool(txn_receipt.status):
                break
            _timeout.sleep(0.1)

    return txn_hash
