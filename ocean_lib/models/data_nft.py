#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import warnings
from enum import IntEnum, IntFlag
from typing import Optional

from base64 import b64encode
from brownie import network
from cryptography.fernet import Fernet
from enforce_typing import enforce_types
from eth_account.messages import encode_defunct
from hashlib import sha256
from web3 import Web3

from ocean_lib.models.datatoken import Datatoken
from ocean_lib.ocean.util import create_checksum, get_address_of_type
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.utils import check_network, sign_with_key


from ecies import decrypt as asymmetric_decrypt


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

    def create_datatoken(self, datatoken_args, wallet) -> Datatoken:
        return datatoken_args.create_datatoken(self, wallet)

    def calculate_did(self):
        check_network(self.network)
        chain_id = network.chain.id
        return f"did:op:{create_checksum(self.address + str(chain_id))}"

    def set_data(self, field_label:str, field_value:str, tx_dict:dict):
        """Set key/value data via ERC725, with strings for key/value"""
        field_label_hash = Web3.keccak(text=field_label) # to keccak256 hash
        field_value_bytes = field_value.encode() # to array of bytes
        tx = self.contract.setNewData(
            field_label_hash, field_value_bytes, tx_dict
        )
        return tx

    def get_data(self, field_label:str) -> str:
        """Get key/value data via ERC725, with strings for key/value"""
        field_label_hash = Web3.keccak(text=field_label) # to keccak256 hash
        field_value_hex = self.contract.getData(field_label_hash)
        field_value = field_value_hex.decode('ascii')
        return field_value
        
    def set_encrypted_data(self,
        field_label : str,
        field_value : str,
        tx_dict : dict,
    ) -> str:
        """
        Set key/value data via ERC725, with strings for key/value
          and where value (field_value) is symmetrically encrypted.
        
        Internally, it generates a symmetric private key (symkey), then
          uses that to encrypt the data. The setter can calculate the symkey 
          anytime via data_nft.calc_symkey().
        """        
        # Prep key for setter. Contract/ERC725 requires keccak256 hash
        field_label_hash = Web3.keccak(text=field_label)

        # Prep value for setter
        symkey = self.get_symkey(field_label, tx_dict["from"])
        field_value_encr = Fernet(symkey).encrypt(field_value.encode('utf-8'))
        field_value_encr_hex = field_value_encr.hex()
    
        tx = self.contract.setNewData(
            field_label_hash, field_value_encr_hex, tx_dict
        )
        return tx
    
    def get_encrypted_data(self, field_label:str, symkey: bytes) -> str:
        """
        Get *encrypted* key/value data from the chain, via ERC725,
          using key/value formats that are easy for developers to work with.

        How: 
        - converts the input key string arg into a format friendly for ERC725.
        - converts the value into a string, before returning
        """
        field_label_hash = Web3.keccak(text=field_label)
        field_value_encr_hex2 = self.contract.getData(field_label_hash)
        field_value2_bytes = Fernet(symkey).decrypt(field_value_encr_hex2)
        field_value2 = field_value2_bytes.decode('utf-8')

        return field_value2
    
    def get_symkey(self, field_label:str, wallet) -> bytes:
        """
        Compute a symmetric private key:
        - it's a function of this data nft's address & field_label field
          - therefore, sharing it only unlocks a single data field in this nft
        - it's also a function of the input wallet's private key
          - therefore only the input wallet can compute it anytime

        Return
          symkey -- symmetric private key
        """
        k1 = self.address + field_label + wallet.private_key
        k2 = sha256(k1.encode('utf-8'))
        symkey = b64encode(str(k2).encode('ascii'))[:43] + b'='  # bytes
        return symkey

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
        self.uri = uri or "https://oceanprotocol.com/nft/"
        self.transferable = transferable or True
        self.owner = owner

    def deploy_contract(self, config_dict, wallet) -> DataNFT:
        from ocean_lib.models.data_nft_factory import (  # isort:skip
            DataNFTFactoryContract,
        )

        address = get_address_of_type(config_dict, DataNFTFactoryContract.CONTRACT_NAME)
        data_nft_factory = DataNFTFactoryContract(config_dict, address)

        receipt = data_nft_factory.deployERC721Contract(
            self.name,
            self.symbol,
            self.template_index,
            self.additional_metadata_updater,
            self.additional_datatoken_deployer,
            self.uri,
            self.transferable,
            self.owner or wallet.address,
            {"from": wallet},
        )

        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message=".*Event log does not contain enough topics for the given ABI.*",
            )
            registered_event = receipt.events["NFTCreated"]

        data_nft_address = registered_event["newTokenAddress"]
        return DataNFT(config_dict, data_nft_address)
