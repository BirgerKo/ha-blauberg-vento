"""Credential probe for Blauberg Vento devices.

Why this module exists
----------------------
``blauberg_vento`` declares and exports ``VentoAuthError`` but never raises it:
``parse_response`` rejects every function byte that is not ``0x06`` with a
generic ``VentoProtocolError``. A wrong password therefore reaches the config
flow as ``CannotConnect`` ("Failed to connect"), which points the user at the
network instead of at the password.

Measured against the live unit (Vento Expert A50 V.2, firmware v0.7,
``001C002958425704``):

    wrong password  -> fdfd 02 10 <id> 04 39393939 07 01 4404   (FUNC = 0x07)
    wrong device id -> no reply at all (the ID is an address filter)
    correct both    -> FUNC = 0x06 with the requested parameters

So ``FUNC = 0x07`` is the device's authentication rejection, and a timeout is
genuinely "not reachable, or not this device ID". This module speaks just
enough of the protocol to tell those two apart, and nothing else: all real
traffic still goes through the upstream library.

Frame layout (B133-4-1EN-02):

    FD FD | 02 | 10 | <16-byte device id> | <pwlen> <password> | <func> | <data> | <crc16 LE>

The checksum is the low 16 bits of the sum of every byte after the two 0xFD.
"""

from __future__ import annotations

import asyncio
import struct

PACKET_START = b"\xfd\xfd"
PROTOCOL_TYPE = 0x02
FUNC_READ = 0x01
FUNC_RESPONSE = 0x06
FUNC_AUTH_REJECTED = 0x07
PARAM_DEVICE_SEARCH = 0x7C
DEFAULT_PORT = 4000


class ProbeAuthError(Exception):
    """The device rejected the password (FUNC = 0x07)."""


class ProbeConnectionError(Exception):
    """The device did not answer, or answered with something unreadable."""


def build_read(device_id: str, password: str, param: int) -> bytes:
    """Build a single-parameter read frame."""
    id_bytes = device_id.encode("ascii")
    if len(id_bytes) != 16:
        raise ValueError(f"Device ID must be 16 characters, got {len(id_bytes)}")
    pwd_bytes = password.encode("ascii")
    if len(pwd_bytes) > 8:
        raise ValueError("Password must be at most 8 characters")
    payload = (
        bytes([PROTOCOL_TYPE, len(id_bytes)])
        + id_bytes
        + bytes([len(pwd_bytes)])
        + pwd_bytes
        + bytes([FUNC_READ, param])
    )
    return PACKET_START + payload + struct.pack("<H", sum(payload) & 0xFFFF)


def read_func_byte(raw: bytes) -> int:
    """Return the function byte of a response frame.

    The header is variable length because both the device ID and the password
    are length-prefixed, so the function byte has to be walked to. The trailing
    checksum is verified first, so a corrupted reply cannot be mistaken for a
    function byte.
    """
    if len(raw) < 6 or raw[:2] != PACKET_START:
        raise ProbeConnectionError("Reply is not a Blauberg Vento frame")
    if struct.unpack("<H", raw[-2:])[0] != sum(raw[2:-2]) & 0xFFFF:
        raise ProbeConnectionError("Reply checksum mismatch")
    id_len = raw[3]
    pwd_len_at = 4 + id_len
    if pwd_len_at >= len(raw):
        raise ProbeConnectionError("Reply is truncated in the device ID")
    func_at = pwd_len_at + 1 + raw[pwd_len_at]
    if func_at >= len(raw):
        raise ProbeConnectionError("Reply is truncated in the password")
    return raw[func_at]


class _ProbeProtocol(asyncio.DatagramProtocol):
    """Capture the first datagram that comes back."""

    def __init__(self, future: asyncio.Future[bytes]) -> None:
        self._future = future

    def datagram_received(self, data: bytes, addr: tuple) -> None:
        if not self._future.done():
            self._future.set_result(data)

    def error_received(self, exc: Exception) -> None:
        if not self._future.done():
            self._future.set_exception(ProbeConnectionError(str(exc)))


async def async_probe_credentials(
    host: str,
    device_id: str,
    password: str,
    port: int = DEFAULT_PORT,
    timeout: float = 3.0,
) -> None:
    """Check one host/ID/password combination.

    Returns None when the credentials are good. Raises ProbeAuthError when the
    credentials cannot be valid (malformed ID or password) or the device
    rejects the password, or ProbeConnectionError when it stays silent.
    """
    try:
        frame = build_read(device_id, password, PARAM_DEVICE_SEARCH)
    except ValueError as err:
        raise ProbeAuthError(str(err)) from err
    loop = asyncio.get_running_loop()
    future: asyncio.Future[bytes] = loop.create_future()
    transport, _ = await loop.create_datagram_endpoint(
        lambda: _ProbeProtocol(future), remote_addr=(host, port)
    )
    try:
        transport.sendto(frame)
        try:
            raw = await asyncio.wait_for(future, timeout)
        except TimeoutError as err:
            raise ProbeConnectionError(
                f"No reply from {host}:{port} for device ID {device_id}"
            ) from err
    finally:
        transport.close()

    func = read_func_byte(raw)
    if func == FUNC_AUTH_REJECTED:
        raise ProbeAuthError("The device rejected the password")
    if func != FUNC_RESPONSE:
        raise ProbeConnectionError(f"Unexpected function byte {func:#04x}")
