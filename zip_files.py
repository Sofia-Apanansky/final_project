import zipfile
from pathlib import Path


def create_zip_file(filepaths_to_compress: list[str | Path], output_zip: str | Path):
    with zipfile.ZipFile(output_zip, 'w') as zipf:
        for file in filepaths_to_compress:
            zipf.write(filename=file, arcname=Path(file).name)


def extract_zip_file(zip_file_path: str | Path, extract_to_folder: str | Path):
    with zipfile.ZipFile(zip_file_path, 'r') as zipf:
        zipf.extractall(extract_to_folder)
