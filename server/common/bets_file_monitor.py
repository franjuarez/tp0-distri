from multiprocessing import Lock, Condition, Value
from .bets import Bet
import csv

class BetsFileMonitor:
    def __init__(self, file_path):
        self.file_path = file_path
        self.readers = Value('i', 0) #TODO: cambiar por un numero
        self.lock = Lock()
        self.read_ready = Condition(self.lock)

    def __acquire_read(self):
        """Permite lectura si no hay escritores activos."""
        with self.lock:
            while self.read_ready.wait_for(lambda: self.readers.value >= 0):
                self.readers.value += 1
                break

    def __release_read(self):
        """Libera un lector y notifica si no quedan más lectores."""
        with self.lock:
            self.readers.value -= 1
            if self.readers.value == 0:
                self.read_ready.notify_all()

    def __acquire_write(self):
        """Bloquea nuevas lecturas y espera a que terminen las actuales."""
        with self.lock:
            while self.readers.value != 0:
                self.read_ready.wait()
            self.readers.value = -1

    def __release_write(self):
        """Libera el bloqueo de escritura y permite nuevas lecturas."""
        with self.lock:
            self.readers.value = 0
            self.read_ready.notify_all()

    def store_bets(self, bets):
        """
        Persist the information of each bet in the STORAGE_FILEPATH file.
        Not thread-safe/process-safe.
        """
        try:
            self.__acquire_write()

            with open(self.file_path, 'a+') as file:
                writer = csv.writer(file, quoting=csv.QUOTE_MINIMAL)
                for bet in bets:
                    writer.writerow([bet.agency, bet.first_name, bet.last_name,
                                    bet.document, bet.birthdate, bet.number])
                    
        except Exception as e:
            print(f"Error al almacenar apuestas: {e}")
        finally:
            self.__release_write()

    def load_bets(self):
        """Carga todas las apuestas en una lista (serializable con pickle)."""
        try:
            self.__acquire_read()
            bets = []

            with open(self.file_path, 'r') as file:
                reader = csv.reader(file, quoting=csv.QUOTE_MINIMAL)
                for row in reader:
                    bets.append(Bet(row[0], row[1], row[2], row[3], row[4], row[5]))

            return bets

        except Exception as e:
            print(f"Error al cargar apuestas: {e}")
            return []
        finally:
            self.__release_read()

