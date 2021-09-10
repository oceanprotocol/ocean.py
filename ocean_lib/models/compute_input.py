#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#


from typing import Dict, Optional, Union

from enforce_typing import enforce_types


class ComputeInput:
    @enforce_types
    def __init__(
        self,
        did: Optional[str],
        transfer_tx_id: str,
        service_id: Union[str, int],
        userdata: Optional[Dict] = None,
    ) -> None:
        """Initialise and validate arguments."""
        assert (
            did and transfer_tx_id and service_id is not None
        ), f"bad argument values: did={did}, transfer_ts_id={transfer_tx_id}, service_id={service_id}"

        if userdata:
            assert isinstance(userdata, dict), "Userdata must be a dictionary."

        self.did = did
        self.transfer_tx_id = transfer_tx_id
        self.service_id = service_id
        self.userdata = userdata

    @enforce_types
    def as_dictionary(self) -> Dict[str, Union[str, Dict]]:
        res = {
            "documentId": self.did,
            "transferTxId": self.transfer_tx_id,
            "serviceId": self.service_id,
        }

        if self.userdata:
            res["userdata"] = self.userdata

        return res
