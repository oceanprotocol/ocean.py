#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import sys
from pathlib import Path

from web3 import HTTPProvider, IPCProvider
from web3.main import Web3


def get_clef_accounts(uri: str = None, timeout: int = 120) -> None:
    provider = None
    if uri is None:
        if sys.platform == "win32":
            uri = "http://localhost:8550/"
        else:
            uri = Path.home().joinpath(".clef/clef.ipc").as_posix()
    try:
        if Path(uri).exists():
            provider = IPCProvider(uri, timeout=timeout)
    except OSError:
        if uri is not None and uri.startswith("http"):
            provider = HTTPProvider(uri, {"timeout": timeout})
    if provider is None:
        raise ValueError(
            "Unknown URI, must be IPC socket path or URL starting with 'http'"
        )

    response = provider.make_request("account_list", [])
    if "error" in response:
        raise ValueError(response["error"]["message"])

    clef_accounts = [ClefAccount(address, provider) for address in response["result"]]
    return clef_accounts


class ClefAccount:
    def __init__(self, address: str, provider: [HTTPProvider, IPCProvider]) -> None:
        self.address = Web3.to_checksum_address(address)
        self.provider = provider
