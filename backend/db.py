"""Database paths and connections.

- data/campus_customs.db      ORIGINAL — never opened by the app, never modified (file is read-only).
- data/campus_customs_new.db  WORKING COPY — every read and write by the app goes here.

Reset the working copy back to the original with hw4/reset_db.sh.
"""

import os
import shutil
import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ORIGINAL_DB = DATA_DIR / "campus_customs.db"
WORKING_DB = DATA_DIR / "campus_customs_new.db"


def check_data_pack() -> None:
    """The data pack (campus_customs.db + products/ images) is not in the GitHub repo."""
    missing = [p for p in (ORIGINAL_DB, DATA_DIR / "products") if not p.exists()]
    if missing:
        raise RuntimeError(
            "Data pack not found: " + ", ".join(str(m) for m in missing) +
            ". Copy campus_customs.db and the products/ image folder into hw4/data/ (see README.md)."
        )


def ensure_working_copy() -> None:
    # First run (or after someone deletes it): start from the original data.
    if not WORKING_DB.exists():
        check_data_pack()
        shutil.copyfile(ORIGINAL_DB, WORKING_DB)
        os.chmod(WORKING_DB, 0o600)


def connect(write: bool = False) -> sqlite3.Connection:
    ensure_working_copy()
    uri = f"file:{WORKING_DB}" + ("" if write else "?mode=ro")
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn
