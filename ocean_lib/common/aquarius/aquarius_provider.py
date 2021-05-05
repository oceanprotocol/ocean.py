#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from .aquarius import Aquarius


class AquariusProvider:
    """Provides the Aquarius instance."""

    _aquarius_class = Aquarius

    @staticmethod
    def get_aquarius(url):
        """Get an Aquarius instance."""
        return AquariusProvider._aquarius_class(url)

    @staticmethod
    def set_aquarius_class(aquarius_class):
        """
         Set an Aquarius class

        :param aquarius_class: Aquarius or similar compatible class
        """
        AquariusProvider._aquarius_class = aquarius_class
