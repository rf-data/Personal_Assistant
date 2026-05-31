## txt_file_helper.py
# import
from pathlib import Path

# import src.utils.general_helper as gh
from src.utils.path_helper import ensure_dir, shorten_path
from src.core.memory import app_session

def read_text_file(f_path):

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
