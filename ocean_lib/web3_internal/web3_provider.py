#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

from ocean_lib.web3_internal.web3_overrides.http_provider import CustomHTTPProvider
from web3 import Web3


class Web3Provider(object):

    """Provides the Web3 instance."""

    _web3 = None

    @staticmethod
    def init_web3(network_url=None, provider=None):
        """One of `network_url` or `provider` is required.

        If `provider` is given, `network_url` will be ignored.

        :param network_url:
        :param provider:
        :return:
        """
        if not provider:
            assert network_url, "network_url or a provider instance is required."
            provider = CustomHTTPProvider(network_url)

        Web3Provider._web3 = Web3(provider)

        # Reset attributes to avoid lint issue about no attribute
        Web3Provider._web3.eth = getattr(Web3Provider._web3, "eth")
        Web3Provider._web3.net = getattr(Web3Provider._web3, "net")
        Web3Provider._web3.version = getattr(Web3Provider._web3, "version")
        Web3Provider._web3.parity = getattr(Web3Provider._web3, "parity")
        Web3Provider._web3.testing = getattr(Web3Provider._web3, "testing")

    @staticmethod
    def get_web3(network_url=None, provider=None):
        """Return the web3 instance to interact with the ethereum client."""
        if Web3Provider._web3 is None:
            Web3Provider.init_web3(network_url, provider)
        return Web3Provider._web3

    @staticmethod
    def set_web3(web3):
        """Set web3 instance."""
        Web3Provider._web3 = web3
