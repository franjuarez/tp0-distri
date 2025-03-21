import socket
from enum import Enum
from . import utils


class MessageType(Enum):
    NEW_BET = 0
    ACK = 1
    NEW_BETS_BATCH = 2
    NACK = 3

class Protocol:
    def __init__(self, client_socket):
        self.client_socket = client_socket

    def __recvall(self, skt, n):
        return skt.recv(n, socket.MSG_WAITALL)

    def __read_field(self, sock, size):
        """Lee un campo de tamaño variable correctamente."""
        try:
            raw_len = self.__recvall(sock, size)
            field_len = int.from_bytes(raw_len, "big")
            return self.__recvall(sock, field_len).decode("utf-8")
        except Exception as e:
            raise ValueError(f"Error al leer campo: {e}")

    def send_ack(self):
        """Envía un mensaje ACK al cliente."""
        self.client_socket.sendall(MessageType.ACK.value.to_bytes(1, "big"))
    
    def send_nack(self):
        """Envía un mensaje NACK al cliente."""
        self.client_socket.sendall(MessageType.NACK.value.to_bytes(1, "big"))
    
    def _read_bet_fields(self):
        """Lee y devuelve los campos comunes de una apuesta."""
        name = self.__read_field(self.client_socket, 2)
        last_name = self.__read_field(self.client_socket, 2)
        document = self.__read_field(self.client_socket, 2)
        birth_day = self.__read_field(self.client_socket, 2)
        number = self.__read_field(self.client_socket, 2)
        return name, last_name, document, birth_day, number

    def read_new_client_bet(self):
        """Lee y parsea un mensaje NEW_BET del cliente."""
        agency_number = self.__recvall(self.client_socket, 1).decode("utf-8")
        name, last_name, document, birth_day, number = self._read_bet_fields()

        print(f"agency: {agency_number}, name: {name}, last name: {last_name}, "
            f"document: {document}, birthday: {birth_day}, number: {number}")
        
        return utils.Bet(agency_number, name, last_name, document, birth_day, number)

    def read_new_bets_batch(self):
        """Lee y parsea un mensaje NEW_BETS_BATCH del cliente."""
        try:
            bets = []
            agency_number = int.from_bytes(self.__recvall(self.client_socket, 1), "big")
            bets_amount = int.from_bytes(self.__recvall(self.client_socket, 2), "big")
            
            for _ in range(bets_amount):
                name, last_name, document, birth_day, number = self._read_bet_fields()
                bet = utils.Bet(agency_number, name, last_name, document, birth_day, number)
                bets.append(bet)
            
            return bets
        except ValueError as e:
            raise ValueError(f"Error al leer apuestas: {e}")
        except Exception as e:
            raise ValueError(f"Error inesperado al leer apuestas: {e}")

    def read_new_message(self):
        """Lee y devuelve el tipo de mensaje."""
        msg_type_bytes = self.__recvall(self.client_socket, 1)
        msg_type_int = int.from_bytes(msg_type_bytes, "big")

        try:
            return MessageType(msg_type_int)
        except ValueError:
            raise ValueError(f"Tipo de mensaje desconocido: {msg_type_int}")

    def close(self):
        self.client_socket.close()