# Core/server.py
import asyncio
import websockets
import json
from Core.paths import get_data_path
from PyQt6.QtCore import QThread, pyqtSignal

class ServerWorker(QThread):
    log_signal = pyqtSignal(str, str)  
    status_signal = pyqtSignal(bool)   
    effects_signal = pyqtSignal(list)
    tooltip_signal = pyqtSignal(str) 

    def __init__(self):
        super().__init__()
        self.premiere_clients = set()
        self.effects_buffer = [] 

    async def premiere_handler(self, websocket):
        self.log_signal.emit("🟢 Premiere Pro connected!", "#55ff55")
        self.status_signal.emit(True)
        self.premiere_clients.add(websocket)
        try:
            async for message in websocket:
                try:
                    payload = json.loads(message)
                    action = payload.get("action")
                    
                    if action == "sync_done":
                        effects = payload.get("effects", [])
                        # On envoie les données directement au minuteur d'assemblage dans gui.py
                        self.effects_signal.emit(effects)
                    
                    # Maintien de tes anciennes règles au cas où
                    elif action == "sync_effects":
                        effects = payload.get("data", [])
                        self.log_signal.emit(f"✅ {len(effects)} effects received at once!", "#55ff55")
                        self.effects_signal.emit(effects)
                    
                    elif action == "sync_effects_chunk":
                        chunk = payload.get("data", [])
                        idx = payload.get("chunkIndex", 0)
                        total = payload.get("totalChunks", 1)
                        
                        if idx == 0:
                            self.effects_buffer = [] 
                            self.log_signal.emit("⏳ Receiving effects...", "#aaaaaa")
                            
                        self.effects_buffer.extend(chunk) 
                        
                        if idx == total - 1:
                            self.log_signal.emit(f"✅ {len(self.effects_buffer)} effects successfully reconstructed!", "#55ff55")
                            self.effects_signal.emit(list(self.effects_buffer))
                            self.effects_buffer = [] 
                    
                    elif action == "tooltip_error":
                        self.tooltip_signal.emit(payload.get("message"))
                        self.log_signal.emit(f"⚠️ {payload.get('message')}", "#ffaa00")

                    else:
                        log_msg = message if len(message) < 100 else message[:100] + "..."
                        self.log_signal.emit(f"Premiere message: {log_msg}", "#aaaaaa")
                        
                except Exception as e:
                    self.log_signal.emit(f"Payload error: {e}", "#ff5555")
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.log_signal.emit("🔴 Premiere Pro disconnected.", "#ff5555")
            self.status_signal.emit(False)
            self.premiere_clients.remove(websocket)

    async def cli_handler(self, reader, writer):
        data = await reader.read(1024)
        message = data.decode().strip()
        if not message:
            writer.close()
            return
        
        self.log_signal.emit(f"⚡ CLI Command: {message}", "#ffaa00")
        if self.premiere_clients:
            for client in self.premiere_clients:
                await client.send(message)
            writer.write("Success.\n".encode())
        else:
            writer.write("Error.\n".encode())
        await writer.drain()
        writer.close()

    async def serve(self):
        import os
        import json
        
        # Load custom ports
        port_settings_path = get_data_path("port_settings.json")
        ws_port = 8090
        tcp_port = 8091
        if os.path.exists(port_settings_path):
            try:
                with open(port_settings_path, "r") as f:
                    data = json.load(f)
                    ws_port = data.get("ws_port", 8090)
                    tcp_port = data.get("tcp_port", 8091)
            except:
                pass

        ws_server = await websockets.serve(self.premiere_handler, "127.0.0.1", ws_port)
        tcp_server = await asyncio.start_server(self.cli_handler, '127.0.0.1', tcp_port)
        self.log_signal.emit(f"🚀 Server started (Ports: WS={ws_port} & TCP={tcp_port})", "#ffffff")
        await asyncio.gather(ws_server.wait_closed(), tcp_server.serve_forever())

    def run(self):
        asyncio.run(self.serve())