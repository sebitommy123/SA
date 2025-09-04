from __future__ import annotations

# Query Language for generic JSON objects

from dataclasses import dataclass
from typing import Callable, Optional, Union, List, TYPE_CHECKING

if TYPE_CHECKING:
    from sa.core.sa_object import SAObject, SAType
    from sa.query_language.object_list import ObjectList

@dataclass
class ObjectGrouping:
    objects: List['SAObject']

    @property
    def id_types(self) -> set[tuple[str, str]]:
        # it's the union of all the id_types of the objects in the object_grouping
        return set.union(*[set(obj.id_types) for obj in self.objects])

    def has_id_type(self, id_type: tuple[str, str]) -> bool:
        return id_type in self.id_types
    
    @staticmethod
    def combine(groupings: list['ObjectGrouping']) -> 'ObjectGrouping':
        return ObjectGrouping(
            objects=[obj for grouping in groupings for obj in grouping.objects],
        )

@dataclass
class ObjectGroupings:
    groupings: list['ObjectGrouping']

    def get_grouping_for_id_type(self, id_type: tuple[str, str]) -> Optional['ObjectGrouping']:
        results = [grouping for grouping in self.groupings if grouping.has_id_type(id_type)]
        if len(results) == 0:
            return None
        if len(results) > 1:
            raise ValueError(f"Multiple object groupings with id type {id_type}: {results}")
        return results[0]
    
    def get_groupings_for_id_types(self, id_types: list[tuple[str, str]]) -> list['ObjectGrouping']:
        groupings = []
        for id_type in id_types:
            grouping = self.get_grouping_for_id_type(id_type)
            if grouping is not None and not grouping in groupings:
                groupings.append(grouping)
        return groupings
    
    def remove_groupings(self, groupings: list['ObjectGrouping']) -> None:
        self.groupings = [grouping for grouping in self.groupings if grouping not in groupings]

@dataclass
class Operator:
    name: str
    runner: Callable[['QueryPrimitive', 'Arguments', 'ObjectList'], 'QueryType']

@dataclass
class OperatorNode:
    operator: 'Operator'
    arguments: list['QueryType']

    def run(self, context: 'QueryPrimitive', all_data: 'ObjectList') -> 'QueryPrimitive':
        return self.operator.runner(context, self.arguments, all_data)

@dataclass
class Chain:
    operator_nodes: list['OperatorNode']

    def run(self, context: 'QueryPrimitive', all_data: 'ObjectList') -> 'QueryPrimitive':
        for operator_node in self.operator_nodes:
            context = operator_node.run(context, all_data)
        return context

# Type alias for query types
QueryPrimitive = Union['ObjectList', 'SAType']
QueryType = Union[QueryPrimitive, 'Chain']
Arguments = list['QueryType']

def is_valid_primitive(t: any) -> bool:
    # Import here to avoid circular import
    from sa.core.sa_object import is_valid_sa_type
    from sa.query_language.object_list import ObjectList
    return is_valid_sa_type(t) or isinstance(t, ObjectList)

def is_valid_querytype(t: any) -> bool:
    from sa.query_language.main import Chain
    return is_valid_primitive(t) or isinstance(t, Chain)
