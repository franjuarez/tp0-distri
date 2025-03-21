import socket
import logging
import signal
import sys
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

        signal.signal(signal.SIGTERM, self.__signal_handler)

        while True:
            client_sock = self.__accept_new_connection()
            protocol = Protocol(client_sock)
            self.__handle_client_connection(protocol)

    def stop(self):
        self._server_socket.close()

    def __handle_new_bet_message(self, protocol):
        try:
            bet_data = protocol.read_new_client_bet()
            utils.store_bets([bet_data])
            protocol.send_ack()
            logging.info(f'action: apuesta_almacenada | result: success | dni: {bet_data.document} | numero: {bet_data.number}')
        except ValueError as e:
            logging.error(f"action: apuesta_almacenada | result: fail | dni: {bet_data.document} | numero: {bet_data.number}")
            logging.error(f"error: {e}")

    def __handle_new_bets_batch_message(self, protocol):
        try:
            bets_data = protocol.read_new_bets_batch()
            utils.store_bets(bets_data)
            protocol.send_ack()
            logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets_data)}')
        except Exception as e:
            logging.error(f"action: apuesta_recibida | result: fail | cantidad: {len(bets_data) if 'bets_data' in locals() else 0}")
            logging.error(f"error: {e}")
            try:
                protocol.send_nack()
            except Exception as nack_error:
                logging.error(f"action: send_nack | result: fail | error: {nack_error}")

    def __read_new_message(self, protocol):
        """Lee el tipo de mensaje y maneja NEW_BET."""
        try: 
            msg_type = protocol.read_new_message()
            
            if msg_type == MessageType.NEW_BET:
                self.__handle_new_bet_message(protocol)
            elif msg_type == MessageType.NEW_BETS_BATCH:
                self.__handle_new_bets_batch_message(protocol)
            else:
                raise ValueError(f"Unexpected message type:{msg_type}")
        except ValueError as e:
            logging.error(f"action: receive_message | result: fail | error: {e}")
        except Exception as e:
            logging.error(f"action: receive_message | result: fail | unexpected error: {e}")


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
    
    def __signal_handler(self, sig, frame):
        self.stop()
        logging.info(f"action: signal_handler | result: success | signal: {sig}")
        sys.exit()
