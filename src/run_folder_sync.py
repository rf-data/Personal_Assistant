## run_folder_sync.py
# import
from pathlib import Path
import hashlib
import shutil
import os

from src.core.memory import app_session

"""
Was noch fehlt:

# gelöschte Dateien im Ziel ebenfalls löschen
# Fehlerbehandlung
# Ausschlussregeln für .git, __pycache__, große Temp-Dateien etc.
# Dry-run-Modus
# Logging
# Umgang mit Symlinks
"""


def file_hash(path, chunk_size=65536):
    h = hashlib.blake2b()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def build_hash_index(base_dir):
    base_dir = Path(base_dir)
    hashes = {}

    for path in base_dir.rglob("*"):
        if path.is_file():
            rel_path = path.relative_to(base_dir)
            hashes[str(rel_path)] = file_hash(path)

    return hashes


def sync_folders(source_dir, target_dir):
    source_dir = Path(source_dir)
    target_dir = Path(target_dir)

    target_hashes = build_hash_index(target_dir)

    for src_path in source_dir.rglob("*"):
        if not src_path.is_file():
            continue

        rel_path = src_path.relative_to(source_dir)
        dst_path = target_dir / rel_path

        src_hash = file_hash(src_path)
        old_hash = target_hashes.get(str(rel_path))

        if old_hash != src_hash:
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dst_path)
            
            if app_session.logger is not None:
                app_session.logger.info(f"Copied: {rel_path}")

            else:
                print(f"Copied: {rel_path}")

# def changed_files(source_dir, target_hashes):
#     for path in Path(source_dir).rglob("*"):
#         if path.is_file():
#             current = file_hash(path)

#             if target_hashes.get(str(path)) != current:
#                 yield path


# from pathlib import Path
# import hashlib
# import shutil


if __name__ == "__main__":

    source_dir = os.getenv("BACKUP_SOURCE")
    assert source_dir is not None

    target_dir = os.getenv("BACKUP_TARGET")
    assert target_dir is not None

    sync_folders(source_dir, target_dir)