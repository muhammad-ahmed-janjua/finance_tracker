from __future__ import annotations

import app.models 
from app.db import init_db, save_transactions
from app.ingest import load_commbank_csv
from app.reports import print_summary, print_monthly_summary, print_all_transaction
from pathlib import Path
import shutil

IMPORTS_DIR = Path("data/imports")
ARCHIVE_DIR = Path("data/archive")
REJECTED_DIR = Path("data/rejected")

def ensure_dirs():
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    REJECTED_DIR.mkdir(parents=True, exist_ok=True)

def main():
    init_db()
    ensure_dirs()

    csv_files = sorted(IMPORTS_DIR.glob("*.csv"))
    if not csv_files:
        print("No csv files found in data/imports")
        return
    
    total_inserted = 0
    total_skipped = 0

    for path in csv_files:
        try:
            txs = load_commbank_csv(path)
            inserted, skipped = save_transactions(txs)

            total_inserted += inserted
            total_skipped += skipped

            print(f"[OK] {path.name}: inserted={inserted}, skipped={skipped}")

            shutil.move(str(path), str(ARCHIVE_DIR / path.name))

        except Exception as e:
            print(f"[FAIL] {path.name}: {e}")
            shutil.move(str(path), str(REJECTED_DIR / path.name))
        
        
    print(f"Total inserted={total_inserted}, Total skipped={total_skipped}")

    
if __name__ == "__main__":
    main()
    print_summary()
    print_monthly_summary()
    print_all_transaction()