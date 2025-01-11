from enum import Enum

class CodecID(Enum):
    """Supported Teltonika codec IDs"""
    CODEC8 = 0x08
    CODEC8_EXTENDED = 0x8E
    CODEC16 = 0x10 

class PacketType(Enum):
    """Packet Types"""
    IMEI = 1
    AVL_DATA = 2
    RESPONSE = 3

class Priority(Enum):
    """AVL data priority levels"""
    LOW = 0
    HIGH = 1
    PANIC = 2
    SECURITY = 3

PACKET_START = b'\x00\x00\x00\x00'
IMEI_PACKET_LENGTH = 2                # IMEI length field size
MAX_PACKET_SIZE = 8192

