from .attribute import Attribute
from uc3m_travel.hotel_management_exception import HotelManagementException

class AttributePhoneNumber(Attribute):
    def __init__(self, attr_value):
        """"Definition of attribute PhoneNumber init"""
        super().__init__(r"^(\+)[0-9]{9}", "Invalid phone number format")
        self.value = attr_value

    def _validate(self, attr_value):
        return super()._validate(attr_value)
