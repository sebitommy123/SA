from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Literal, Union

@dataclass
class Scope:
    type: str
    fields: Union[list[str], Literal["*"]]
    
    def __str__(self) -> str:
        if self.fields == "*":
            return f"{self.type}"
        else:
            return f"{self.type}[{self.fields}]"

    @staticmethod
    def union(scopes: list[Scope]) -> list[Scope]:
        by_type: dict[str, Scope] = {}
        for scope in scopes:
            if scope.type not in by_type:
                by_type[scope.type] = scope
            else:
                by_type[scope.type] = Scope(
                    type=scope.type,
                    fields=list(set(by_type[scope.type].fields + scope.fields))
                )
        return list(by_type.values())

