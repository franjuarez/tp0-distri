import socket
import logging
import signal
from .protocol import MessageType, Protocol
from . import utils

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

        signal.signal(signal.SIGTERM, self.__stop_signal_handler)

        try:
            while True:
                    client_sock = self.__accept_new_connection()
                    client_protocol = Protocol(client_sock)
                    self.__handle_client_connection(client_protocol)
        except OSError as e:
            try:
                self.stop()
            except Exception as e:
                logging.error(f"action: stop_server | result: fail | error: {e}")
            logging.info(f"server stopped")
        except Exception as e:
            try:
                self.stop()
            except Exception as e:
                logging.error(f"action: stop_server | result: fail | error: {e}")
            logging.error(f"action: accept_connection | result: fail | unexpected error: {e}")

    def stop(self):
        self._server_socket.close()

    def __read_new_message(self, protocol):
        """Lee el tipo de mensaje y maneja NEW_BET."""
        msg_type = protocol.read_new_message()
        
        if msg_type == MessageType.NEW_CLIENT:
            try:
                bet_data = protocol.read_new_client_bet()
                utils.store_bets([bet_data])
                protocol.send_ack()
                logging.info(f'action: apuesta_almacenada | result: success | dni: {bet_data.document} | numero: {bet_data.number}')
            except Exception as e:
                logging.error(f'action: apuesta_almacenada | result: fail | error: {e}')
                protocol.send_nack()
        else:
            raise ValueError(f"Unexpected message type:{msg_type}")


    def __handle_client_connection(self, protocol):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            self.__read_new_message(protocol)
        except OSError as e:
            logging.error("action: receive_message | result: fail | error: {}".format(e))
        except Exception as e:
            logging.error("action: receive_message or send_message | result: fail | unexpected error: {}".format(e))
        finally:
            protocol.close()

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
    
    def __stop_signal_handler(self, sig, frame):
        self.stop()
        logging.info(f"action: signal_handler | result: success | signal: {sig}")