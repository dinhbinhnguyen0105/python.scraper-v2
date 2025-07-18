# src/my_types.py
from PyQt6.QtCore import pyqtSignal, QObject
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class IgnoreUID_Type:
    id: int
    value: str
    created_at: str

    @staticmethod
    def from_db_row(row_data: Dict[str, Any]) -> "IgnoreUID_Type":
        return IgnoreUID_Type(
            id=row_data.get("id"),
            value=row_data.get("value"),
            created_at=row_data.get("created_at"),
        )


@dataclass
class IgnorePhoneNumber_Type:
    id: int
    value: str
    created_at: str

    @staticmethod
    def from_db_row(row_data: Dict[str, Any]) -> "IgnorePhoneNumber_Type":
        return IgnorePhoneNumber_Type(
            id=row_data.get("id"),
            value=row_data.get("value"),
            created_at=row_data.get("created_at"),
        )


@dataclass
class Result_Type:
    id: int
    article_url: str
    article: str
    author_url: str
    author: str
    contact: str
    created_at: str

    @staticmethod
    def from_db_row(row_data: Dict[str, Any]) -> "Result_Type":
        return Result_Type(
            id=row_data.get("id"),
            article_url=row_data.get("article_url"),
            article=row_data.get("article"),
            author_url=row_data.get("author_url"),
            author=row_data.get("author"),
            contact=row_data.get("contact"),
            created_at=row_data.get("created_at"),
        )


class ControllerSignals(QObject):
    error = pyqtSignal(str)
    info = pyqtSignal(str)
    warning = pyqtSignal(str)
    success = pyqtSignal()
