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


class EventFilter:
    @enforce_types
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
        self.address = address
        self.topics = topics
        self._create_filter()

    @property
    @enforce_types
    def filter_id(self) -> Optional[str]:
        return self.filter.filter_id if self.filter else None

    @enforce_types
    def uninstall(self) -> None:
        self.event.web3.eth.uninstall_filter(self.filter.filter_id)

    @enforce_types
    def recreate_filter(self) -> None:
        self._create_filter()

    @enforce_types
    def _create_filter(self) -> None:
        self.filter = self.event.createFilter(
            fromBlock=self.block_range[0],
            toBlock=self.block_range[1],
            address=self.address,
            topics=self.topics,
            argument_filters=self.argument_filters,
        )

    @enforce_types
    def get_new_entries(self, max_tries: Optional[int] = 1) -> list:
        return self._get_entries(self.filter.get_new_entries, max_tries=max_tries)

    @enforce_types
    def get_all_entries(self, max_tries: Optional[int] = 1) -> list:
        return self._get_entries(self.filter.get_all_entries, max_tries=max_tries)

    @enforce_types
    def _get_entries(
        self, entries_getter: Callable, max_tries: Optional[int] = 1
    ) -> list:
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
