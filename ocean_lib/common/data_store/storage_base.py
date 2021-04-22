#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import sqlite3


class StorageBase:
    """
    Provide basic database connection management (connect/close).
    """

    def __init__(self, storage_path):
        self._storage_path = storage_path
        self._conn = None
        if self._storage_path == ":memory:":
            self._conn = sqlite3.connect(self._storage_path)

    def _connect(self):
        if self._storage_path != ":memory:":
            self._conn = sqlite3.connect(self._storage_path)

    def _disconnect(self):
        if self._storage_path != ":memory:":
            self._conn.close()

    def _run_query(self, query, args=None):
        """

        :param query: str the sql query to execute in sqlite3.
        :param args: tuple/list of arguments that go along with the query. Number of arguments
            must match the number of positional `?` in the query string
        :return:
            iterator on rows resulting from the query.
        """
        if not self._conn:
            self._connect()

        cursor = self._conn.cursor()
        result = cursor.execute(query, args or ())
        self._conn.commit()
        return result
