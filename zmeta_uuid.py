import os
import time
import uuid


def uuid7():
    """
    Generate a UUIDv7 value (time-ordered). Uses stdlib uuid.uuid7 when available.
    """
    uuid7_fn = getattr(uuid, "uuid7", None)
    if uuid7_fn:
        return uuid7_fn()

    ts_ms = int(time.time() * 1000)
    time_high = ts_ms & 0xFFFFFFFFFFFF
    rand_a = int.from_bytes(os.urandom(2), "big") & 0x0FFF
    rand_b = int.from_bytes(os.urandom(8), "big") & 0x3FFFFFFFFFFFFFFF

    uuid_int = (time_high << 80) | (0x7 << 76) | (rand_a << 64) | (0x2 << 62) | rand_b
    return uuid.UUID(int=uuid_int)
