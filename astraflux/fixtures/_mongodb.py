# -*- encoding: utf-8 -*-

import logging
import pymongo
from typing import Dict, Any, List, Tuple

from astraflux.definitions.constants import *
from astraflux.core import global_manager


class MongoDBClient:
    """
    A base class for interacting with a MongoDB collection.

    This class encapsulates common MongoDB operations such as find, insert, update,
    and delete. It manages the connection pool and provides a simplified interface
    for database interactions. It is designed to be inherited by subclasses that
    specify a particular collection.
    """
    _collection_name = None  # Must be overridden by subclasses

    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize the MongoDB client and establish a connection pool.

        Args:
            config (Dict[str, Any]): A configuration dictionary containing MongoDB
                connection parameters. Expected keys include 'host', 'port', 'username',
                'password', 'database', and 'max_connections'. Default values are used
                if these keys are not present.
            logger (logging.Logger): A logger instance for recording runtime status,
                errors, and debugging information.

        Raises:
            pymongo.errors.ConnectionFailure: If a connection to the MongoDB server
                cannot be established within the specified timeout.
            pymongo.errors.ConfigurationError: If there is a configuration error,
                such as an invalid connection string.
        """
        self.logger = logger
        self._host = config.get(MONGODB.CONFIG.HOST.value, MONGODB.DEFAULT.HOST.value)
        self._port = config.get(MONGODB.CONFIG.PORT.value, MONGODB.DEFAULT.PORT.value)
        self._username = config.get(MONGODB.CONFIG.USERNAME.value, MONGODB.DEFAULT.USERNAME.value)
        self._password = config.get(MONGODB.CONFIG.PASSWORD.value, MONGODB.DEFAULT.PASSWORD.value)
        self._database = config.get(MONGODB.CONFIG.DATABASE.value, MONGODB.DEFAULT.DATABASE.value)
        self._max_connections = config.get(MONGODB.CONFIG.MAX_CONNECTIONS.value, MONGODB.DEFAULT.MAX_CONNECTIONS.value)

        self._max_pool_size = int(self._max_connections)

        connection_string = f"mongodb://{self._username}:{self._password}@{self._host}:{self._port}/"

        self._connection_pool = pymongo.MongoClient(
            connection_string,
            maxPoolSize=self._max_pool_size,
            minPoolSize=1,
            connectTimeoutMS=5000,
            socketTimeoutMS=30000,
            serverSelectionTimeoutMS=5000,
            retryWrites=True,
            retryReads=True
        )

        self._collection = self._connection_pool[self._database][self._collection_name]

    def find_one_and_update(self, query: Dict, data: Dict, upsert: bool = True):
        """
        Finds a single document and updates it, or inserts a new one if not found.

        Args:
            query (Dict): A dictionary specifying the filter to find the document.
            data (Dict): A dictionary containing the fields and values to update using
                the `$set` operator.
            upsert (bool, optional): If True, creates a new document when no match is
                found. Defaults to True.
        """
        self._collection.find_one_and_update(query, {"$set": data}, upsert=upsert)

    def array_push(self, query: Dict, data: Dict):
        """
        Appends a value to an array field in a document.

        Args:
            query (Dict): A dictionary specifying the filter to find the document.
            data (Dict): A dictionary where the key is the array field name and the
                value is the item to append, used with the `$push` operator.
        """
        self._collection.find_one_and_update(query, {"$push": data})

    def array_pull(self, query: Dict, data: Dict):
        """
        Removes a value from an array field in a document.

        Args:
            query (Dict): A dictionary specifying the filter to find the document.
            data (Dict): A dictionary where the key is the array field name and the
                value is the item to remove, used with the `$pull` operator.
        """
        self._collection.find_one_and_update(query, {"$pull": data})

    def insert(self, data: Dict) -> None:
        """
        Inserts a single document into the collection.

        Args:
            data (Dict): A dictionary representing the document to be inserted.
        """
        self._collection.insert_one(data)

    def delete(self, query: Dict) -> None:
        """
        Deletes all documents matching the given query filter.

        Args:
            query (Dict): A dictionary specifying the filter to select documents for deletion.
        """
        self._collection.delete_many(query)

    def find(self, query: Dict, fields: Dict = None) -> List[Dict]:
        """
        Retrieves all documents matching the provided query filter.

        This method can optionally project specific fields to include or exclude in the result.

        Args:
            query (Dict): A dictionary specifying the query filter. Use an empty dict `{}`
                to retrieve all documents in the collection.
            fields (Dict, optional): A dictionary specifying the field projection. Use 1 to
                include a field and 0 to exclude it. Mixing include and exclude is not allowed
                except for the `_id` field. Defaults to None, which returns all fields.

        Returns:
            List[Dict]: A list of dictionaries, each representing a document that matches
                the query. Returns an empty list if no matches are found.
        """
        fields = fields or {}
        cursor = self._collection.find(query, fields)
        return list(cursor)

    def count(self, query: Dict) -> int:
        """
        Counts the number of documents matching the provided query filter.

        This method is efficient for large collections as it uses the metadata where possible.

        Args:
            query (Dict): A dictionary specifying the query filter. Use an empty dict `{}`
                to count all documents in the collection.

        Returns:
            int: The number of documents that match the query filter.
        """
        return self._collection.count_documents(filter=query)

    def find_paginated(self, query: Dict, fields: Dict = None, limit: int = 10, skip: int = 0,
                       sort_field: str = 'create_time', sort_order: int = -1) -> Tuple[int, List[Dict]]:
        """
        Retrieves a paginated and sorted subset of documents matching the query.

        This method is ideal for implementing pagination in applications, as it returns
        both the data for the current page and the total number of matching documents.

        Args:
            query (Dict): A dictionary specifying the query filter.
            fields (Dict, optional): A dictionary specifying the field projection.
                Defaults to None.
            limit (int, optional): The maximum number of documents to return per page.
                Defaults to 10.
            skip (int, optional): The number of documents to skip before starting to return
                results. Used to navigate to subsequent pages. Defaults to 0 (first page).
            sort_field (str, optional): The name of the field by which to sort the results.
                Defaults to 'create_time'.
            sort_order (int, optional): The sort direction. Use 1 for ascending order and
                -1 for descending order. Defaults to -1 (descending).

        Returns:
            Tuple[int, List[Dict]]: A tuple containing:
                - int: The total number of documents that match the query (for pagination controls).
                - List[Dict]: A list of documents for the current page.
        """
        fields = fields or {}
        total = self.count(query)
        cursor = self._collection.find(query, fields) \
            .sort(sort_field, sort_order) \
            .limit(limit) \
            .skip(skip)
        return total, list(cursor)


class TASKS(MongoDBClient):
    """
    A concrete implementation of `MongoDBClient` for interacting with the 'TASKS' collection.

    This class inherits all database operations from `MongoDBClient` and is specifically
    configured to target the 'TASKS' collection within the MongoDB database.
    """
    _collection_name = 'TASKS'

    def __init__(self, config, logger):
        """
        Initializes the TASKS collection client.

        Args:
            config (Dict[str, Any]): The MongoDB configuration dictionary.
            logger (logging.Logger): The logger instance for this client.
        """
        super(TASKS, self).__init__(config, logger)


@global_manager.register_fixture(name="fixture_mongodb_tasks", scope=Scope.GLOBAL)
def _mongodb_tasks(fixture_config, fixture_logger):
    """
    A factory function to create and register a `TASKS` client as a global fixture.

    This function is decorated to be registered with the `global_manager`, making the
    `TASKS` client instance available application-wide as a singleton.

    Args:
        fixture_config: The global application configuration fixture containing Redis settings
        fixture_logger: The global logging fixture for creating Redis-specific loggers

    Yields:
        TASKS: An instance of the `TASKS` client, ready for use.
    """

    _mongodb_config = fixture_config[MONGODB.CONFIG.KEY.value]
    _logger = fixture_logger.get_logger(PROJECT.NAME.value, RABBITMQ.CONFIG.KEY.value)

    _mongodb_producer = TASKS(
        config=_mongodb_config,
        logger=_logger,
    )

    yield _mongodb_producer
