# Modules/fetch_effects.py
import socket
import json
import time

def trigger_effect_sync():
    payload = {"action": "get_effects"}
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # On met un timeout de 2 secondes
        s.settimeout(2.0)
        s.connect(('127.0.0.1', 8091))
        
        # 1. On envoie le signal de départ
        s.sendall((json.dumps(payload) + "\n").encode())
        print("✅ Signal sent. Dynamic synchronization in progress...")
        
        # 2. LA BOUCLE D'ABSORPTION (Le correctif anti-crash)
        # On reste en ligne et on réceptionne silencieusement tous les paquets 
        # en écho. Ça empêche le serveur principal de crasher sur un "Broken Pipe" 
        # en essayant de nous parler dans le vide.
        try:
            while True:
                data = s.recv(8192)
                if not data:
                    break # Le serveur a terminé
        except socket.timeout:
            # Timeout normal : Premiere a fini d'envoyer tous ses paquets
            pass 
            
        s.close()
        print("✅ Packet transmission complete. The GUI takes over.")
        
    except Exception as e:
        print(f"❌ Main server connection error: {e}")

if __name__ == "__main__":
    trigger_effect_sync()