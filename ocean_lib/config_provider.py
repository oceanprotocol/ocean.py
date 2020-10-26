#  Copyright 2018 Ocean Protocol Foundation
#  SPDX-License-Identifier: Apache-2.0


class ConfigProvider:
    """Provides the Config instance."""
    _config = None

    @staticmethod
    def get_config():
        """ Get a Config instance."""
        if not ConfigProvider._config:
            raise AssertionError(f'set_config first.')
        return ConfigProvider._config

    @staticmethod
    def set_config(config):
        """
         Set a Config instance.

        :param config: Config
        :return:  New Config instance.
        """
        ConfigProvider._config = config
