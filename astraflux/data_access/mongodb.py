# -*- encoding: utf-8 -*-
import pymongo
from typing import Optional, Dict, List, Tuple

from astraflux.definitions.constants import *
from astraflux.interface.definitions import get_mongo_uri


class MongoDBCollector:
    """
    MongoDB Collection Operation Wrapper Class.

    This class encapsulates core CRUD (Create, Read, Update, Delete) operations for MongoDB collections,
    supports array manipulation (push/pull), and implements instance caching by collection name to avoid
    redundant connections and improve performance.

    Subclasses must specify the `_collection_name` class attribute to bind to a specific MongoDB collection.
    """
    _instance_map: Dict[str, 'MongoDBCollector'] = {}
    _collection_name: Optional[str] = None

    def __new__(cls, *args, **kwargs):
        """
        Singleton Pattern Implementation by Collection Name.

        Ensures only one instance exists per collection to avoid duplicate database connections.
        Creates a new instance only if it doesn't exist in the cache.

        Returns:
            MongoDBCollector: Cached or newly created instance for the target collection.
        """
        if cls._collection_name not in cls._instance_map:
            instance = super().__new__(cls)
            cls._instance_map[cls._collection_name] = instance
        return cls._instance_map[cls._collection_name]

    def __init__(self):
        """
        Initialize MongoDB Client and Collection Connection.

        Establishes a connection to MongoDB using the global URI and binds to the target collection.
        Uses `_client_initialized` flag to prevent repeated initialization on instance reuse.
        """
        if not hasattr(self, '_client_initialized'):
            mongo_uri = get_mongo_uri()
            self._client = pymongo.MongoClient(mongo_uri, connect=False)
            self._collection = self._client[PROJECT_NAME][self._collection_name]
            self._client_initialized = True

    def update(self, query: Dict, data: Dict, upsert: bool = False) -> None:
        """
        Update Multiple Documents Matching the Query.

        Uses MongoDB's $set operator to update specified fields without overwriting the entire document.
        Supports upsert (insert new document if no match is found).

        Args:
            query (Dict): Query filter to match target documents (e.g., {"task_id": "123456"}).
            data (Dict): Fields to update (e.g., {"status": "completed", "update_time": "2024-01-01"}).
            upsert (bool, optional): Whether to insert a new document if no match exists. Defaults to False.

        Returns:
            None
        """
        self._collection.update_many(query, {"$set": data}, upsert=upsert)

    def array_push(self, query: Dict, data: Dict, single: bool = False, upsert: bool = False) -> None:
        """
        Push Data to Array Fields in Documents.

        Uses MongoDB's $push operator to add elements to array-type fields. Supports single or multiple documents.

        Args:
            query (Dict): Query filter to match target documents (e.g., {"user_id": "789"}).
            data (Dict): Array fields and values to push (e.g., {"tags": "urgent", "subtasks": {"id": "sub_1"}}).
            single (bool, optional): Whether to update only the first matching document. Defaults to False (update all).
            upsert (bool, optional): Whether to insert a new document if no match exists. Defaults to False.

        Returns:
            None
        """
        if single:
            self._collection.find_one_and_update(query, {"$push": data}, upsert=upsert)
        else:
            self._collection.update_many(query, {"$push": data}, upsert=upsert)

    def array_pull(self, query: Dict, data: Dict, single: bool = True) -> None:
        """
        Remove Data from Array Fields in Documents.

        Uses MongoDB's $pull operator to remove elements from array-type fields. Supports single or multiple documents.

        Args:
            query (Dict): Query filter to match target documents (e.g., {"user_id": "789"}).
            data (Dict): Array fields and values to remove (e.g., {"tags": "urgent", "subtasks": {"id": "sub_1"}}).
            single (bool, optional): Whether to update only the first matching document.
                Defaults to True (update first).

        Returns:
            None
        """
        if single:
            self._collection.find_one_and_update(query, {"$pull": data})
        else:
            self._collection.update_many(query, {"$pull": data})

    def insert(self, data: Dict) -> None:
        """
        Insert a Single Document into the Collection.

        Adds a new document to the target collection. The document must be a valid MongoDB BSON-serializable dict.

        Args:
            data (Dict): Document to insert (e.g., {"task_id": "123", "name": "Task A", "status": "pending"}).

        Returns:
            None
        """
        self._collection.insert_one(data)

    def delete(self, query: Dict) -> None:
        """
        Delete Multiple Documents Matching the Query.

        Removes all documents that match the query filter. Use with caution to avoid accidental data loss.

        Args:
            query (Dict): Query filter to match documents to delete (e.g., {"expired": True}).

        Returns:
            None
        """
        self._collection.delete_many(query)

    def find(self, query: Dict, fields: Dict = None) -> List[Dict]:
        """
        Query All Documents Matching the Filter.

        Retrieves all documents that satisfy the query, with optional field projection to include/exclude fields.

        Args:
            query (Dict): Query filter (e.g., {"status": "running"}). Use {} to retrieve all documents.
            fields (Dict, optional): Field projection (e.g., {"_id": 0, "task_id": 1, "status": 1}).
                - 1: Include the field
                - 0: Exclude the field (cannot mix 1 and 0 except for _id)
                Defaults to None (return all fields).

        Returns:
            List[Dict]: List of matching documents (empty list if no matches).
        """
        fields = fields or {}
        cursor = self._collection.find(query, fields)
        return list(cursor)

    def find_one(self, query: Dict, fields: Dict = None) -> Optional[Dict]:
        """
        Query a Single Document Matching the Filter.

        Retrieves the first document that matches the query filter (ordered by insertion time by default).

        Args:
            query (Dict): Query filter (e.g., {"task_id": "123456"}).
            fields (Dict, optional): Field projection (same as `find` method). Defaults to None.

        Returns:
            Optional[Dict]: Matching document (None if no match is found).
        """
        fields = fields or {}
        return self._collection.find_one(query, fields)

    def count(self, query: Dict) -> int:
        """
        Count Documents Matching the Query.

        Returns the total number of documents that satisfy the query filter (supports large collections efficiently).

        Args:
            query (Dict): Query filter (e.g., {"queue": "task_queue_1"}). Use {} to count all documents.

        Returns:
            int: Number of matching documents.
        """
        return self._collection.count_documents(filter=query)

    def find_paginated(self, query: Dict, fields: Dict = None, limit: int = 10, skip: int = 0,
                       sort_field: str = 'create_time', sort_order: int = -1) -> Tuple[int, List[Dict]]:
        """
        Paginated Query with Sorting.

        Retrieves a paginated subset of documents with specified sorting, returns total count and current page data.
        Ideal for large datasets to avoid loading all documents at once.

        Args:
            query (Dict): Query filter (e.g., {"status": "completed"}).
            fields (Dict, optional): Field projection. Defaults to None.
            limit (int, optional): Maximum number of documents per page. Defaults to 10.
            skip (int, optional): Number of documents to skip (for pagination). Defaults to 0 (first page).
            sort_field (str, optional): Field to sort by (e.g., "create_time", "priority"). Defaults to 'create_time'.
            sort_order (int, optional): Sort direction:
                - 1: Ascending (from oldest to newest)
                - -1: Descending (from newest to oldest)
                Defaults to -1.

        Returns:
            Tuple[int, List[Dict]]:
                - First element: Total number of matching documents (for pagination controls)
                - Second element: List of documents for the current page
        """
        fields = fields or {}
        total = self.count(query)
        cursor = self._collection.find(query, fields) \
            .sort(sort_field, sort_order) \
            .limit(limit) \
            .skip(skip)
        return total, list(cursor)


class NodeMongoDBCollector(MongoDBCollector):
    """
    MongoDB Collector for Node Collection.

    Binds to the "node list" collection (TABLE.KEY_NODE_LIST) to handle node-related data operations.
    Inherits all core operations from MongoDBCollector.
    """
    _collection_name = DEFINITIONS.TABLE.NODE_LIST


class TaskMongoDBCollector(MongoDBCollector):
    """
    MongoDB Collector for Task Collection.

    Binds to the "task list" collection (TABLE.KEY_TASK_LIST) to handle task-related data operations.
    Inherits all core operations from MongoDBCollector.
    """
    _collection_name = DEFINITIONS.TABLE.TASK_LIST


class ServiceMongoDBCollector(MongoDBCollector):
    """
    MongoDB Collector for Service Collection.

    Binds to the "service list" collection (TABLE.KEY_SERVICE_LIST) to handle service-related data operations.
    Inherits all core operations from MongoDBCollector.
    """
    _collection_name = DEFINITIONS.TABLE.SERVICE_LIST


def mongodb_get_node_collector() -> MongoDBCollector:
    """
    Get Instance of NodeMongoDBCollector.

    Provides global access to the node collection operation wrapper.

    Returns:
        MongoDBCollector: Instance of NodeMongoDBCollector for node collection operations.
    """
    return NodeMongoDBCollector()


def mongodb_get_task_collector() -> MongoDBCollector:
    """
    Get Instance of TaskMongoDBCollector.

    Provides global access to the task collection operation wrapper.

    Returns:
        MongoDBCollector: Instance of TaskMongoDBCollector for task collection operations.
    """
    return TaskMongoDBCollector()


def mongodb_get_service_collector() -> MongoDBCollector:
    """
    Get Instance of ServiceMongoDBCollector.

    Provides global access to the service collection operation wrapper.

    Returns:
        MongoDBCollector: Instance of ServiceMongoDBCollector for service collection operations.
    """
    return ServiceMongoDBCollector()
