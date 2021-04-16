#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
"""DID Lib to do DID's and DDO's."""


#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0


class AdditionalInfoMeta(object):
    """Attributes that can enhance the discoverability of a resource."""

    KEY = "additionalInformation"
    VALUES_KEYS = (
        "categories",
        "copyrightHolder",
        "description",
        "inLanguage",
        "links",
        "tags",
        "updateFrequency",
        "structuredMarkup",
        "workExample",
    )
    REQUIRED_VALUES_KEYS = tuple()


class CurationMeta(object):
    """To normalize the different possible rating attributes after a curation process."""

    KEY = "curation"
    VALUES_KEYS = ("rating", "numVotes", "schema", "isListed")
    REQUIRED_VALUES_KEYS = {"rating", "numVotes"}


class MetadataMain(object):
    """The main attributes that need to be included in the Asset Metadata."""

    KEY = "main"
    VALUES_KEYS = {"author", "name", "type", "dateCreated", "license", "price", "files"}
    REQUIRED_VALUES_KEYS = {
        "name",
        "dateCreated",
        "author",
        "license",
        "price",
        "files",
    }


class Metadata(object):
    """Every Asset (dataset, algorithm, etc.) in the Ocean Network has an associated Decentralized
    Identifier (DID) and DID document / DID Descriptor Object (DDO)."""

    REQUIRED_SECTIONS = {MetadataMain.KEY}
    MAIN_SECTIONS = {
        MetadataMain.KEY: MetadataMain,
        CurationMeta.KEY: CurationMeta,
        AdditionalInfoMeta.KEY: AdditionalInfoMeta,
    }

    @staticmethod
    def validate(metadata):
        """Validator of the metadata composition

        :param metadata: conforming to the Metadata accepted by Ocean Protocol, dict
        :return: bool
        """
        # validate required sections and their sub items
        for section_key in Metadata.REQUIRED_SECTIONS:
            if (
                section_key not in metadata
                or not metadata[section_key]
                or not isinstance(metadata[section_key], dict)
            ):
                return False

            section = Metadata.MAIN_SECTIONS[section_key]
            section_metadata = metadata[section_key]
            for subkey in section.REQUIRED_VALUES_KEYS:
                if subkey not in section_metadata or section_metadata[subkey] is None:
                    return False

        return True
