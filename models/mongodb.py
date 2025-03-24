import os
from typing import Any, Dict, List, Optional, Tuple, Union
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.database import Database
from pymongo.cursor import Cursor

class MongoDB:
    """
    Custom MongoDB manager
    """
    # Constants for sort directions
    ASC = ASCENDING
    DESC = DESCENDING

    def __init__(self, uri: Optional[str] = None, db_name: Optional[str] = None):
        if uri is None:
            load_dotenv()
            uri = os.getenv("MONGODB_URI")
        
        if not uri:
            raise ValueError("MONGODB_URI is not set in the environment variables.")
        
        self.client = MongoClient(uri)
        self._db: Optional[Database] = None

        if db_name is not None:
            self.select_db(db_name)

    @property
    def db(self) -> Optional[Database]:
        """Get current database instance"""
        return self._db

    def select_db(self, db_name):
        """
        Select a database
        """
        self._db = self.client[db_name]
        return self.db
    
    def list_databases(self):
        return self.client.list_database_names()

    def list_collections(self):
        if self._db is None:
            raise ValueError("No database selected. Please select a database first.")
        return self._db.list_collection_names()

    def get_collection(self, collection_name):
        if self._db is None:
            raise ValueError("No database selected. Please select a database first.")
        return self._db[collection_name]
    
    def find(
            self, 
            collection_name: str, 
            query: Dict[str, Any], 
            projection: Optional[Dict[str, Any]] = None,
            sort: Optional[List[tuple]] = None,
            skip: Optional[int] = None,
            limit: Optional[int] = None,
            return_cursor: bool = False
            ) -> Cursor | List[Dict[str, Any]]:
        """
        Find documents in a collection.
        
        Args:
            collection_name: Name of the collection to query.
            query: MongoDB query dictionary.
            projection: Optional projection to specify returned fields.
            sort: Optional list of (field, direction) tuples to sort by.
            skip: Optional number of documents to skip.
            limit: Optional maximum number of documents to return.
            return_cursor: Optional flag to return a cursor instead of a list.
            
        Returns:
            List of matching documents list or a cursor if return_cursor is `True`.
        """
        collection = self.get_collection(collection_name)
        cursor = collection.find(query, projection)
    
        if sort is not None:
            cursor = cursor.sort(sort)
        if skip is not None:
            cursor = cursor.skip(skip)
        if limit is not None:
            cursor = cursor.limit(limit)
        
        if return_cursor:
            return cursor
        
        return list(cursor)
    
    def find_one(
            self, 
            collection_name: str, 
            query: Dict[str, Any], 
            projection: Optional[Dict[str, Any]] = None,
            sort: Optional[List[tuple]] = None
            ):
        """
        Find a single document in a collection.
        
        Args:
            collection_name: Name of the collection to query.
            query: MongoDB query dictionary.
            projection: Optional projection to specify returned fields.
            sort: Optional list of (field, direction) tuples to sort by.
            
        Returns:
            Single matching document or None if not found.
        """
        if sort:
            cursor = self.find(
                collection_name=collection_name,
                query=query,
                projection=projection,
                sort=sort,
                limit=1,
                return_cursor=True
            )
            try:
                return next(cursor)
            except StopIteration:
                return None
        else:
            collection = self.get_collection(collection_name)
            return collection.find_one(query, projection)
        
    def aggregate(
            self, 
            collection_name: str, 
            pipeline: List[Dict[str, Any]],
            return_cursor: bool = False
            ) -> List[Dict[str, Any]] | Cursor:
        """
        Perform an aggregation pipeline on a collection.

        Args:
            collection_name: Name of the collection.
            pipeline: List of aggregation pipeline stages.
            return_cursor: If True, returns the raw cursor instead of a list.
            
        Returns:
            List of aggregation results or cursor if return_cursor is True.
        """
        collection = self.get_collection(collection_name)
        cursor = collection.aggregate(pipeline)
        
        if return_cursor:
            return cursor
        
        return list(cursor)
    
    def insert_one(self, collection_name: str, document: Dict[str, Any]) -> str:
        """
        Insert a document into a collection.
        
        Args:
            collection_name: Name of the collection.
            document: Document to insert.
            
        Returns:
            ID of the inserted document.
        """
        collection = self.get_collection(collection_name)
        result = collection.insert_one(document)
        return str(result.inserted_id)
    
    def insert_many(self, collection_name: str, documents: List[Dict[str, Any]]) -> List[str]:
        """
        Insert multiple documents into a collection.
        
        Args:
            collection_name: Name of the collection.
            documents: List of documents to insert.
            
        Returns:
            List of inserted document IDs.
        """
        collection = self.get_collection(collection_name)
        result = collection.insert_many(documents)
        return [str(doc_id) for doc_id in result.inserted_ids]
    
    def update_one(self, collection_name: str, query: Dict[str, Any], update: Dict[str, Any], upsert: bool = False) -> int:
        """
        Update a single document in a collection.
        
        Args:
            collection_name: Name of the collection.
            query: Query to find document to update.
            update: Update operations to apply.
            upsert: Whether to insert if document doesn't exist.
            
        Returns:
            Number of documents modified.
        """
        collection = self.get_collection(collection_name)
        result = collection.update_one(query, update, upsert=upsert)
        return result.modified_count
    
    def update_many(self, collection_name: str, query: Dict[str, Any], update: Dict[str, Any], upsert: bool = False) -> int:
        """
        Update multiple documents in a collection.
        
        Args:
            collection_name: Name of the collection.
            query: Query to find documents to update.
            update: Update operations to apply.
            upsert: Whether to insert if document doesn't exist.
            
        Returns:
            Number of documents modified.
        """
        collection = self.get_collection(collection_name)
        result = collection.update_many(query, update, upsert=upsert)
        return result.modified_count
    
    def delete_one(self, collection_name: str, query: Dict[str, Any]) -> int:
        """
        Delete a single document from a collection.
        
        Args:
            collection_name: Name of the collection.
            query: Query to find document to delete.
            
        Returns:
            Number of documents deleted.
        """
        collection = self.get_collection(collection_name)
        result = collection.delete_one(query)
        return result.deleted_count
    
    def delete_many(self, collection_name: str, query: Dict[str, Any]) -> int:
        """
        Delete multiple documents from a collection.
        
        Args:
            collection_name: Name of the collection.
            query: Query to find documents to delete.
            
        Returns:
            Number of documents deleted.
        """
        collection = self.get_collection(collection_name)
        result = collection.delete_many(query)
        return result.deleted_count
    
    def count_documents(self, collection_name: str, query: Dict[str, Any]) -> int:
        """
        Count the number of documents in a collection.
        
        Args:
            collection_name: Name of the collection.
            query: Query to filter documents.
            
        Returns:
            Number of documents.
        """
        collection = self.get_collection(collection_name)
        return collection.count_documents(query)
    
    def drop_collection(self, collection_name: str) -> None:
        """
        Drop a collection from the database.
        
        Args:
            collection_name: Name of the collection to drop.
        """
        if self._db is None:
            raise ValueError("No database selected. Use select_db() first.")
            
        self._db.drop_collection(collection_name)
    
    def close(self):
        """Close MongoDB connection"""
        self.client.close()