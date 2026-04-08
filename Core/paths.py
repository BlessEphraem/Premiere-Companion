# Core/paths.py
import os
import sys

def get_app_path():
    """Retourne le chemin vers les ressources internes du programme (Assets, etc.)"""
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Alias pour compatibilité
get_base_path = get_app_path

def get_data_path(filename=""):
    """Retourne le chemin vers le dossier Data (externe et persistant)"""
    if hasattr(sys, '_MEIPASS'):
        # En mode compilé, on veut que Data soit à côté de l'EXE, pas dans le dossier temporaire
        base = os.path.dirname(sys.executable)
    else:
        # En mode script, Data est à la racine du projet
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    path = os.path.join(base, "Data")
    
    if not os.path.exists(path):
        try:
            os.makedirs(path, exist_ok=True)
        except:
            pass
            
    if filename:
        return os.path.join(path, filename)
    return path
