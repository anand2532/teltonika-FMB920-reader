import socket
import struct
import logging
import threading
from datetime import datetime
import binascii

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TeltonikaServer:
    def __init__(self, host='0.0.0.0', port=12345):
        self.host = host
        self.port = port
        self.sock = None
        self.running = False
        self.codec8_length = 8 + 1 + 15  # Timestamp + Priority + GPS Element
        self.known_imeis = set()

    def start(self):
        """Start TCP server"""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.listen(5)
        self.running = True
        logger.info(f"Server started on {self.host}:{self.port}")

        while self.running:
            try:
                client, address = self.sock.accept()
                logger.info(f"New connection from {address}")
                client_thread = threading.Thread(target=self.handle_client, args=(client, address))
                client_thread.start()
            except Exception as e:
                logger.error(f"Error accepting connection: {e}")

    def handle_client(self, client_socket, address):
        """Handle individual client connection"""
        try:
            # First receive IMEI
            imei = self.receive_imei(client_socket)
            if not imei:
                logger.error(f"Failed to receive IMEI from {address}")
                client_socket.close()
                return

            # Accept all IMEIs and send confirmation
            logger.info(f"Received IMEI: {imei} from {address}")
            self.known_imeis.add(imei)
            client_socket.send(struct.pack("!B", 1))

            # Continue receiving data
            while self.running:
                avl_data = self.receive_avl_data(client_socket)
                if not avl_data:
                    break

                # Send acknowledgment with number of data records received
                num_records = avl_data.get('number_of_data2', 0)
                client_socket.send(struct.pack("!I", num_records))

        except Exception as e:
            logger.error(f"Error handling client {address}: {e}")
        finally:
            client_socket.close()
            logger.info(f"Connection closed for {address}")

    def receive_imei(self, sock):
        """Receive and decode IMEI"""
        try:
            # Receive 2 bytes containing IMEI length
            length_bytes = sock.recv(2)
            if not length_bytes:
                return None
            
            imei_length = struct.unpack("!H", length_bytes)[0]
            if not 0 < imei_length <= 20:  # Reasonable IMEI length
                logger.error(f"Invalid IMEI length: {imei_length}")
                return None

            # Receive IMEI
            imei_bytes = sock.recv(imei_length)
            if not imei_bytes:
                return None

            return imei_bytes.decode('ascii')
        except Exception as e:
            logger.error(f"Error receiving IMEI: {e}")
            return None

    def receive_avl_data(self, sock):
        """Receive and decode AVL data packet"""
        try:
            # Read packet header (4 zeros + 4 length)
            header = sock.recv(8)
            if not header or len(header) != 8:
                return None

            # Verify zeros
            if header[:4] != b'\x00\x00\x00\x00':
                logger.error("Invalid AVL data header")
                return None

            # Get data length
            data_length = struct.unpack("!I", header[4:])[0]
            if not 0 < data_length <= 8192:  # Reasonable packet size limit
                logger.error(f"Invalid data length: {data_length}")
                return None

            # Read AVL data
            data = sock.recv(data_length)
            if not data or len(data) != data_length:
                return None

            # Read CRC
            crc_bytes = sock.recv(4)
            if not crc_bytes or len(crc_bytes) != 4:
                return None

            # Parse AVL data
            return self.parse_avl_data(data)

        except Exception as e:
            logger.error(f"Error receiving AVL data: {e}")
            return None

    def parse_avl_data(self, data):
        """Parse AVL data according to protocol"""
        try:
            codec = data[0]
            number_of_data1 = data[1]
            
            avl_data = []
            offset = 2  # Start after codec and number of data

            for _ in range(number_of_data1):
                # Parse timestamp (8 bytes)
                timestamp = struct.unpack("!Q", data[offset:offset + 8])[0]
                timestamp = datetime.fromtimestamp(timestamp / 1000.0)
                offset += 8

                # Priority (1 byte)
                priority = data[offset]
                offset += 1

                # GPS Element (15 bytes)
                gps = self.parse_gps_element(data[offset:offset + 15])
                offset += 15

                # IO Element (variable length)
                io_element, new_offset = self.parse_io_element(data[offset:])
                offset += new_offset

                record = {
                    'timestamp': timestamp,
                    'priority': priority,
                    'gps': gps,
                    'io': io_element
                }
                avl_data.append(record)
                logger.info(f"Parsed AVL record: {record}")

            # Verify number of data at the end
            number_of_data2 = data[offset]
            if number_of_data1 != number_of_data2:
                logger.error(f"Number of records mismatch: {number_of_data1} != {number_of_data2}")

            return {
                'codec': codec,
                'number_of_data1': number_of_data1,
                'number_of_data2': number_of_data2,
                'records': avl_data
            }

        except Exception as e:
            logger.error(f"Error parsing AVL data: {e}")
            return None

    def parse_gps_element(self, data):
        """Parse GPS element from bytes"""
        try:
            longitude = struct.unpack('!i', data[0:4])[0] / 10000000.0
            latitude = struct.unpack('!i', data[4:8])[0] / 10000000.0
            altitude = struct.unpack('!h', data[8:10])[0]
            angle = struct.unpack('!H', data[10:12])[0]
            satellites = data[12]
            speed = struct.unpack('!H', data[13:15])[0]

            return {
                'longitude': longitude,
                'latitude': latitude,
                'altitude': altitude,
                'angle': angle,
                'satellites': satellites,
                'speed': speed
            }
        except Exception as e:
            logger.error(f"Error parsing GPS element: {e}")
            return None

    def parse_io_element(self, data):
        """Parse IO element from bytes"""
        try:
            event_io_id = data[0]
            n_total = data[1]
            offset = 2

            io_elements = {
                '1b': [],
                '2b': [],
                '4b': [],
                '8b': []
            }

            # Parse 1 byte elements
            n1 = data[offset]
            offset += 1
            for _ in range(n1):
                io_id = data[offset]
                value = data[offset + 1]
                io_elements['1b'].append({'id': io_id, 'value': value})
                offset += 2

            # Parse 2 byte elements
            n2 = data[offset]
            offset += 1
            for _ in range(n2):
                io_id = data[offset]
                value = struct.unpack('!H', data[offset + 1:offset + 3])[0]
                io_elements['2b'].append({'id': io_id, 'value': value})
                offset += 3

            # Parse 4 byte elements
            n4 = data[offset]
            offset += 1
            for _ in range(n4):
                io_id = data[offset]
                value = struct.unpack('!I', data[offset + 1:offset + 5])[0]
                io_elements['4b'].append({'id': io_id, 'value': value})
                offset += 5

            # Parse 8 byte elements
            n8 = data[offset]
            offset += 1
            for _ in range(n8):
                io_id = data[offset]
                value = struct.unpack('!Q', data[offset + 1:offset + 9])[0]
                io_elements['8b'].append({'id': io_id, 'value': value})
                offset += 9

            return {
                'event_io_id': event_io_id,
                'total': n_total,
                'elements': io_elements
            }, offset

        except Exception as e:
            logger.error(f"Error parsing IO element: {e}")
            return None, 0

    def stop(self):
        """Stop the server"""
        self.running = False
        if self.sock:
            self.sock.close()

if __name__ == "__main__":
    # Create and start server
    server = TeltonikaServer(port=12345)  # Change port as needed
    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("Server stopping...")
        server.stop()