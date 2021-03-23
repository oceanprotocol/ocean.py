#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
import time

from ocean_lib.web3_internal.web3_provider import Web3Provider

logger = logging.getLogger(__name__)


class EventFilter:
    def __init__(
        self,
        event_name,
        event,
        argument_filters,
        from_block,
        to_block,
        poll_interval=None,
    ):
        """Initialises EventFilter."""
        self.event_name = event_name
        self.event = event
        self.argument_filters = argument_filters
        self.block_range = (from_block, to_block)
        self._filter = None
        self._poll_interval = poll_interval if poll_interval else 0.5
        self._create_filter()

    @property
    def filter_id(self):
        return self._filter.filter_id if self._filter else None

    def uninstall(self):
        Web3Provider.get_web3().eth.uninstallFilter(self._filter.filter_id)

    def set_poll_interval(self, interval):
        self._poll_interval = interval
        if self._filter and self._poll_interval is not None:
            self._filter.poll_interval = self._poll_interval

    def recreate_filter(self):
        self._create_filter()

    def _create_filter(self):
        self._filter = self.event().createFilter(
            fromBlock=self.block_range[0],
            toBlock=self.block_range[1],
            argument_filters=self.argument_filters,
        )
        if self._poll_interval is not None:
            self._filter.poll_interval = self._poll_interval

    def get_new_entries(self, max_tries=1):
        return self._get_entries(self._filter.get_new_entries, max_tries=max_tries)

    def get_all_entries(self, max_tries=1):
        return self._get_entries(self._filter.get_all_entries, max_tries=max_tries)

    def _get_entries(self, entries_getter, max_tries=1):
        i = 0
        while i < max_tries:
            try:
                logs = entries_getter()
                if logs:
                    logger.debug(
                        f"found event logs: event-name={self.event_name}, "
                        f"range={self.block_range}, "
                        f"logs={logs}"
                    )
                    return logs
            except ValueError as e:
                if "Filter not found" in str(e):
                    logger.debug(
                        f"recreating filter (Filter not found): event={self.event_name}, "
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
