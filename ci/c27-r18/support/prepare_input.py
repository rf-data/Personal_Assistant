"""CI-only allowlist copy. Does not import application code or modify checkout."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import verify_payload as verifier

PIN = 'e4e6ddb334f15aa164d31a9dce3b9b59aff3a84c17de1d34819e1ed9c3d808b6'
PLAN = Path(__file__).resolve().parents[1]


def verify(root, scope, sender=False):
    command = [sys.executable, '-B', str(PLAN/'support/verify_payload.py'),
               '--manifest', str(PLAN/'support/r16_manifest.json'),
               '--expected-manifest-sha256', PIN, '--root', str(root), '--scope', scope]
    if sender:
        command.append('--allow-source-extras')
    subprocess.run(command, check=True)


def copy_entries(source, target, entries, replace=False):
    root_fd = verifier.absolute_root(str(source))
    try:
        for entry in entries:
            verifier.verify_file(root_fd, entry)
            parts = verifier.components(entry['path'])
            parent = os.dup(root_fd)
            try:
                for part in parts[:-1]:
                    child = verifier.directory(parent, part)
                    os.close(parent)
                    parent = child
                fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent)
                with os.fdopen(fd, 'rb') as stream:
                    raw = stream.read(entry['bytes'] + 1)
                if len(raw) != entry['bytes'] or hashlib.sha256(raw).hexdigest() != entry['sha256']:
                    raise ValueError('Source changed while copying: ' + entry['path'])
            finally:
                os.close(parent)
            destination = target/entry['path']
            destination.parent.mkdir(parents=True, exist_ok=True)
            prior = entry.get('prior_sha256')
            if replace and prior:
                if not destination.is_file() or hashlib.sha256(destination.read_bytes()).hexdigest() != prior:
                    raise ValueError('Overlay prior mismatch: ' + entry['path'])
                destination.unlink()  # Only the new disposable copy, after exact prior hash.
            with destination.open('xb') as stream:
                stream.write(raw)
            destination.chmod(int(entry['mode'], 8))
    finally:
        os.close(root_fd)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--destination', required=True, type=Path)
    parser.add_argument('--namespace', action='store_true')
    args = parser.parse_args()
    raw = (PLAN/'support/r16_manifest.json').read_bytes()
    if hashlib.sha256(raw).hexdigest() != PIN:
        raise ValueError('Manifest pin mismatch')
    manifest = json.loads(raw, object_pairs_hook=verifier.unique_object)
    verify(args.source, 'input', sender=True)
    args.destination.mkdir(parents=False, exist_ok=False)
    learning = args.destination/'learning'
    learning.mkdir()
    copy_entries(args.source, learning, manifest['input_files'])
    verify(learning, 'input')
    if args.namespace:
        verify(PLAN/'acceptance-overlay', 'overlay')
        acceptance = args.destination/'acceptance'
        acceptance.mkdir()
        copy_entries(learning, acceptance, manifest['input_files'])
        copy_entries(PLAN/'acceptance-overlay', acceptance, manifest['overlay_files'], replace=True)
        verify(acceptance, 'acceptance')
    for directory in args.destination.rglob('*'):
        if directory.is_dir():
            directory.chmod(0o755)
    verify(args.source, 'input', sender=True)


if __name__ == '__main__':
    main()
