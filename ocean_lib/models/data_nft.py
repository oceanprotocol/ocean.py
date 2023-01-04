#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import json
import warnings
from base64 import b64encode
from enum import IntEnum, IntFlag
from typing import Optional

from brownie import network
from enforce_typing import enforce_types

from ocean_lib.models.datatoken import Datatoken
from ocean_lib.ocean.util import create_checksum, get_address_of_type, get_from_address
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.utils import check_network


class DataNFTPermissions(IntEnum):
    MANAGER = 0
    DEPLOY_DATATOKEN = 1
    UPDATE_METADATA = 2
    STORE = 3


class MetadataState(IntEnum):
    ACTIVE = 0
    END_OF_LIFE = 1
    DEPRECATED = 2
    REVOKED = 3
    TEMPORARILY_DISABLED = 4


class Flags(IntFlag):
    PLAIN = 0
    COMPRESSED = 1
    ENCRYPTED = 2

    def to_byte(self):
        return self.to_bytes(1, "big")


@enforce_types
class DataNFT(ContractBase):
    CONTRACT_NAME = "ERC721Template"

    def create_datatoken(self, datatoken_args, tx_dict) -> Datatoken:
        return datatoken_args.create_datatoken(self, tx_dict)

    def calculate_did(self):
        check_network(self.network)
        chain_id = network.chain.id
        return f"did:op:{create_checksum(self.address + str(chain_id))}"


class DataNFTArguments:
    def __init__(
        self,
        name: str,
        symbol: str,
        template_index: Optional[int] = 1,
        additional_datatoken_deployer: Optional[str] = None,
        additional_metadata_updater: Optional[str] = None,
        uri: Optional[str] = None,
        transferable: Optional[bool] = None,
        owner: Optional[str] = None,
    ):
        """
        :param name: str name of data NFT if creating a new one
        :param symbol: str symbol of data NFT  if creating a new one
        :param template_index: int template index of the data NFT, by default is 1.
        :param additional_datatoken_deployer: str address of an additional ERC20 deployer.
        :param additional_metadata_updater: str address of an additional metadata updater.
        :param uri: str URL of the data NFT.
        """
        self.name = name
        self.symbol = symbol or name
        self.template_index = template_index
        self.additional_datatoken_deployer = (
            additional_datatoken_deployer or ZERO_ADDRESS
        )
        self.additional_metadata_updater = additional_metadata_updater or ZERO_ADDRESS
        self.uri = uri or self.get_default_token_uri()
        self.transferable = transferable or True
        self.owner = owner

    def get_default_token_uri(self):
        data = {
            "name": self.name,
            "symbol": self.symbol,
            "background_color": "141414",
            "image_data": "data:image/svg+xml,%3Csvg viewBox='0 0 99 99' fill='undefined' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath fill='%23ff409277' d='M0,99L0,29C9,24 19,19 31,19C42,18 55,23 67,25C78,26 88,23 99,21L99,99Z'/%3E%3Cpath fill='%23ff4092bb' d='M0,99L0,43C9,45 18,47 30,48C41,48 54,46 66,45C77,43 88,43 99,43L99,99Z'%3E%3C/path%3E%3Cpath fill='%23ff4092ff' d='M0,99L0,78C10,75 20,72 31,71C41,69 53,69 65,70C76,70 87,72 99,74L99,99Z'%3E%3C/path%3E%3C/svg%3E",
        }

        return b"data:application/json;base64," + b64encode(
            json.dumps(data, separators=(",", ":")).encode("utf-8")
        )

    def deploy_contract(self, config_dict, tx_dict) -> DataNFT:
        from ocean_lib.models.data_nft_factory import (  # isort:skip
            DataNFTFactoryContract,
        )

        address = get_address_of_type(config_dict, DataNFTFactoryContract.CONTRACT_NAME)
        data_nft_factory = DataNFTFactoryContract(config_dict, address)

        wallet_address = get_from_address(tx_dict)

        receipt = data_nft_factory.deployERC721Contract(
            self.name,
            self.symbol,
            self.template_index,
            self.additional_metadata_updater,
            self.additional_datatoken_deployer,
            self.uri,
            self.transferable,
            self.owner or wallet_address,
            tx_dict,
        )

        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message=".*Event log does not contain enough topics for the given ABI.*",
            )
            registered_event = receipt.events["NFTCreated"]

        data_nft_address = registered_event["newTokenAddress"]
        return DataNFT(config_dict, data_nft_address)
