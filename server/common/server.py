import socket
import logging
import signal
import sys

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

        # TODO: Modify this program to handle signal to graceful shutdown
        # the server
        signal.signal(signal.SIGTERM, self.__stop_signal_handler)

        try:
            while True:
                    client_sock = self.__accept_new_connection()
                    self.__handle_client_connection(client_sock)
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

    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            # TODO: Modify the receive to avoid short-reads
            msg = client_sock.recv(1024).rstrip().decode('utf-8')
            addr = client_sock.getpeername()
            logging.info(f'action: receive_message | result: success | ip: {addr[0]} | msg: {msg}')
            # TODO: Modify the send to avoid short-writes
            client_sock.send("{}\n".format(msg).encode('utf-8'))
        except OSError as e:
            logging.error("action: receive_message | result: fail | error: {e}")
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
    
    def __stop_signal_handler(self, sig, frame):
        self.stop()
        logging.info(f"action: signal_handler | result: success | signal: {sig}")
