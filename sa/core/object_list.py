from __future__ import annotations
from dataclasses import dataclass
from sa.core.object_grouping import ObjectGrouping, group_objects


class ObjectList:
    _objects: list[ObjectGrouping]
    _type_index: dict[str, list[ObjectGrouping]] = None
    _id_index: dict[str, ObjectGrouping] = None
    _source_index: dict[str, list[ObjectGrouping]] = None

    def __init__(self, objects: list[ObjectGrouping]):
        self._objects = objects
        # Ensure all objects are unique by their unique_id property
        assert all(isinstance(obj, ObjectGrouping) for obj in self._objects), f"ObjectList must contain ObjectGrouping objects, got {', '.join([type(obj).__name__ for obj in self._objects])}"
        seen = set()
        for obj in self._objects:
            uids = obj.unique_ids
            assert uids & seen == set(), f"Duplicate object found: {uids}"
            seen.update(uids)
        
        # Pre-compute indexes for fast filtering
        self._build_type_index()
        self._build_id_index()
        self._build_source_index()

    @property
    def objects(self) -> list[ObjectGrouping]:
        return self._objects
    
    def _build_type_index(self):
        """Build an index of objects by type for fast filtering."""
        self._type_index = {}
        for obj in self._objects:
            for obj_type in obj.types:
                if obj_type not in self._type_index:
                    self._type_index[obj_type] = []
                self._type_index[obj_type].append(obj)
    
    def _build_id_index(self):
        """Build an index of objects by ID for fast filtering."""
        self._id_index = {}
        for obj in self._objects:
            obj_id = obj.id
            assert obj_id not in self._id_index, f"Duplicate object found: {obj_id}"
            self._id_index[obj_id] = obj
    
    def _build_source_index(self):
        """Build an index of objects by source for fast filtering."""
        self._source_index = {}
        for obj in self._objects:
            for source in obj.sources:
                if source not in self._source_index:
                    self._source_index[source] = []
                self._source_index[source].append(obj)
    
    def filter_by_type(self, type_name: str) -> 'ObjectList':
        """Fast filtering by type using pre-computed index."""
        if self._type_index is None:
            self._build_type_index()
        
        matching_objects = self._type_index.get(type_name, [])
        
        # Create ObjectList without triggering __post_init__ to avoid rebuilding indexes
        result = ObjectList.__new__(ObjectList)
        result._objects = matching_objects
        result._type_index = None  # Will be built on demand
        result._id_index = None    # Will be built on demand
        result._source_index = None  # Will be built on demand
        return result
    
    def filter_by_source(self, source_name: str) -> 'ObjectList':
        """Fast filtering by source using pre-computed index."""
        if self._source_index is None:
            self._build_source_index()
        
        matching_objects = self._source_index.get(source_name, [])
        
        # Create ObjectList without triggering __post_init__ to avoid rebuilding indexes
        result = ObjectList.__new__(ObjectList)
        result._objects = matching_objects
        result._type_index = None  # Will be built on demand
        result._id_index = None    # Will be built on demand
        result._source_index = None  # Will be built on demand
        return result
    
    def get_by_id(self, obj_id: str) -> ObjectList:
        if self._id_index is None:
            self._build_id_index()

        matching_object = self._id_index.get(obj_id, None)
        if matching_object is not None:
            return ObjectList([matching_object])
        return ObjectList([])
    
    @property
    def unique_ids(self) -> set[tuple[str, str, str]]:
        return {
            uid
            for obj in self._objects
            for uid in obj.unique_ids
        }
    
    def add_object(self, obj: ObjectGrouping):
        uids = obj.unique_ids
        assert uids & self.unique_ids == set(), f"Duplicate object found: {uids}"
        self._objects.append(obj)
    
    def __str__(self) -> str:
        return "ObjectList(" + ", ".join([
            f"{'|'.join(obj.types)}#{obj.id}"
            for obj in self._objects
        ]) + ")"
    
    def __repr__(self) -> str:
        return self.__str__()