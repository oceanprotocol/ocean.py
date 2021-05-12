#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_lib.common.agreements.consumable import ConsumableCodes
from ocean_lib.common.utils.utilities import simplify_credential_to_address


class AddressCredential:
    def __init__(self, asset):
        self.asset = asset

    def get_addresses_of_class(self, access_class="allow"):
        """Get a filtered list of addresses from credentials (use with allow/deny)."""
        entries = self.asset._credentials.get(access_class, [])

        for entry in entries:
            if entry["type"] == "address":
                return [val.lower() for val in entry["values"]]

        return []

    def requires_credential(self):
        allowed_addresses = self.get_addresses_of_class("allow")
        denied_addresses = self.get_addresses_of_class("deny")

        return allowed_addresses or denied_addresses

    def get_allowed_code(self, credential=None):
        address = simplify_credential_to_address(credential)

        allowed_addresses = self.get_addresses_of_class("allow")
        denied_addresses = self.get_addresses_of_class("deny")

        if not address and not self.requires_credential():
            return ConsumableCodes.OK

        if allowed_addresses and address.lower() not in allowed_addresses:
            return ConsumableCodes.CREDENTIAL_NOT_IN_ALLOW_LIST

        if not allowed_addresses and address.lower() in denied_addresses:
            return ConsumableCodes.CREDENTIAL_IN_DENY_LIST

        return ConsumableCodes.OK

    def add_address_to_list_class(self, address, list_class="allow"):
        address = address.lower()

        if not self.asset._credentials or list_class not in self.asset._credentials:
            self.asset._credentials[list_class] = [
                {"type": "address", "values": [address]}
            ]
            return

        address_type = [
            entry
            for entry in self.asset._credentials[list_class]
            if entry["type"] == "address"
        ]

        if not address_type:
            self.asset._credentials[list_class].append(
                {"type": "address", "values": [address]}
            )
            return

        address_type = address_type[0]
        lc_addresses = [addr.lower() for addr in address_type["values"]]

        if address not in lc_addresses:
            lc_addresses.append(address)

        address_type["values"] = lc_addresses

    def remove_address_from_list_class(self, address, list_class="allow"):
        address = address.lower()

        if not self.asset._credentials or list_class not in self.asset._credentials:
            return

        address_type = [
            entry
            for entry in self.asset._credentials[list_class]
            if entry["type"] == "address"
        ]

        if not address_type:
            return

        address_type = address_type[0]
        lc_addresses = [addr.lower() for addr in address_type["values"]]

        if address not in lc_addresses:
            return

        lc_addresses.remove(address)
        address_type["values"] = lc_addresses
