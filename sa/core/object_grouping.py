from __future__ import annotations
from dataclasses import dataclass, field
from ast import List
from typing import TYPE_CHECKING, Optional
from itertools import chain

from sa.query_language.errors import QueryError

if TYPE_CHECKING:
    from .sa_object import SAObject
    from sa.core.object_list import ObjectList
    from .types import SAType
    from sa.query_language.query_state import QueryState

@dataclass
class ObjectGrouping:
    _objects: List[SAObject]
    _field_overrides: dict[str, SAType]
    _selected_fields: Optional[set[str]]
    # Pre-computed cached properties
    types: set[str] = field(default=None, init=False, repr=False)
    id_types: set[tuple[str, str]] = field(default=None, init=False, repr=False)
    unique_ids: set[tuple[str, str, str]] = field(default=None, init=False, repr=False)
    sources: set[str] = field(default=None, init=False, repr=False)

    def __post_init__(self):
        from sa.query_language.debug import debugger
        assert len({obj.id for obj in self._objects}) == 1, f"ObjectGrouping has multiple ids: {self._objects}"
        for obj in self._objects:
            from sa.core.sa_object import SAObject
            assert isinstance(obj, SAObject), f"ObjectGrouping must contain SAObject objects, got {type(obj).__name__}"
        assert len({obj.source for obj in self._objects}) == len(self._objects), f"ObjectGrouping has objects from the same source: {self._objects}"
        
        # Pre-compute all cached values
        # Use chain.from_iterable to flatten without creating intermediate lists
        self.types = set(chain.from_iterable(obj.types for obj in self._objects))
        
        # obj.id_types already returns a set, so we can chain them directly
        self.id_types = set(chain.from_iterable(obj.id_types for obj in self._objects))
        
        # obj.unique_ids already returns a set, so we can chain them directly
        self.unique_ids = set(chain.from_iterable(obj.unique_ids for obj in self._objects))
        
        # Use set comprehension for better performance
        self.sources = {obj.source for obj in self._objects}

    def reset(self):
        """Reset field overrides and selected fields if they are set."""
        # Only reset if there's actually something to reset
        if self._field_overrides or self._selected_fields is not None:
            self._field_overrides = {}
            self._selected_fields = None
        # Note: We don't reset cache here because field_overrides/selected_fields
        # don't affect types/id_types/unique_ids/sources (which are computed from _objects)

    @property
    def id(self) -> str:
        return self._objects[0].id

    def has_id_type(self, id_type: tuple[str, str]) -> bool:
        return id_type in self.id_types

    def select_sources(self, sources: set[str]) -> Optional[ObjectGrouping]:
        matching_objects = [obj for obj in self._objects if obj.source in sources]
        if len(matching_objects) == 0:
            return None
        # Create new grouping - cache will be rebuilt automatically when accessed
        return ObjectGrouping(matching_objects, self._field_overrides, self._selected_fields)
    
    @property
    def name(self) -> str:
        return f"#{self.id} ({', '.join(self.types)} @{'@'.join(self.sources)})"
    
    @property
    def fields(self) -> set[str]:
        all_fields = set.union(*[set(obj.properties.keys()) for obj in self._objects])
        if self._selected_fields is not None:
            all_fields = all_fields.intersection(self._selected_fields)
        return all_fields

    def select_fields(self, fields: set[str]) -> ObjectGrouping:
        return ObjectGrouping(self._objects, self._field_overrides, self._selected_fields | fields if self._selected_fields is not None else fields)

    def get_field(self, field_name: str, query_state: 'QueryState') -> 'SAType':
        if field_name in self._field_overrides:
            return self._field_overrides[field_name]
        field_values_list = [obj.get_field(field_name, query_state) for obj in self._objects if obj.has_field(field_name)]
        if len(field_values_list) == 0:
            raise QueryError(f"Object {self} has no field \"{field_name}\"", could_succeed_with_more_data=True)
        any_field_values_are_list_or_dict = any(isinstance(field_value, list) or isinstance(field_value, dict) for field_value in field_values_list)
        if any_field_values_are_list_or_dict:
            if len(field_values_list) > 1:
                raise QueryError(f"Field \"{field_name}\" of {self} has multiple definitions of list or dict from different sources. These can't be reconciled, please pick a source.")
            return field_values_list[0]
        field_values = set(field_values_list)
        if len(field_values) > 1:
            raise QueryError(f"Field \"{field_name}\" of {self} has multiple conflicting definitions from different sources. Please pick a source.")
        return field_values.pop()

    def has_field(self, field_name: str) -> bool:
        if field_name in self._field_overrides:
            return True
        return any(obj.has_field(field_name) for obj in self._objects)

    def get_all_field_values(self, field_name: str, query_state: 'QueryState') -> list['SAType']:
        if field_name in self._field_overrides:
            return [self._field_overrides[field_name]]
        return [obj.get_field(field_name, query_state) for obj in self._objects if obj.has_field(field_name)]

    def __str__(self) -> str:
        return f"Obj({','.join(self.types)}#{self.id}@{'@'.join(self.sources)})"


def group_objects(objects: List['SAObject']) -> List[ObjectGrouping]:
    from sa.query_language.debug import debugger
    id_to_objects = {}
    
    for obj in objects:
        obj_id = obj.id
        if obj_id not in id_to_objects:
            id_to_objects[obj_id] = []
        id_to_objects[obj_id].append(obj)
            # Create ObjectList for each group
    debugger.start_part("GROUP_OBJECTS", "Group objects")
    object_groups = []
    for obj_id, objects in id_to_objects.items():
        debugger.start_part("GROUP_OBJECTS_OBJECT", "Group objects iter")
        object_groups.append(ObjectGrouping(objects, {}, None))
        debugger.end_part("Group objects iter")
    debugger.end_part("Group objects")
    return object_groups

def ungroup_objects(object_groups: List[ObjectGrouping]) -> List['SAObject']:
    return [obj for group in object_groups for obj in group._objects]

def regroup_objects(objects: List['ObjectGrouping']) -> List[ObjectGrouping]:
    return group_objects(ungroup_objects(objects))
