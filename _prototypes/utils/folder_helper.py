## folder_helper.py
# import

import difflib
from pathlib import Path

from src.utils.path_helper import find_project_root


def meaningful_change(old, new):
    ratio = difflib.SequenceMatcher(None, old, new).ratio()

    return ratio < 0.98


"""
def backup(src, dst):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{dst}/backup_{ts}.tar.gz"
    with tarfile.open(filename, "w:gz") as tar:
        tar.add(src, arcname=".")

backup("my_project", "backups")
"""


"""

import shutil

source_folder = "C:/Users/Kola/Downloads"
destination_folder = "C:/Users/Kola/Documents/Sorted_Files"

# Create folders for file types if they don't exist
file_types = ["Images", "Documents", "Videos"]
for ftype in file_types:
    os.makedirs(os.path.join(destination_folder, ftype), exist_ok=True)

# Move files based on extensions
for filename in os.listdir(source_folder):
    if filename.endswith((".jpg", ".png")):
        shutil.move(os.path.join(source_folder, filename), os.path.join(destination_folder, "Images", filename))
    elif filename.endswith((".pdf", ".docx")):
        shutil.move(os.path.join(source_folder, filename), os.path.join(destination_folder, "Documents", filename))
    elif filename.endswith((".mp4", ".mkv")):
        shutil.move(os.path.join(source_folder, filename), os.path.join(destination_folder, "Videos", filename))

print("Files sorted successfully!")
"""


def context_aware_backup(folder: str, text_type: str = "txt"):
    for file in Path(folder).glob(f"*.{text_type}"):
        backup = Path("backup") / file.name

        if backup.exists():
            if meaningful_change(backup.read_text(), file.read_text()):
                backup.write_text(file.read_text())
        else:
            backup.write_text(file.read_text())

    return


def get_folder_size(
    path: str | Path, *, logger=None, skip_symlinks: bool = True
) -> int:
    root = Path(path)
    total = 0

    for item in root.rglob("*"):
        try:
            if skip_symlinks and item.is_symlink():
                continue

            if item.is_file():
                total += item.stat().st_size

        except OSError as exc:
            if logger:
                logger.debug(
                    "Could not inspect file '%s': %s",
                    item,
                    exc,
                )

    return total


EXCLUDED_DIRS = {
    # ".git",
    # ".venv",
    # "__pycache__",
    # ".mypy_cache",
    # ".pytest_cache",
    "data",
    "logs",
    # "cache",
    "chroma",
    "mlflow",
}


def is_excluded(path: Path, root: Path) -> bool:
    relative_parts = path.relative_to(root).parts
    return (
        any(part in EXCLUDED_DIRS for part in relative_parts)
        or any("cache" in part for part in relative_parts)
        or any(part.startswith(".") for part in relative_parts)
    )


def create_report(
    folder: str | Path = None, output_file: str | Path = "project_report.md"
) -> Path:

    if folder is None:
        root = find_project_root()
    else:
        root = Path(folder).resolve()

    output_path = Path(output_file)

    report: list[str] = [
        f"# Project structure: `{root.name}`",
        "",
    ]

    for path in sorted(root.rglob("*")):
        try:
            if path.resolve() == output_path:
                continue
        except OSError:
            continue

        if is_excluded(path, root):
            continue

        relative_path = path.relative_to(root)
        depth = len(relative_path.parts) - 1
        marker = "📁" if path.is_dir() else "📄"

        report.append(f"{'  ' * depth}- {marker} {path.name}")

    output_path.write_text(
        "\n".join(report) + "\n",
        encoding="utf-8",
    )

    return output_path


# create_report(".")


def folder_profile(
    folder: str | Path = ".", *, limit: int = 10
) -> list[tuple[Path, int]]:

    root = Path(folder)

    results = [
        (item, get_folder_size(item)) for item in root.iterdir() if item.is_dir()
    ]

    results.sort(
        key=lambda entry: entry[1],
        reverse=True,
    )

    top_results = results[:limit]

    for path, size in top_results:
        print(f"{path.name}: {size / (1024**3):.2f} GB")

    return top_results
