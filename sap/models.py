from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional

from .types import encode_value


@dataclass
class SAPObject:
    id: str
    types: List[str]
    source: str
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "__types__": list(self.types),
            "__id__": self.id,
            "__source__": self.source,
        }
        for key, value in self.properties.items():
            payload[key] = encode_value(value)
        return payload


def make_object(id: str, types: List[str], source: str, **properties: Any) -> Dict[str, Any]:
    return SAPObject(id=id, types=types, source=source, properties=properties).to_json()