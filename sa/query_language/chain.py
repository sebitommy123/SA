
from dataclasses import dataclass
from typing import Callable, Optional
from sa.query_language.scopes import Scopes
from sa.query_language.debug import debugger
from sa.core.object_grouping import ObjectGrouping
from sa.query_language.types import QueryContext, Arguments, QueryType, query_type_to_string
from sa.core.object_list import ObjectList
from sa.query_language.errors import QueryError, error_area_to_string, QueryArea
from sa.query_language.query_state import QueryState

@dataclass
class Operator:
    name: str
    runner: Callable[['QueryContext', 'Arguments', 'QueryState'], 'QueryType']

@dataclass
class OperatorNode:
    operator: 'Operator'
    arguments: list['QueryType']
    area: QueryArea

    def __str__(self):
        return f"{self.operator.name}({', '.join(query_type_to_string(arg) for arg in self.arguments)})"
    
    def __repr__(self):
        return f"OperatorNode({self.operator.name}, {', '.join(query_type_to_string(arg) for arg in self.arguments)})"

    def run(self, context: 'QueryContext', query_state: 'QueryState') -> 'QueryType':
        try:
            debugger.start_part("OPERATOR", str(self))
            debugger.log("OPERATOR_ARGS", ', '.join(query_type_to_string(arg) for arg in self.arguments))
            debugger.log("OPERATOR_CONTEXT", context)
            debugger.log("OPERATOR_SCOPES_START", Scopes(query_state.final_needed_scopes))
            result = self.operator.runner(context, self.arguments, query_state)
            if isinstance(result, ObjectList) or isinstance(result, ObjectGrouping):
                if result.id_types:
                    query_state.needed_scopes = query_state.needed_scopes.set_id_types(result.id_types)
            debugger.log("OPERATOR_RESULT", result)
            debugger.log("OPERATOR_SCOPES_END", Scopes(query_state.final_needed_scopes))
            debugger.end_part(str(self))
            return result
        except QueryError as e:
            e.area_stack.append(self.area)
            debugger.end_part(str(self))
            raise e

@dataclass
class Chain:
    operator_nodes: list['OperatorNode']

    def __str__(self):
        return ''.join(f".{node}" for node in self.operator_nodes)
    
    def __repr__(self):
        return f"Chain({', '.join(str(node) for node in self.operator_nodes)})"

    def run(self, context: 'QueryContext', query_state: 'QueryState') -> 'QueryType':
        for operator_node in self.operator_nodes:
            context = operator_node.run(context, query_state)
        return context
