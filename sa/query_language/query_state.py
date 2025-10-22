from __future__ import annotations
from dataclasses import dataclass
from sa.core.scope import Scope
from sa.shell.provider_manager import Providers
from sa.core.object_list import ObjectList
from sa.query_language.scopes import Scopes


@dataclass
class QueryState:
    providers: Providers
    staged_object_lists: dict[str, ObjectList]
    needed_scopes: Scopes
    staged_scopes: Scopes

    @property
    def all_data(self) -> ObjectList:
        return self.providers.all_data
    
    @property
    def all_scopes(self) -> set[Scope]:
        return self.providers.all_scopes

    @property
    def final_needed_scopes(self) -> set[Scope]:
        return self.staged_scopes.scopes | self.needed_scopes.scopes

    @staticmethod
    def setup(providers: Providers) -> "QueryState":
        scopes = Scopes.setup(providers.all_scopes)
        return QueryState(
            providers=providers,
            staged_object_lists={},
            needed_scopes=scopes,
            staged_scopes=Scopes(scopes=set())
        )

    def stage(self):
        self.staged_scopes = Scopes(self.staged_scopes.scopes | self.needed_scopes.scopes)
        self.needed_scopes = Scopes(self.all_scopes)