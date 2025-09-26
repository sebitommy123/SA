from __future__ import annotations
from dataclasses import dataclass
from ast import List
from typing import TYPE_CHECKING, Optional

from sa.query_language.errors import QueryError

if TYPE_CHECKING:
    from sa.core.object_list import ObjectList
    from .sa_object import SAObject
    from .types import SAType

@dataclass
class ObjectGrouping:
    _objects: List[SAObject]
    _field_overrides: dict[str, SAType]
    _selected_fields: Optional[set[str]]

    def __post_init__(self):
        assert len({obj.id for obj in self._objects}) == 1, f"ObjectGrouping has multiple ids: {self._objects}"

    @property
    def id_types(self) -> set[tuple[str, str]]:
        # it's the union of all the id_types of the objects in the object_grouping
        return set.union(*[set(obj.id_types) for obj in self._objects])

    @property
    def unique_ids(self) -> set[tuple[str, str, str]]:
        # it's the union of all the unique_ids of the objects in the object_grouping
        return set.union(*[set(obj.unique_ids) for obj in self._objects])

    @property
    def types(self) -> set[str]:
        return set.union(*[set(obj.types) for obj in self._objects])

    @property
    def id(self) -> str:
        return self._objects[0].id

    @property
    def sources(self) -> set[str]:
        return set([obj.source for obj in self._objects])

    def has_id_type(self, id_type: tuple[str, str]) -> bool:
        return id_type in self.id_types

    def select_sources(self, sources: set[str]) -> Optional[ObjectGrouping]:
        matching_objects = [obj for obj in self._objects if obj.source in sources]
        if len(matching_objects) == 0:
            return None
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
        return ObjectGrouping(self._objects, self._field_overrides, fields)

    def get_field(self, field_name: str, all_data: 'ObjectList') -> 'SAType':
        if field_name in self._field_overrides:
            return self._field_overrides[field_name]
        field_values_list = [obj.get_field(field_name, all_data) for obj in self._objects if obj.has_field(field_name)]
        if len(field_values_list) == 0:
            raise QueryError(f"Object {self} has no field \"{field_name}\"")
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

    def get_all_field_values(self, field_name: str, all_data: 'ObjectList') -> list['SAType']:
        if field_name in self._field_overrides:
            return [self._field_overrides[field_name]]
        return [obj.get_field(field_name, all_data) for obj in self._objects if obj.has_field(field_name)]

    def __str__(self) -> str:
        HEADER_COLOR = "\033[96m"
        RESET_COLOR = "\033[0m"
        return f"{HEADER_COLOR}Obj({','.join(self.types)}#{self.id}@{'@'.join(self.sources)}){RESET_COLOR}"


def group_objects(objects: List['SAObject']) -> List[ObjectGrouping]:
    id_to_objects = {}
    
    for obj in objects:
        obj_id = obj.id
        if obj_id not in id_to_objects:
            id_to_objects[obj_id] = []
        id_to_objects[obj_id].append(obj)
    
    # Create ObjectList for each group
    object_groups = []
    for obj_id, objects in id_to_objects.items():
        object_groups.append(ObjectGrouping(objects, {}, None))
    
    return object_groups