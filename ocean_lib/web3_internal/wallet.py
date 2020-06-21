import logging

logger = logging.getLogger(__name__)


class Wallet:
    """
    The wallet is responsible for signing transactions and messages by using an account's
    private key.

    The private key is always red from the encrypted keyfile and is never saved in memory beyond
    the life span of the signing function.

    The use of this wallet allows Ocean tools to send rawTransactions which keeps the user
    key and password safe and they are never sent outside. Another advantage of this is that
    we can interact directly with remote keeper nodes without having to run a local parity
    node since we only send the raw transaction hash so the user info is safe.

    Note that currently a local node is still necessary for completing the consume flow because
    the secretstore needs a parity node to encrypt/decrypt the asset urls. We could eliminate
    this dependency on local parity node by using Brizo's publish endpoint for encryption and
    sending url index to Brizo's consume endpoint instead of decrypting locally first.
    The secretstore also uses the parity node to sign the document key id which is necessary
    for communicating with the secret store nodes.

    """
    _last_tx_count = dict()
    MIN_GAS_PRICE = 1000000000

    def __init__(self, web3, key=None, password=None, address=None):
        self._web3 = web3

        self._password = password
        self._address = address
        self._key = key

    @staticmethod
    def reset_tx_count():
        Wallet._last_tx_count = dict()

    def __get_key(self):
        if not self._password:
            return self._key

        return self._web3.eth.account.decrypt(self._key, self._password)

    def validate(self):
        key = self.__get_key()
        account = self._web3.eth.account.privateKeyToAccount(key)
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
        private_key = self.__get_key()
        account = self._web3.eth.account.privateKeyToAccount(private_key)
        nonce = Wallet._get_nonce(self._web3, account.address)
        logger.debug(f'`Wallet` signing tx: sender address: {account.address} nonce: {nonce}, '
                     f'gasprice: {self._web3.eth.gasPrice}')
        gas_price = int(self._web3.eth.gasPrice / 100)
        gas_price = max(gas_price, self.MIN_GAS_PRICE)
        tx['nonce'] = nonce
        tx['gasPrice'] = gas_price
        signed_tx = self._web3.eth.account.signTransaction(tx, private_key)
        logger.debug(f'`Wallet` signed tx is {signed_tx}')
        return signed_tx.rawTransaction

    def sign(self, msg_hash):
        private_key = self.__get_key()
        account = self._web3.eth.account.privateKeyToAccount(private_key)
        return account.signHash(msg_hash)
