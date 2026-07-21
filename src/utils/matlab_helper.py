## matlab_helper.py
# import
import h5py
from pymatreader import read_mat
from scipy.io import loadmat

from src.core.memory import app_session
from src.utils.path_helper import shorten_path


def load_simple_mat(f_path) -> dict:
    return loadmat(f_path)


def load_read_mat(f_path: str) -> dict:
    return read_mat(f_path)


def preview_h5py_mat(f_path: str) -> None:
    logger = app_session.logger

    with h5py.File(f_path, "r") as file:
        logger.info(
            "File '%s'contains following keys:\n%s",
            shorten_path(f_path),
            list(file.keys()),
        )

    return


def preview_mat_keys(f_path: str) -> None:
    logger = app_session.logger

    mat_data = load_simple_mat(f_path)
    logger.info(
        "File '%s'contains following keys:\n%s", shorten_path(f_path), mat_data.keys()
    )

    return


def load_key_from_mat(f_path: str, key: str) -> str:
    mat_data = load_simple_mat(f_path)
    # meine_variable =
    return mat_data[key]
