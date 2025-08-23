from __future__ import annotations
from abc import ABC
from dataclasses import dataclass
from typing import Union, TYPE_CHECKING, Optional
import datetime

from sa.core.sa_types import SATypeCustom, resolve_primitive_recursively

from .types import SATypePrimitive, SAType

if TYPE_CHECKING:
    from sa.query_language.main import ObjectList
    from sa.query_language.parser import QueryType, Chain
    from sa.query_language.operators import GetFieldOperator
    from sa.query_language.execute import execute_query
    from sa.query_language.parser import get_tokens_from_query, parse_tokens_into_querytype

def is_valid_sa_type_primitive(t: any) -> bool:
    if isinstance(t, str) or isinstance(t, int) or isinstance(t, bool):
        return True
    if isinstance(t, list):
        return all(is_valid_sa_type(i) for i in t)
    if isinstance(t, dict):
        return all(is_valid_sa_type(i) for i in t.values())
    if t is None:
        return True
    return False

def is_valid_sa_type(t: any) -> bool:
    if is_valid_sa_type_primitive(t):
        return True
    # Import here to avoid circular import issues
    from sa.core.sa_types import SATypeCustom
    if isinstance(t, SATypeCustom):
        return True
    return False

@dataclass
class SAObject:
    json: dict[str, 'SAType']

    def __post_init__(self):
        # Check if the object is valid
        assert "__types__" in self.json, "Object must have a __types__ field"
        assert isinstance(self.json["__types__"], list), "Object __types__ field must be a list"
        assert all(isinstance(t, str) for t in self.json["__types__"]), "Object __types__ field must be a list of strings"
        assert "__id__" in self.json, "Object must have a __id__ field"
        assert isinstance(self.json["__id__"], str), "Object __id__ field must be a string"
        assert "__source__" in self.json, "Object must have a __source__ field"
        assert isinstance(self.json["__source__"], str), "Object __source__ field must be a string"
        self.json = {
            k: resolve_primitive_recursively(v)
            for k, v in self.json.items()
        }

    @property
    def types(self) -> list[str]:
        return self.json["__types__"]
    
    @property
    def id(self) -> str:
        return self.json["__id__"]
    
    @property
    def source(self) -> str:
        return self.json["__source__"]
    
    @property
    def properties(self) -> dict[str, 'SAType']:
        return {k: v for k, v in self.json.items() if k not in ["__types__", "__id__", "__source__"]}
    
    @property
    def unique_ids(self) -> set[tuple[str, str, str]]:
        return {
            (self.id, type, self.source)
            for type in self.types
        }
    
    @property
    def id_types(self) -> set[tuple[str, str]]:
        return {
            (self.id, type)
            for type in self.types
        }
    
    def set_field(self, field_name: str, value: 'SAType'):
        self.json[field_name] = value

    def get_field(self, field_name: str, all_data: 'ObjectList') -> 'SAType':
        assert self.has_field(field_name), f"Field {field_name} not found in object {self.id}"
        value = self.json[field_name]
        if isinstance(value, SATypeCustom):
            return value.resolve(all_data)
        return value
    
    def has_field(self, field_name: str) -> bool:
        return field_name in self.json.keys()
    
    def empty_copy(self) -> 'SAObject':
        return SAObject({
            "__types__": self.types,
            "__id__": self.id,
            "__source__": self.source,
        })
