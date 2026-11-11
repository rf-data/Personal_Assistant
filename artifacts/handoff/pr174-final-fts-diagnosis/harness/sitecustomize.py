"""Test-process guards: offline and no writes to the actual PR worktree."""
import os
from pathlib import Path
import socket
import sys
import threading

TARGET = Path(os.environ['FTS_DIAG_TARGET']).resolve()
OPEN_STATE = threading.local()


def forbidden(*args, **kwargs):
    raise AssertionError('Synthetic diagnosis forbids network')


for name in ('connect', 'connect_ex', 'bind', 'listen', 'sendto', 'sendmsg'):
    if hasattr(socket.socket, name):
        setattr(socket.socket, name, forbidden)
socket.getaddrinfo = socket.create_connection = forbidden


def under_target(value, dir_fd=None):
    if not isinstance(value, (str, bytes, os.PathLike)):
        return False
    path = Path(os.fsdecode(value))
    if not path.is_absolute():
        base = Path.cwd() if dir_fd in (None, -1) else Path(os.readlink(f'/proc/self/fd/{dir_fd}'))
        path = base / path
    return path.resolve().is_relative_to(TARGET)


def audit(event, args):
    denied = False
    if event == 'open':
        path, mode, flags = args
        writing = (isinstance(mode, str) and any(c in mode for c in 'wax+')) or (
            isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
        )
        denied = bool(writing and not getattr(OPEN_STATE, 'validated', False) and under_target(path))
    elif event in {'os.mkdir', 'os.remove', 'os.rmdir', 'os.chmod', 'os.chown', 'os.utime'}:
        denied = under_target(args[0], args[-1] if isinstance(args[-1], int) else None)
    elif event in {'os.rename', 'os.link', 'os.symlink'}:
        denied = under_target(args[0], args[2] if len(args) > 2 else None) or under_target(args[1], args[3] if len(args) > 3 else None)
    elif event == 'os.truncate':
        denied = under_target(args[0])
    if denied:
        raise AssertionError('Diagnostic attempted a forbidden PR-worktree write')


sys.addaudithook(audit)

# The open audit event omits dir_fd. Validate os.open with its actual base before
# the syscall, and let the audit hook handle builtins.open / pathlib.open normally.
original_open = os.open


def guarded_open(path, flags, mode=0o777, *, dir_fd=None):
    writing = flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
    if writing and under_target(path, dir_fd):
        raise AssertionError('Diagnostic attempted a forbidden PR-worktree write')
    previous = getattr(OPEN_STATE, 'validated', False)
    OPEN_STATE.validated = True
    try:
        return original_open(path, flags, mode, dir_fd=dir_fd)
    finally:
        OPEN_STATE.validated = previous


os.open = guarded_open
