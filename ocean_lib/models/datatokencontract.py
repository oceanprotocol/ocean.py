import enforce
import os
import time

from web3 import Web3

from ocean_lib.web3_internal import ContractBase, Web3Helper
from ocean_lib.web3_internal.event_filter import EventFilter
from ocean_lib.web3_internal.web3_provider import Web3Provider
from ocean_utils.http_requests.requests_session import get_requests_session

from ocean_lib.data_provider.data_service_provider import DataServiceProvider


class DataTokenContract(ContractBase):
    CONTRACT_NAME = 'DataTokenTemplate'

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

        if transfer_event.args['from'] != sender or transfer_event.args['to'] != receiver:
            raise AssertionError(f'The transfer event from/to do not match the expected values.')

        return tx_id

    def _send_token_tx(self, method, to, value, account):
        tx_hash = self.send_transaction(
            method,
            (to,
             value),
            transact={'from': account.address,
                      'passphrase': account.password,
                      'account_key': account.key},
        )
        return tx_hash

    def mint(self, to, value, account):
        return self._send_token_tx('mint', to, Web3Helper.to_wei(value), account)

    def approve(self, spender, value, account):
        return self._send_token_tx('approve', spender, Web3Helper.to_wei(value), account)

    def transfer_wei(self, to, value, account):
        return self._send_token_tx('transfer', to, value, account)

    def transfer(self, to, value, account):
        return self.transfer_token(to, value, account)

    def transfer_token(self, to, value, account):
        return self.transfer_wei(to, Web3Helper.to_wei(value), account)

    def set_minter(self, new_minter, current_minter_account):
        tx_hash = self.send_transaction(
            'setMinter',
            (new_minter, ),
            transact={'from': current_minter_account.address,
                      'passphrase': current_minter_account.password,
                      'account_key': current_minter_account.key},
        )
        return tx_hash

    def token_balance(self, address):
        return self.balance(address)

    def balance(self, address):
        return Web3Helper.from_wei(self.wei_balance(address))

    def wei_balance(self, address):
        return self.contract_concise.balanceOf(address)

    def get_metadata_url(self):
        # grab the metadatastore URL from the DataToken contract (@token_address)
        return self.contract_concise.blob()

    def download(self, account: Account, tx_id: str, destination_folder: str):
        url = self.get_metadata_url()
        download_url = (
            f'{url}?'
            f'consumerAddress={account.address}'
            f'&dataToken={self.address}'
            f'&transferTxId={tx_id}'
        )
        response = get_requests_session().get(download_url, stream=True)
        file_name = f'file-{self.address}'
        DataServiceProvider.write_file(response, destination_folder, file_name)
        return os.path.join(destination_folder, file_name)

    #============================================================
    #reflect DataToken Solidity methods (new ones beyond BToken)
    def blob(self) -> str:
        return self.contract.functions.blob().call()

    def mint(self, account: str, value_base: int, from_wallet: Wallet):
        f = self.contract.functions.mint(account, value_base)
        return util.buildAndSendTx(f, from_wallet)

    def setMinter(self, minter: str, from_wallet: Wallet):
        f = self.contract.functions.setMinter(minter)
        return util.buildAndSendTx(f, from_wallet)


