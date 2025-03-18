import socket
import logging
import signal
import sys
from . import utils
from enum import Enum

class MessageType(Enum):
    NEW_CLIENT = 0
    ACK = 1

class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        signal.signal(signal.SIGTERM, self.__signal_handler)

        while True:
            client_sock = self.__accept_new_connection()
            self.__handle_client_connection(client_sock)

    def stop(self):
        self._server_socket.close()

    def __read_new_client_bet(self, client_sock):
        """Lee y parsea un mensaje NEW_BET del cliente."""

        def read_field(sock, size):
            """Lee un campo de tamaño variable correctamente."""
            raw_len = utils.recvall(sock, size)
            field_len = int.from_bytes(raw_len, "big")
            return utils.recvall(sock, field_len).decode("utf-8")
        
        name = read_field(client_sock, 2)
        last_name = read_field(client_sock, 2)
        document = read_field(client_sock, 2)
        birth_day = read_field(client_sock, 2)
        number = read_field(client_sock, 2)

        print("name: {}, last name: {}, document: {}, birthday: {}, number: {}".format(name, last_name, document, birth_day, number))
        bet = utils.Bet("1", name, last_name, document,birth_day, number)
        return bet
    
    def __read_new_message(self, client_sock):
        """Lee el tipo de mensaje y maneja NEW_BET."""
        msg_type = utils.recvall(client_sock, 1)
        msg_type = MessageType(int.from_bytes(msg_type, "big"))
        
        if msg_type == MessageType.NEW_CLIENT:
            bet_data = self.__read_new_client_bet(client_sock)
            utils.store_bets([bet_data])
            logging.info(f'action: apuesta_almacenada | result: success | dni: {bet_data.document} | numero: {bet_data.number}')
            client_sock.sendall(MessageType.ACK.value.to_bytes(1, "big"))
        else:
            raise Exception(f"Unexpected message type:{msg_type}")


    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            self.__read_new_message(client_sock)
        except OSError as e:
            logging.error("action: receive_message | result: fail | error: {}".format(e))
        except Exception as e:
            logging.error("action: receive_message or send_message | result: fail | unexpected error: {}".format(e))
        finally:
            client_sock.close()

    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        logging.info('action: accept_connections | result: in_progress')
        c, addr = self._server_socket.accept()
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        return c
    
    def __signal_handler(self, sig, frame):
        self.stop()
        logging.info(f"action: signal_handler | result: success | signal: {sig}")
        sys.exit()
