from common.utils import Bet
from enum import Enum

AGENCY_SIZE = 1
BATCH_SIZE = 2
WINNERS_LIST_LEN = 2
DNI_LEN = 8

class MessageType(Enum):
    NEW_BET = 0
    ACK = 1
    NEW_BETS_BATCH = 2
    NACK = 3
    BETS_FINISHED = 4
    ASK_WINNERS = 5
    WAIT_WINNERS = 6
    WINNERS_READY = 7

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
    
    def read_bets_finished(self):
        """Lee y parsea un mensaje BETS_FINISHED del cliente."""
        return int.from_bytes(self.__recv_all(AGENCY_SIZE), "big")

    def read_ask_winners(self):
        """Lee y parsea un mensaje ASK_WINNERS del cliente."""
        return int.from_bytes(self.__recv_all(AGENCY_SIZE), "big")

    def send_winners(self, winners):
        """Envía un mensaje WINNERS_READY al cliente."""
        self.__send_all(MessageType.WINNERS_READY.value.to_bytes(1, "big"))
        self.__send_all(len(winners).to_bytes(WINNERS_LIST_LEN, "big"))
        for winner in winners:
            self.__send_all(winner.encode("utf-8"))

    def send_wait_winners(self):
        """Envía un mensaje WAIT_WINNERS al cliente."""
        self.__send_all(MessageType.WAIT_WINNERS.value.to_bytes(1, "big"))

    def send_ack(self):
        """Envía un mensaje ACK al cliente."""
        self.__send_all(MessageType.ACK.value.to_bytes(1, "big"))

    def send_nack(self):
        """Envía un mensaje NACK al cliente."""
        self.__send_all(MessageType.NACK.value.to_bytes(1, "big"))

    def close(self):
        self.client_socket.close()