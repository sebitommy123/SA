from __future__ import annotations

from dataclasses import dataclass
from typing import List
from sa.core.scope import Scope

@dataclass
class QueryScope:
    scope: Scope
    conditions: list[tuple[str, str, str]] # (field, operator, value)
    
    def __str__(self) -> str:
        if not self.conditions:
            return f"QueryScope(scope={self.scope}, conditions=[])"
        else:
            cond_str = ", ".join([f"{field}{op}'{value}'" for field, op, value in self.conditions])
            return f"QueryScope(scope={self.scope}, conditions=[{cond_str}])"

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

    def __str__(self) -> str:
        if not self.scopes:
            return "Scopes(scopes=[])"
        else:
            scopes_str = ", ".join(str(scope) for scope in self.scopes)
            return f"Scopes(scopes=[{scopes_str}])"
    
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
