"""Get the UT-HAR dataset (SenseFi version) into data/UT_HAR/.

About 380 MB download, about 900 MB after unzipping.

Run:
    python download_data.py                    # download from Google Drive, then unzip
    python download_data.py path\\to\\UT_HAR.zip  # unzip a copy you already have

Google Drive sometimes blocks the download for a while with "Too many users
have viewed or downloaded this file recently". If that happens, get
UT_HAR.zip from a teammate (or download it by hand in a browser) and pass its
path as shown above.
"""

import hashlib
import shutil
import sys
import zipfile
from pathlib import Path

import gdown

UT_HAR_FILE_ID = "1fEiI3nAoOsddR5qcJQXqz4ocM3aMAcwz"  # UT_HAR.zip in the SenseFi Drive folder
DRIVE_FOLDER = "https://drive.google.com/drive/folders/1R0R8SlVbLI1iUFQCzh_mH90H_4CW2iwt"
UT_HAR_SHA256 = "5a0adaf244f5fa656e32250c5ac8fd53a4d1fdae8005739b4bbd336dcf1aae94"
DATA_DIR = Path(__file__).parent / "data"
TARGET = DATA_DIR / "UT_HAR"


def download(zip_path):
    print("Downloading UT_HAR.zip (about 380 MB)...")
    try:
        gdown.download(id=UT_HAR_FILE_ID, output=str(zip_path), quiet=False)
    except Exception as e:  # gdown raises several error types
        print(f"\nDownload failed: {e}\n")
    if not zip_path.exists():
        sys.exit(
            "Could not download UT_HAR.zip. Either try again later, or get the file\n"
            f"from a teammate or by hand from {DRIVE_FOLDER}\n"
            "and run:  python download_data.py path/to/UT_HAR.zip"
        )


def check_hash(zip_path):
    sha = hashlib.sha256()
    with open(zip_path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            sha.update(chunk)
    if sha.hexdigest() != UT_HAR_SHA256:
        sys.exit(f"{zip_path} is not the expected UT_HAR.zip (SHA-256 mismatch).")


def unzip(zip_path):
    check_hash(zip_path)
    print(f"Unzipping {zip_path}...")
    base = DATA_DIR.resolve()
    with zipfile.ZipFile(zip_path) as z:
        members = [m for m in z.namelist()
                   if m.startswith("UT_HAR/") and ".ipynb_checkpoints" not in m]
        if not members:
            sys.exit(f"{zip_path} has no UT_HAR/ folder inside. Is it the right file?")
        for m in members:  # refuse any entry that would land outside data/
            if not (base / m).resolve().is_relative_to(base):
                sys.exit(f"Unsafe path in archive: {m}")
        z.extractall(DATA_DIR, members=members)


def main():
    if (TARGET / "data" / "X_train.csv").exists():
        print(f"UT-HAR already present in {TARGET}")
        return
    DATA_DIR.mkdir(exist_ok=True)

    if len(sys.argv) > 1:
        unzip(Path(sys.argv[1]))
    else:
        zip_path = DATA_DIR / "UT_HAR.zip"
        if not zip_path.exists():
            download(zip_path)
        unzip(zip_path)
        zip_path.unlink()

    shutil.rmtree(TARGET / ".ipynb_checkpoints", ignore_errors=True)
    print(f"Done: {TARGET}")


if __name__ == "__main__":
    main()
