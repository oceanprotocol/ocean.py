#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import Optional

from enforce_typing import enforce_types
from ocean_lib.common.agreements.consumable import ConsumableCodes, MalformedCredential


@enforce_types
class AddressCredential:
    def __init__(self, asset) -> None:
        self.asset = asset

    def get_addresses_of_class(self, access_class: str = "allow") -> list:
        """Get a filtered list of addresses from credentials (use with allow/deny)."""
        address_entry = self.get_address_entry_of_class(access_class)
        if not address_entry:
            return []

        if "values" not in address_entry:
            raise MalformedCredential("No values key in the address credential.")

        return [addr.lower() for addr in address_entry["values"]]

    def requires_credential(self) -> bool:
        """Checks whether the asset requires an address credential."""
        allowed_addresses = self.get_addresses_of_class("allow")
        denied_addresses = self.get_addresses_of_class("deny")

        return bool(allowed_addresses or denied_addresses)

    def validate_access(self, credential: Optional[dict] = None) -> int:
        """Checks a credential dictionary against the address allow/deny lists."""
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

    def add_address_to_access_class(
        self, address: str, access_class: str = "allow"
    ) -> None:
        """Adds an address to an address list (either allow or deny)."""
        address = address.lower()

        if not self.asset._credentials or access_class not in self.asset._credentials:
            self.asset._credentials[access_class] = [
                {"type": "address", "values": [address]}
            ]
            return

        address_entry = self.get_address_entry_of_class(access_class)

        if not address_entry:
            self.asset._credentials[access_class].append(
                {"type": "address", "values": [address]}
            )
            return

        lc_addresses = self.get_addresses_of_class(access_class)

        if address not in lc_addresses:
            lc_addresses.append(address)

        address_entry["values"] = lc_addresses

    def remove_address_from_access_class(
        self, address: str, access_class: str = "allow"
    ) -> None:
        """Removes an address from an address list (either allow or deny)i."""
        address = address.lower()

        if not self.asset._credentials or access_class not in self.asset._credentials:
            return

        address_entry = self.get_address_entry_of_class(access_class)

        if not address_entry:
            return

        lc_addresses = self.get_addresses_of_class(access_class)

        if address not in lc_addresses:
            return

        lc_addresses.remove(address)
        address_entry["values"] = lc_addresses

    def get_address_entry_of_class(self, access_class: str = "allow") -> Optional[dict]:
        """Get address credentials entry of the specified access class. access_class = "allow" or "deny"."""
        entries = self.asset._credentials.get(access_class, [])
        address_entries = [entry for entry in entries if entry.get("type") == "address"]
        return address_entries[0] if address_entries else None


def simplify_credential_to_address(credential: Optional[dict]) -> Optional[str]:
    """Extracts address value from credential dictionary."""
    if not credential:
        return None

    if not credential.get("value"):
        raise MalformedCredential("Received empty address.")

    return credential["value"]
