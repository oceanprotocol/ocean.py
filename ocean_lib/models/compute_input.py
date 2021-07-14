#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#


class ComputeInput:
    def __init__(self, did, transfer_tx_id, service_id, userdata=None):
        """Initialise and validate arguments."""
        assert (
            did and transfer_tx_id and service_id is not None
        ), f"bad argument values: did={did}, transfer_ts_id={transfer_tx_id}, service_id={service_id}"

        self.did = did
        self.transfer_tx_id = transfer_tx_id
        self.service_id = service_id
        self.userdata = userdata

    def as_dictionary(self):
        res = {
            "documentId": self.did,
            "transferTxId": self.transfer_tx_id,
            "serviceId": self.service_id,
        }

        if self.userdata:
            res["userdata"] = self.userdata

        return res
