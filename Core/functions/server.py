# Core/server.py
import asyncio
import websockets
import json
import threading
from Core.paths import get_data_path
from Core.theme_qss import THEME_USER_COLORS
from Core.configs.port_config import DEFAULT_PORTS
from PyQt6.QtCore import QThread, pyqtSignal

_server_worker_instance = None

def set_server_worker(worker):
    """Called by MainWindow to register the ServerWorker instance"""
    global _server_worker_instance
    _server_worker_instance = worker

def send_to_plugin(payload):
    """
    Thread-safe method to send a command to Premiere Pro via WebSocket.
    Uses the ServerWorker's queue for reliable delivery.
    Returns True if queued, False if server not ready.
    """
    if _server_worker_instance is None:
        return False
    
    return _server_worker_instance.send_to_plugin(payload)

class ServerWorker(QThread):
    log_signal = pyqtSignal(str, str)
    status_signal = pyqtSignal(bool)
    effects_signal = pyqtSignal(list)
    tooltip_signal = pyqtSignal(str)
    version_detected_signal = pyqtSignal(str, str)
    premiere_connected_signal = pyqtSignal()
    bm_ready_signal = pyqtSignal(str, object)

    def __init__(self):
        super().__init__()
        self.premiere_clients = set()
        self.effects_buffer = [] 
        self._clients_lock = asyncio.Lock() 
        self._outgoing_queue = asyncio.Queue(maxsize=200)
        self._loop = None
        self._server_ready = threading.Event()
        self._premiere_connected = threading.Event()
        self._ws_server = None
        self._tcp_server = None
        self._running = False

    async def premiere_handler(self, websocket):
        async with self._clients_lock:
            self.premiere_clients.add(websocket)
            self._premiere_connected.set()
        
        self.log_signal.emit("🟢 Premiere Pro connected!", THEME_USER_COLORS["success"])
        self.status_signal.emit(True)
        self.premiere_connected_signal.emit()
        
        try:
            await websocket.send(json.dumps({"action": "get_premiere_version"}))
            async for message in websocket:
                try:
                    payload = json.loads(message)
                    action = payload.get("action")
                    
                    if action == "sync_done":
                        effects = payload.get("effects", [])
                        self.effects_signal.emit(effects)
                    
                    elif action == "sync_effects":
                        effects = payload.get("data", [])
                        self.log_signal.emit(f" {len(effects)} effects received at once!", THEME_USER_COLORS["success"])
                        self.effects_signal.emit(effects)
                    
                    elif action == "sync_effects_chunk":
                        chunk = payload.get("data", [])
                        idx = payload.get("chunkIndex", 0)
                        total = payload.get("totalChunks", 1)
                        
                        if idx == 0:
                            self.effects_buffer = [] 
                            self.log_signal.emit(" Receiving effects...", THEME_USER_COLORS["info_text"])
                        
                        self.effects_buffer.extend(chunk) 
                        
                        if idx == total - 1:
                            self.log_signal.emit(f" {len(self.effects_buffer)} effects successfully reconstructed!", THEME_USER_COLORS["success"])
                            self.effects_signal.emit(list(self.effects_buffer))
                            self.effects_buffer = [] 
                    
                    elif action == "tooltip_error":
                        self.tooltip_signal.emit(payload.get("message"))
                        self.log_signal.emit(f" {payload.get('message')}", THEME_USER_COLORS["warning"])

                    elif action == "log":
                        self.log_signal.emit(f" UXP: {payload.get('message')}", THEME_USER_COLORS["info"])

                    elif action == "bm_ready":
                        self.bm_ready_signal.emit(payload.get("prop", ""), payload.get("value"))

                    elif action == "host_info":
                        from Core.functions.bridge import set_premiere_version
                        host_version = payload.get("version", "")
                        host_name = payload.get("name", "")
                        set_premiere_version(host_version, host_name)
                        self.version_detected_signal.emit(host_version, host_name)
                        self.log_signal.emit(f" Premiere version: {host_version} ({host_name})", THEME_USER_COLORS["success"])

                    else:
                        log_msg = message if len(message) < 100 else message[:100] + "..."
                        self.log_signal.emit(f"Premiere message: {log_msg}", THEME_USER_COLORS["info_text"])
                        
                except Exception as e:
                    self.log_signal.emit(f"Payload error: {e}", THEME_USER_COLORS["error"])
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            async with self._clients_lock:
                if websocket in self.premiere_clients:
                    self.premiere_clients.remove(websocket)
            
            self.log_signal.emit(" Premiere Pro disconnected.", THEME_USER_COLORS["error"])
            self.status_signal.emit(False)
            self._premiere_connected.clear()

    async def cli_handler(self, reader, writer):
        try:
            data = await reader.read(1024)
            message = data.decode().strip()
            if not message:
                writer.close()
                return
            
            self.log_signal.emit(f" CLI Command: {message}", THEME_USER_COLORS["warning"])
            async with self._clients_lock:
                has_clients = bool(self.premiere_clients)
                if has_clients:
                    for client in self.premiere_clients:
                        try:
                            await client.send(message)
                        except Exception as e:
                            self.log_signal.emit(f" Send error: {e}", THEME_USER_COLORS["error"])
            
            if has_clients:
                writer.write("Success.\n".encode())
            else:
                writer.write("Error.\n".encode())
            await writer.drain()
        except Exception as e:
            self.log_signal.emit(f" CLI handler error: {e}", THEME_USER_COLORS["error"])
        finally:
            try:
                writer.close()
            except Exception:
                pass

    async def process_outgoing(self):
        while True:
            try:
                payload = await self._outgoing_queue.get()
                async with self._clients_lock:
                    for client in self.premiere_clients:
                        try:
                            await client.send(json.dumps(payload))
                        except Exception as e:
                            self.log_signal.emit(f" Outgoing send error: {e}", THEME_USER_COLORS["error"])
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.log_signal.emit(f" Queue processing error: {e}", THEME_USER_COLORS["error"])

    async def serve(self):
        import os
        import json
        
        self._loop = asyncio.get_event_loop()
        
        port_settings_path = get_data_path("port_settings.json")
        ws_port = DEFAULT_PORTS["ws_port"]
        tcp_port = DEFAULT_PORTS["tcp_port"]
        if os.path.exists(port_settings_path):
            try:
                with open(port_settings_path, "r") as f:
                    data = json.load(f)
                    ws_port = data.get("ws_port", DEFAULT_PORTS["ws_port"])
                    tcp_port = data.get("tcp_port", DEFAULT_PORTS["tcp_port"])
            except:
                pass

        self._ws_server = await websockets.serve(self.premiere_handler, "127.0.0.1", ws_port)
        self._tcp_server = await asyncio.start_server(self.cli_handler, '127.0.0.1', tcp_port)
        self._server_ready.set()
        self._running = True
        
        self.log_signal.emit(f" Server started (Ports: WS={ws_port} & TCP={tcp_port})", THEME_USER_COLORS["text_white"])
        
        await asyncio.gather(self._ws_server.wait_closed(), self._tcp_server.serve_forever(), self.process_outgoing())

    def run(self):
        asyncio.run(self.serve())

    def start_server(self):
        """Start the server. Call this manually or when auto_connect=True."""
        if not self.isRunning():
            self.start()

    def stop_server(self):
        """Stop the server gracefully."""
        self._running = False
        if self._ws_server:
            self._ws_server.close()
        if self._tcp_server:
            self._tcp_server.close()
        self._server_ready.clear()
        self.quit()
        self.wait(1000)

    def send_to_plugin(self, payload):
        """Thread-safe method to send payload to Premiere via WebSocket."""
        if not self._server_ready.is_set() or self._loop is None:
            return False
        
        def _send():
            loop = self._loop
            if loop is not None:
                asyncio.run_coroutine_threadsafe(
                    self._outgoing_queue.put(payload),
                    loop
                )
        
        thread = threading.Thread(target=_send, daemon=True)
        thread.start()
        return True

    def wait_for_ready(self, timeout=5.0):
        """Attend que le serveur soit prêt (max timeout secondes). Retourne True si prêt."""
        return self._server_ready.wait(timeout=timeout)

    def wait_for_premiere_connection(self, timeout=5.0):
        """Attend qu'une connexion Premiere soit établie (max timeout secondes). Retourne True si connecté."""
        if self._premiere_connected.is_set():
            return True
        return self._premiere_connected.wait(timeout=timeout)