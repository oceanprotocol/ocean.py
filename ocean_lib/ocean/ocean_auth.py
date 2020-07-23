"""Ocean module."""
#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0

import logging
from datetime import datetime

from ocean_lib.config_provider import ConfigProvider
from ocean_lib.web3_internal.utils import add_ethereum_prefix_and_hash_msg
from ocean_lib.web3_internal.web3_provider import Web3Provider

from ocean_lib.data_store.auth_tokens import AuthTokensStorage
from ocean_lib.web3_internal.web3helper import Web3Helper


class OceanAuth:
    """Ocean auth class.
    Provide basic management of a user auth token. This token can be used to emulate
    sign-in behaviour. The token can be stored and associated with an expiry time.
    This is useful in front-end applications that interact with a 3rd-party wallet
    apps. The advantage of using the auth token is to reduce the number of confirmation
    prompts requiring user action.

    The auth token works with a provider service such as Ocean provider-py which also uses this
    ocean module to handle auth tokens.

    Token format is "signature-timestamp".

    """
    DEFAULT_EXPIRATION_TIME = 30 * 24 * 60 * 60  # in seconds
    DEFAULT_MESSAGE = "Ocean Protocol Authentication"

    def __init__(self, storage_path):
        self._tokens_storage = AuthTokensStorage(storage_path)

    @staticmethod
    def _get_timestamp():
        return int(datetime.now().timestamp())

    def _get_expiration(self):
        return int(ConfigProvider.get_config().auth_token_expiration
                   or self.DEFAULT_EXPIRATION_TIME)

    def _get_raw_message(self):
        return ConfigProvider.get_config().auth_token_message or self.DEFAULT_MESSAGE

    def _get_message(self, timestamp):
        return f'{self._get_raw_message()}\n{timestamp}'

    def _get_message_and_time(self):
        timestamp = self._get_timestamp()
        return self._get_message(timestamp), timestamp

    @staticmethod
    def is_token_valid(token):
        return isinstance(token, str) and token.startswith('0x') and len(token.split('-')) == 2

    def get(self, wallet):
        """
        :param wallet: Wallet instance signing the token
        :return: hex str the token generated/signed by the users wallet
        """
        _message, _time = self._get_message_and_time()
        try:
            prefixed_msg_hash = Web3Helper.sign_hash(
                add_ethereum_prefix_and_hash_msg(_message), wallet)
            return f'{prefixed_msg_hash}-{_time}'
        except Exception as e:
            logging.error(f'Error signing token: {str(e)}')

    def check(self, token):
        """
        :param token: hex str consist of signature and timestamp
        :return: hex str ethereum address
        """
        parts = token.split('-')
        if len(parts) < 2:
            return '0x0'

        sig, timestamp = parts
        if self._get_timestamp() > (int(timestamp) + self._get_expiration()):
            return '0x0'

        message = self._get_message(timestamp)
        address = Web3Helper.personal_ec_recover(message, sig)
        return Web3Provider.get_web3().toChecksumAddress(address)

    def store(self, wallet):
        """
        :param wallet: Wallet instance signing the token
        :return:
            token that was generated and stored for this users wallet
        """
        token = self.get(wallet)
        timestamp = token.split('-')[1]
        self._tokens_storage.write_token(wallet.address, token, timestamp)
        return token

    def restore(self, wallet):
        """
        :param wallet: Wallet instance to fetch the saved token
        :return:
            hex str the token retreived from storage
            None if no token found for this users wallet
        """
        token = self._tokens_storage.read_token(wallet.address)[0]
        if not token:
            return None

        address = self.check(token)

        return token if address == wallet.address else None

    def is_stored(self, wallet):
        """
        :param wallet: Wallet instance
        :return: bool whether this wallet has a stored token
        """
        return self.restore(wallet) is not None
