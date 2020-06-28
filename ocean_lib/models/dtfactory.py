import enforce
import logging
import typing

from ocean_lib.models.datatoken import DataToken
from ocean_lib.web3_internal import ContractBase
from ocean_lib.web3_internal.account import Account

class DTFactoryContract(ContractBase):
    
    @property
    def contract_name(self):
        return 'DTFactory'

    def create_data_token(self, account: Account, metadata_url: str) -> typing.Union[DataToken, None]:
        tx_hash = self.send_transaction(
            'createToken',
            (metadata_url,),
            transact={'from': account.address,
                      'passphrase': account.password,
                      'account_key': account.key},
        )
        tx_receipt = self.get_tx_receipt(tx_hash)
        if not tx_receipt:
            logging.warning(f'Cannot get the transaction receipt for tx {tx_hash}.')
            return None

        logs = getattr(self.events, 'TokenRegistered')().processReceipt(tx_receipt)
        if not logs:
            logging.warning(f'No logs where found for tx {tx_hash}.')
            return None

        return DataToken(logs[0].args.tokenAddress)

    @enforce.runtime_validation
    def get_token_registered_event(self, block_number:int, metadata_url:str, sender):
        event = getattr(self.events, 'TokenRegistered')
        filter_params = {}
        event_filter = event().createFilter(
            fromBlock=block_number,
            toBlock=block_number,
            argument_filters=filter_params
        )
        logs = event_filter.get_all_entries()
        for log in logs:
            if log.args.blob == metadata_url and sender == log.args.RegisteredBy:
                return log

        return None

    @enforce.runtime_validation
    def get_token_minter(self, token_address: str) -> typing.Union[str, None]:
        """Returns the address of the token minter"""
        event = getattr(self.events, 'TokenRegistered')
        filter_params = {'tokenAddress': token_address}
        event_filter = event().createFilter(
            fromBlock=0,
            toBlock='latest',
            argument_filters=filter_params
        )
        logs = event_filter.get_all_entries()
        for log in logs:
            assert log.args.tokenAddress == token_address
            return log.args.RegisteredBy

        return None
