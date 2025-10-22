from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Literal, Union

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sa.shell.provider_manager import ProviderConnection

@dataclass
class Scope:
    provider: ProviderConnection
    type: str
    fields: Union[list[str], Literal["*"]]
    filtering_fields: list[str]
    needs_id_types: bool
    conditions: list[tuple[str, str, str]]
    id_types: set[tuple[str, str]]

    def __eq__(self, other: Scope) -> bool:
        assert isinstance(other, Scope), f"Scope.__eq__ expected Scope, got {type(other).__name__}"
        return (
            self.provider == other.provider and
            self.type == other.type and
            set(self.fields) == set(other.fields) and
            set(self.filtering_fields) == set(other.filtering_fields) and
            self.needs_id_types == other.needs_id_types and
            set(self.conditions) == set(other.conditions) and
            self.id_types == other.id_types
        )
    
    def __hash__(self) -> int:
        return hash((
            self.provider.url,
            self.type,
            tuple(sorted(self.fields)),
            tuple(sorted(self.filtering_fields)),
            self.needs_id_types,
            tuple(sorted(self.conditions)),
            tuple(sorted(self.id_types))
        ))
    
    def __str__(self) -> str:
        cond_str = "".join([f"[.{field} {op} '{value}']" for field, op, value in self.conditions])
        fields_str = "" if self.fields == "*" else f"[{self.fields}]"
        id_types_str = "" if not self.id_types else f" ({len(self.id_types)} id types)"
        return f"{self.type}{cond_str}{fields_str}{id_types_str}"

    def copy_fresh(self) -> Scope:
        copy = self.copy()
        copy.conditions = []
        copy.id_types = set()
        return copy
    
    def copy(self) -> Scope:
        return Scope(
            provider=self.provider,
            type=self.type,
            fields=self.fields.copy() if isinstance(self.fields, list) else self.fields,
            filtering_fields=self.filtering_fields.copy(),
            needs_id_types=self.needs_id_types,
            conditions=self.conditions.copy(),
            id_types=self.id_types.copy()
        )

