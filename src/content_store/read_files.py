"""Linux anonymous sealed response files; fixed ABI, no content execution.

Some standalone CPython builds omit memfd/fcntl wrappers. The fixed libc bridge
follows job_control.guardian's ctypes pattern; it accepts no caller expressions.
Linux UAPI: linux/fcntl.h, asm-generic/fcntl.h, linux/memfd.h.
"""

import ctypes
import fcntl
import os
import sys

from src.content_store.errors import Unavailable

ADD_SEALS = 1033  # F_LINUX_SPECIFIC_BASE (1024) + 9
GET_SEALS = 1034
SEAL_WRITE = 8
ALL_SEALS = 15  # SEAL_SEAL | SEAL_SHRINK | SEAL_GROW | SEAL_WRITE


def anonymous_file():
    if sys.platform != "linux":
        raise Unavailable("Linux sealed response files required")
    if hasattr(os, "memfd_create"):
        return os.memfd_create("content-download", 3)  # CLOEXEC | ALLOW_SEALING
    libc = ctypes.CDLL(None, use_errno=True)
    try:
        create = libc.memfd_create
    except AttributeError:
        raise Unavailable("Sealed response files unavailable") from None
    create.argtypes = (ctypes.c_char_p, ctypes.c_uint)
    create.restype = ctypes.c_int
    fd = create(b"content-download", 3)
    if fd < 0:
        raise OSError(ctypes.get_errno(), "Response snapshot unavailable")
    return fd


def seal(fd):
    fcntl.fcntl(fd, ADD_SEALS, ALL_SEALS)
    if fcntl.fcntl(fd, GET_SEALS) & ALL_SEALS != ALL_SEALS:
        raise Unavailable("Response snapshot could not be sealed")


def check_support():
    fd = anonymous_file()
    try:
        seal(fd)
    finally:
        os.close(fd)
