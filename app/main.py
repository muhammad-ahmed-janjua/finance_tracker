from __future__ import annotations

from app.db import init_db
import app.models

if __name__ == "__main__":
    init_db()
    print("Db initiliased")