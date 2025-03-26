import socket
import logging
import signal
import sys
from multiprocessing import Process
from multiprocessing.managers import BaseManager
from .bets_file_monitor import BetsFileMonitor
from .client import Client
from .lottery import Lottery

""" Bets storage location. """
STORAGE_FILEPATH = "./bets.csv"

class CustomManager(BaseManager):
    pass


CustomManager.register('BetsFileMonitor', BetsFileMonitor)
CustomManager.register('Lottery', Lottery)

class Server:
    def __init__(self, port, listen_backlog, agency_number):
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self.agency_number = agency_number
        self.clients = []
        self.clients_processes = [] #TODO: cambiar a lista cuando tenga 1 conex?

        self.manager = CustomManager()
        self.manager.start()


    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """
        signal.signal(signal.SIGTERM, self.__stop_signal_handler)

        bets_file = self.manager.BetsFileMonitor(STORAGE_FILEPATH)
        lottery = self.manager.Lottery(self.agency_number, bets_file)

        try:
            while True:
                    client_sock = self.__accept_new_connection()
                    
                    client = Client(client_sock, bets_file, lottery)
                    
                    p = Process(target=client.run)
                    p.start()

                    self.clients.append(client)
                    self.clients_processes.append(p)
        except OSError as e:
            client.stop()
            logging.info(f"server stopped")
        except Exception as e:
            client.stop()
            logging.error(f"action: accept_connection | result: fail | unexpected error: {e}")

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

    def stop(self):
        try:
            self._server_socket.close()
            for client in self.clients:
                client.stop()
            for p in self.clients_processes:
                p.terminate()
                p.join()
        except OSError as e:
            return

    def __stop_signal_handler(self, sig, frame):
        self.stop()
        logging.info(f"action: signal_handler | result: success | signal: {sig}")

