from __future__ import annotations
from abc import ABC
from ast import List
from dataclasses import dataclass
from typing import Union, TYPE_CHECKING, Optional
import datetime

from sa.query_language.errors import QueryError
from sa.core.sa_types import SATypeCustom, resolve_primitive_recursively

from sa.core.types import SATypePrimitive, SAType

if TYPE_CHECKING:
    from sa.core.object_list import ObjectList
    from sa.query_language.query_state import QueryState

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

    def get_field(self, field_name: str, query_state: 'QueryState') -> 'SAType':
        assert self.has_field(field_name), f"Field {field_name} not found in object {self.id}"
        value = self.json[field_name]
        if isinstance(value, SATypeCustom):
            return value.resolve(query_state)
        return value
    
    def has_field(self, field_name: str) -> bool:
        return field_name in self.json.keys()
    
    def empty_copy(self) -> 'SAObject':
        return SAObject({
            "__types__": self.types,
            "__id__": self.id,
            "__source__": self.source,
        })
