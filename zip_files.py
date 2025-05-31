import zipfile
from pathlib import Path

# Creates a ZIP archive from a list of files
# - filepaths_to_compress: list of file paths to include in the ZIP
# - output_zip: path where the output ZIP file should be created
def create_zip_file(filepaths_to_compress: list[str | Path], output_zip: str | Path):
    # Open the ZIP file in write mode
    with zipfile.ZipFile(output_zip, 'w') as zipf:
        for file in filepaths_to_compress:
            # Add file to ZIP using only its filename (not full path)
            zipf.write(filename=file, arcname=Path(file).name)

# Extracts all files from a ZIP archive into a specified folder
# - zip_file_path: path to the ZIP file to extract
# - extract_to_folder: folder where contents should be extracted
def extract_zip_file(zip_file_path: str | Path, extract_to_folder: str | Path):
    # Open the ZIP file in read mode
    with zipfile.ZipFile(zip_file_path, 'r') as zipf:
        # Extract all contents into the specified folder
        zipf.extractall(extract_to_folder)
