from __future__ import annotations
from dataclasses import dataclass
from sa.shell.provider_manager import Providers
from sa.core.object_list import ObjectList
from sa.query_language.query_scope import QueryScope, Scopes


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
    def final_needed_scopes(self) -> Scopes:
        return self.staged_scopes.add_scopes(self.needed_scopes)

    @staticmethod
    def setup(providers: Providers) -> "QueryState":
        scopes = Scopes.setup(providers.all_scopes)
        return QueryState(
            providers=providers,
            staged_object_lists={},
            needed_scopes=scopes,
            staged_scopes=Scopes(scopes=[])
        )

    def stage_scopes(self, new_scopes: Scopes):
        self.staged_scopes = self.staged_scopes.add_scopes(self.needed_scopes)
        self.needed_scopes = new_scopes