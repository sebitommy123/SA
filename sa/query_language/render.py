from ..core.object_list import ObjectList
from ..core.sa_object import SAObject
from ..core.object_grouping import ObjectGrouping
from .errors import assert_query

def render_object_list(objects: ObjectList) -> str:
    result = ""
    for obj in objects.objects:
        result += render_object_as_group(obj)

    return result

def render_object_as_group(objects: ObjectGrouping) -> str:
    """
    Render a list of objects as a group.
    
    Example output:
    #ft_cme_ags_1 (type1, type2, type3..., @source1, @source2, @source3...)
        underlyings (all agree): QQQ, DIA, IWM
        desk (all agree): sp500
        cores@source1: 5
        cores@source2@source3@source4: 3
        ...
    """
    assert_query(len(set(obj.id for obj in objects._objects)) == 1, "All objects in the group must have the same ID")

    # Use ANSI escape codes for color (e.g., bright cyan)
    HEADER_COLOR = "\033[96m"
    RESET_COLOR = "\033[0m"
    header = f"{HEADER_COLOR}{objects.name}{RESET_COLOR}"
    
    # Collect all unique property names
    all_properties = set()
    for obj in objects._objects:
        all_properties.update(obj.properties.keys())
    all_properties = all_properties.intersection(objects.fields)
    
    properties_txt = ""
    
    # Check each property to see if all providers agree
    for field in sorted(all_properties):
        # Get all values for this field from all objects
        field_values = []
        for obj in objects._objects:
            if field in obj.properties:
                field_values.append((obj.source, obj.properties[field]))
        
        # Check if all values are the same
        first_value = field_values[0][1]
        all_same = all(value == first_value for _, value in field_values)
        
        if all_same:
            # All providers agree on the value
            properties_txt += f"    {field}: {first_value}\n"
        else:
            # Providers disagree, show each one with source
            for source, value in field_values:
                properties_txt += f"    {field}@{source}: {value}\n"
    
    return f"{header}\n{properties_txt}"
    

def render_object_individually(obj: SAObject) -> str:
    """
    Render a single SAObject with clean formatting.
    
    Example output:
    #ft_cme_ags_1 (app @config_intent_master)
        underlyings: <QQQ>, <DIA>, <IWM>
        desk: sp500
    """

    types_str = ', '.join(obj.types)
    
    # Format the header line
    header = f"#{obj.id} ({types_str} @{obj.source})"
    
    # Format the properties with consistent indentation
    if obj.properties:
        properties_lines = []
        for key, value in obj.properties.items():
            properties_lines.append(f"    {key}: {value}")
        properties_section = '\n'.join(properties_lines)
        return f"{header}\n{properties_section}"
    else:
        return header
