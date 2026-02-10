'''
Ce module permet de synchoniqer les données d'un périphérique de stockage de masse USB avec un dossier local.
Il utilise fmount.Fmount pour détecter les nouveaux lecteurs montés.
'''
import logging, time, os
from pathlib import Path
import configparser

import pystray
from PIL import Image
import FreeSimpleGUI  as sg
import dirsync

from fmount import Fmount


class FMassStorageSync:
    '''
    Synchonise les données d'un périphérique de stockage de masse USB avec un dossier local.
     - Il détecte les nouveaux lecteurs montés et synchronise les données avec un dossier local.
    '''

    default_sync_interval = 1.0  # Intervalle de scan des volumes montés par défaut en secondes
    default_icon_path = "icon.png"  # Chemin par défaut de l'icône de la barre des tâches
    sleep_before_sync = 2.0  # Délai avant de synchroniser pour que notre popup se place devant l'explorateur de fichiers
    defaut_remote_path = 'DCIM'

    def __init__(self, ini_path:str='fusb_mass_storage_sync.ini'):
        self.ini_path = Path(ini_path)
        self.config = self.read_ini()
        self.fmount = Fmount()
        logging.info(f"FMassStorageSync initialized with local folder: {self.local_folder}")
        try:
            image = Image.open(self.icon_path)
        except Exception:
            image = None
        self.icon = pystray.Icon("FMassStorageSync",
                                 icon=image,
                                 title="FMassStorageSync",
                                 menu=pystray.Menu(
                                     pystray.MenuItem("Ouvrir le dossier cible", self.open_folder),
                                     pystray.MenuItem("Paramètres", self.open_settings),
                                     pystray.MenuItem("Quitter", self.quit)
                                 ))
        sg.theme('dark grey 9')
        sg.set_options(icon=self.icon_path)
        self.icon.run_detached() # Démarre l'icône de la barre des tâches
        self.scan_drives()

    def read_ini(self):
        config = configparser.ConfigParser()
        if self.ini_path.exists():
            config.read(self.ini_path)
            if not config.has_section('Settings'):
                config.add_section('Settings')
            logging.info(f"INI file loaded from {self.ini_path}")
        else:
            logging.warning(f"INI file not found at {self.ini_path}. Using default configuration.")
        return config

    @property
    def local_folder(self):
        return self.config.get('Settings', 'local_folder', fallback=None)
    @local_folder.setter
    def local_folder(self, value):
        self.set_settings('local_folder', value)

    @property
    def remote_path(self):
        remote_path =  self.config.get('Settings', 'remote_path', fallback=None)
        if remote_path is None:
            remote_path = self.defaut_remote_path
            self.set_settings("remote_path", remote_path)
        return remote_path
    @remote_path.setter
    def remote_path(self, value):
        self.set_settings('remote_path', value)

    @property
    def icon_path(self):
        icon_path = self.config.get('Settings', 'icon_path', fallback=None)
        if icon_path is None:
            icon_path = self.default_icon_path  # Définir la valeur par défaut si non définie
            self.set_settings('icon_path', str(icon_path))
        return icon_path
    @icon_path.setter
    def icon_path(self, value):
        self.set_settings('icon_path', value)

    @property
    def sync_interval(self):
        sync_interval = self.config.getfloat('Settings', 'sync_interval', fallback=None)
        if sync_interval is None:
            sync_interval = self.default_sync_interval  # Définir la valeur par défaut si non définie
            self.set_settings('sync_interval', sync_interval) # Enregistrer la valeur par défaut dans le fichier INI
        return sync_interval
    @sync_interval.setter
    def sync_interval(self, value):
        self.set_settings('sync_interval', value)

    def set_settings(self, key:str, value):
        '''Met à jour la config
        '''
        if not self.config.has_section('Settings'):
            self.config.add_section('Settings')
        self.config.set('Settings', key , str(value))
        self.write_ini()


    def write_ini(self):
        '''
        Enregistre la configuration dans un fichier INI.
        '''
        with open(self.ini_path, 'w') as configfile:
            self.config.write(configfile)
        logging.info(f"Configuration saved to INI file at {self.ini_path}")

    def scan_drives(self,*args, **kwargs):
        '''
        Scanne les lecteurs montés et synchronise les données avec le dossier local.
        '''
        logging.debug(f"scan_drives called with args: {args}, kwargs: {kwargs}")
        self.fmount.scan(callback=self.ui_sync_drive, delay=self.sync_interval)

    def ui_sync_drive(self, drive:Path, sleep_before_sync:float=None):
        '''
        Synchronise les données du lecteur avec le dossier local.
        '''
        time.sleep(sleep_before_sync if sleep_before_sync is not None else self.sleep_before_sync)  # Attendre un délai avant de synchroniser pour que notre popup se place devant l'explorateur de fichiers
        filename = sg.popup_get_folder("Repertoire cible de synchronisation", default_path=self.local_folder)
        if filename:
            local_path = Path(filename)
            if local_path.is_dir() and local_path.exists():
                logging.info(f"Selected local folder: {local_path}")
                if filename != self.local_folder:
                    self.local_folder = filename
                    logging.info(f"Local folder updated to: {self.local_folder}")
                self.sync_drive(drive)
            else:
                logging.warning(f"Selected path is not a valid directory: {local_path}")
                sg.popup_error("Le chemin sélectionné n'est pas un répertoire valide. Veuillez sélectionner un dossier existant.")
                self.ui_sync_drive(drive, 0.0)  # Relancer la sélection du dossier

    def sync_drive(self, drive:Path):
        '''
        Synchronise les données du lecteur avec le dossier local.
        (Cette fonction doit être implémentée pour effectuer la synchronisation réelle des fichiers.)
        '''
        logging.info(f"Synchronizing drive {drive} with local folder {self.local_folder}")
        source = Path(drive) / self.remote_path
        target = Path(self.local_folder)
        result = dirsync.sync(sourcedir=source, targetdir=target, action='sync')
        logging.info(f"result = {result}")
        #TODO : sg.popup_animated
        reponse = sg.popup_ok_cancel(
            f"Transfert terminé ({len(result)} fichier(s) copié(s)).\n Voulez vous effacer la source?",
            title="Tranfert des fichiers.",
                 )
        if reponse == "OK":
            logging.info("Supression des fichiers et dossiers source.")
            nb_files = self.del_tree(source)   
            sg.popup_ok(f"{nb_files} fichier(s) supprimé(s) de la source.",
                        title="Nettoyage de la source.")

    def del_tree(self, p:Path, level=0)->int:
        '''
        Vide un repertoire récursivement
        (sans supprimer le répertoir en lui même)
        renvoie le nombre de fichier supprimés
        '''
        nb_files = 0
        for child in p.iterdir():
            if child.is_file():
                child.unlink()
                nb_files+=1
            else:
                nb_files += self.del_tree(child, level+1)
        if level>0:
            p.rmdir()
        return nb_files

    def open_folder(self):
        '''
        Ouvre le dossier local dans l'explorateur de fichiers.
        '''
        if self.local_folder:
            import os
            os.startfile(self.local_folder)
        else:
            logging.warning("Local folder is not set. Cannot open folder.")
    
    def open_settings(self):
        '''
        Ouvre la fenêtre de paramètres (non implémentée).
        '''
        logging.info("Open setting")
        os.system(str(self.ini_path))  # Ouvre le fichier de configuration dans l'éditeur de texte par défaut
    
    def quit(self):
        '''
        Quitte l'application.
        '''
        logging.info("Quitting FMassStorageSync.")
        self.fmount.stop()  # Arrête le scan des lecteurs montés
        self.icon.stop()

if __name__ == "__main__":
    from FUTIL.my_logging import *
    my_logging(console_level=logging.INFO, logfile_level=logging.DEBUG)
    fmss = FMassStorageSync()  