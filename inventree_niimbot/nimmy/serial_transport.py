import serial
from .packet import NiimbotPacket
from .logger_config import get_logger

logger = get_logger()


class SerialTransport:
    """USB serial transport for Niimbot printers."""

    def __init__(self, port="/dev/niimbot", baudrate=115200, timeout=2):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._serial = None

    async def connect(self, address=None):
        port = address or self.port
        self._serial = serial.Serial(port, self.baudrate, timeout=self.timeout)
        logger.info(f"Connected to serial port {port}")
        return True

    async def disconnect(self):
        if self._serial and self._serial.is_open:
            self._serial.close()
            logger.info("Serial port closed.")

    @property
    def is_connected(self):
        return self._serial is not None and self._serial.is_open

    async def write(self, data, char_uuid=None):
        if not self.is_connected:
            raise IOError("Serial port not connected")
        self._serial.write(data)

    def read_packet(self):
        """Read one complete Niimbot packet from serial."""
        # Read until we find the start marker 0x55 0x55
        buf = bytearray()
        while True:
            b = self._serial.read(1)
            if not b:
                return None
            buf.append(b[0])
            if len(buf) >= 2 and buf[-2:] == bytearray(b"\x55\x55"):
                break

        # Read type and length
        header = self._serial.read(2)
        if len(header) < 2:
            return None
        pkt_type = header[0]
        pkt_len = header[1]

        # Read data + checksum + end marker (0xAA 0xAA)
        remaining = self._serial.read(pkt_len + 3)
        if len(remaining) < pkt_len + 3:
            return None

        raw = b"\x55\x55" + header + remaining
        return NiimbotPacket.from_bytes(raw)
