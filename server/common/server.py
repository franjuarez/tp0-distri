import socket
import logging
import signal
import sys
from . import utils
from .protocol import MessageType, Protocol

class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self.client_protocol = None

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """
        signal.signal(signal.SIGTERM, self.__signal_handler)

        while True:
            try:
                client_sock = self.__accept_new_connection()
                self.client_protocol = Protocol(client_sock)
                self.__handle_client_connection()
            except Exception as e:
                logging.error(f"action: accept_connection | result: fail | unexpected error: {e}")

    def stop(self):
        self._server_socket.close()
        if self.client_protocol:
            self.client_protocol.close()

    def __handle_client_connection(self):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            self.__read_new_message()
        except OSError as e:
            logging.error("action: receive_message | result: fail | error: {}".format(e))
        except Exception as e:
            logging.error("action: receive_message or send_message | result: fail | unexpected error: {}".format(e))
        finally:
            self.client_protocol.close()

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
    
    def __read_new_message(self):
        """Lee el tipo de mensaje y maneja NEW_BET."""
        try: 
            msg_type = self.client_protocol.read_new_message()
            if msg_type == MessageType.NEW_BET:
                self.__handle_new_bet_message()
            elif msg_type == MessageType.NEW_BETS_BATCH:
                self.__handle_new_bets_batch_message()
            else:
                raise ValueError(f"Unexpected message type:{msg_type}")
        except ValueError as e:
            logging.error(f"action: receive_message | result: fail | error: {e}")
        except Exception as e:
            logging.error(f"action: receive_message | result: fail | unexpected error: {e}")

    def __handle_new_bet_message(self):
        try:
            bet_data = self.client_protocol.read_new_client_bet()
            utils.store_bets([bet_data])
            self.client_protocol.send_ack()
            logging.info(f'action: apuesta_almacenada | result: success | dni: {bet_data.document} | numero: {bet_data.number}')
        except ValueError as e:
            logging.error(f"action: apuesta_almacenada | result: fail")
            logging.error(f"error: {e}")

    def __handle_new_bets_batch_message(self):
        try:
            bets = self.client_protocol.read_new_bets_batch()
            utils.store_bets(bets)
            self.client_protocol.send_ack()
            logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)}')
        except Exception as e:
            logging.error(f"action: apuesta_recibida | result: fail | cantidad: {len(bets) if 'bets_data' in locals() else 0}")
            logging.error(f"error: {e}")
            try:
                self.client_protocol.send_nack()
            except Exception as nack_error:
                logging.error(f"action: send_nack | result: fail | error: {nack_error}")

    def __signal_handler(self, sig, frame):
        self.stop()
        logging.info(f"action: signal_handler | result: success | signal: {sig}")
        sys.exit()

