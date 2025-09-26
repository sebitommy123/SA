from __future__ import annotations
from typing import TYPE_CHECKING
from sa.query_language.argument_parser import ArgumentParser
from sa.query_language.validators import is_valid_primitive
from sa.query_language.chain import Operator

if TYPE_CHECKING:
    from sa.query_language.types import QueryType, Arguments, QueryContext
    from sa.core.object_list import ObjectList

def describe_operator_runner(context: QueryContext, arguments: Arguments, all_data: ObjectList) -> QueryType:
    parser = ArgumentParser("describe")
    parser.validate_context(is_valid_primitive)
    context, args = parser.parse(context, arguments, all_data)
    
    # If input is not an ObjectList, just return str() representation
    if not isinstance(context, ObjectList):
        result = str(context)
        return result
    
    # Handle ObjectList input
    
    if len(context.objects) == 0:
        return "Empty ObjectList"
    
    # Collect basic statistics
    total_count = len(context.objects)
    types = set()
    sources = set()
    
    # Analyze each object to collect types, sources, and properties
    type_properties = {}  # type -> set of properties
    type_sources = {}     # type -> set of sources
    
    for obj in context.objects:
        obj_types = obj.types  # This is a list of types
        obj_source = obj.source
        
        # Add all types from this object
        for obj_type in obj_types:
            types.add(obj_type)
            
            # Track properties for this type
            if obj_type not in type_properties:
                type_properties[obj_type] = set()
                type_sources[obj_type] = set()
            
            type_sources[obj_type].add(obj_source)
            
            # Collect all properties from this object
            for prop_name in obj.properties.keys():
                type_properties[obj_type].add(prop_name)
        
        sources.add(obj_source)
    
    # Build description string
    description_parts = []
    description_parts.append(f"ObjectList with {total_count} objects")
    
    if len(types) > 0:
        types_str = ", ".join(sorted(types))
        description_parts.append(f"Types: {types_str}")
    
    if len(sources) > 0:
        sources_str = ", ".join(sorted(sources))
        description_parts.append(f"Sources: {sources_str}")
    
    # Add schema information for each type
    for obj_type in sorted(types):
        type_count = sum(1 for obj in context.objects if obj_type in obj.types)
        type_sources_list = sorted(type_sources[obj_type])
        properties_list = sorted(type_properties[obj_type])
        
        type_info = f"\n  {obj_type} ({type_count} objects)"
        if type_sources_list:
            type_info += f" from sources: {', '.join(type_sources_list)}"
        
        if properties_list:
            type_info += f"\n    Properties: {', '.join(properties_list)}"
        else:
            type_info += "\n    No properties"
        
        description_parts.append(type_info)
    
    result = "\n".join(description_parts)
    return result

DescribeOperator = Operator(
    name="describe",
    runner=describe_operator_runner
)

def summary_operator_runner(context: QueryContext, arguments: Arguments, all_data: ObjectList) -> QueryType:
    parser = ArgumentParser("summary")
    parser.validate_context(is_valid_primitive)
    context, args = parser.parse(context, arguments, all_data)
    
    # If input is not an ObjectList, just return str() representation
    if not isinstance(context, ObjectList):
        result = str(context)
        return result
    
    # Handle ObjectList input
    
    if len(context.objects) == 0:
        return "Empty ObjectList"
    
    # Collect basic statistics
    total_count = len(context.objects)
    types = set()
    sources = set()
    
    # Analyze each object to collect types, sources, and properties
    type_properties = {}  # type -> set of properties
    type_sources = {}     # type -> set of sources
    property_values = {}  # property -> list of values (for variance calculation)
    
    for obj in context.objects:
        obj_types = obj.types  # This is a list of types
        obj_source = obj.source
        
        # Add all types from this object
        for obj_type in obj_types:
            types.add(obj_type)
            
            # Track properties for this type
            if obj_type not in type_properties:
                type_properties[obj_type] = set()
                type_sources[obj_type] = set()
            
            type_sources[obj_type].add(obj_source)
            
            # Collect all properties from this object
            for prop_name in obj.properties.keys():
                type_properties[obj_type].add(prop_name)
        
        sources.add(obj_source)
        
        # Collect property values for variance calculation
        for prop_name, prop_value in obj.properties.items():
            if prop_name not in property_values:
                property_values[prop_name] = []
            property_values[prop_name].append(prop_value)
    
    # Calculate variance for each property (using unique value count as proxy for variance)
    property_variance = {}
    for prop_name, values in property_values.items():
        # Count unique values as a measure of variance
        unique_values = len(set(str(v) for v in values))
        property_variance[prop_name] = unique_values
    
    # Build description string
    description_parts = []
    description_parts.append(f"ObjectList with {total_count} objects")
    
    if len(types) > 0:
        types_str = ", ".join(sorted(types))
        description_parts.append(f"Types: {types_str}")
    
    if len(sources) > 0:
        sources_str = ", ".join(sorted(sources))
        description_parts.append(f"Sources: {sources_str}")
    
    # Add schema information for each type
    for obj_type in sorted(types):
        type_count = sum(1 for obj in context.objects if obj_type in obj.types)
        type_sources_list = sorted(type_sources[obj_type])
        properties_list = sorted(type_properties[obj_type])
        
        type_info = f"\n  {obj_type} ({type_count} objects)"
        if type_sources_list:
            type_info += f" from sources: {', '.join(type_sources_list)}"
        
        if properties_list:
            # If more than 15 properties, show only the 15 with most variance
            if len(properties_list) > 15:
                # Get properties for this type and their variance scores
                type_property_variance = []
                for prop in properties_list:
                    if prop in property_variance:
                        type_property_variance.append((prop, property_variance[prop]))
                
                # Sort by variance (descending) and take top 15
                type_property_variance.sort(key=lambda x: x[1], reverse=True)
                top_properties = [prop for prop, _ in type_property_variance[:15]]
                type_info += f"\n    Properties ({len(properties_list)} total, showing 15 most variable): {', '.join(top_properties)}"
            else:
                type_info += f"\n    Properties: {', '.join(properties_list)}"
        else:
            type_info += "\n    No properties"
        
        description_parts.append(type_info)
    
    result = "\n".join(description_parts)
    return result

SummaryOperator = Operator(
    name="summary",
    runner=summary_operator_runner
)
