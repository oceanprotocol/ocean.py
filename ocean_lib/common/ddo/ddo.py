#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import copy
import json
import logging
from pathlib import Path
from typing import Any, Optional, Union

from enforce_typing import enforce_types
from eth_account.account import Account
from eth_utils import add_0x_prefix
from ocean_lib.common.agreements.consumable import ConsumableCodes
from ocean_lib.common.agreements.service_agreement import ServiceAgreement
from ocean_lib.common.agreements.service_types import ServiceTypes
from ocean_lib.common.ddo.constants import DID_DDO_CONTEXT_URL, PROOF_TYPE
from ocean_lib.common.ddo.credentials import AddressCredential
from ocean_lib.common.ddo.service import Service
from ocean_lib.common.did import did_to_id
from ocean_lib.common.utils.utilities import get_timestamp
from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.web3_internal.wallet import Wallet

logger = logging.getLogger("ddo")


class DDO:
    """DDO class to create, import, export, validate DDO objects."""

    @enforce_types
    def __init__(
        self,
        did: Optional[str] = None,
        json_text: Optional[str] = None,
        json_filename: Optional[Path] = None,
        created: Optional[Any] = None,
        dictionary: Optional[dict] = None,
    ) -> None:
        """Clear the DDO data values."""
        self.did = did
        self.services = []
        self.proof = None
        self.credentials = {}
        self.created = created if created else get_timestamp()
        self.other_values = {}

        if not json_text and json_filename:
            with open(json_filename, "r") as file_handle:
                json_text = file_handle.read()

        if json_text:
            self._read_dict(json.loads(json_text))
        elif dictionary:
            self._read_dict(dictionary)

    @property
    @enforce_types
    def is_disabled(self) -> bool:
        """Returns whether the asset is disabled."""
        return self.is_flag_enabled("isOrderDisabled")

    @property
    @enforce_types
    def is_enabled(self) -> bool:
        """Returns the opposite of is_disabled, for convenience."""
        return not self.is_disabled

    @property
    @enforce_types
    def is_retired(self) -> bool:
        """Returns whether the asset is retired."""
        return self.is_flag_enabled("isRetired")

    @property
    @enforce_types
    def is_listed(self) -> bool:
        """Returns whether the asset is listed."""
        return self.is_flag_enabled("isListed")

    @property
    @enforce_types
    def asset_id(self) -> Optional[str]:
        """The asset id part of the DID"""
        if not self.did:
            return None
        return add_0x_prefix(did_to_id(self.did))

    @property
    @enforce_types
    def publisher(self) -> Optional[str]:
        return self.proof.get("creator") if self.proof else None

    @property
    @enforce_types
    def metadata(self) -> Optional[dict]:
        """Get the metadata service."""
        metadata_service = self.get_service(ServiceTypes.METADATA)
        return metadata_service.attributes if metadata_service else None

    @property
    @enforce_types
    def encrypted_files(self) -> Optional[dict]:
        """Return encryptedFiles field in the base metadata."""
        return self.metadata["encryptedFiles"]

    @enforce_types
    def add_service(
        self,
        service_type: Union[str, Service],
        service_endpoint: Optional[str] = None,
        values: Optional[dict] = None,
        index: Optional[int] = None,
    ) -> None:
        """
        Add a service to the list of services on the DDO.

        :param service_type: Service
        :param service_endpoint: Service endpoint, str
        :param values: Python dict with index, templateId, serviceAgreementContract,
        list of conditions and purchase endpoint.
        """
        if isinstance(service_type, Service):
            service = service_type
        else:
            values = copy.deepcopy(values) if values else {}
            service = Service(
                service_endpoint,
                service_type,
                values.pop("attributes", None),
                values,
                index,
            )
        logger.debug(
            f"Adding service with service type {service_type} with did {self.did}"
        )
        self.services.append(service)

    @enforce_types
    def as_text(self, is_proof: bool = True, is_pretty: bool = False) -> str:
        """Return the DDO as a JSON text.

        :param if is_proof: if False then do not include the 'proof' element.
        :param is_pretty: If True return dictionary in a prettier way, bool
        :return: str
        """
        data = self.as_dictionary(is_proof)
        if is_pretty:
            return json.dumps(data, indent=2, separators=(",", ": "))

        return json.dumps(data)

    @enforce_types
    def as_dictionary(self, is_proof: bool = True) -> dict:
        """
        Return the DDO as a JSON dict.

        :param if is_proof: if False then do not include the 'proof' element.
        :return: dict
        """
        if self.created is None:
            self.created = get_timestamp()

        data = {
            "@context": DID_DDO_CONTEXT_URL,
            "id": self.did,
            "created": self.created,
        }

        data["publicKey"] = [
            {"id": self.did, "type": "EthereumECDSAKey", "owner": self.publisher}
        ]

        data["authentication"] = [
            {"type": "RsaSignatureAuthentication2018", "publicKey": self.did}
        ]

        if self.services:
            data["service"] = [service.as_dictionary() for service in self.services]
        if self.proof and is_proof:
            data["proof"] = self.proof
        if self.credentials:
            data["credentials"] = self.credentials
        if self.other_values:
            data.update(self.other_values)

        return data

    @enforce_types
    def _read_dict(self, dictionary: dict) -> None:
        """Import a JSON dict into this DDO."""
        values = copy.deepcopy(dictionary)
        id_key = "id" if "id" in values else "_id"
        self.did = values.pop(id_key)
        self.created = values.pop("created", None)

        if "service" in values:
            self.services = []
            for value in values.pop("service"):
                if isinstance(value, str):
                    value = json.loads(value)

                if value["type"] in [
                    ServiceTypes.ASSET_ACCESS,
                    ServiceTypes.CLOUD_COMPUTE,
                ]:
                    service = ServiceAgreement.from_json(value)
                else:
                    service = Service.from_json(value)

                self.services.append(service)
        if "proof" in values:
            self.proof = values.pop("proof")
        if "credentials" in values:
            self.credentials = values.pop("credentials")

        self.other_values = values

    @enforce_types
    def add_proof(
        self, checksums: dict, publisher_account: Union[Account, Wallet]
    ) -> None:
        """Add a proof to the DDO, based on the public_key id/index and signed with the private key
        add a static proof to the DDO, based on one of the public keys.

        :param checksums: dict with the checksum of the main attributes of each service, dict
        :param publisher_account: account of the publisher, account
        """
        self.proof = {
            "type": PROOF_TYPE,
            "created": get_timestamp(),
            "creator": publisher_account.address,
            "signatureValue": "",
            "checksum": checksums,
        }

    @enforce_types
    def get_service(self, service_type: str) -> Optional[Service]:
        """Return a service using."""
        return next(
            (service for service in self.services if service.type == service_type), None
        )

    @enforce_types
    def get_service_by_index(self, index: int) -> Optional[Service]:
        """
        Get service for a given index.

        :param index: Service id, str
        :return: Service
        """
        return next(
            (service for service in self.services if service.index == index), None
        )

    @enforce_types
    def enable(self) -> None:
        """Enables asset for ordering."""
        self.disable_flag("isOrderDisabled")

    @enforce_types
    def disable(self) -> None:
        """Disables asset from ordering."""
        self.enable_flag("isOrderDisabled")

    @enforce_types
    def retire(self) -> None:
        """Retires an asset."""
        self.enable_flag("isRetired")

    @enforce_types
    def unretire(self) -> None:
        """Unretires an asset."""
        self.disable_flag("isRetired")

    @enforce_types
    def list(self) -> None:
        """Lists a previously unlisted asset."""
        self.enable_flag("isListed")

    @enforce_types
    def unlist(self) -> None:
        """Unlists an asset."""
        self.disable_flag("isListed")

    @property
    @enforce_types
    def requires_address_credential(self) -> bool:
        """Checks if an address credential is required on this asset."""
        manager = AddressCredential(self)
        return manager.requires_credential()

    @property
    @enforce_types
    def allowed_addresses(self) -> list:
        """Lists addresses that are explicitly allowed in credentials."""
        manager = AddressCredential(self)
        return manager.get_addresses_of_class("allow")

    @property
    @enforce_types
    def denied_addresses(self) -> list:
        """Lists addresesses that are explicitly denied in credentials."""
        manager = AddressCredential(self)
        return manager.get_addresses_of_class("deny")

    @enforce_types
    def add_address_to_allow_list(self, address: str) -> None:
        """Adds an address to allowed addresses list."""
        manager = AddressCredential(self)
        manager.add_address_to_access_class(address, "allow")

    @enforce_types
    def add_address_to_deny_list(self, address: str) -> None:
        """Adds an address to the denied addresses list."""
        manager = AddressCredential(self)
        manager.add_address_to_access_class(address, "deny")

    @enforce_types
    def remove_address_from_allow_list(self, address: str) -> None:
        """Removes address from allow list (if it exists)."""
        manager = AddressCredential(self)
        manager.remove_address_from_access_class(address, "allow")

    @enforce_types
    def remove_address_from_deny_list(self, address: str) -> None:
        """Removes address from deny list (if it exists)."""
        manager = AddressCredential(self)
        manager.remove_address_from_access_class(address, "deny")

    @enforce_types
    def is_consumable(
        self,
        credential: Optional[dict] = None,
        with_connectivity_check: bool = True,
        provider_uri: Optional[str] = None,
    ) -> bool:
        """Checks whether an asset is consumable and returns a ConsumableCode."""
        if self.is_disabled or self.is_retired:
            return ConsumableCodes.ASSET_DISABLED

        if (
            with_connectivity_check
            and provider_uri
            and not DataServiceProvider.check_asset_file_info(
                self.did, DataServiceProvider.get_root_uri(provider_uri)
            )
        ):
            return ConsumableCodes.CONNECTIVITY_FAIL

        # to be parameterized in the future, can implement other credential classes
        manager = AddressCredential(self)

        if manager.requires_credential():
            return manager.validate_access(credential)

        return ConsumableCodes.OK

    @enforce_types
    def enable_flag(self, flag_name: str) -> None:
        """
        :return: None
        """
        metadata_service = self.get_service(ServiceTypes.METADATA)

        if not metadata_service:
            return

        if "status" not in metadata_service.attributes:
            metadata_service.attributes["status"] = {}

        if flag_name == "isListed":  # only one that defaults to True
            metadata_service.attributes["status"].pop(flag_name)
        else:
            metadata_service.attributes["status"][flag_name] = True

    @enforce_types
    def disable_flag(self, flag_name: str) -> None:
        """
        :return: None
        """
        metadata_service = self.get_service(ServiceTypes.METADATA)

        if not metadata_service:
            return

        if "status" not in metadata_service.attributes:
            metadata_service.attributes["status"] = {}

        if flag_name == "isListed":  # only one that defaults to True
            metadata_service.attributes["status"][flag_name] = False
        else:
            metadata_service.attributes["status"].pop(flag_name)

    @enforce_types
    def is_flag_enabled(self, flag_name: str) -> bool:
        """
        :return: `isListed` or `bool` in metadata_service.attributes["status"]
        """
        metadata_service = self.get_service(ServiceTypes.METADATA)
        default = flag_name == "isListed"  # only one that defaults to True

        if not metadata_service or "status" not in metadata_service.attributes:
            return default

        return metadata_service.attributes["status"].get(flag_name, default)
