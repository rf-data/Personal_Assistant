## txt_file_helper.py
# import
import shutil
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pandas as pd
# from docx import Document

from src.core.config import folder_env_vars
from src.core.memory import app_session

# import src.utils.general_helper as gh
from src.utils.path_helper import ensure_dir, shorten_path


def get_soffice() -> str:
    soffice = shutil.which("soffice")
    if soffice is None:
        raise RuntimeError("LibreOffice (soffice) wurde nicht gefunden.")
        # sudo apt update
        # sudo apt install libreoffice-writer

    return soffice


def convert_docx(
    f_path: str | Path,
    out_format: str,
    overwrite: bool = False,
) -> Path:
    f_path = Path(f_path)

    if not f_path.exists():
        raise FileNotFoundError(f_path)

    if f_path.suffix.lower() != ".docx":
        raise ValueError("Input file must be a DOCX file.")

    save_path = f_path.with_suffix(f".{out_format}")

    if save_path.exists() and not overwrite:
        return save_path

    subprocess.run(
        [
            get_soffice(),
            "--headless",
            "--convert-to",
            out_format,
            "--outdir",
            str(f_path.parent),
            str(f_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    if not save_path.exists():
        raise RuntimeError("LibreOffice did not create the ODT file.")

    print(f"Saved converted file (docx -> {out_format}): '{shorten_path(save_path)}'")

    return save_path


# def convert_docx_to_odt(f_path: str|Path, save=False) -> aw.Document:
#     f_path = Path(f_path)

#     doc = aw.Document(f_path)

#     if save:
#         # Als OpenOffice ODT speichern
#         save_path = f"{f_path.parent}/{f_path.stem}.odt"
#         doc.save(save_path)
#         print(f"Konvertierte Datei gespeichert: '{shorten_path(save_path)}")

#     return doc


def read_docx_tables(path: str) -> Iterator[tuple[int, pd.DataFrame]]:
    doc = Document(path)
    for idx, tbl in enumerate(doc.tables, start=1):
        rows = [[cell.text.strip() for cell in row.cells] for row in tbl.rows]

        if not rows:
            continue

        header = rows[0]
        data = rows[1:]
        df = pd.DataFrame(data, columns=header)

        yield idx, df


def read_docx_text(path):
    doc = Document(path)
    lines = []

    for p in doc.paragraphs:
        if p.text.strip():
            lines.append(p.text.strip())

    return "\n\n".join(lines)


def read_text_file(f_path) -> str:
    txt_file = Path(f_path).read_text(encoding="utf-8")

    return txt_file


# def _flat_sort_nb_elements(extract):
#     cells = extract.get("elements")
#     cells_sorted = sorted(
#                         cells,
#                         key=lambda c: c.get("meta",
#                                             {}).get("cell_id",
#                                                     0)
#                                         #             ,
#                                         # c.get("elements",
#                                         #       {}).get("meta",
#                                         #               {}).get("element_id",
#                                         #                       0)
#                                         )


#     elements_flat = []
#     for cell in cells_sorted:
#         cell_type = cell.get("meta", {}).get("cell_type")

#         if cell_type == "code_block":
#             elements_flat.extend(cell.get("elements"))

#         elif cell_type == "md_block":
#             elements_sorted = sorted(cell.get("elements"),
#                                      key=lambda e: e.get("meta",
#                                                         {}).get("element_id",
#                                                                 0)
#                                     )
#             for element in elements_sorted:
#                 elements_flat.extend(element.get("elements"))
#         else:
#             print("Invalid 'cell_type' found:", cell_type)


#     return elements_flat


def save_text_file(data, file_name, folder, suffix="md"):
    logger = app_session.logger

    folder = ensure_dir(folder)
    f_path = Path(f"{folder}/{file_name}.{suffix}")
    with open(f_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(data)

    logger.info("File saved as %s", shorten_path(f_path))

    return


def extract_docx(path):
    doc = Document(path)

    doc_para = []
    for para in doc.paragraphs:
        doc_para.append(para.text)

    return doc_para


#####################
# BINARY_FILE_PARSER
#####################

# import struct

# with open("data.bin", "rb") as f:
#     header = f.read(8)

# magic, version = struct.unpack(
#     ">4sI",
#     header
# )

# print(magic, version)


# if __name__ == "__main__":
#     # from src.utils.general_helper import load_env_vars

#     # load_env_vars()

#     folder = folder_env_vars.data_qms

#     files = [f for f in Path(folder).iterdir() if f.suffix == ".docx"]
#     print(f"Length 'files': {len(files)}")

#     for file in files:
#         convert_docx(
#             f_path=file,
#             out_format="odt",
#             overwrite=False,
#         )
