from __future__ import annotations
from dataclasses import dataclass
from sa.core.sa_object import SAObject
from sa.query_language.main import ObjectGrouping, ObjectGroupings


@dataclass
class ObjectList:
    objects: list[SAObject]

    def __post_init__(self):
        # Ensure all objects are unique by their unique_id property
        seen = set()
        for obj in self.objects:
            uids = obj.unique_ids
            assert uids & seen == set(), f"Duplicate object found: {uids}"
            seen.update(uids)
    
    @property
    def unique_ids(self) -> set[tuple[str, str, str]]:
        return {
            uid
            for obj in self.objects
            for uid in obj.unique_ids
        }
    
    def add_object(self, obj: SAObject):
        uids = obj.unique_ids
        assert uids & self.unique_ids == set(), f"Duplicate object found: {uids}"
        self.objects.append(obj)

    def group_by_id_types(self) -> list[ObjectList]:
        groupings = ObjectGroupings([])
        for obj in self.objects:
            matching_groupings = groupings.get_groupings_for_id_types(obj.id_types)
            groupings.remove_groupings(matching_groupings)
            matching_groupings = matching_groupings + [ObjectGrouping([obj])]
            new_grouping = ObjectGrouping.combine(matching_groupings)
            groupings.groupings.append(new_grouping)

        return [
            ObjectList(grouping.objects)
            for grouping in groupings.groupings
        ]
    
    def __str__(self) -> str:
        return ", ".join([
            f"{'|'.join(objList.objects[0].types)}#{objList.objects[0].id}"
            for objList in self.group_by_id_types()
        ])
    
    def __repr__(self) -> str:
        return self.__str__()