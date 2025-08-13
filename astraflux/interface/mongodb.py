# -*- encoding: utf-8 -*-

from astraflux.inject import inject_implementation

__all__ = ['initialization_mongo', 'mongodb_node', 'mongodb_task', 'mongodb_services']


class MongoClient:
    """
    This class is used to interact with a MongoDB database,
    providing a series of methods to operate on database collections.
    """

    def update_many(self, query: dict, update_data: dict, upsert=False) -> None:
        """
        Update multiple documents in the collection that match the query.

        Args:
            query (dict): A dictionary specifying the query criteria.
            update_data (dict): A dictionary containing the data to update.
            upsert (bool, optional): If True, insert a new document if no documents match the query. Defaults to False.

        Returns:
            None
        """

    def push_many(self, query: dict, update_data: dict, upsert=False) -> None:
        """
        Push data to an array field in multiple documents that match the query.

        Args:
            query (dict): A dictionary specifying the query criteria.
            update_data (dict): A dictionary containing the data to push.
            upsert (bool, optional): If True, insert a new document if no documents match the query. Defaults to False.

        Returns:
            None
        """

    def push_one(self, query: dict, update_data: dict, upsert=False) -> None:
        """
        Push data to an array field in the first document that matches the query.

        Args:
            query (dict): A dictionary specifying the query criteria.
            update_data (dict): A dictionary containing the data to push.
            upsert (bool, optional): If True, insert a new document if no documents match the query. Defaults to False.

        Returns:
            None
        """

    def pull_one(self, query: dict, update_data: dict) -> None:
        """
        Pull data from an array field in the first document that matches the query.

        Args:
            query (dict): A dictionary specifying the query criteria.
            update_data (dict): A dictionary containing the data to pull.

        Returns:
            None
        """

    def insert_data(self, data: dict) -> None:
        """
        Insert a single document into the collection.

        Args:
            data (dict): A dictionary containing the data to insert.

        Returns:
            None
        """

    def delete_data(self, query: dict) -> None:
        """
        Delete multiple documents from the collection that match the query.

        Args:
            query (dict): A dictionary specifying the query criteria.

        Returns:
            None
        """

    def query_all(self, query: dict, field: dict) -> list[dict]:
        """
        Retrieve all documents from the collection that match the query.

        Args:
            query (dict): A dictionary specifying the query criteria.
            field (dict): A dictionary specifying the fields to include or exclude in the result.

        Returns:
            list: A list of documents that match the query.
        """

    def query_count(self, query) -> int:
        """
        Get the count of documents in the collection that match the query.

        Args:
            query (dict): A dictionary specifying the query criteria.

        Returns:
            int: The count of documents that match the query.
        """

    def query_list_sort(self, query: dict, field: dict, limit: int, skip_no: int,
                        sort_field: str = 'create_time', sort: int = -1) -> tuple[int, list[dict]]:
        """
        Retrieve a list of documents from the collection based on the given query,
        field projection, limit, skip, and sorting criteria.

        Args:
            query (dict): A dictionary specifying the query criteria.
            field (dict): A dictionary specifying the fields to include or exclude in the result.
            limit (int): The maximum number of documents to return.
            skip_no (int): The number of documents to skip before starting to return results.
            sort_field (str, optional): The field to sort the results by. Defaults to 'update_time'.
            sort (int, optional): The sorting order. -1 for descending, 1 for ascending. Defaults to -1.

        Returns:
            pymongo.cursor.Cursor: A cursor object that can be iterated over to access the documents.
        """

    def query_one(self, query: dict, field: dict) -> list[dict]:
        """
        Retrieve a list of documents from the collection based on the given query,
        field projection, limit, skip, and sorting criteria.

        Args:
            query (dict): A dictionary specifying the query criteria.
            field (dict): A dictionary specifying the fields to include or exclude in the result.

        Returns:
            pymongo.cursor.Cursor: A cursor object that can be iterated over to access the documents.
        """


@inject_implementation()
def initialization_mongo(config: dict):
    """
    Initialize a MongoDB database connection with a MongoDB configuration.
    """


@inject_implementation()
def mongodb_node() -> MongoClient:
    """
    Generate a MongoDB node with a MongoDB configuration.
    """


@inject_implementation()
def mongodb_task() -> MongoClient:
    """
    Generate a MongoDB task with a MongoDB configuration.
    """


@inject_implementation()
def mongodb_services() -> MongoClient:
    """
    Generate a MongoDB services with a MongoDB configuration.
    """
