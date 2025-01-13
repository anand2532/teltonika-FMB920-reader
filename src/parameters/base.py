from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

class DataType(Enum):
    """Data types for parameters"""
    UINT8 = "Uint8"
    UINT16 = "Uint16"
    UINT32 = "Uint32"
    UINT64 = "Uint64"
    INT8 = "Int8"
    INT16 = "Int16"
    INT32 = "Int32"
    CHAR = "Char"
    STRING = "String"
    DOUBLE = "Double"

@dataclass
class Parameter:
    """Base parameter definition"""
    id: int
    name: str
    data_type: DataType
    default_value: Any
    min_value: Any
    max_value: Any
    description: str = ""
    options: Optional[Dict[int, str]] = None