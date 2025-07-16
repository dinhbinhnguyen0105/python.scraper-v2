# src/services/base_service.py
from typing import List, Any, Dict, Optional
from contextlib import contextmanager
from PyQt6.QtSql import QSqlQuery, QSqlDatabase

from src import my_constants as constants


@contextmanager
def transaction(db: QSqlDatabase):
    """Context manager for database transactions with automatic rollback on exception."""
    if not db.transaction():
        print("[DB_TRANSACTION] Failed to start transaction.")
        raise RuntimeError("Failed to start transaction")
    try:
        yield
        if not db.commit():
            print("[DB_TRANSACTION] Failed to commit transaction.")
            raise RuntimeError("Failed to commit transaction")
    except Exception:
        if db.isOpen():
            db.rollback()
        raise


class BaseSerivce:
    def __init__(self, connection_name: str):
        self._connection_name = connection_name
        self._db: Optional[QSqlDatabase] = None
        self._query: Optional[QSqlQuery] = None

    def _initialize_database_connection(self):
        if not QSqlDatabase.contains(self._connection_name):
            error_message = (
                f"Database connection '{self._connection_name}' does not exist. "
                f"Please add it using QSqlDatabase.addDatabase() before initializing service."
            )
            raise ConnectionError(error_message)

        self._db = QSqlDatabase.database(self._connection_name)
        if not self._db.isValid():
            error_message = f"Database connection '{self._connection_name}' is invalid."
            raise ConnectionError(error_message)
        if not self._db.isOpen():
            error_message = (
                f"Failed to open database connection '{self._connection_name}': "
                f"{self._db.lastError().text()}"
            )
            raise ConnectionError(error_message)
        else:
            print(f"Database connection '{self._connection_name}' opened successfully.")

    def execute_query(
        self, sql_query: str, params: Optional[Dict[str, Any]] = None
    ) -> bool:
        if not self._query or not self._db.isOpen():
            print(
                f"Cannot execute query: Database connection '{self._connection_name}' "
                f"is not open or query object is not initialized."
            )
            return False
        self._query.clear()

        if params:
            self._query.prepare(sql_query)
            for key, value in params.items():
                self._query.bindValue(key, value)
            if not self._query.exec():
                print(
                    f"Query execution failed for connection '{self._connection_name}': "
                    f"{self._query.lastError().text()}"
                )
                print(f"SQL: {sql_query}, Params: {params}")
                return False
        else:
            if not self._query.exec(sql_query):
                print(
                    f"Query execution failed for connection '{self._connection_name}': "
                    f"{self._query.lastError().text()}"
                )
                print(f"SQL: {sql_query}")
                return False
        return True

    def fetch_all(
        self, sql_query: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        results = []
        if self.execute_query(sql_query=sql_query, params=params):
            record = self._query.record()
            while self._query.next():
                row_data = {}
                for i in range(record.count()):
                    field_name = record.fieldName(i)
                    field_value = self._query.value(i)
                    row_data[field_name] = field_value
                results.append(row_data)
        return results

    def fetch_one(
        self, sql_query: str, params: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        result = None
        if self.execute_query(sql_query, params=params):
            record = self._query.record()
            while self._query.next():
                row_data = {}
                for i in range(record.count()):
                    field_name = record.fieldName(i)
                    field_value = self._query.value(i)
                    row_data[field_name] = field_value
                return row_data
        return result

    def get_last_insert_id(self) -> Optional[int]:
        if not self._query or not self._db.isOpen():
            print(
                f"Cannot get last insert ID: Database connection '{self._connection_name}' "
                f"is not open or query object is not initialized."
            )
            return None
        return self._query.lastInsertId()

    def get_database(self) -> QSqlDatabase:
        if not self._db:
            print(
                f"Attempted to get database object for '{self._connection_name}' before it was initialized. Attempting to re-initialize."
            )
            self._initialize_database_connection()
        return self._db

    def get_query(self) -> QSqlQuery:
        if not self._query:
            print(
                f"Attempted to get query object for '{self._connection_name}' before it was initialized. Attempting to re-initialize."
            )
            self._initialize_database_connection()
        return self._query
