from __future__ import annotations
from typing import TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum

if TYPE_CHECKING:
    from .parser import Tokens


class QueryError(Exception):
    pass

def assert_query(condition: bool, message: str) -> None:
    """Custom assert function that raises QueryError instead of AssertionError."""
    if not condition:
        raise QueryError(message)

class QueryAreaTerms(Enum):
    CHAR = "CHAR"
    TOKEN = "TOKEN"

@dataclass
class QueryArea:
    start_index: int # inclusive
    end_index: int # exclusive
    terms: QueryAreaTerms
    all_tokens: Tokens

    def clone(self) -> QueryArea:
        return QueryArea(self.start_index, self.end_index, self.terms, self.all_tokens)
    
    def __getitem__(self, key):
        return QueryArea(
            self.start_index + key.start,
            self.end_index if key.stop is None else self.start_index + key.stop,
            self.terms,
            self.all_tokens
        )

    def __add__(self, other: int) -> QueryArea:
        return QueryArea(
            self.start_index + other,
            self.end_index + other,
            self.terms,
            self.all_tokens
        )
 
    def to_char_terms(self, tokens: Tokens) -> QueryArea:
        assert_query(self.terms == QueryAreaTerms.TOKEN, f"Expected TOKEN area, got {self.terms}")
        assert_query(self.start_index >= 0, f"Expected start index >= 0, got {self.start_index}")
        assert_query(self.end_index <= len(tokens), f"Expected end index <= {len(tokens)}, got {self.end_index}")
        assert_query(self.start_index <= self.end_index, f"Expected start index <= end index, got {self.start_index} > {self.end_index}")
        lengths = [len(token) for token in tokens]
        start_char_index = sum(lengths[:self.start_index])
        end_char_index = sum(lengths[:self.end_index])
        return QueryArea(start_char_index, end_char_index, QueryAreaTerms.CHAR, self.all_tokens)

@dataclass
class ProcessingAreaStack:
    areas: list[QueryArea]

    def push(self, area: QueryArea):
        self.areas.append(area)
    
    def pop(self) -> QueryArea:
        return self.areas.pop()

def print_error_area(area: QueryArea):
    area_char_terms = area.to_char_terms(area.all_tokens)
    query = "".join(area.all_tokens)

    # highlight the area in the query
    highlighted_query = ""
    for i in range(len(query)):
        if i >= area_char_terms.start_index and i < area_char_terms.end_index:
            highlighted_query += f"\033[91m{query[i]}\033[0m"
        else:
            highlighted_query += query[i]

    # create ^^^^^ icons for the area
    caret_icons = " " * area_char_terms.start_index + "^" * (area_char_terms.end_index - area_char_terms.start_index) + " " * (len(query) - area_char_terms.end_index)
 
    print(highlighted_query)
    print(caret_icons)

    
