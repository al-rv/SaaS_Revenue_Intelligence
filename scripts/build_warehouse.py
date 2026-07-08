""" Build DuckDB warehouse by executing SQL files in order."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT= Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
    
from src.config import RAW_DATA_DIR, SQL_DIR, ensure_directories
from src.db import get_connection

SQL_PATTERN = "[0-9][0-9]_*.sql"

def render_sql(sql_text: str) -> str:
    raw_dir = RAW_DATA_DIR.as_posix()
    return sql_text.replace("{{RAW_DATA_DIR}}", raw_dir)

def run_sql_files(sql_file: Path) -> None:
    sql_text = render_sql(sql_file.read_text(encoding="utf-8"))
    with get_connection() as conn:
        conn.execute(sql_text)
        
def main() -> None:
    ensure_directories()
    sql_files = sorted(SQL_DIR.glob(SQL_PATTERN))
    if not sql_files:
        raise RuntimeError(f'No SQL file found in {SQL_DIR} matching {SQL_PATTERN}')   
    
    print('Running SQL pipelines')
    for sql_file in sql_files:
        print(f' - {sql_file.name}')
        run_sql_files(sql_file)
    
    with get_connection() as conn:
        counts = conn.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM raw.accounts) AS accounts,
                (SELECT COUNT(*) FROM raw.subscriptions) AS subscriptions,
                (SELECT COUNT(*) FROM raw.feature_usage) AS feature_usage,
                (SELECT COUNT(*) FROM raw.support_tickets) AS support_tickets,
                (SELECT COUNT(*) FROM raw.churn_events) AS churn_events
            """
        ).fetchone()
    
    labels = ['accounts', 'subscription', 'feature_usage', 'support_tickets', 'churn_evnets']  
    print('Raw tabel row counts:')
    for label, value in zip(labels, counts, strict=True):
        print(f' - {label}: {value}')
        
    print('Warehouse build completed.')
    
if __name__ == "__main__":
    main()  
             