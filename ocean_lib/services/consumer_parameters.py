#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
"""
    Consumer Parameters Class for V4
    To handle the consumerParameters key of a service in a DDO record
"""
import copy
import logging
from distutils.util import strtobool
from typing import Any, Dict, List, Optional

from enforce_typing import enforce_types

logger = logging.getLogger(__name__)


class ConsumerParameters:
    def __init__(
        self,
        name: str,
        type: str,
        label: str,
        required: bool,
        default: str,
        description: str,
        options: Optional[List[str]] = None,
    ) -> None:

        fn_args = locals().copy()
        for attr_name in ConsumerParameters.required_attrs():
            setattr(self, attr_name, fn_args[attr_name])

        if options is not None and not isinstance(options, list):
            raise TypeError("Options should be a list")

        self.options = options

    @classmethod
    def from_dict(
        cls, consumer_parameters_dict: Dict[str, Any]
    ) -> "ConsumerParameters":
        """Create a ConsumerParameters object from a JSON string."""
        cpd = copy.deepcopy(consumer_parameters_dict)
        missing_attributes = [
            x for x in ConsumerParameters.required_attrs() if x not in cpd.keys()
        ]

        if missing_attributes:
            raise TypeError(
                "ConsumerParameters is missing the keys "
                + ", ".join(missing_attributes)
            )

        required = cpd["required"] if "required" in cpd else None

        return cls(
            cpd["name"],
            cpd["type"],
            cpd["label"],
            bool(strtobool(required)) if isinstance(required, str) else required,
            cpd["default"],
            cpd["description"],
            cpd.pop("options", None),
        )

    @enforce_types
    def as_dictionary(self) -> Dict[str, Any]:
        """Return the consume parameters object as a python dictionary."""

        result = {
            attr_name: getattr(self, attr_name)
            for attr_name in ConsumerParameters.required_attrs()
        }

        if self.options is not None:
            result["options"] = self.options

        return result

    @staticmethod
    @enforce_types
    def required_attrs():
        return [
            "name",
            "type",
            "label",
            "required",
            "default",
            "description",
        ]
