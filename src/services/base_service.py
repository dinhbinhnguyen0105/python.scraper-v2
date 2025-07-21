# src/services/base_service.py
from datetime import datetime
from typing import List, Any, Dict, Optional
from contextlib import contextmanager
from dataclasses import asdict
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


class EnforceAttributeMeta(type):
    def __new__(mcs, name, bases, namespace):
        table_name_attribute = "TABLE_NAME"
        # connection_name_attribute = "CONNECTION_NAME"
        if name != "BaseService":
            if table_name_attribute not in namespace:
                raise TypeError(
                    f"Class {name} must define a class attribute {table_name_attribute}"
                )
            # if connection_name_attribute not in namespace:
            #     raise TypeError(
            #         f"Class {name} must define a class attribute {connection_name_attribute}"
            #     )
        return super().__new__(mcs, name, bases, namespace)


class BaseService(metaclass=EnforceAttributeMeta):
    def __init__(self, connection_name: str, table_name: str):
        self._connection_name = connection_name
        self._table_name = table_name
        self._db: Optional[QSqlDatabase] = None
        self._query: Optional[QSqlQuery] = None
        self._initialize_database_connection()

    def _initialize_database_connection(self):
        if not QSqlDatabase.contains(self._connection_name):
            db = QSqlDatabase.addDatabase("QSQLITE", self._connection_name)
            db.setDatabaseName(
                constants.DB_CONTAINER_PATH + "/db.db"
            )  # hoặc đường dẫn phù hợp
            if not db.open():
                error_message = (
                    f"Failed to open database connection '{self._connection_name}': "
                    f"{db.lastError().text()}"
                )
                raise ConnectionError(error_message)
            self._db = db
        else:
            self._db = QSqlDatabase.database(self._connection_name)
            if not self._db.isOpen():
                if not self._db.open():
                    error_message = (
                        f"Failed to open database connection '{self._connection_name}': "
                        f"{self._db.lastError().text()}"
                    )
                    raise ConnectionError(error_message)
        if not self._db.isValid():
            raise ConnectionError(
                f"Database connection '{self._connection_name}' is invalid."
            )
        self._query = QSqlQuery(self._db)

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
                self._query.bindValue(f":{key}", value)
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

    def remove_database(self):
        QSqlDatabase.removeDatabase(self._connection_name)

    def create(self, payload: Any) -> Optional[int]:
        data_dict = asdict(payload)

        filtered_data_dict = {}

        for key, value in data_dict.items():
            if key == "id" and value == None:
                continue
            elif key == "created_at" and value == None:
                continue
            if key == "updated_at":
                filtered_data_dict[key] = str(datetime.now())
            else:
                filtered_data_dict[key] = value

        fields = list(filtered_data_dict.keys())
        columns = ", ".join(fields)
        placeholders = ", ".join([f":{field}" for field in fields])

        sql_query = (
            f"INSERT INTO {self._table_name} ({columns}) VALUES ({placeholders})"
        )
        params = filtered_data_dict

        with transaction(self.get_database()):
            if self.execute_query(sql_query=sql_query, params=params):
                return self.get_last_insert_id()
            else:
                print(
                    f"Failed to create new record in '{self._table_name}' for payload: {payload}"
                )
                # in ra lỗi ở đây
                return None

    def read(self, record_id: Any, id_field: str = "id") -> Optional[Dict[str, Any]]:
        sql_query = f"SELECT * FROM {self._table_name} WHERE {id_field} = :id"
        params = {"id": record_id}
        return self.fetch_one(sql_query, params)

    def read_all(
        self, where: Optional[str] = None, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        sql_query = f"SELECT * FROM {self._table_name}"
        if where:
            sql_query += f" WHERE {where}"
        return self.fetch_all(sql_query, params)

    def delete(self, record_id: Any, id_field: str = "id") -> bool:
        sql_query = f"DELETE FROM {self._table_name} WHERE {id_field} = :id"
        params = {"id": record_id}
        with transaction(self.get_database()):
            return self.execute_query(sql_query, params)

    def delete_multiple(self, ids: List[Any], id_field: str = "id") -> bool:
        if not ids:
            return False
        placeholders = ", ".join([f":id{i}" for i in range(len(ids))])
        sql_query = (
            f"DELETE FROM {self._table_name} WHERE {id_field} IN ({placeholders})"
        )
        params = {f"id{i}": id_val for i, id_val in enumerate(ids)}
        with transaction(self.get_database()):
            return self.execute_query(sql_query, params)

    def update(self, payload: Any, id_field: str = "id") -> bool:
        data_dict = asdict(payload)
        set_clause = ", ".join([f"{field} = :{field}" for field in data_dict.keys()])
        sql_query = f"UPDATE {self._table_name} SET {set_clause} WHERE {id_field} = :id"
        params = {**data_dict, "id": payload.id}
        with transaction(self.get_database()):
            return self.execute_query(sql_query, params)

    def is_existed(self, field: str, value: str) -> bool:
        sql_query = f"SELECT 1 FROM {self._table_name} WHERE {field} = :value LIMIT 1"
        params = {"value": value}
        result = self.fetch_one(sql_query, params)
        return result is not None
