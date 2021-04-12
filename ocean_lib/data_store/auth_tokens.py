#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
import os

from ocean_lib.config_provider import ConfigProvider
from ocean_lib.sql_models import AuthToken
from ocean_lib.web3_internal.web3_provider import Web3Provider
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


class AuthTokensStorage:
    AUTH_TOKENS_TABLE = "auth_tokens"

    def __init__(self, storage_path):
        if (
            storage_path == ":memory:"
            or ConfigProvider.get_config().storage_path == ":memory:"
        ):
            _sql_engine = create_engine("sqlite://")
            return self._make_session(_sql_engine)

        if not storage_path:
            storage_path = ConfigProvider.get_config().storage_path

        if not os.path.exists(storage_path):
            # TODO: not sure if this is ok, but if the storage path does not exist?
            _sql_engine = create_engine("sqlite://")
            return self._make_session(_sql_engine)

        url = "sqlite:////" + storage_path
        _sql_engine = create_engine(url)
        return self._make_session(_sql_engine)

    def _make_session(self, engine):
        with engine.connect() as con:
            con.execute(
                f"""CREATE TABLE IF NOT EXISTS {self.AUTH_TOKENS_TABLE} (
                        address VARCHAR PRIMARY KEY,
                        signed_token VARCHAR,
                        created VARCHAR
                    );
                 """
            )

        Session = sessionmaker(bind=engine)
        self.session = Session()

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

        result = self.session.query(AuthToken).filter_by(address=address).first()

        if not result:
            result = AuthToken(
                address=address, signed_token=signed_token, created=created_at
            )

        result.signed_token = signed_token
        result.created = created_at
        self.session.add(result)
        self.session.commit()

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
        result = self.session.query(AuthToken).filter_by(address=address).first()

        if not result:
            return None

        result.signed_token = signed_token
        result.created = created_at
        self.session.add(result)
        self.session.commit()

        return result

    def read_token(self, address):
        """
        Retrieve stored signed token for the given ethereum address

        :param address: hex str the ethereum address that signed the token
        :return: tuple (signed_token, created_at)
        """
        checksum_address = Web3Provider.get_web3().toChecksumAddress(address)
        result = (
            self.session.query(AuthToken).filter_by(address=checksum_address).first()
        )

        if result:
            return result.signed_token, result.created

        return None, None
