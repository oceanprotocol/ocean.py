#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import copy
import json
import logging

from eth_utils import add_0x_prefix
from ocean_lib.common.agreements.consumable import ConsumableCodes
from ocean_lib.common.agreements.service_agreement import ServiceAgreement
from ocean_lib.common.agreements.service_types import ServiceTypes
from ocean_lib.common.ddo.credentials import AddressCredential
from ocean_lib.common.ddo.public_key_base import PublicKeyBase
from ocean_lib.common.ddo.public_key_rsa import PUBLIC_KEY_TYPE_ETHEREUM_ECDSA
from ocean_lib.common.did import OCEAN_PREFIX, did_to_id
from ocean_lib.common.utils.utilities import get_timestamp
from ocean_lib.data_provider.data_service_provider import DataServiceProvider

from .constants import DID_DDO_CONTEXT_URL, PROOF_TYPE
from .public_key_rsa import PUBLIC_KEY_TYPE_RSA, PublicKeyRSA
from .service import Service

logger = logging.getLogger("ddo")


class DDO:
    """DDO class to create, import, export, validate DDO objects."""

    def __init__(
        self,
        did=None,
        json_text=None,
        json_filename=None,
        created=None,
        dictionary=None,
    ):
        """Clear the DDO data values."""
        self._did = did
        self._public_keys = []
        self._authentications = []
        self._services = []
        self._proof = None
        self._credentials = {}
        self._created = None
        self._status = {}
        self._other_values = {}

        if created:
            self._created = created
        else:
            self._created = get_timestamp()

        if not json_text and json_filename:
            with open(json_filename, "r") as file_handle:
                json_text = file_handle.read()

        if json_text:
            self._read_dict(json.loads(json_text))
        elif dictionary:
            self._read_dict(dictionary)

    @property
    def did(self):
        """Get the DID."""
        return self._did

    @property
    def is_disabled(self):
        """Returns whether the asset is disabled."""
        if not self._status:
            return False

        return self._status.get("isOrderDisabled", False)

    @property
    def is_enabled(self):
        """Returns the opposite of is_disabled, for convenience."""
        return not self.is_disabled

    @property
    def asset_id(self):
        """The asset id part of the DID"""
        if not self._did:
            return None
        return add_0x_prefix(did_to_id(self._did))

    @property
    def services(self):
        """Get the list of services."""
        return self._services[:]

    @property
    def proof(self):
        """Get the static proof, or None."""
        return self._proof

    @property
    def credentials(self):
        """Get the credentials."""
        return self._credentials

    @property
    def publisher(self):
        return self._proof.get("creator") if self._proof else None

    @property
    def metadata(self):
        """Get the metadata service."""
        metadata_service = self.get_service(ServiceTypes.METADATA)
        return metadata_service.attributes if metadata_service else None

    @property
    def created(self):
        return self._created

    @property
    def encrypted_files(self):
        """Return encryptedFiles field in the base metadata."""
        files = self.metadata["encryptedFiles"]
        return files

    def assign_did(self, did):
        if self._did:
            raise AssertionError('"did" is already set on this DDO instance.')
        assert did and isinstance(
            did, str
        ), f"did must be of str type, got {did} of type {type(did)}"
        assert did.startswith(
            OCEAN_PREFIX
        ), f'"did" seems invalid, must start with {OCEAN_PREFIX} prefix.'
        self._did = did
        return did

    def add_public_key(self, did, public_key):
        """
        Add a public key object to the list of public keys.

        :param public_key: Public key, PublicKeyHex
        """
        logger.debug(f"Adding public key {public_key} to the did {did}")
        self._public_keys.append(
            PublicKeyBase(
                did, **{"owner": public_key, "type": PUBLIC_KEY_TYPE_ETHEREUM_ECDSA}
            )
        )

    def add_authentication(self, public_key, authentication_type):
        """
        Add a authentication public key id and type to the list of authentications.

        :param public_key: Key id, Authentication
        :param authentication_type: Authentication type, str
        """
        authentication = {}
        if public_key:
            authentication = {"type": authentication_type, "publicKey": public_key}
        logger.debug(f"Adding authentication {authentication}")
        self._authentications.append(authentication)

    def add_service(self, service_type, service_endpoint=None, values=None, index=None):
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
            f"Adding service with service type {service_type} with did {self._did}"
        )
        self._services.append(service)

    def as_text(self, is_proof=True, is_pretty=False):
        """Return the DDO as a JSON text.

        :param if is_proof: if False then do not include the 'proof' element.
        :param is_pretty: If True return dictionary in a prettier way, bool
        :return: str
        """
        data = self.as_dictionary(is_proof)
        if is_pretty:
            return json.dumps(data, indent=2, separators=(",", ": "))

        return json.dumps(data)

    def as_dictionary(self, is_proof=True):
        """
        Return the DDO as a JSON dict.

        :param if is_proof: if False then do not include the 'proof' element.
        :return: dict
        """
        if self._created is None:
            self._created = get_timestamp()

        data = {
            "@context": DID_DDO_CONTEXT_URL,
            "id": self._did,
            "created": self._created,
        }
        if self._public_keys:
            values = []
            for public_key in self._public_keys:
                values.append(public_key.as_dictionary())
            data["publicKey"] = values
        if self._authentications:
            values = []
            for authentication in self._authentications:
                values.append(authentication)
            data["authentication"] = values
        if self._services:
            values = []
            for service in self._services:
                values.append(service.as_dictionary())
            data["service"] = values
        if self._proof and is_proof:
            data["proof"] = self._proof
        if self._credentials:
            data["credentials"] = self._credentials
        if self._status:
            data["status"] = self._status

        if self._other_values:
            data.update(self._other_values)

        return data

    def _read_dict(self, dictionary):
        """Import a JSON dict into this DDO."""
        values = copy.deepcopy(dictionary)
        self._did = values.pop("id")
        self._created = values.pop("created", None)

        if "publicKey" in values:
            self._public_keys = []
            for value in values.pop("publicKey"):
                if isinstance(value, str):
                    value = json.loads(value)
                self._public_keys.append(DDO.create_public_key_from_json(value))
        if "authentication" in values:
            self._authentications = []
            for value in values.pop("authentication"):
                if isinstance(value, str):
                    value = json.loads(value)
                self._authentications.append(DDO.create_authentication_from_json(value))
        if "service" in values:
            self._services = []
            for value in values.pop("service"):
                if isinstance(value, str):
                    value = json.loads(value)

                if value["type"] == ServiceTypes.ASSET_ACCESS:
                    service = ServiceAgreement.from_json(value)
                elif value["type"] == ServiceTypes.CLOUD_COMPUTE:
                    service = ServiceAgreement.from_json(value)
                else:
                    service = Service.from_json(value)

                self._services.append(service)
        if "proof" in values:
            self._proof = values.pop("proof")
        if "credentials" in values:
            self._credentials = values.pop("credentials")
        if "status" in values:
            self._status = values.pop("status")

        self._other_values = values

    def add_proof(self, checksums, publisher_account):
        """Add a proof to the DDO, based on the public_key id/index and signed with the private key
        add a static proof to the DDO, based on one of the public keys.

        :param checksums: dict with the checksum of the main attributes of each service, dict
        :param publisher_account: account of the publisher, account
        """
        self._proof = {
            "type": PROOF_TYPE,
            "created": get_timestamp(),
            "creator": publisher_account.address,
            "signatureValue": "",
            "checksum": checksums,
        }

    def get_public_key(self, key_id):
        """Key_id can be a string, or int. If int then the index in the list of keys."""
        if isinstance(key_id, int):
            return self._public_keys[key_id]

        for item in self._public_keys:
            if item.get_id() == key_id:
                return item

        return None

    def _get_public_key_count(self):
        """Return the count of public keys in the list and embedded."""
        return len(self._public_keys)

    def _get_authentication_from_public_key_id(self, key_id):
        """Return the authentication based on it's id."""
        for authentication in self._authentications:
            if authentication["publicKey"] == key_id:
                return authentication
        return None

    def get_service(self, service_type=None):
        """Return a service using."""
        for service in self._services:
            if service.type == service_type and service_type:
                return service
        return None

    def get_service_by_index(self, index):
        """
        Get service for a given index.

        :param index: Service id, str
        :return: Service
        """
        try:
            index = int(index)
        except ValueError:
            logging.error(f"The index {index} can not be converted into a int")
            return None

        for service in self._services:
            if service.index == index:
                return service

        # try to find by type
        return self.get_service(index)

    @property
    def public_keys(self):
        """Get the list of public keys."""
        return self._public_keys[:]

    @property
    def authentications(self):
        """Get the list authentication records."""
        return self._authentications[:]

    @staticmethod
    def create_public_key_from_json(values):
        """Create a public key object based on the values from the JSON record."""
        # currently we only support RSA public keys
        _id = values.get("id")
        if not _id:
            # Make it more forgiving for now.
            _id = ""
            # raise ValueError('publicKey definition is missing the "id" value.')

        if values.get("type") == PUBLIC_KEY_TYPE_RSA:
            public_key = PublicKeyRSA(_id, owner=values.get("owner"))
        else:
            public_key = PublicKeyBase(
                _id, owner=values.get("owner"), type=PUBLIC_KEY_TYPE_ETHEREUM_ECDSA
            )

        public_key.set_key_value(values)
        return public_key

    @staticmethod
    def create_authentication_from_json(values):
        """Create authentication object from a JSON dict."""
        key_id = values.get("publicKey")
        authentication_type = values.get("type")
        if not key_id:
            raise ValueError(
                f'Invalid authentication definition, "publicKey" is missing: {values}'
            )

        authentication = {"type": authentication_type, "publicKey": key_id}
        return authentication

    def enable(self):
        """Enables asset for ordering."""
        if not self._status:
            self._status = {}

        self._status.pop("isOrderDisabled")

    def disable(self):
        """Disables asset from ordering."""
        if not self._status:
            self._status = {}

        self._status["isOrderDisabled"] = True

    @property
    def requires_address_credential(self):
        """Checks if an address credential is required on this asset."""
        manager = AddressCredential(self)
        return manager.requires_credential()

    @property
    def allowed_addresses(self):
        """Lists addresses that are explicitly allowed in credentials."""
        manager = AddressCredential(self)
        return manager.get_addresses_of_class("allow")

    @property
    def denied_addresses(self):
        """Lists addresesses that are explicitly denied in credentials."""
        manager = AddressCredential(self)
        return manager.get_addresses_of_class("deny")

    def add_address_to_allow_list(self, address):
        """Adds an address to allowed addresses list."""
        manager = AddressCredential(self)
        manager.add_address_to_access_class(address, "allow")

    def add_address_to_deny_list(self, address):
        """Adds an address to the denied addresses list."""
        manager = AddressCredential(self)
        manager.add_address_to_access_class(address, "deny")

    def remove_address_from_allow_list(self, address):
        """Removes address from allow list (if it exists)."""
        manager = AddressCredential(self)
        manager.remove_address_from_access_class(address, "allow")

    def remove_address_from_deny_list(self, address):
        """Removes address from deny list (if it exists)."""
        manager = AddressCredential(self)
        manager.remove_address_from_access_class(address, "deny")

    def is_consumable(
        self, credential=None, with_connectivity_check=True, provider_uri=None
    ):
        """Checks whether an asset is consumable and returns a ConsumableCode."""
        if self.is_disabled:
            return ConsumableCodes.ASSET_DISABLED

        if with_connectivity_check and not DataServiceProvider.check_asset_file_info(
            self, provider_uri
        ):
            return ConsumableCodes.CONNECTIVITY_FAIL

        # to be parameterized in the future, can implement other credential classes
        manager = AddressCredential(self)

        if manager.requires_credential():
            return manager.validate_access(credential)

        return ConsumableCodes.OK
