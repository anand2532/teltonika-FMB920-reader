import socket 
import struct 
from typing import Optional, Tuple
from .exception import ConnectionError
from .protocol import PACKET_START, MAX_PACKET_SIZE

class TeltonikaConnection:
    """Handles TCP connection and raw data communication"""

    def __init__(self, socket:Optional[socket.socket] = None):
        self.sock = sock or socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)

    def accept(self, host: str = '0.0.0.0', port: int = 12345) -> Tuple[socket.socket, str]:
        """Accept incoming connection"""
        try:
            self.sock.bind((host, port))
            self.sock.listen(1)
            client_sock, addr = self.sock.accept()
            return TeltonikaConnection(client_sock), addr
        except Exception as e:
            raise ConnectionError(f"Failed to accept connection: {e}")
        
    def receive_packet(self)-> bytes:
        """Receive complete packet"""
        try:
            # Read Header
            header = self.sock.recv(8)
            if not header.startswith(PACKET_START):
                raise ConnectionError("Invalid packet header")
            
            #Get data length
            length = struct.unpack("!I", header[4:])[0]
            if length > MAX_PACKET_SIZE:
                raise ConnectionError(f"Packet too large: {length}")
            
            #Read data
            data = self.sock.recv(length)
            if len(data) != length:
                raise ConnectionError("Incomplete packet")
            
            return data
        except Exception as e:
            raise ConnectionError(f"Failed to receive packet: {e}")
        
    def send_response(self, data: bytes) -> None:
        """Send response to device"""
        try:
            self.sock.send(data)
        except Exception as e:
            raise ConnectionError(f"Failed to send response: {e}")
        
    def close(self) -> None:
        """Close connection"""
        if self.sock:
            self.sock.close()