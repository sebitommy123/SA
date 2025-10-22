from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from sa.core.scope import Scope
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sa.query_language.chain import Chain

@dataclass
class Scopes:
    scopes: set[Scope]

    def __post_init__(self):
        assert isinstance(self.scopes, set), f"Scopes must be a set, got {type(self.scopes).__name__}"

    @staticmethod
    def setup(scopes: set[Scope]) -> Scopes:
        return Scopes({scope.copy_fresh() for scope in scopes})

    def __str__(self) -> str:
        if not self.scopes:
            return "Scopes([])"
        else:
            scopes_str = ",\n    ".join(str(scope) for scope in self.scopes)
            return f"Scopes(\n    {scopes_str}\n)"

    def set_id_types(self, id_types: set[tuple[str, str]]) -> Scopes:
        """Set the id types for all scopes."""
        new_scopes = set()
        for scope in self.scopes:
            new_scope = scope.copy()
            if new_scope.needs_id_types:
                new_scope.id_types = {(id_, type_) for id_, type_ in id_types if type_ == new_scope.type}
            new_scopes.add(new_scope)
        return Scopes(new_scopes)
    
    def filter_type(self, type: str) -> Scopes:
        """Keep only scopes with the specified type."""
        filtered_scopes = {scope for scope in self.scopes if scope.type == type}
        return Scopes(filtered_scopes)
    
    def filter_fields(self, fields: list[str]) -> Scopes:
        """For each scope, keep only the specified fields (intersection), then remove scopes with no fields left."""
        filtered_scopes = set()
        for scope in self.scopes:
            if scope.fields == "*":
                # If scope has all fields, keep it as is
                filtered_scopes.add(scope)
            else:
                # Find intersection of scope fields and requested fields
                intersection = [field for field in scope.fields if field in fields]
                if intersection:  # Only keep scopes that have at least one matching field
                    new_scope = scope.copy()
                    new_scope.fields = intersection
                    filtered_scopes.add(new_scope)
        return Scopes(filtered_scopes)
    
    def add_condition(self, condition: tuple[str, str, str]) -> Scopes:
        """Add a condition to all scopes."""
        new_scopes = set()
        for scope in self.scopes:
            new_scope = scope.copy()
            new_scope.conditions.append(condition)
            new_scopes.add(new_scope)
        return Scopes(new_scopes)

def chain_to_condition(chain: Chain) -> Optional[tuple[str, str, str]]:
    # Chain(.equals(.get_field("field"), "value"))
    from sa.query_language.chain import Chain
    if not len(chain.operator_nodes) == 1:
        return None
    equals_node = chain.operator_nodes[0]
    if equals_node.operator.name != "equals":
        return None
    if not len(equals_node.arguments) == 2:
        return None
    get_field_node_chain: Chain = equals_node.arguments[0]
    value = equals_node.arguments[1]
    if not isinstance(get_field_node_chain, Chain):
        return None
    if not len(get_field_node_chain.operator_nodes) == 1:
        return None
    get_field_node = get_field_node_chain.operator_nodes[0]
    if get_field_node.operator.name != "get_field":
        return None
    if not len(get_field_node.arguments) >= 1:
        return None
    if not isinstance(get_field_node.arguments[0], str):
        return None
    return (get_field_node.arguments[0], "==", value)