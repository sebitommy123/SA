from __future__ import annotations
from dataclasses import dataclass
from .object_grouping import ObjectGrouping, group_objects


@dataclass
class ObjectList:
    objects: list[ObjectGrouping]
    _type_index: dict[str, list[ObjectGrouping]] = None
    _id_index: dict[str, ObjectGrouping] = None

    def __post_init__(self):
        # Ensure all objects are unique by their unique_id property
        assert all(isinstance(obj, ObjectGrouping) for obj in self.objects), f"ObjectList must contain ObjectGrouping objects, got {', '.join([type(obj).__name__ for obj in self.objects])}"
        seen = set()
        for obj in self.objects:
            uids = obj.unique_ids
            assert uids & seen == set(), f"Duplicate object found: {uids}"
            seen.update(uids)
        
        # Pre-compute indexes for fast filtering
        self._build_type_index()
        self._build_id_index()
    
    def _build_type_index(self):
        """Build an index of objects by type for fast filtering."""
        self._type_index = {}
        for obj in self.objects:
            for obj_type in obj.types:
                if obj_type not in self._type_index:
                    self._type_index[obj_type] = []
                self._type_index[obj_type].append(obj)
    
    def _build_id_index(self):
        """Build an index of objects by ID for fast filtering."""
        self._id_index = {}
        for obj in self.objects:
            obj_id = obj.id
            assert obj_id not in self._id_index, f"Duplicate object found: {obj_id}"
            self._id_index[obj_id] = obj
    
    def filter_by_type(self, type_name: str) -> 'ObjectList':
        """Fast filtering by type using pre-computed index."""
        if self._type_index is None:
            self._build_type_index()
        
        matching_objects = self._type_index.get(type_name, [])
        
        # Create ObjectList without triggering __post_init__ to avoid rebuilding indexes
        result = ObjectList.__new__(ObjectList)
        result.objects = matching_objects
        result._type_index = None  # Will be built on demand
        result._id_index = None    # Will be built on demand
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
            for obj in self.objects
            for uid in obj.unique_ids
        }
    
    def add_object(self, obj: ObjectGrouping):
        uids = obj.unique_ids
        assert uids & self.unique_ids == set(), f"Duplicate object found: {uids}"
        self.objects.append(obj)
    
    def __str__(self) -> str:
        return "ObjectList(" + ", ".join([
            f"{'|'.join(obj.types)}#{obj.id}"
            for obj in self.objects
        ]) + ")"
    
    def __repr__(self) -> str:
        return self.__str__()