import json
import os
import time

from ocean_lib.ocean.util import to_base_18, from_base_18
from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.event_filter import EventFilter
from ocean_lib.web3_internal.wallet import Wallet
from ocean_lib.web3_internal.web3_provider import Web3Provider
from ocean_utils.http_requests.requests_session import get_requests_session

from ocean_lib.data_provider.data_service_provider import DataServiceProvider


class DataToken(ContractBase):
    CONTRACT_NAME = 'DataTokenTemplate'
    DEFAULT_CAP = 1000000000
    DEFAULT_CAP_BASE = to_base_18(DEFAULT_CAP)

    def get_transfer_event(self, block_number, sender, receiver):
        event = getattr(self.events, 'Transfer')
        filter_params = {'from': sender, 'to': receiver}
        event_filter = EventFilter(
            'Transfer',
            event,
            filter_params,
            from_block=block_number-1,
            to_block=block_number+10
        )

        logs = event_filter.get_all_entries(max_tries=10)
        if not logs:
            return None

        if len(logs) > 1:
            raise AssertionError(f'Expected a single transfer event at '
                                 f'block {block_number}, but found {len(logs)} events.')

        return logs[0]

    def verify_transfer_tx(self, tx_id, sender, receiver):
        w3 = Web3Provider.get_web3()
        tx = w3.eth.getTransaction(tx_id)
        if not tx:
            raise AssertionError('Transaction is not found, or is not yet verified.')

        if tx['from'] != sender or tx['to'] != self.address:
            raise AssertionError(
                f'Sender and receiver in the transaction {tx_id} '
                f'do not match the expected consumer and contract addresses.'
            )

        _iter = 0
        while tx['blockNumber'] is None:
            time.sleep(0.1)
            tx = w3.eth.getTransaction(tx_id)
            _iter = _iter + 1
            if _iter > 100:
                break

        tx_receipt = self.get_tx_receipt(tx_id)
        if tx_receipt.status == 0:
            raise AssertionError(f'Transfer transaction failed.')

        logs = getattr(self.events, 'Transfer')().processReceipt(tx_receipt)
        transfer_event = logs[0] if logs else None
        # transfer_event = self.get_transfer_event(tx['blockNumber'], sender, receiver)
        if not transfer_event:
            raise AssertionError(f'Cannot find the event for the transfer transaction with tx id {tx_id}.')
        assert len(logs) == 1, \
            f'Multiple Transfer events in the same transaction !!! {logs}'

        if transfer_event.args['from'] != sender or transfer_event.args['to'] != receiver:
            raise AssertionError(f'The transfer event from/to do not match the expected values.')

        return tx, transfer_event

    def download(self, wallet: Wallet, tx_id: str, destination_folder: str):
        url = self.blob()
        download_url = (
            f'{url}?'
            f'consumerAddress={wallet.address}'
            f'&dataToken={self.address}'
            f'&transferTxId={tx_id}'
        )
        response = get_requests_session().get(download_url, stream=True)
        file_name = f'file-{self.address}'
        DataServiceProvider.write_file(response, destination_folder, file_name)
        return os.path.join(destination_folder, file_name)

    def token_balance(self, account: str):
        return from_base_18(self.balanceOf(account))

    def get_metadata_url(self):
        # grab the metadatastore URL from the DataToken contract (@token_address)
        url_object = json.loads(self.blob())
        assert url_object['t'] == 1, f'This datatoken does not appear to have a metadata store url.'
        return url_object['url']

    def get_simple_url(self):
        url_object = json.loads(self.blob())
        assert url_object['t'] == 0, f'This datatoken does not appear to have a direct consume url.'
        return url_object['url']

    # ============================================================
    # Token transactions using amount of tokens as a float instead of int
    # amount of tokens will be converted to the base value before sending
    # the transaction
    def approve_tokens(self, spender: str, value: float, from_wallet: Wallet):
        return self.approve(spender, to_base_18(value), from_wallet)

    def mint_tokens(self, to_account: str, value: float, from_wallet: Wallet):
        return self.mint(to_account, to_base_18(value), from_wallet)

    def transfer_tokens(self, to: str, value: float, from_wallet: Wallet):
        return self.transfer(to, to_base_18(value), from_wallet)

    # ============================================================
    # reflect DataToken Solidity methods
    def blob(self) -> str:
        return self.contract_concise.blob()

    def symbol(self) -> str:
        return self.contract_concise.symbol()

    def decimals(self) -> str:
        return self.contract_concise.decimals()

    def allowance(self, owner_address: str, spender_address: str) -> str:
        return self.contract_concise.allowance(owner_address, spender_address)

    def balanceOf(self, account: str) -> int:
        return self.contract_concise.balanceOf(account)

    def mint(self, to_account: str, value_base: int, from_wallet: Wallet) -> str:
        return self.send_transaction('mint', (to_account, value_base), from_wallet)

    def approve(self, spender: str, value_base: int, from_wallet: Wallet) -> str:
        return self.send_transaction('approve', (spender, value_base), from_wallet)

    def transfer(self, to: str, value_base: int, from_wallet: Wallet) -> str:
        return self.send_transaction('transfer', (to, value_base), from_wallet)

    def setMinter(self, minter, from_wallet) -> str:
        return self.send_transaction('setMinter', (minter, ), from_wallet)
