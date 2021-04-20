#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging

from ocean_lib.common.data_store.storage_base import StorageBase
from ocean_lib.web3_internal.web3_provider import Web3Provider

logger = logging.getLogger(__name__)


class AuthTokensStorage(StorageBase):
    AUTH_TOKENS_TABLE = "auth_tokens"

    def write_token(self, address, signed_token, created_at):
        """
        Store signed token for session management.

        :param address: hex str the ethereum address that signed the token
        :param signed_token: hex str the signed token
        :param created_at: date-time of token creation
        """
        logger.debug(
            f"Writing token to `auth_tokens` storage: "
            f"account={address}, token={signed_token}"
        )
        self._run_query(
            f"""CREATE TABLE IF NOT EXISTS {self.AUTH_TOKENS_TABLE}
               (address VARCHAR PRIMARY KEY, signed_token VARCHAR, created VARCHAR);"""
        )
        self._run_query(
            f"""INSERT OR REPLACE
                INTO {self.AUTH_TOKENS_TABLE}
                VALUES (?,?,?)""",
            [address, signed_token, created_at],
        )

    def update_token(self, address, signed_token, created_at):
        """
        Update/replace the stored signed token for the given ethereum address.

        :param address: hex str the ethereum address that signed the token
        :param signed_token: hex str the signed token
        :param created_at: date-time of token creation
        """
        logger.debug(
            f"Updating token already in `auth_tokens` storage: "
            f"account={address}, token={signed_token}"
        )
        self._run_query(
            f"""UPDATE {self.AUTH_TOKENS_TABLE}
                SET signed_token=?, created=?
                WHERE address=?""",
            (signed_token, created_at, address),
        )

    def read_token(self, address):
        """
        Retrieve stored signed token for the given ethereum address

        :param address: hex str the ethereum address that signed the token
        :return: tuple (signed_token, created_at)
        """
        try:
            checksumAddress = Web3Provider.get_web3().toChecksumAddress(address)
            rows = [
                row
                for row in self._run_query(
                    f"""SELECT signed_token, created
                    FROM {self.AUTH_TOKENS_TABLE}
                    WHERE address=?;""",
                    (checksumAddress,),
                )
            ]
            token, timestamp = rows[0] if rows else (None, None)
            logger.debug(
                f"Read auth token from `auth_tokens` storage: "
                f"account={address}, token={token}"
            )
            return token, timestamp

        except Exception as e:
            logging.error(f"Error reading token: {e}")
            return None, None
