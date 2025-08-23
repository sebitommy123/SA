import pytest
from sa import SAObject, ObjectList


def test_sa_object_creation():
    """Test creating an SAObject with valid data."""
    obj_data = {
        "__types__": ["person", "employee"],
        "__id__": "12345",
        "__source__": "hr_database"
    }
    
    obj = SAObject(obj_data)
    
    assert obj.types == ["person", "employee"]
    assert obj.id == "12345"
    assert obj.source == "hr_database"


def test_sa_object_validation():
    """Test that SAObject validates required fields."""
    # Missing __types__
    with pytest.raises(AssertionError):
        SAObject({
            "__id__": "12345",
            "__source__": "hr_database"
        })
    
    # Missing __id__
    with pytest.raises(AssertionError):
        SAObject({
            "__types__": ["person"],
            "__source__": "hr_database"
        })
    
    # Missing __source__
    with pytest.raises(AssertionError):
        SAObject({
            "__types__": ["person"],
            "__id__": "12345"
        })


def test_object_list():
    """Test ObjectList creation and usage."""
    obj1 = SAObject({
        "__types__": ["person"],
        "__id__": "1",
        "__source__": "test"
    })
    
    obj2 = SAObject({
        "__types__": ["employee"],
        "__id__": "2",
        "__source__": "test"
    })
    
    obj_list = ObjectList([obj1, obj2])
    
    assert len(obj_list.objects) == 2
    assert obj_list.objects[0].id == "1"
    assert obj_list.objects[1].id == "2" 