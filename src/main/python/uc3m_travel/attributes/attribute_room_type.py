from .attribute import Attribute

class AttributeRoomType(Attribute):
    def __init__(self, attr_value):
        """"Definition of attribute Roomtype init"""
        super().__init__(r"(SINGLE|DOUBLE|SUITE)", "Invalid roomtype value")
        self.value = attr_value

    def _validate(self, attr_value):
        return super()._validate(attr_value)