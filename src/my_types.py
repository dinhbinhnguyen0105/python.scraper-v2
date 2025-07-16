from dataclasses import dataclass


@dataclass
class IgnoreUID_Type:
    id: int
    value: str
    created_at: str


@dataclass
class IgnorePhoneNumber_Type:
    id: int
    value: str
    created_at: str


@dataclass
class Result_Type:
    id: int
    article_url: str
    article: str
    author_url: str
    author: str
    contact: str
    created_at: str
