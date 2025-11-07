from __future__ import annotations
from sa.core.object_grouping import ObjectGrouping, group_objects, regroup_objects, ungroup_objects


class ObjectList:
    _objects: list[ObjectGrouping]

    def __init__(self, objects: list[ObjectGrouping]):
        """
        Create a new ObjectList.
        
        Args:
            objects: List of ObjectGrouping objects
        """
        self._objects = objects
        assert all(isinstance(obj, ObjectGrouping) for obj in self._objects), \
            f"ObjectList must contain ObjectGrouping objects, got {', '.join([type(obj).__name__ for obj in self._objects])}"
    
    def validate_uniqueness(self):
        """Validate that all objects have unique IDs."""
        from sa.query_language.debug import debugger
        debugger.start_part("VALIDATE_UNIQUENESS", "Validate object uniqueness")
        seen = set()
        for obj in self._objects:
            debugger.start_part("VALIDATE_UNIQUENESS_OBJECT", "Validate object uniqueness")
            uids = obj.unique_ids  # This will cache unique_ids, but that's necessary for validation
            assert uids & seen == set(), f"Duplicate object found: {uids}"
            seen.update(uids)
            debugger.end_part("Validate object uniqueness")
        debugger.end_part("Validate object uniqueness")

    def reset(self):
        """Reset all objects that have field overrides or selected fields set."""
        from sa.query_language.debug import debugger
        debugger.start_part("RESET_OBJECTS", "Reset objects")
        
        reset_count = 0
        for obj in self._objects:
            if len(obj._field_overrides) > 0 or obj._selected_fields is not None:
                obj.reset()
                reset_count += 1
        
        debugger.log("RESET_COUNT", f"Reset {reset_count} out of {len(self._objects)} objects")
        debugger.end_part("Reset objects")

    @staticmethod
    def combine(ol1: ObjectList, ol2: ObjectList) -> ObjectList:
        result = ObjectList(regroup_objects(ol1.objects + ol2.objects))
        result.validate_uniqueness()
        return result

    @property
    def objects(self) -> list[ObjectGrouping]:
        return self._objects
    
    def filter_by_type(self, type_name: str) -> 'ObjectList':
        """Filter objects by type.
        
        The filtered result is guaranteed to be unique since it's a subset of this validated list.
        """
        from sa.query_language.debug import debugger
        debugger.start_part("FILTER_LOOKUP", "Filter by type")
        
        matching_objects = []
        for obj in self._objects:
            obj_types = obj.types
            if type_name in obj_types:
                matching_objects.append(obj)
        
        debugger.end_part("Filter by type")
        return ObjectList(matching_objects)
    
    def filter_by_source(self, source_name: str) -> 'ObjectList':
        """Filter objects by source.
        
        The filtered result is guaranteed to be unique since it's a subset of this validated list.
        """
        matching_objects = []
        for obj in self._objects:
            if source_name in obj.sources:
                matching_objects.append(obj.select_sources({source_name}))
        
        return ObjectList(matching_objects)
    
    def get_by_id(self, obj_id: str) -> ObjectList:
        """Get object by ID."""
        from sa.query_language.debug import debugger
        debugger.start_part("GET_BY_ID_LOOKUP", "Lookup ID")
        
        for obj in self._objects:
            if obj.id == obj_id:
                debugger.end_part("Lookup ID")
                return ObjectList([obj])
        
        debugger.end_part("Lookup ID")
        return ObjectList([])
    
    @property
    def unique_ids(self) -> set[tuple[str, str, str]]:
        return {
            uid
            for obj in self._objects
            for uid in obj.unique_ids
        }
    
    @property
    def id_types(self) -> set[tuple[str, str]]:
        return {
            id_type
            for obj in self._objects
            for id_type in obj.id_types
        }

    @property
    def types(self) -> set[str]:
        return {
            type
            for obj in self._objects
            for type in obj.types
        }
    
    def add_object(self, obj: ObjectGrouping):
        uids = obj.unique_ids
        assert uids & self.unique_ids == set(), f"Duplicate object found: {uids}"
        self._objects.append(obj)
    
    def __str__(self) -> str:
        max_show = 10
        if len(self._objects) <= max_show:
            return "ObjectList(" + ", ".join([
                str(obj)
                for obj in self._objects
            ]) + ")"
        else:
            shown = ", ".join([
                str(obj)
                for obj in self._objects[:max_show]
            ])
            remaining = len(self._objects) - max_show
            return f"ObjectList({shown}, ... ({remaining} more))"
    
    def __repr__(self) -> str:
        return self.__str__()