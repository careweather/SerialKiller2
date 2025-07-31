"""
SerialKiller2 Synchronization Module
Provides network-based synchronization between multiple SK2 instances
"""

import socket
import threading
import time
import json
from typing import Optional, Dict, Any
from enum import Enum

class SyncCommand(Enum):
    WAIT_FOR_SIGNAL = "wait_for_signal"
    SEND_SIGNAL = "send_signal"
    SYNC_POINT = "sync_point"
    READY = "ready"
    START = "start"

class SK2Synchronizer:
    """
    Handles synchronization between multiple SerialKiller2 instances
    Uses TCP sockets for communication
    """
    
    def __init__(self, sync_id: str = "default", port: int = 55555, is_master: bool = False):
        self.sync_id = sync_id
        self.port = port
        self.is_master = is_master
        self.connected_clients: Dict[str, socket.socket] = {}
        self.signals: Dict[str, Any] = {}
        self.server_socket: Optional[socket.socket] = None
        self.client_socket: Optional[socket.socket] = None
        self.running = False
        self.ready_clients = set()
        
    def start_as_master(self, expected_clients: int = 1):
        """Start as master/coordinator instance"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('localhost', self.port))
        self.server_socket.listen(expected_clients)
        self.running = True
        
        print(f"[SYNC] Master instance started on port {self.port}, waiting for {expected_clients} clients...")
        
        # Start server thread
        server_thread = threading.Thread(target=self._server_loop)
        server_thread.daemon = True
        server_thread.start()
        
        return True
    
    def connect_as_client(self, master_host: str = 'localhost', timeout: int = 10):
        """Connect as client instance to master"""
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(timeout)
            self.client_socket.connect((master_host, self.port))
            self.running = True
            
            # Send identification
            self._send_message(self.client_socket, {
                'type': 'identify',
                'sync_id': self.sync_id,
                'timestamp': time.time()
            })
            
            print(f"[SYNC] Connected to master at {master_host}:{self.port}")
            
            # Start client listener thread
            client_thread = threading.Thread(target=self._client_loop)
            client_thread.daemon = True
            client_thread.start()
            
            return True
            
        except Exception as e:
            print(f"[SYNC] Failed to connect to master: {e}")
            return False
    
    def _server_loop(self):
        """Main server loop for master instance"""
        while self.running:
            try:
                client_sock, addr = self.server_socket.accept()
                print(f"[SYNC] Client connected from {addr}")
                
                # Handle client in separate thread
                client_thread = threading.Thread(
                    target=self._handle_client, 
                    args=(client_sock, addr)
                )
                client_thread.daemon = True
                client_thread.start()
                
            except Exception as e:
                if self.running:
                    print(f"[SYNC] Server error: {e}")
                break
    
    def _handle_client(self, client_sock: socket.socket, addr):
        """Handle individual client connection"""
        client_id = None
        try:
            while self.running:
                message = self._receive_message(client_sock)
                if not message:
                    break
                    
                if message['type'] == 'identify':
                    client_id = message['sync_id']
                    self.connected_clients[client_id] = client_sock
                    print(f"[SYNC] Client {client_id} identified")
                    
                elif message['type'] == 'ready':
                    if client_id:
                        self.ready_clients.add(client_id)
                        print(f"[SYNC] Client {client_id} ready ({len(self.ready_clients)} total)")
                        
                elif message['type'] == 'signal':
                    # Broadcast signal to all clients
                    self._broadcast_signal(message['signal'], message.get('data'))
                    
        except Exception as e:
            print(f"[SYNC] Client {addr} error: {e}")
        finally:
            if client_id and client_id in self.connected_clients:
                del self.connected_clients[client_id]
                self.ready_clients.discard(client_id)
            client_sock.close()
    
    def _client_loop(self):
        """Main client loop for non-master instances"""
        try:
            while self.running:
                message = self._receive_message(self.client_socket)
                if not message:
                    break
                    
                if message['type'] == 'signal':
                    signal_name = message['signal']
                    data = message.get('data')
                    self.signals[signal_name] = data
                    print(f"[SYNC] Received signal: {signal_name}")
                    
                elif message['type'] == 'start':
                    print(f"[SYNC] Received start command")
                    self.signals['__start__'] = True
                    
        except Exception as e:
            print(f"[SYNC] Client loop error: {e}")
    
    def wait_for_signal(self, signal_name: str, timeout: int = 30) -> bool:
        """Wait for a specific signal"""
        print(f"[SYNC] Waiting for signal: {signal_name}")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if signal_name in self.signals:
                print(f"[SYNC] Signal {signal_name} received!")
                return True
            time.sleep(0.01)  # Small sleep to prevent busy waiting
            
        print(f"[SYNC] Timeout waiting for signal: {signal_name}")
        return False
    
    def send_signal(self, signal_name: str, data: Any = None):
        """Send a signal to all connected instances"""
        message = {
            'type': 'signal',
            'signal': signal_name,
            'data': data,
            'timestamp': time.time()
        }
        
        if self.is_master:
            self._broadcast_signal(signal_name, data)
        else:
            self._send_message(self.client_socket, message)
    
    def sync_point(self, point_name: str, timeout: int = 30) -> bool:
        """Synchronization point - wait for all instances to reach this point"""
        self.send_signal(f"sync_point_{point_name}")
        return self.wait_for_signal(f"sync_point_{point_name}_complete", timeout)
    
    def mark_ready(self):
        """Mark this instance as ready"""
        if not self.is_master:
            self._send_message(self.client_socket, {
                'type': 'ready',
                'sync_id': self.sync_id,
                'timestamp': time.time()
            })
    
    def start_synchronized_execution(self):
        """Master sends start signal to all clients"""
        if self.is_master:
            self._broadcast_message({
                'type': 'start',
                'timestamp': time.time()
            })
            self.signals['__start__'] = True
    
    def wait_for_start(self, timeout: int = 30) -> bool:
        """Wait for start signal from master"""
        return self.wait_for_signal('__start__', timeout)
    
    def _send_message(self, sock: socket.socket, message: dict):
        """Send JSON message over socket"""
        try:
            data = json.dumps(message).encode('utf-8')
            length = len(data)
            sock.sendall(length.to_bytes(4, byteorder='big'))
            sock.sendall(data)
        except Exception as e:
            print(f"[SYNC] Send error: {e}")
    
    def _receive_message(self, sock: socket.socket) -> Optional[dict]:
        """Receive JSON message from socket"""
        try:
            # Receive message length
            length_bytes = sock.recv(4)
            if len(length_bytes) != 4:
                return None
            length = int.from_bytes(length_bytes, byteorder='big')
            
            # Receive message data
            data = b''
            while len(data) < length:
                chunk = sock.recv(length - len(data))
                if not chunk:
                    return None
                data += chunk
            
            return json.loads(data.decode('utf-8'))
        except Exception as e:
            print(f"[SYNC] Receive error: {e}")
            return None
    
    def _broadcast_signal(self, signal_name: str, data: Any = None):
        """Broadcast signal to all connected clients"""
        message = {
            'type': 'signal',
            'signal': signal_name,
            'data': data,
            'timestamp': time.time()
        }
        self._broadcast_message(message)
    
    def _broadcast_message(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = []
        for client_id, sock in self.connected_clients.items():
            try:
                self._send_message(sock, message)
            except Exception as e:
                print(f"[SYNC] Failed to send to {client_id}: {e}")
                disconnected.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected:
            if client_id in self.connected_clients:
                del self.connected_clients[client_id]
                self.ready_clients.discard(client_id)
    
    def shutdown(self):
        """Shutdown synchronizer"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        if self.client_socket:
            self.client_socket.close()
        print("[SYNC] Synchronizer shutdown")

# Global synchronizer instance
_synchronizer: Optional[SK2Synchronizer] = None

def init_sync(sync_id: str = "sk2_sync", port: int = 55555, is_master: bool = False) -> bool:
    """Initialize synchronization"""
    global _synchronizer
    _synchronizer = SK2Synchronizer(sync_id, port, is_master)
    
    if is_master:
        return _synchronizer.start_as_master()
    else:
        return _synchronizer.connect_as_client()

def sync_wait_signal(signal_name: str, timeout: int = 30) -> bool:
    """Wait for synchronization signal"""
    if _synchronizer:
        return _synchronizer.wait_for_signal(signal_name, timeout)
    return False

def sync_send_signal(signal_name: str, data: Any = None):
    """Send synchronization signal"""
    if _synchronizer:
        _synchronizer.send_signal(signal_name, data)

def sync_point(point_name: str, timeout: int = 30) -> bool:
    """Synchronization point"""
    if _synchronizer:
        return _synchronizer.sync_point(point_name, timeout)
    return False 