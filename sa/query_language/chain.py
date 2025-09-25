
from dataclasses import dataclass
from typing import Callable, Optional
from sa.query_language.types import QueryContext, Arguments, QueryType, query_type_to_string
from sa.core.object_list import ObjectList
from sa.query_language.errors import print_error_area, QueryArea

@dataclass
class Operator:
    name: str
    runner: Callable[['QueryContext', 'Arguments', 'ObjectList'], 'QueryType']

@dataclass
class OperatorNode:
    operator: 'Operator'
    arguments: list['QueryType']
    area: QueryArea

    def __str__(self):
        return f"{self.operator.name}({', '.join(query_type_to_string(arg) for arg in self.arguments)})"
    
    def __repr__(self):
        return f"OperatorNode({self.operator.name}, {', '.join(query_type_to_string(arg) for arg in self.arguments)})"

    def run(self, context: 'QueryContext', all_data: 'ObjectList') -> 'QueryType':
        try:
            return self.operator.runner(context, self.arguments, all_data)
        except Exception as e:
            print("Error while running this area:")
            print_error_area(self.area)
            raise e

@dataclass
class Chain:
    operator_nodes: list['OperatorNode']

    def __str__(self):
        return f"{''.join(f".{node}" for node in self.operator_nodes)}"
    
    def __repr__(self):
        return f"Chain({', '.join(str(node) for node in self.operator_nodes)})"

    def run(self, context: 'QueryContext', all_data: 'ObjectList') -> 'QueryType':
        for operator_node in self.operator_nodes:
            context = operator_node.run(context, all_data)
        return context


        