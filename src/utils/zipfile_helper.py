## zipfile_helper.py
# import
import zipfile
from pathlib import Path

from src.core.memory import app_session
from src.utils.path_helper import shorten_path


def preview_zip_content(src_path: str) -> None:
    logger = app_session.logger

    logger.info("File '%s'contains following files & folder", shorten_path(src_path))
    with zipfile.ZipFile(src_path, "r") as zip_ref:
        # Gibt eine Liste aller Dateinamen im Archiv aus
        print(zip_ref.namelist())

    return


def unpack_single_zipfile(
    src_path: str, f_name: str, dst_folder: str, password=None
) -> None:
    logger = app_session.logger

    with zipfile.ZipFile(src_path, "r") as zip_ref:
        zip_ref.extract(f_name, pwd=password)

    logger.info(
        "Extracting file '%s' to folder '%s'",
        Path(src_path).name,
        shorten_path(dst_folder),
    )

    return


def unpack_entire_zipfolder(src_path: str, dst_folder: str, password=None) -> None:
    logger = app_session.logger

    # Pfad zur ZIP-Datei und zum Zielordner
    # zip_pfad = "archiv.zip"
    # ziel_ordner = "entpackt_ordner"

    # ZIP-Datei öffnen und komplett entpacken

    with zipfile.ZipFile(src_path, "r") as zip_ref:
        zip_ref.extractall(dst_folder, pwd=password)

    logger.info(
        "Extracting file '%s' to folder '%s'",
        Path(src_path).name,
        shorten_path(dst_folder),
    )

    return
