"""Validate write denial before syscalls, allowed temp dir_fd writes, and offline."""
import json
import os
from pathlib import Path
import socket
import tempfile

target = Path(os.environ['FTS_DIAG_TARGET'])
with tempfile.TemporaryDirectory(prefix='pr174-guard-') as temporary:
    folder = Path(temporary)
    directory = os.open(folder, os.O_RDONLY | os.O_DIRECTORY)
    try:
        fd = os.open('allowed', os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600, dir_fd=directory)
        os.close(fd)
    finally:
        os.close(directory)
    assert (folder / 'allowed').is_file()
for operation in (
    lambda: (target / '.pr174-forbidden-nonexistent').open('w'),
    lambda: os.open(target / '.pr174-forbidden-nonexistent', os.O_CREAT | os.O_WRONLY, 0o600),
    lambda: os.mkdir(target / '.pr174-forbidden-nonexistent'),
    lambda: socket.create_connection(('127.0.0.1', 1)),
):
    try:
        operation()
    except AssertionError:
        pass
    else:
        raise AssertionError('Diagnostic guard failed')
assert not (target / '.pr174-forbidden-nonexistent').exists()
print(json.dumps(dict(dir_fd_temp_write='allowed', target_writes='denied before syscalls', network='denied')))
