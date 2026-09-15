# imports
import shutil
from pathlib import Path

from src.core.memory import app_session

# from src.core.session import session


def find_project_root() -> Path:
    start = Path(__file__).resolve()

    for p in [start, *start.parents]:
        if (p / "pyproject.toml").exists():
            return p
    raise RuntimeError("Project root not found")


def ensure_dir(f_path: str | Path) -> Path:
    p = Path(f_path)

    target_dir = p.parent if p.suffix else p

    # target_dir.parent.mkdir(parents=True, exist_ok=True)
    target_dir.mkdir(parents=True, exist_ok=True)

    return p


def find_folder_files(
    file_name: str,
    folder: str | Path,
    suffix: str | None = None,
    exact: bool = True,
    recursive: bool = False,
) -> list[Path]:
    #

    folder = Path(folder)

    if not folder.exists():
        raise FileNotFoundError(f"Folder does not exist: {folder}")

    if not folder.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {folder}")

    suffix = suffix.removeprefix(".") if suffix else None

    if exact:
        pattern = f"{file_name}.{suffix}" if suffix else f"{file_name}.*"

    else:
        pattern = f"{file_name}*.{suffix}" if suffix else f"{file_name}*"

    iterator = (
        folder.rglob(pattern, case_sensitive=False)
        if recursive
        else folder.glob(pattern, case_sensitive=False)
    )

    file_matches = [path for path in iterator if path.is_file()]

    app_session.logger.info(
        "Found %s matching file(s):\n%s",
        len(file_matches),
        "\n".join(f"  {shorten_path(path, 4)}" for path in file_matches) or "  none",
    )

    return file_matches


def shorten_path(path, n=3):
    p = Path(path).parts
    return "/".join(p[-n:])


def move_file(src_path: Path, dst_path: Path):
    dst_path = ensure_dir(dst_path)
    src_path = ensure_dir(src_path)

    if dst_path.exists():
        try:
            app_session.logger.error(
                "File already exists at destination path. Hence, file will not be moved."
            )
        except TypeError:
            print(
                "File already exists at destination path. Hence, file will not be moved."
            )
            return

    shutil.move(src_path, dst_path)
    app_session.logger.info(
        "File '%s' has been moved to '%s'",
        shorten_path(src_path),
        shorten_path(dst_path),
    )
    return


def create_save_path(name_suffix, file_suffix):  # folder_name,
    # as lazy imports
    # import src.utils.general_helper as gh
    from src.core.memory import session_state

    # gh.load_env_vars()
    # folder = folder_env_vars("PATH_EVALUATED", None)
    folder = session_state.save_folder
    now = session_state.timestamp  # ", None)
    # run_name = session.model_class # log_file", None)

    f_path = Path(f"{folder}/{now}_{run_name}_{name_suffix}.{file_suffix}")
    ensure_dir(f_path)

    return f_path


def list_files(folder: str | Path | list, suffix: str):
    if isinstance(folder, (str, Path)):
        folder = [folder]

    if not suffix.startswith("."):
        suffix = "." + suffix

    files = []
    for fold in folder:
        fold = ensure_dir(fold)

        if not fold.is_dir():
            if fold.is_file() and fold.suffix == suffix:
                files.append(fold)
            else:
                raise ValueError(
                    f"Provided 'folder' argument is neither a folder not a file carrying the correct suffix:\n{folder} (dtype = {type(folder)})"
                )

        files.extend([f for f in Path(fold).iterdir() if f.suffix == suffix])

    return files
