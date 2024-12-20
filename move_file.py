from pathlib import Path


def move_file(old_filepath: str, new_filepath: str) -> None:
    old_path = Path(old_filepath).resolve()
    new_path = Path(new_filepath).resolve()
    if old_path.exists() and not new_path.exists():
        old_path.rename(new_path)
