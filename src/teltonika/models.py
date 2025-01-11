from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

@dataclass
class GPSElement:
    longitude: float
    latitude: float
    altitude: int
    angle: int 
    satellites: int
    speed: int

@dataclass
class IOElement:
    event_id: int
    element_1b: List[Dict[int, int]]
    element_2b: List[Dict[int, int]]
    element_4b: List[Dict[int, int]]
    element_8b: List[Dict[int, int]]

@dataclass
class AVLData:
    timestamp: datetime
    priority: int
    gps: GPSElement
    io: IOElement

@dataclass
class AVLPacket:
    codec: int
    data_count: int
    records: List[AVLData]