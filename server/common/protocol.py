from common.utils import Bet
from enum import Enum

AGENCY_SIZE = 1
BATCH_SIZE = 2

class MessageType(Enum):
    NEW_BET = 0
    ACK = 1
    NEW_BETS_BATCH = 2
    NACK = 3

class Protocol:
    def __init__(self, client_socket):
        self.client_socket = client_socket


    def __recv_all(self, size):
        data = b'' 
        while len(data) < size:
            pkt = self.client_socket.recv(size - len(data))
            if len(pkt) == 0:
                raise OSError("Couldn't receive all data")
            data += pkt

        return data

    def __send_all(self, data): 
        while len(data) > 0:
            sent = self.client_socket.send(data)
            if sent == 0:
                raise OSError("Couldn't send all data")
            data = data[sent:]

    def read_new_message(self):
        """Lee y devuelve el tipo de mensaje."""
        msg_type_int = int.from_bytes(self.__recv_all(1), "big")
        try:
            return MessageType(msg_type_int)
        except ValueError:
            raise ValueError(f"Tipo de mensaje desconocido: {msg_type_int}")

    def __read_field(self, size):
        """Lee un campo de tamaño variable correctamente."""
        try:
            raw_len = self.__recv_all(size)
            field_len = int.from_bytes(raw_len, "big")
            return self.__recv_all(field_len).decode("utf-8")
        except Exception as e:
            raise ValueError(f"Error al leer campo: {e}")
    
    def read_bet(self, agency):
        """Lee y parsea un mensaje NEW_BET del cliente."""
        data = self.__read_field(1)
        first_name = data
        data = self.__read_field(1)
        last_name = data
        data = self.__read_field(1)
        document = data
        data = self.__read_field(1)
        birthdate = data
        data = self.__read_field(1)
        number = data

        return Bet(agency, first_name, last_name, document, birthdate, number)
    
    def read_new_client_bet(self):
        """Lee y parsea un mensaje NEW_BET del cliente."""
        agency_number = self.__recv_all(1).decode("utf-8")
        bet = self.read_bet(agency_number)

        print(f"agency: {agency_number}, name: {bet.name}, last name: {bet.last_name}, "
            f"document: {bet.document}, birthday: {bet.birth_day}, number: {bet.number}")
        
        return bet


    def read_new_bets_batch(self):
        """Lee y parsea un mensaje NEW_BETS_BATCH del cliente."""
        try:
            agency_number = int.from_bytes(self.__recv_all(AGENCY_SIZE), "big")
            size = int.from_bytes(self.__recv_all(BATCH_SIZE), "big")
            bets = []
            for _ in range(size):
                bets.append(self.read_bet(agency_number))
            return bets
        except ValueError as e: 
            raise ValueError(f"Error al leer apuestas: {e}")
        except Exception as e:
            raise ValueError(f"Error inesperado al leer apuestas: {e}")
        

    def send_ack(self):
        """Envía un mensaje ACK al cliente."""
        self.__send_all(MessageType.ACK.value.to_bytes(1, "big"))

    def send_nack(self):
        """Envía un mensaje NACK al cliente."""
        self.__send_all(MessageType.NACK.value.to_bytes(1, "big"))

    def close(self):
        self.client_socket.close()