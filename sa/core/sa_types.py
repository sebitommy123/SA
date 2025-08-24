from __future__ import annotations
from abc import ABC
from typing import TYPE_CHECKING, Optional
import datetime

if TYPE_CHECKING:
    from sa.query_language.object_list import ObjectList

# Forward references for types defined elsewhere
SATypePrimitive = 'SATypePrimitive'
SAType = 'SAType'

class SATypeCustom(ABC):
    name: str = ""
    def __init_subclass__(cls):
        assert getattr(cls, "name", "") != "", "SATypeCustom subclass must define a non-blank 'name'"
    value: dict[str, 'SATypePrimitive']

    def __init__(self, value: 'SATypePrimitive'):
        assert isinstance(value, dict), "Value must be a dict"
        assert self.name == value["__sa_type__"], f"Value must have __sa_type__ {self.name}, got {value['__sa_type__']}"
        self.value = value
        self.validate()
    
    def validate(self):
        assert False, "validate must be implemented by subclass"

    def resolve(self, all_data: 'ObjectList') -> 'SAType':
        assert False, "resolve must be implemented by subclass"

    def to_text(self) -> str:
        assert False, "to_text must be implemented by subclass"

    def __str__(self) -> str:
        return self.to_text()

    def __repr__(self) -> str:
        return f"{self.name}<{self.to_text()}>({self.value})"

class SATimestamp(SATypeCustom):
    name = "timestamp"

    def validate(self):
        assert "timestamp" in self.value, "Timestamp must be a dict"
        assert isinstance(self.value["timestamp"], int), "Timestamp must be a int"

    def resolve(self, _) -> 'SAType':
        return self.value["timestamp"]

    def to_text(self) -> str:
        return datetime.datetime.fromtimestamp(self.value["timestamp"] / 1_000_000_000).isoformat()

class SALink(SATypeCustom):
    name = "link"

    def validate(self):
        assert "query" in self.value, "Link must have a query"
        assert "show_text" in self.value, "Link must have a show_text"
        assert isinstance(self.value["query"], str), "Link query must be a string"
        assert isinstance(self.value["show_text"], str), "Link show_text must be a string"

    def resolve(self, all_data: 'ObjectList') -> 'SAType':
        assert isinstance(self.value["query"], str)
        from sa.query_language.execute import execute_query
        return execute_query(self.value["query"], all_data)
    
    def to_text(self) -> str:
        return f"<{self.value['show_text']}>"        

class SARef(SATypeCustom):
    name = "ref"

    def validate(self):
        assert "id" in self.value, "Ref must have an id"
        assert isinstance(self.value["id"], str), "Ref id must be a string"
        if "type" in self.value:
            assert isinstance(self.value["type"], str), "Ref type must be a string"
        if "source" in self.value:
            assert isinstance(self.value["source"], str), "Ref source must be a string"
        if "show_text" in self.value:
            assert isinstance(self.value["show_text"], str), "Ref show_text must be a string"

    def resolve(self, all_data: 'ObjectList') -> 'SAType':
        from sa.query_language.object_list import ObjectList
        ref_id = self.value["id"]
        ref_type = self.value.get("type")
        ref_source = self.value.get("source")
        matched = [
            obj for obj in all_data.objects
            if obj.id == ref_id and (ref_type is None or ref_type in obj.types) and (ref_source is None or obj.source == ref_source)
        ]
        return ObjectList(matched)

    def to_text(self) -> str:
        if "show_text" in self.value:
            return self.value["show_text"]
        if "type" in self.value:
            return f"{self.value['type']}#{self.value['id']}"
        return self.value["id"]

class SAQuery(SATypeCustom):
    name = "query"

    def validate(self):
        assert "query" in self.value, "Query must have a query"
        assert isinstance(self.value["query"], str), "Query query must be a string"

    def resolve(self, all_data: 'ObjectList') -> 'SAType':
        from sa.query_language.execute import execute_query
        return execute_query(self.value["query"], all_data)

    def to_text(self) -> str:
        return f"? {self.value['query']}"

class SAEmail(SATypeCustom):
    name = "email"

    def validate(self):
        assert "email" in self.value, "Email must have an email"
        assert isinstance(self.value["email"], str), "Email must be a string"

    def resolve(self, _) -> 'SAType':
        return self.value["email"]

    def to_text(self) -> str:
        return self.value["email"]

class SAURL(SATypeCustom):
    name = "url"

    def validate(self):
        assert "url" in self.value, "URL must have a url"
        assert isinstance(self.value["url"], str), "URL must be a string"

    def resolve(self, _) -> 'SAType':
        return self.value["url"]

    def to_text(self) -> str:
        return self.value["url"]

class SAPhone(SATypeCustom):
    name = "phone"

    def validate(self):
        assert "phone" in self.value, "Phone must have a phone"
        assert isinstance(self.value["phone"], str), "Phone must be a string"

    def resolve(self, _) -> 'SAType':
        return self.value["phone"]

    def to_text(self) -> str:
        return self.value["phone"]

class SADateRange(SATypeCustom):
    name = "date_range"

    def validate(self):
        assert "start" in self.value and "end" in self.value, "DateRange must have start and end"
        assert isinstance(self.value["start"], int) and isinstance(self.value["end"], int), "start and end must be ints"

    def resolve(self, _) -> 'SAType':
        return {"start": self.value["start"], "end": self.value["end"]}

    def to_text(self) -> str:
        s = datetime.datetime.fromtimestamp(self.value["start"] / 1_000_000_000).isoformat()
        e = datetime.datetime.fromtimestamp(self.value["end"] / 1_000_000_000).isoformat()
        return f"{s} – {e}"

class SAMoney(SATypeCustom):
    name = "money"

    def validate(self):
        assert "amount" in self.value and "currency" in self.value, "Money must have amount and currency"
        assert isinstance(self.value["amount"], (int, float)), "Money amount must be a number"
        assert isinstance(self.value["currency"], str), "Money currency must be a string"

    def resolve(self, _) -> 'SAType':
        return self.value["amount"]

    def to_text(self) -> str:
        amount = self.value["amount"]
        currency = self.value["currency"].upper()
        return f"{currency} {amount:,.2f}" if isinstance(amount, float) else f"{currency} {amount}"

class SAImage(SATypeCustom):
    name = "image"

    def validate(self):
        assert "url" in self.value, "Image must have a url"
        assert isinstance(self.value["url"], str), "Image url must be a string"
        if "alt" in self.value:
            assert isinstance(self.value["alt"], str), "Image alt must be a string"

    def resolve(self, _) -> 'SAType':
        return self.value["url"]

    def to_text(self) -> str:
        return self.value.get("alt", self.value["url"]) or self.value["url"]

class SATagList(SATypeCustom):
    name = "tag_list"

    def validate(self):
        assert "tags" in self.value, "TagList must have a tags key"
        assert isinstance(self.value["tags"], list), "TagList tags must be a list"
        assert all(isinstance(t, str) for t in self.value["tags"]), "TagList tags must be list of strings"

    def resolve(self, _) -> 'SAType':
        return list(self.value["tags"])

    def to_text(self) -> str:
        return ", ".join(self.value["tags"]) if self.value["tags"] else ""

class SATemplate(SATypeCustom):
    name = "template"

    def validate(self):
        assert "template" in self.value and isinstance(self.value["template"], str), "Template must have a template string"
        assert "values" in self.value and isinstance(self.value["values"], dict), "Template must have a values dict"

    def resolve(self, all_data: 'ObjectList') -> 'SAType':
        # Import here to avoid circular import issues in annotation
        from sa.core.sa_types import SATypeCustom as _SATypeCustom
        # Resolve nested primitives into SA types, then fully resolve them
        resolved_values: dict[str, 'SAType'] = {}
        for key, raw_val in self.value["values"].items():
            intermediate = resolve_primitive_recursively(raw_val)
            if isinstance(intermediate, _SATypeCustom):
                resolved_values[key] = intermediate.resolve(all_data)
            else:
                resolved_values[key] = intermediate
        # Render using Python format maps; convert complex values to str
        safe_values = {k: (v if isinstance(v, (str, int, float, bool)) or v is None else str(v)) for k, v in resolved_values.items()}
        try:
            return self.value["template"].format_map(safe_values)
        except KeyError:
            # If a key is missing, fall back to best-effort replacement
            return self.to_text()

    def to_text(self) -> str:
        # A non-resolving textual hint
        return self.value["template"]

class SAJoin(SATypeCustom):
    name = "join"

    def validate(self):
        assert "items" in self.value and isinstance(self.value["items"], list), "Join must have an items list"
        assert "sep" in self.value and isinstance(self.value["sep"], str), "Join must have a sep string"

    def resolve(self, all_data: 'ObjectList') -> 'SAType':
        parts: list[str] = []
        for item in self.value["items"]:
            intermediate = resolve_primitive_recursively(item)
            if isinstance(intermediate, SATypeCustom):
                final_val = intermediate.resolve(all_data)
            else:
                final_val = intermediate
            parts.append(str(final_val))
        return self.value["sep"].join(parts)

    def to_text(self) -> str:
        return self.value["sep"].join([str(i) for i in self.value.get("items", [])])

class SAFirstNonNull(SATypeCustom):
    name = "first_non_null"

    def validate(self):
        assert "items" in self.value and isinstance(self.value["items"], list), "first_non_null must have an items list"

    def resolve(self, all_data: 'ObjectList') -> 'SAType':
        for item in self.value["items"]:
            intermediate = resolve_primitive_recursively(item)
            candidate = intermediate.resolve(all_data) if isinstance(intermediate, SATypeCustom) else intermediate
            if candidate is not None and candidate != "":
                return candidate
        return None

    def to_text(self) -> str:
        return "first_non_null(...)"

SA_TYPES = [
    SATimestamp,
    SALink,
    SARef,
    SAQuery,
    SAEmail,
    SAURL,
    SAPhone,
    SADateRange,
    SAMoney,
    SAImage,
    SATagList,
    SATemplate,
    SAJoin,
    SAFirstNonNull,
]


def resolve_primitive_recursively(primitive: 'SATypePrimitive') -> 'SAType':
    # Import here to avoid circular import
    from sa.core.sa_object import is_valid_sa_type_primitive
    assert is_valid_sa_type_primitive(primitive), "Primitive is not a valid primitive"
    if isinstance(primitive, dict):
        if "__sa_type__" in primitive:
            for sa_type_cls in SA_TYPES:
                if sa_type_cls.name == primitive["__sa_type__"]:
                    return sa_type_cls(primitive)
            raise ValueError(f"Unknown SA type: {primitive['__sa_type__']}")
        else:
            return {k: resolve_primitive_recursively(v) for k, v in primitive.items()}
    elif isinstance(primitive, list):
        return [resolve_primitive_recursively(v) for v in primitive]
    return primitive