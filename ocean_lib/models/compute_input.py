#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#


from typing import Dict, Optional, Union


class ComputeInput:
    def __init__(
        self, did: Optional[str], transfer_tx_id: str, service_id: Union[str, int]
    ) -> None:
        """Initialise and validate arguments."""
        assert (
            did and transfer_tx_id and service_id is not None
        ), f"bad argument values: did={did}, transfer_ts_id={transfer_tx_id}, service_id={service_id}"

        self.did = did
        self.transfer_tx_id = transfer_tx_id
        self.service_id = service_id

    def as_dictionary(self) -> Dict[str, str]:
        return {
            "documentId": self.did,
            "transferTxId": self.transfer_tx_id,
            "serviceId": self.service_id,
        }
