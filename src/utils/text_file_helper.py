## txt_md_helper.py
# import
from pathlib import Path


# import src.utils.general_helper as gh
import src.utils.path_helper as ph

def read_text_file(path):

    txt_file = Path(path).read_text(encoding="utf-8")

    return txt_file



def save_text_file(data, file_name, folder, suffix="md"):
    from src.core.memory import session
    logger = session.logger

    folder= ph.ensure_dir(folder)
    f_path = Path(f"{folder}/{file_name}.{suffix}")
    with open(f_path, "w", 
                encoding="utf-8", 
                newline="\n") as f:
        f.write(data)

    logger.info("File saved as %s",
                ph.shorten_path(f_path))

    return 
