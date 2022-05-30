#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enforce_typing import enforce_types

from ocean_lib.models.bconst import BConst


class BFactory(BConst):
    CONTRACT_NAME = "BFactory"

    EVENT_BPOOL_CREATED = "BPoolCreated"
    EVENT_POOL_TEMPLATE_ADDED = "PoolTemplateAdded"
    EVENT_POOL_TEMPLATE_REMOVED = "PoolTemplateRemoved"

    @property
    def event_BPoolCreated(self):
        return self.events.BPoolCreated()

    @property
    def event_PoolTemplateAdded(self):
        return self.events.PoolTemplateAdded()

    @property
    def event_PoolTemplateRemoved(self):
        return self.events.PoolTemplateRemoved()

    @enforce_types
    def is_pool_template(self, pool_template) -> bool:
        return self.contract.caller.isPoolTemplate(pool_template)
