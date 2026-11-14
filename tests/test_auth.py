"""Tests for the raw credential probe."""

from __future__ import annotations

import struct

import pytest
from custom_components.blauberg_vento.auth import (
    FUNC_AUTH_REJECTED,
    FUNC_RESPONSE,
    PACKET_START,
    PARAM_DEVICE_SEARCH,
    PROTOCOL_TYPE,
    ProbeAuthError,
    ProbeConnectionError,
    async_probe_credentials,
    build_read,
    read_func_byte,
)

from .conftest import DEVICE_ID, HOST, PASSWORD


def _reply(func: int, password: str = PASSWORD, device_id: str = DEVICE_ID) -> bytes:
    """Build a syntactically valid response frame with a correct checksum."""
    id_bytes = device_id.encode("ascii")
    pwd_bytes = password.encode("ascii")
    payload = (
        bytes([PROTOCOL_TYPE, len(id_bytes)])
        + id_bytes
        + bytes([len(pwd_bytes)])
        + pwd_bytes
        + bytes([func, 0x00])
    )
    return PACKET_START + payload + struct.pack("<H", sum(payload) & 0xFFFF)


def test_build_read_rejects_overlong_password() -> None:
    with pytest.raises(ValueError):
        build_read(DEVICE_ID, "123456789", PARAM_DEVICE_SEARCH)


def test_build_read_rejects_wrong_id_length() -> None:
    with pytest.raises(ValueError):
        build_read("SHORT", PASSWORD, PARAM_DEVICE_SEARCH)


async def test_probe_rejects_malformed_password_without_network() -> None:
    """A password that cannot be encoded is an auth failure, not a crash."""
    with pytest.raises(ProbeAuthError):
        await async_probe_credentials(HOST, DEVICE_ID, "123456789")


def test_read_func_byte_walks_variable_header() -> None:
    assert read_func_byte(_reply(FUNC_RESPONSE)) == FUNC_RESPONSE
    assert read_func_byte(_reply(FUNC_AUTH_REJECTED)) == FUNC_AUTH_REJECTED
    assert read_func_byte(_reply(FUNC_RESPONSE, password="")) == FUNC_RESPONSE


def test_read_func_byte_rejects_bad_checksum() -> None:
    raw = bytearray(_reply(FUNC_AUTH_REJECTED))
    raw[-1] ^= 0xFF
    with pytest.raises(ProbeConnectionError):
        read_func_byte(bytes(raw))


def test_read_func_byte_rejects_garbage() -> None:
    for bad in (b"", b"\xfd\xfd", b"not a frame"):
        with pytest.raises(ProbeConnectionError):
            read_func_byte(bad)
