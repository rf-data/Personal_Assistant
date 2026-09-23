# imports
import shutil
from pathlib import Path
from collections import Counter

from src.core.memory import app_session
from src.model_lecture.data_resources import LectureResource
# from src.core.session import session


RESOURCE_FILE_FOLDERS = {
    "audio": "audio",
    "subtitle": "subtitles",
    "transcript": "transcripts",
    "knowledge": "knowledge",
    "visual_analysis": "visual_analysis",
    "metadata": "metadata",
    "document": "documents",
    "image": "images",
    "text": "text",
    "other": "other",
}


def organize_resource_file(
    resource: LectureResource,
    source_path: Path,
    course_root: Path,
    dry_run: bool = False,
) -> Path | None:

    source_path = Path(source_path)

    if not source_path.is_file():
        raise ValueError(f"Source path is not a file: {source_path}")

    dst_folder = get_resource_target_folder(
        resource=resource,
        path=source_path,
    )

    dst_path = course_root / dst_folder / source_path.name

    if source_path.resolve() == dst_path.resolve():
        app_session.logger.debug(
            "File already organized: %s",
            source_path,
        )
        return source_path

    if dst_path.exists():
        app_session.logger.warning(
            "Destination already exists. "
            "File will not be moved:\n"
            "source: %s\n"
            "target: %s",
            source_path,
            dst_path,
        )
        return dst_path

    if dry_run:
        app_session.logger.info(
            "Would move:\n%s\n-> %s",
            source_path,
            dst_path,
        )

        return dst_path

    move_file(source_path, dst_path)
    return dst_path


def get_resource_target_folder(
    resource: LectureResource,
    path: Path,
) -> str:

    file_type = classify_resource_file(path)

    if resource.resource_type == "script":
        return "scripts"

    if resource.resource_type == "exam":
        return "exams"

    if resource.resource_type == "material":
        return "material"

    if file_type == "other":
        app_session.logger.warning(
            "Unclassified file, not moving: %s",
            path,
        )
        return path

    return RESOURCE_FILE_FOLDERS[file_type]


def normalize_name(name: str) -> str:
    return (
        name.casefold()
        .replace("ä", "a")
        .replace("ö", "o")
        .replace("ü", "u")
        .replace("ß", "ss")
    )


def build_file_index(
    folder: str | Path,
) -> list[Path]:

    folder = Path(folder)

    app_session.logger.info("Start building file index")
    if not folder.exists():
        raise FileNotFoundError(f"Folder does not exist: {folder}")

    if not folder.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {folder}")

    files = [path for path in folder.rglob("*") if path.is_file()]

    app_session.logger.info(
        "Built file index with %s files from %s",
        len(files),
        shorten_path(folder, 4),
    )

    return files


def find_indexed_files(
    file_name: str,
    files: list[Path],
    suffix: str | None = None,
    exact: bool = True,
) -> list[Path]:

    search_name = normalize_name(file_name)

    suffix = suffix.removeprefix(".").casefold() if suffix else None

    matches = []

    for path in files:
        if suffix and path.suffix.removeprefix(".").casefold() != suffix:
            continue

        stem = normalize_name(path.stem)  # .casefold()

        if exact:
            is_match = stem == search_name
        else:
            is_match = stem.startswith(search_name)

        if is_match:
            matches.append(path)

    app_session.logger.info(
        "Found %s indexed matching file(s):\n%s",
        len(matches),
        "\n".join(f"  {shorten_path(path, 4)}" for path in matches) or "  none",
    )

    return matches


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


def list_folder_files(folder: Path, recursive: bool = True) -> list[Path]:

    folder = Path(folder)

    app_session.logger.info(
        "Start listing files in folder '%s'", shorten_path(folder, 4)
    )

    if not folder.exists():
        raise FileNotFoundError(f"Folder does not exist: {folder}")

    if not folder.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {folder}")

    pattern = "*.*"

    iterator = (
        folder.rglob(pattern, case_sensitive=False)
        if recursive
        else folder.glob(pattern, case_sensitive=False)
    )

    files = [path for path in iterator if path.is_file()]

    f_types = Counter(path.suffix.lower() or "<no_suffix>" for path in files)
    f_types_sum = "\n".join(
        f"  {suffix}: {count}" for suffix, count in f_types.most_common()
    )

    app_session.logger.info(
        "Found %s file(s) in %s:\n%s", len(files), shorten_path(folder), f_types_sum
    )

    return files


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
