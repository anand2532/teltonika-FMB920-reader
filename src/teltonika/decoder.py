import struct
from datetime import datetime
from typing import Tuple, Optional
from .models import AVLPackets, AVLData, GPSElement, IOElement
from .exceptions import ParsingError
from .protocol import CodecID, PACKET_START

class TeltonikaDecoder:
    """Handles decoding of Teltonika protocol packets"""

    @staticmethod
    def decode_imei(data: bytes) -> Optional[str]:
        """Decodes IMEI from bytes"""
        try:
            length = struct.unpack("!H", data[:2])[0]
            imei = data[2:2+length].decode('ascii')
            return imei
        except Exception as e:
            raise ParsingError(f"Failed to decode IMEI: {e}")
        
    @staticmethod
    def decode_gps(data: bytes) -> Tuple[GPSElement, int]:
        """Decode GPS elements from bytes"""
        try:
            longitude = struct.unpack('!i', data[0:4])[0] / 10000000.0
            latitude = struct.unpack('!i', data[4:8])[0] / 10000000.0
            altitude = struct.unpack('!h', data[8:10])[0]
            angle = struct.unpack('!H', data[10:12])[0]
            satellites = data[12]
            speed = struct.unpack('!H', data[13:15])[0]

            gps = GPSElement(
                longitude = longitude,
                latitude = latitude,
                altitude = altitude,
                angle = angle,
                satellites = satellites,
                speed = speed
            )
            return gps, 15
        except Exception as e:
            raise ParsingError(f"Failed to decode GPS elements: {e}")
        
    @staticmethod
    def decode_io(data: bytes) -> Tuple[IOElement, int]:
        """Decode IO element of bytes"""
        try: 
            event_io_id = data[0]
            n_total = data[1]
            offset = 2

            elements_1b = []
            elements_2b = []
            elements_4b = []
            elements_8b = []

            # Parsing 1-byte elements
            n1 = data[offset]
            offset += 1

            for _ in range(n1):
                io_id = data[offset]
                value = data[offset + 1]
                elements_1b.append({io_id: value})
                offset += 2

            # Parsing 2-byte elements
            n2 = data[offset]
            offset += 2

            for _ in range(n1):
                io_id = data[offset]
                value = data[offset + 1]
                elements_2b.append({io_id: value})
                offset += 2

            # Parsing 4-byte elements
            n4 = data[offset]
            offset += 4

            for _ in range(n1):
                io_id = data[offset]
                value = data[offset + 1]
                elements_4b.append({io_id: value})
                offset += 2

            # Parsing 8-byte elements
            n8 = data[offset]
            offset += 8

            for _ in range(n1):
                io_id = data[offset]
                value = data[offset + 1]
                elements_8b.append({io_id: value})
                offset += 2


            
            