import logging
from multiprocessing import Lock
from .bets import Bet

""" Simulated winner number in the lottery contest. """
LOTTERY_WINNER_NUMBER = 7574

class Lottery():
    def __init__(self, agency_number, bet_file):
        self.agency_number = agency_number
        self.finished_agencies = set()
        self.finished_lock = Lock()
        self.bet_file = bet_file
        self.winners = []

    def has_won(self, bet: Bet) -> bool:
        """ Checks whether a bet won the prize or not. """
        return bet.number == LOTTERY_WINNER_NUMBER

    def agency_finish(self, agency_id):
        """
        Marks an agency as finished and checks if all agencies have finished.
        If all agencies have finished, it calculates the winners.
        """
        with self.finished_lock:
            if agency_id in self.finished_agencies:
                logging.info(f"action: apuestas_finalizadas | result: fail | agency duplicated: {agency_id}")
                return
            
            print(f"adding agency {agency_id}")
            self.finished_agencies.add(agency_id)

            print(f"AF: Finished agencies: {self.finished_agencies}, number: {self.agency_number}")
            
            if len(self.finished_agencies) == self.agency_number:
                bets = self.bet_file.load_bets()
                self.winners = [bet for bet in bets if self.has_won(bet)]
                
                for winner in self.winners:
                    logging.info(f"winner: {winner}")

                logging.info(f"action: sorteo | result: success")

    def are_winner_ready(self):
        """ Returns whether the winners are ready or not. """
        with self.finished_lock: #TODO: ver de sacar el lock
            print(f"WR: Finished agencies: {self.finished_agencies}, number: {self.agency_number}")
            return len(self.finished_agencies) == self.agency_number

    def get_winners_for_agency(self, agency_id):
        """ Returns the winners for a specific agency. """
        if not self.winners:
            return None
        return [winner.document for winner in self.winners if winner.agency == agency_id]