## folder_helper.py
# import

import difflib
from pathlib import Path


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


def get_folder_size(path):
    total = 0

    for dirpath, _, filenames in os.walk(path):
        for file in filenames:
            try:
                fp = os.path.join(dirpath, file)
                total += os.path.getsize(fp)
            except:
                pass

    return total


def create_report(folder):
    report = []

    for path in Path(folder).rglob("*"):
        depth = len(path.parts)

        report.append("  " * depth + f"- {path.name}")

    with open("project_report.md", "w") as f:
        f.write("\n".join(report))


# create_report(".")


def folder_profile(folder: str = "."):
    results = []

    for item in os.listdir(folder):
        full_path = os.path.join(folder, item)

        if os.path.isdir(full_path):
            size = get_folder_size(full_path)
            results.append((item, size))

    for folder, size in sorted(results, key=lambda x: x[1], reverse=True)[:10]:
        print(f"{folder}: {size / (1024**3):.2f} GB")
