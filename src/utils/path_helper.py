# imports
from pathlib import Path

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
    target_dir.mkdir(parents=True, exist_ok=True)

    return p


def shorten_path(path, n=3):
    p = Path(path).parts
    return "/".join(p[-n:])


def create_save_path(name_suffix, file_suffix):  # folder_name,
    # as lazy imports
    # import src.utils.general_helper as gh
    from src.core.memory import session_state

    # gh.load_env_vars()
    # folder = os.getenv("PATH_EVALUATED", None)
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
