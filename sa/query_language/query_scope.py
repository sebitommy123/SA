from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from sa.core.scope import Scope
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sa.query_language.chain import Chain
@dataclass
class QueryScope:
    scope: Scope
    conditions: list[tuple[str, str, str]] # (field, operator, value)
    
    def __str__(self) -> str:
        cond_str = "".join([f"[.{field} {op} '{value}']" for field, op, value in self.conditions])
        return f"{self.scope}{cond_str}"

    @staticmethod
    def union(scopes: list[QueryScope]) -> list[QueryScope]:
        by_type: dict[str, QueryScope] = {}
        for scope in scopes:
            if scope.scope.type not in by_type:
                by_type[scope.scope.type] = scope
            else:
                by_type[scope.scope.type] = QueryScope(
                    scope=Scope(
                        type=scope.scope.type,
                        fields=list(set(by_type[scope.scope.type].scope.fields + scope.scope.fields))
                    ),
                    conditions=by_type[scope.scope.type].conditions + scope.conditions
                )
        return list(by_type.values())
    
    @staticmethod
    def minus(scopes: list[QueryScope], minus_scopes: list[QueryScope]) -> list[QueryScope]:
        # ensure already just one per type
        scopes = QueryScope.union(scopes)
        minus_scopes = Scope.union(minus_scopes)
        final_scopes = []

        for scope in scopes:
            matching_minus_scope = next((
                s for s in minus_scopes
                if s.type == scope.scope.type
            ), None)
            if matching_minus_scope:
                new_fields = list(set(scope.scope.fields) - set(matching_minus_scope.fields))
                if new_fields:
                    final_scopes.append(
                        QueryScope(
                            scope=Scope(
                                type=scope.scope.type,
                                fields=new_fields
                            ),
                            conditions=scope.conditions
                        )
                    )
            else:
                final_scopes.append(scope)
        return final_scopes

@dataclass
class Scopes:
    scopes: list[QueryScope]

    @staticmethod
    def setup(scopes: list[Scope]) -> Scopes:
        return Scopes(scopes=[QueryScope(scope=scope, conditions=[]) for scope in scopes])
    
    def add_scopes(self, new_scopes: Scopes) -> Scopes:
        return Scopes(
            scopes=QueryScope.union([*self.scopes, *new_scopes.scopes])
        )
    
    def minus_scopes(self, other_scopes: list[QueryScope]) -> Scopes:
        return Scopes(
            scopes=QueryScope.minus(self.scopes, other_scopes)
        )

    def __str__(self) -> str:
        if not self.scopes:
            return "Scopes([])"
        else:
            scopes_str = ", ".join(str(scope) for scope in self.scopes)
            return f"Scopes({scopes_str})"
    
    def filter_type(self, type: str) -> Scopes:
        """Keep only scopes with the specified type."""
        filtered_scopes = [scope for scope in self.scopes if scope.scope.type == type]
        return Scopes(scopes=filtered_scopes)
    
    def filter_fields(self, fields: list[str]) -> Scopes:
        """For each scope, keep only the specified fields (intersection), then remove scopes with no fields left."""
        filtered_scopes = []
        for scope in self.scopes:
            if scope.scope.fields == "*":
                # If scope has all fields, keep it as is
                filtered_scopes.append(scope)
            else:
                # Find intersection of scope fields and requested fields
                intersection = [field for field in scope.scope.fields if field in fields]
                if intersection:  # Only keep scopes that have at least one matching field
                    new_scope = Scope(type=scope.scope.type, fields=intersection)
                    new_query_scope = QueryScope(scope=new_scope, conditions=scope.conditions.copy())
                    filtered_scopes.append(new_query_scope)
        return Scopes(scopes=filtered_scopes)
    
    def add_condition(self, condition: tuple[str, str, str]) -> Scopes:
        """Add a condition to all scopes."""
        new_scopes = []
        for scope in self.scopes:
            new_conditions = scope.conditions.copy()
            new_conditions.append(condition)
            new_scope = QueryScope(scope=scope.scope, conditions=new_conditions)
            new_scopes.append(new_scope)
        return Scopes(scopes=new_scopes)

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