from __future__ import annotations
from typing import Optional
from typing import TYPE_CHECKING
from itertools import chain

if TYPE_CHECKING:
    from sa.core.object_grouping import ObjectGrouping
    from sa.core.object_list import ObjectList


class ObjectGroupingCache:
    """Cache for computed properties of ObjectGrouping. All values are pre-computed on initialization."""
    
    def __init__(self, grouping: 'ObjectGrouping'):
        self._grouping = grouping
        
        # Pre-compute all values on initialization
        from sa.query_language.debug import debugger
        
        debugger.start_part("TYPES", "Get types")
        # Use chain.from_iterable to flatten without creating intermediate lists
        self._cached_types = set(chain.from_iterable(obj.types for obj in self._grouping._objects))
        debugger.end_part("Get types")
        
        debugger.start_part("ID_TYPES", "Get id types")
        # obj.id_types already returns a set, so we can chain them directly
        self._cached_id_types = set(chain.from_iterable(obj.id_types for obj in self._grouping._objects))
        debugger.end_part("Get id types")
        
        debugger.start_part("UNIQUE_IDS", "Get unique ids")
        # obj.unique_ids already returns a set, so we can chain them directly
        self._cached_unique_ids = set(chain.from_iterable(obj.unique_ids for obj in self._grouping._objects))
        debugger.end_part("Get unique ids")
        
        debugger.start_part("SOURCES", "Get sources")
        # Use set comprehension for better performance
        self._cached_sources = {obj.source for obj in self._grouping._objects}
        debugger.end_part("Get sources")
    
    def types(self) -> set[str]:
        """Get cached types."""
        return self._cached_types
    
    def id_types(self) -> set[tuple[str, str]]:
        """Get cached id_types."""
        return self._cached_id_types
    
    def unique_ids(self) -> set[tuple[str, str, str]]:
        """Get cached unique_ids."""
        return self._cached_unique_ids
    
    def sources(self) -> set[str]:
        """Get cached sources."""
        return self._cached_sources


class ObjectListCache:
    """Cache for indexes of ObjectList."""
    
    def __init__(self, object_list: Optional['ObjectList'] = None):
        """
        Initialize cache.
        
        Args:
            object_list: The ObjectList this cache belongs to. Can be None if creating a filtered copy (will be bound later).
        """
        self._object_list = object_list
        self._type_index: Optional[dict[str, list['ObjectGrouping']]] = None
        self._id_index: Optional[dict[str, 'ObjectGrouping']] = None
        self._source_index: Optional[dict[str, list['ObjectGrouping']]] = None
    
    def reset(self):
        """Clear all indexes."""
        self._type_index = None
        self._id_index = None
        self._source_index = None
    
    def get_type_index(self) -> dict[str, list['ObjectGrouping']]:
        """Get or build type index."""
        if self._type_index is None:
            self._build_type_index()
        return self._type_index
    
    def get_id_index(self) -> dict[str, 'ObjectGrouping']:
        """Get or build id index."""
        if self._id_index is None:
            self._build_id_index()
        return self._id_index
    
    def get_source_index(self) -> dict[str, list['ObjectGrouping']]:
        """Get or build source index."""
        if self._source_index is None:
            self._build_source_index()
        return self._source_index
    
    def _build_type_index(self):
        """Build an index of objects by type for fast filtering."""
        from sa.query_language.debug import debugger
        debugger.start_part("BUILD_TYPE_INDEX", "Build type index")
        debugger.log("BUILD_TYPE_INDEX_COUNT", f"Building index for {len(self._object_list._objects)} objects")
        
        self._type_index = {}
        for obj in self._object_list._objects:
            obj_types = obj.types  # Use pre-computed cached types
            for obj_type in obj_types:
                if obj_type not in self._type_index:
                    self._type_index[obj_type] = []
                self._type_index[obj_type].append(obj)
        
        debugger.end_part("Build type index")
    
    def _build_id_index(self):
        """Build an index of objects by ID for fast filtering."""
        from sa.query_language.debug import debugger
        debugger.start_part("BUILD_ID_INDEX", "Build ID index")
        debugger.log("BUILD_ID_INDEX_COUNT", f"Building index for {len(self._object_list._objects)} objects")
        
        self._id_index = {}
        for obj in self._object_list._objects:
            obj_id = obj.id
            assert obj_id not in self._id_index, f"Duplicate object found: {obj_id}"
            self._id_index[obj_id] = obj
        
        debugger.end_part("Build ID index")
    
    def _build_source_index(self):
        """Build an index of objects by source for fast filtering."""
        self._source_index = {}
        for obj in self._object_list._objects:
            # Sources are pre-computed in the cache
            for source in obj.sources:
                if source not in self._source_index:
                    self._source_index[source] = []
                self._source_index[source].append(obj)
    
    def filtered_copy(self, filtered_objects: list['ObjectGrouping']) -> 'ObjectListCache':
        """
        Create a filtered copy of this cache containing only indexes for the given objects.
        
        Args:
            filtered_objects: List of ObjectGrouping objects to include in the filtered cache
        
        Returns:
            New ObjectListCache with filtered indexes (only includes the given objects)
        """
        from sa.query_language.debug import debugger
        debugger.start_part("FILTER_CACHE", "Filter cache indexes")
        debugger.log("FILTER_CACHE_COUNT", f"Filtering cache for {len(filtered_objects)} objects")
        
        filtered_cache = ObjectListCache(None)  # Will be bound to new ObjectList
        
        # Use id() to create a set of object identities for O(1) lookup
        # ObjectGrouping is not hashable, but id(obj) returns the memory address which is hashable
        filtered_object_ids = {id(obj) for obj in filtered_objects}
        
        # Filter type index if it exists
        if self._type_index is not None:
            filtered_cache._type_index = {}
            for obj_type, objects in self._type_index.items():
                filtered_objs = [obj for obj in objects if id(obj) in filtered_object_ids]
                if filtered_objs:
                    filtered_cache._type_index[obj_type] = filtered_objs
        
        # Filter ID index if it exists
        if self._id_index is not None:
            filtered_cache._id_index = {
                obj_id: obj for obj_id, obj in self._id_index.items()
                if id(obj) in filtered_object_ids
            }
        
        # Filter source index if it exists
        if self._source_index is not None:
            filtered_cache._source_index = {}
            for source, objects in self._source_index.items():
                filtered_objs = [obj for obj in objects if id(obj) in filtered_object_ids]
                if filtered_objs:
                    filtered_cache._source_index[source] = filtered_objs
        
        debugger.end_part("Filter cache indexes")
        return filtered_cache

