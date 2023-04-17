#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
from typing import Any, Optional

from enforce_typing import enforce_types

from ocean_lib.models.datatoken1 import Datatoken1

class Datatoken3(Datatoken1):
    CONTRACT_NAME = "ERC20Template3" #switch to ERC20Template3 when ready

    #placeholders for now
    def submit_predval(self, prediction, stake, predict_blocknum):
        pass

    def get_agg_predval(self, stake, blocknum):
        pass

    def submit_trueval_and_payout(self, blocknum, prediction):
        pass
    
