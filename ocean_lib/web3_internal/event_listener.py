#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import logging
import time
from datetime import datetime
from threading import Thread
from typing import Callable, Optional, Union

from enforce_typing import enforce_types
from web3.main import Web3

from ocean_lib.web3_internal.contract_utils import load_contract
from ocean_lib.web3_internal.event_filter import EventFilter

logger = logging.getLogger(__name__)


class EventListener(object):

    """Class representing an event listener."""

    @enforce_types
    def __init__(
        self,
        web3: Web3,
        contract_name: str,
        address: str,
        event_name: str,
        args: Optional[list] = None,
        from_block: Optional[Union[int, str]] = None,
        to_block: Optional[Union[int, str]] = None,
        filters: Optional[dict] = None,
    ) -> None:
        """Initialises EventListener object."""
        contract = load_contract(web3, contract_name, address)
        self.event_name = event_name
        self.event = getattr(contract.events, event_name)
        self.filters = filters if filters else {}
        self.from_block = from_block if from_block is not None else "latest"
        self.to_block = to_block if to_block is not None else "latest"
        self.event_filter = self.make_event_filter()
        self.timeout = 600  # seconds
        self.args = args

    @enforce_types
    def make_event_filter(self) -> EventFilter:
        """Create a new event filter."""
        event_filter = EventFilter(
            self.event(),
            argument_filters=self.filters,
            from_block=self.from_block,
            to_block=self.to_block,
        )
        return event_filter

    @enforce_types
    def listen_once(
        self,
        callback: Optional[Callable] = None,
        timeout: Optional[int] = None,
        timeout_callback: Optional[Callable] = None,
        start_time: Optional[float] = None,
        blocking: Optional[bool] = False,
    ) -> None:
        """Listens once for event.

        :param callback: a callback function that takes one argument the event dict
        :param timeout: float timeout in seconds
        :param timeout_callback: a callback function when timeout expires
        :param start_time: float start time in seconds, defaults to current time and is used
            for calculating timeout
        :param blocking: bool blocks this call until the event is detected
        :return: event if blocking is True and an event is received, otherwise returns None
        """
        if blocking:
            assert (
                timeout is not None
            ), "`timeout` argument is required when `blocking` is True."

        events = []
        original_callback = callback

        def _callback(event: dict, *args) -> None:
            events.append(event)
            if original_callback:
                original_callback(event, *args)

        if blocking:
            callback = _callback

        # TODO Review where to close this threads.
        Thread(
            target=self.watch_one_event,
            args=(
                self.event_filter,
                callback,
                timeout_callback,
                timeout if timeout is not None else self.timeout,
                self.args,
                start_time,
            ),
            daemon=True,
        ).start()
        if blocking:
            while not events:
                time.sleep(0.2)

            return events

        return None

    @staticmethod
    @enforce_types
    def watch_one_event(
        event_filter: EventFilter,
        callback: Callable,
        timeout_callback: Optional[Callable],
        timeout: int,
        args: list,
        start_time: Optional[int] = None,
    ) -> None:
        """
        Start to watch one event.

        :param event_filter:
        :param callback:
        :param timeout_callback:
        :param timeout:
        :param args:
        :param start_time:
        :return:
        """
        if timeout and not start_time:
            start_time = int(datetime.now().timestamp())

        if not args:
            args = []

        while True:
            try:
                events = event_filter.get_all_entries()
                if events:
                    callback(events[0], *args)
                    return

            except (ValueError, Exception) as err:
                # ignore error, but log it
                logger.debug(f"Got error grabbing keeper events: {str(err)}")

            time.sleep(0.5)
            if timeout:
                elapsed = int(datetime.now().timestamp()) - start_time
                if elapsed > timeout:
                    if timeout_callback is not None:
                        timeout_callback(*args)
                    elif callback is not None:
                        callback(None, *args)
                    break
