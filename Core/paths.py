# Core/paths.py
import os
import sys

def get_base_path():
    """Retourne le chemin de base correct, que l'on soit en script ou en .exe"""
    if hasattr(sys, '_MEIPASS'):
        # Mode PyInstaller (si --onefile, mais utile aussi en --onedir)
        return sys._MEIPASS
    
    # Chemin du fichier actuel
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # On remonte d'un cran car on est dans Core/
    return os.path.dirname(current_dir)

def get_data_path(filename=""):
    """Retourne le chemin vers le dossier Data, gérant le dossier 'lib' de PyInstaller"""
    base = get_base_path()
    
    # En mode compilé avec contents_directory='lib', Data est dans lib/Data
    # On teste si on est dans l'arborescence de l'exe
    if os.path.basename(base) == "lib":
        # On est déjà dans lib
        path = os.path.join(base, "Data")
    else:
        # On teste si lib/Data existe (cas de l'exe lancé depuis la racine)
        lib_data = os.path.join(base, "lib", "Data")
        if os.path.exists(lib_data):
            path = lib_data
        else:
            path = os.path.join(base, "Data")
            
    if filename:
        return os.path.join(path, filename)
    return path
