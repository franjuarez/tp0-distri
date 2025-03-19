import socket
from enum import Enum
from . import utils


class MessageType(Enum):
    NEW_CLIENT = 0
    ACK = 1

class Protocol:
    def __init__(self, client_socket):
        self.client_socket = client_socket

    def __recvall(self, skt, n):
        return skt.recv(n, socket.MSG_WAITALL)

    def __read_field(self, sock, size):
        """Lee un campo de tamaño variable correctamente."""
        raw_len = self.__recvall(sock, size)
        field_len = int.from_bytes(raw_len, "big")
        return self.__recvall(sock, field_len).decode("utf-8")

    def send_ack(self):
        """Envía un mensaje ACK al cliente."""
        self.client_socket.sendall(MessageType.ACK.value.to_bytes(1, "big"))
    
    def read_new_client_bet(self):
        """Lee y parsea un mensaje NEW_BET del cliente."""
        agency_number = self.__recvall(self.client_socket, 1).decode("utf-8")
        name = self.__read_field(self.client_socket, 2)
        last_name = self.__read_field(self.client_socket, 2)
        document = self.__read_field(self.client_socket, 2)
        birth_day = self.__read_field(self.client_socket, 2)
        number = self.__read_field(self.client_socket, 2)

        print("agency: {}, name: {}, last name: {}, document: {}, birthday: {}, number: {}".format(agency_number, name, last_name, document, birth_day, number))
        return utils.Bet(agency_number, name, last_name, document,birth_day, number)
    
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