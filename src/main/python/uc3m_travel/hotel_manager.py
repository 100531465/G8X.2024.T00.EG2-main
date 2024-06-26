"""Module for the hotel manager"""
import json
from datetime import datetime
from freezegun import freeze_time
from uc3m_travel.hotel_management_exception import HotelManagementException
from uc3m_travel.hotel_reservation import HotelReservation
from uc3m_travel.hotel_stay import HotelStay
from uc3m_travel.hotel_management_config import JSON_FILES_PATH
from uc3m_travel.storage.json_store import JsonStore
from uc3m_travel.attributes.attribute_phone_number import AttributePhoneNumber
from uc3m_travel.attributes.attribute_credit_card import AttributeCreditCard
from uc3m_travel.attributes.attribute_room_type import AttributeRoomType
from uc3m_travel.attributes.attribute_arrival_date import AttributeArrivalDate
from uc3m_travel.attributes.attribute_localizer import AttributeLocalizer
from uc3m_travel.attributes.attribute_roomkey import AttributeRoomkey
from uc3m_travel.attributes.attribute_id_card import AttributeIdCard
from uc3m_travel.attributes.attribute_name_surname import AttributeNameSurname
from uc3m_travel.attributes.attribute_num_days import AttributeNumDays


class HotelManager:
    """Class with all the methods for managing reservations and stays"""

    class __HotelManager:
        def __init__(self):
            pass

        def read_data_from_json(self, file_path):
            """reads the content of a json file with two fields: CreditCard and phoneNumber"""
            try:
                with open(file_path, encoding='utf-8') as file:
                    json_data = json.load(file)
            except FileNotFoundError as exception:
                raise HotelManagementException("Wrong file or file path") from exception
            except json.JSONDecodeError as exception:
                raise HotelManagementException("JSON Decode Error - Wrong JSON Format") from exception
            try:
                credit_card_number = json_data["CreditCard"]
                phone_number = json_data["phoneNumber"]
                reservation_request = HotelReservation(id_card="12345678Z",
                                                       credit_card_number=credit_card_number,
                                                       name_surname="John Doe",
                                                       phone_number=phone_number,
                                                       room_type="single",
                                                       num_days=3,
                                                       arrival="20/01/2024")
            except KeyError as exception:
                raise HotelManagementException("JSON Decode Error - Invalid JSON Key") from exception
            if not AttributeCreditCard(credit_card_number):
                raise HotelManagementException("Invalid credit card number")
            # Close the file
            return reservation_request

        # pylint: disable=too-many-arguments
        def room_reservation(self,
                             credit_card: str,
                             name_surname: str,
                             id_card: str,
                             phone_number: str,
                             room_type: str,
                             arrival_date: str,
                             num_days: int) -> str:
            """manges the hotel reservation: creates a reservation and saves it into a json file"""

            AttributeIdCard(id_card)

            room_type = AttributeRoomType(room_type).value

            AttributeNameSurname(name_surname)
            credit_card = AttributeCreditCard(credit_card).value
            arrival_date = AttributeArrivalDate(arrival_date).value
            num_days = AttributeNumDays(num_days).value
            phone_number = AttributePhoneNumber(phone_number).value
            my_reservation = HotelReservation(id_card=id_card,
                                              credit_card_number=credit_card,
                                              name_surname=name_surname,
                                              phone_number=phone_number,
                                              room_type=room_type,
                                              arrival=arrival_date,
                                              num_days=num_days)

            # escribo el fichero Json con todos los datos
            file_store = JSON_FILES_PATH + "store_reservation.json"

            data_list = JsonStore(file_store, "data_list").load_json_store()

            # compruebo que esta reserva no esta en la lista
            for item in data_list:
                if my_reservation.localizer == item["_HotelReservation__localizer"]:
                    raise HotelManagementException("Reservation already exists")
                if my_reservation.id_card == item["_HotelReservation__id_card"]:
                    raise HotelManagementException("This ID card has another reservation")
            # añado los datos de mi reserva a la lista , a lo que hubiera
            data_list.append(my_reservation.__dict__)

            JsonStore(file_store, data_list).load_json_write()

            return my_reservation.localizer

        def guest_arrival(self, file_input: str) -> str:  # pylint = disable:too-many-locals
            """manages the arrival of a guest with a reservation"""

            input_list = JsonStore(file_input, "input_list").load_json_store()

            # comprobar valores del fichero
            try:
                my_localizer = input_list["Localizer"]
                my_id_card = input_list["IdCard"]
            except KeyError as exception:
                raise HotelManagementException("Error - Invalid Key in JSON") from exception

            AttributeIdCard(my_id_card)

            AttributeLocalizer(my_localizer)
            # self.validate_localizer() hay que validar

            # buscar en almacen
            file_store = JSON_FILES_PATH + "store_reservation.json"

            # leo los datos del fichero , si no existe deber dar error porque el almacen de reservaa
            # debe existir para hacer el checkin
            store_list = JsonStore(file_store, "store_list").load_json_store()
            # compruebo si esa reserva esta en el almacen
            found = False
            for item in store_list:
                if my_localizer == item["_HotelReservation__localizer"]:
                    reservation_days = item["_HotelReservation__num_days"]
                    reservation_room_type = item["_HotelReservation__room_type"]
                    reservation_date_timestamp = item["_HotelReservation__reservation_date"]
                    reservation_credit_card = item["_HotelReservation__credit_card_number"]
                    reservation_date_arrival = item["_HotelReservation__arrival"]
                    reservation_name = item["_HotelReservation__name_surname"]
                    reservation_phone = item["_HotelReservation__phone_number"]
                    reservation_id_card = item["_HotelReservation__id_card"]
                    found = True

            if not found:
                raise HotelManagementException("Error: localizer not found")
            if my_id_card != reservation_id_card:
                raise HotelManagementException("Error: Localizer is not correct for this IdCard")
            # regenrar clave y ver si coincide
            reservation_date = datetime.fromtimestamp(reservation_date_timestamp)

            with freeze_time(reservation_date):
                new_reservation = HotelReservation(credit_card_number=reservation_credit_card,
                                                   id_card=reservation_id_card,
                                                   num_days=reservation_days,
                                                   room_type=reservation_room_type,
                                                   arrival=reservation_date_arrival,
                                                   name_surname=reservation_name,
                                                   phone_number=reservation_phone)
            if new_reservation.localizer != my_localizer:
                raise HotelManagementException("Error: reservation has been manipulated")

            # compruebo si hoy es la fecha de checkin
            reservation_format = "%d/%m/%Y"
            date_obj = datetime.strptime(reservation_date_arrival, reservation_format)
            if date_obj.date() != datetime.date(datetime.utcnow()):
                raise HotelManagementException("Error: today is not reservation date")

            # genero la room key para ello llamo a Hotel Stay
            my_checkin = HotelStay(idcard=my_id_card, numdays=int(reservation_days),
                                   localizer=my_localizer, roomtype=reservation_room_type)

            # Ahora lo guardo en el almacen nuevo de checkin
            # escribo el fichero Json con todos los datos
            file_store = JSON_FILES_PATH + "store_check_in.json"

            # leo los datos del fichero si existe , y si no existe creo una lista vacia
            room_key_list = JsonStore(file_store, "room_key_list").load_json_store()
            # comprobar que no he hecho otro ckeckin antes
            for item in room_key_list:
                if my_checkin.room_key == item["_HotelStay__room_key"]:
                    raise HotelManagementException("ckeckin  ya realizado")

            # añado los datos de mi reserva a la lista , a lo que hubiera
            room_key_list.append(my_checkin.__dict__)

            JsonStore(file_store, room_key_list).load_json_write()

            return my_checkin.room_key

        def guest_checkout(self, room_key: str) -> bool:
            """manages the checkout of a guest"""
            AttributeRoomkey(room_key)
            # check thawt the roomkey is stored in the checkins file
            file_store = JSON_FILES_PATH + "store_check_in.json"
            room_key_list = JsonStore(file_store, "room_key_check_in").load_json_store()
            # comprobar que esa room_key es la que me han dado
            found = False
            for item in room_key_list:
                if room_key == item["_HotelStay__room_key"]:
                    departure_date_timestamp = item["_HotelStay__departure"]
                    found = True
            if not found:
                raise HotelManagementException("Error: room key not found")

            today = datetime.utcnow().date()
            if datetime.fromtimestamp(departure_date_timestamp).date() != today:
                raise HotelManagementException("Error: today is not the departure day")

            file_store_checkout = JSON_FILES_PATH + "store_check_out.json"
            room_key_list = JsonStore(file_store_checkout, "room_key_check_out").load_json_store()
            for checkout in room_key_list:
                if checkout["room_key"] == room_key:
                    raise HotelManagementException("Guest is already out")

            room_checkout = {"room_key": room_key, "checkout_time": datetime.timestamp(datetime.utcnow())}

            room_key_list.append(room_checkout)

            JsonStore(file_store_checkout, room_key_list).load_json_write()

            return True

    __instance = None

    def __new__(cls):
        """If instance doesn't exist, create instance"""
        if not cls.__instance:
            cls.__instance = cls.__HotelManager()
        return cls.__instance