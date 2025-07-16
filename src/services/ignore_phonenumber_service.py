# src/services/ignore_phonenumber_service.py
from typing import List, Any, Dict, Optional

from src.services.base_service import BaseSerivce
from src.my_types import IgnorePhoneNumber_Type
from src.my_constants import DB_CONNECTION


class IgnorePhoneNumber_Service(BaseSerivce):
    connection_name = DB_CONNECTION

    def __init__(self, connection_name=connection_name):
        super().__init__(connection_name=connection_name)

    def create(self, payload: IgnorePhoneNumber_Type) -> bool:
        sql_query = ""
        params = ""
