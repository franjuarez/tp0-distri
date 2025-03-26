import logging
from .protocol import MessageType, Protocol

class Client():
    def __init__(self, socket, bets_file, lottery):
        self.client_protocol = Protocol(socket)
        self.lottery = lottery
        self.bets_file = bets_file

    def run(self):
        """
        runs the client, receiving messages and handling them
        """
        try:
            while True:
                self.__read_new_message()
        except ConnectionResetError as e:
            logging.error("error: connection closed by client")
        except Exception as e:
                logging.error(f"unexpected error: {e}")
        finally:
                try:
                    self.stop()
                except Exception as e:
                    logging.error(f"action: stop_client | result: fail | error: {e}")
    
    def __read_new_message(self):
        """Lee el tipo de mensaje y maneja NEW_BET."""
        try: 
            msg_type = self.client_protocol.read_new_message()
            
            if msg_type == MessageType.NEW_BET:
                self.__handle_new_bet_message()
            elif msg_type == MessageType.NEW_BETS_BATCH:
                self.__handle_new_bets_batch_message()
            elif msg_type == MessageType.BETS_FINISHED:
                self.__handle_new_bets_finished_message()
            elif msg_type == MessageType.ASK_WINNERS:
                self.__handle_ask_winners_message()
            else:
                logging.error("unknown message type")
        
        except ValueError as e:
            logging.error(f"action: receive_message | result: fail | unknow message: {e}")

    def __handle_new_bet_message(self):
        try:

            bet_data = self.client_protocol.read_new_client_bet()
            self.bets_file.store_bets([bet_data])
            self.client_protocol.send_ack()
            logging.info(f'action: apuesta_almacenada | result: success | dni: {bet_data.document} | numero: {bet_data.number}')
        
        except ValueError as e:
            logging.error(f"action: apuesta_almacenada | result: fail")
            logging.error(f"error: {e}")
            self.client_protocol.send_nack()

    def __handle_new_bets_batch_message(self):
        try:
            bets = self.client_protocol.read_new_bets_batch()
            self.bets_file.store_bets(bets)
            self.client_protocol.send_ack()
            logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(bets)}')

        except ValueError as e:
            logging.error(f"action: apuesta_recibida | result: fail | cantidad: {len(bets) if 'bets_data' in locals() else 0}")
            logging.error(f"error: {e}")
            self.client_protocol.send_nack()

    def __handle_new_bets_finished_message(self):
        agency = self.client_protocol.read_bets_finished()

        self.lottery.agency_finish(agency)

    def __handle_ask_winners_message(self):
        agency = self.client_protocol.read_ask_winners()

        if not self.lottery.are_winner_ready():
            self.client_protocol.send_wait_winners()
            return
        
        agency_winners = self.lottery.get_winners_for_agency(agency)
        self.client_protocol.send_winners(agency_winners)
        logging.info("action: ask_winners | result: success")

    def stop(self):
        try:
            self.client_protocol.close()
        except OSError as e:
            return
        except Exception as e:
            logging.error(f"action: stop_client | result: fail | error: {e}")