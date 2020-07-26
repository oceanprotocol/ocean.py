import logging
import traceback
import typing

from ocean_lib.web3_internal.constants import MIN_GAS_PRICE
from ocean_lib.web3_internal.utils import privateKeyToAddress
from ocean_lib.web3_internal.utils import privateKeyToPublicKey

logger = logging.getLogger(__name__)


class Wallet:
    """
    The wallet is responsible for signing transactions and messages by using an account's
    private key.

    The private key is always read from the encrypted keyfile and is never saved in memory beyond
    the life span of the signing function.

    The use of this wallet allows Ocean tools to send rawTransactions which keeps the user
    key and password safe and they are never sent outside. Another advantage of this is that
    we can interact directly with remote network nodes without having to run a local parity
    node since we only send the raw transaction hash so the user info is safe.

    """
    _last_tx_count = dict()

    def __init__(self, web3,
                 private_key: typing.Union[str, None] = None,
                 encrypted_key: dict = None,
                 password: typing.Union[str, None] = None,
                 address: typing.Union[str, None] = None):
        self._web3 = web3
        self._last_tx_count.clear()

        self._password = password
        self._address = address
        self._key = private_key
        if encrypted_key and not private_key:
            assert self._password
            self._key = self._web3.eth.account.decrypt(encrypted_key, self._password)

        if self._key:
            address = privateKeyToAddress(self._key)
            assert self._address is None or self._address == address
            self._address = address
            self._password = None

    @property
    def web3(self):
        return self._web3
    
    @property
    def address(self):
        return self._address

    @property
    def password(self):
        return self._password

    @property
    def private_key(self):
        return self._key

    @property
    def key(self):
        return self._key

    @staticmethod
    def reset_tx_count():
        Wallet._last_tx_count = dict()

    def __get_key(self):
        return self._key

    def validate(self):
        account = self._web3.eth.account.privateKeyToAccount(self._key)
        return account.address == self._address

    @staticmethod
    def _get_nonce(web3, address):
        # We cannot rely on `web3.eth.getTransactionCount` because when sending multiple
        # transactions in a row without wait in between the network may not get the chance to
        # update the transaction count for the account address in time.
        # So we have to manage this internally per account address.
        if address not in Wallet._last_tx_count:
            Wallet._last_tx_count[address] = web3.eth.getTransactionCount(address)
        else:
            Wallet._last_tx_count[address] += 1

        return Wallet._last_tx_count[address]

    def sign_tx(self, tx):
        account = self._web3.eth.account.privateKeyToAccount(self.private_key)
        nonce = Wallet._get_nonce(self._web3, account.address)
        logger.debug(f'`Wallet` signing tx: sender address: {account.address} nonce: {nonce}, '
                     f'gasprice: {self._web3.eth.gasPrice}')
        gas_price = int(self._web3.eth.gasPrice / 100)
        gas_price = max(gas_price, MIN_GAS_PRICE)
        tx['gasPrice'] = gas_price
        tx['nonce'] = nonce
        signed_tx = self._web3.eth.account.signTransaction(tx, self.private_key)
        logger.debug(f'`Wallet` signed tx is {signed_tx}')
        return signed_tx.rawTransaction

    def sign(self, msg_hash):
        account = self._web3.eth.account.privateKeyToAccount(self.private_key)
        return account.signHash(msg_hash)

    def keysStr(self):
        s = []
        s += [f"address: {self.address}"]
        if self.private_key is not None:
            s += [f"private key: {self.private_key}"]
            s += [f"public key: {privateKeyToPublicKey(self.private_key)}"]
        s += [""]
        return "\n".join(s)

