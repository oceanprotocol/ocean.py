#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
import time
from typing import Any, Callable, Optional, Union

from enforce_typing import enforce_types
from web3.contract import ContractEvent

logger = logging.getLogger(__name__)


@enforce_types
class EventFilter:
    def __init__(
        self,
        event: ContractEvent,
        argument_filters: dict = None,
        from_block: Optional[Union[int, str]] = None,
        to_block: Optional[Union[int, str]] = None,
        address: Optional[str] = None,
        topics: Any = None,
    ) -> None:
        """Initialises EventFilter."""
        self.event = event
        self.argument_filters = argument_filters
        self.block_range = (from_block, to_block)
        self._filter = None
        self.address = address
        self.topics = topics
        self._create_filter()

    @property
    def filter_id(self) -> Optional[str]:
        return self._filter.filter_id if self._filter else None

    def uninstall(self) -> None:
        self.event.web3.eth.uninstall_filter(self._filter.filter_id)

    def recreate_filter(self) -> None:
        self._create_filter()

    def _create_filter(self) -> None:
        self._filter = self.event.createFilter(
            fromBlock=self.block_range[0],
            toBlock=self.block_range[1],
            address=self.address,
            topics=self.topics,
            argument_filters=self.argument_filters,
        )

    def get_new_entries(self, max_tries: int = 1) -> list:
        return self._get_entries(self._filter.get_new_entries, max_tries=max_tries)

    def get_all_entries(self, max_tries: int = 1) -> list:
        return self._get_entries(self._filter.get_all_entries, max_tries=max_tries)

    def _get_entries(self, entries_getter: Callable, max_tries: int = 1) -> list:
        i = 0
        while i < max_tries:
            try:
                logs = entries_getter()
                if logs:
                    logger.debug(
                        f"found event logs: event-name={self.event.event_name}, "
                        f"range={self.block_range}, "
                        f"logs={logs}"
                    )
                    return logs
            except ValueError as e:
                if "Filter not found" in str(e):
                    logger.debug(
                        f"recreating filter (Filter not found): event={self.event.event_name}, "
                        f"arg-filter={self.argument_filters}, from/to={self.block_range}"
                    )
                    time.sleep(1)
                    self._create_filter()
                else:
                    raise

            i += 1
            if max_tries > 1 and i < max_tries:
                time.sleep(0.5)

        return []
