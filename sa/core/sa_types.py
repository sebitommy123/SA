from __future__ import annotations
from abc import ABC
from typing import TYPE_CHECKING, Optional
import datetime

if TYPE_CHECKING:
    from sa.core.object_list import ObjectList
    from sa.core.types import SATypePrimitive, SAType
    from sa.query_language.query_state import QueryState

class SATypeCustom(ABC):
    name: str = ""
    def __init_subclass__(cls):
        assert getattr(cls, "name", "") != "", "SATypeCustom subclass must define a non-blank 'name'"
    value: dict[str, 'SATypePrimitive']

    def __init__(self, value: 'SATypePrimitive'):
        assert isinstance(value, dict), "Value must be a dict"
        assert self.name == value["__sa_type__"], f"Value must have __sa_type__ {self.name}, got {value['__sa_type__']}"
        self.value = value
        self.validate()
    
    def validate(self):
        assert False, "validate must be implemented by subclass"

    def resolve(self, query_state: 'QueryState') -> 'SAType':
        assert False, "resolve must be implemented by subclass"

    def to_text(self) -> str:
        assert False, "to_text must be implemented by subclass"

    def __str__(self) -> str:
        return self.to_text()

    def __repr__(self) -> str:
        return f"{self.name}<{self.to_text()}>({self.value})"

class SATimestamp(SATypeCustom):
    name = "timestamp"

    def validate(self):
        assert "timestamp" in self.value, "Timestamp must be a dict"
        assert isinstance(self.value["timestamp"], int), "Timestamp must be a int"

    def resolve(self, _) -> 'SAType':
        return self.value["timestamp"]

    def to_text(self) -> str:
        return datetime.datetime.fromtimestamp(self.value["timestamp"] / 1_000_000_000).isoformat()

class SALink(SATypeCustom):
    name = "link"

    def validate(self):
        assert "query" in self.value, "Link must have a query"
        assert "show_text" in self.value, "Link must have a show_text"
        assert isinstance(self.value["query"], str), "Link query must be a string"
        assert isinstance(self.value["show_text"], str), "Link show_text must be a string"

    def resolve(self, query_state: 'QueryState') -> 'SAType':
        from sa.query_language.parser import run_query
        return run_query(self.value["query"], query_state.providers)
    
    def to_text(self) -> str:
        return f"<{self.value['show_text']}>"

SA_TYPES = [
    SATimestamp,
    SALink,
]

def resolve_primitive_recursively(primitive: 'SATypePrimitive') -> 'SAType':
    # Import here to avoid circular import
    from sa.core.types import is_valid_sa_type_primitive
    assert is_valid_sa_type_primitive(primitive), "Primitive is not a valid primitive"
    if isinstance(primitive, dict):
        if "__sa_type__" in primitive:
            for sa_type_cls in SA_TYPES:
                if sa_type_cls.name == primitive["__sa_type__"]:
                    return sa_type_cls(primitive)
            raise ValueError(f"Unknown SA type: {primitive['__sa_type__']}")
        else:
            return {k: resolve_primitive_recursively(v) for k, v in primitive.items()}
    elif isinstance(primitive, list):
        return [resolve_primitive_recursively(v) for v in primitive]
    return primitive