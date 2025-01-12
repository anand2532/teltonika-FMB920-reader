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

            io = IOElement(
                event_id = event_io_id,
                elements_1b=elements_1b,
                elements_2b=elements_2b,
                elements_4b=elements_4b,
                elements_8b=elements_8b
            )
            return io, offset
        except Exception as e:
            raise ParsingError(f"Failed to decide IO Elements: {e}")
        
    @classmethod
    def decode_avl_data(cls, data: bytes) -> AVLPackets:
        """Decode complete AVLData packet"""
        try:
            codec = data[0]
            number_of_data = data[1]

            records = []
            offset = 2

            for _ in range(number_of_data):
                #Timestamp
                timestamp = struct.unpack("!Q", data[offset:offset + 8])[0]
                timestamp = datetime.fromtimestamp(timestamp / 1000.0)
                offset +=8

                #Priority
                priority = data[offset]
                offset += 1

                #GPS Element
                gps, gps_length = cls.decode_gps(data[offset:])
                offset += gps_length

                #IO Element
                io, io_length = cls.decode_io(data[offset:])
                offset += io_length

                #Create AVL data record
                record = AVLData(
                    timestamp=timestamp,
                    priority=priority,
                    gps=gps,
                    io=io
                )
                records.append(record)

            #Verify record count
            if data[offset] != number_of_data:
                raise ParsingError("Record count mismatch")
            
            return AVLPackets(
                codec=codec,
                data_count=number_of_data,
                records=records
            )
        except Exception as e:
            raise ParsingError(f"Failed to deocde AVL packet: {e}")



            
            