from typing import Generator
import os, time, logging
from pathlib import Path

class Fmount:
    '''
    Un detecteur de montage de volumes sur Windows (et potentiellement d'autres OS à l'avenir).
     - Il détecte les nouveaux lecteurs installés depuis la dernière vérification.
        - Il peut exécuter une fonction de rappel pour chaque nouveau lecteur détecté.
    '''
    def __init__(self):
        self.drives = list(self.find_drives())
        logging.info(f"Initial drives detected: {self.drives}")
        self.run = True

    def find_drives(self)-> Generator[Path, None, None]:
        for drive in os.listdrives():
            p_drive = Path(drive)
            if p_drive.is_dir():
                yield p_drive
    
    def detect_new_drives(self, callback:callable=None):
        '''
        Detection des nouveaux lecteurs installés depuis la dernière vérification.
        '''
        _drives = []
        # Ajouter les nouveaux lecteurs détectés et exécuter le callback pour chaque nouveau lecteur
        for drive in self.find_drives():
            if drive not in self.drives:
                logging.info(f"New drive detected: {drive}")
                self.drives.append(drive)
                if callback:
                    logging.info(f"Executing callback for drive: {drive}")
                    callback(drive)
            _drives.append(drive)
        # Supprimer les lecteurs qui ne sont plus présents
        for drive in self.drives:
            if drive not in _drives:
                logging.info(f"Drive removed: {drive}")
                self.drives.remove(drive)

    def scan(self, callback:callable=None, delay:float=1.0):
        '''
        Scan des lecteurs montés et exécution du callback pour chaque lecteur détecté.
        '''
        while self.run:
            self.detect_new_drives(callback=callback)
            time.sleep(delay)
        logging.info("Stopped scanning for new drives.")
        
    def stop(self):
        '''
        Arrête le scan des lecteurs montés.
        '''
        self.run = False

if __name__ == "__main__":
    from FUTIL.my_logging import *
    my_logging(console_level=logging.INFO, logfile_level=logging.DEBUG)
    fmount = Fmount()
    def print_new_drive(drive):
        print(f"New drive detected: {drive}")
    fmount.scan(callback=print_new_drive)
        