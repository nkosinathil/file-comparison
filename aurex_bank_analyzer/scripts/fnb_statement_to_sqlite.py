import os
import re
import hashlib
import sqlite3
import argparse
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple, Set
from pathlib import Path

import pdfplumber

# OCR fallback (used only if no txns are detected via PDF text)
from pdf2image import convert_from_path
import pytesseract


# ---------- OPTIONAL OCR CONFIG (Windows) ----------
# If pytesseract can't find tesseract.exe, uncomment and set:
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# --------------------------------------------------


MONTHS = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12
}

@dataclass
class Txn:
    txn_date: str           # YYYY-MM-DD
    description: str
    debit: Optional[str]    # "123.45" or None
    credit: Optional[str]   # "123.45" or None
    source_file: str        # PDF filename
    file_hash: str          # SHA256 of source file
    statement_date: str     # Statement date from PDF


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def clean_amount(s: str) -> str:
    return s.replace(",", "").strip()


def parse_statement_date(full_text: str) -> Optional[str]:
    """
    Looks for:
      Statement Date : 30 August 2024
    """
    m = re.search(r"Statement Date\s*:\s*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", full_text)
    if m:
        day = int(m.group(1))
        mon_name = m.group(2)[:3].title()
        year = int(m.group(3))
        mon = MONTHS.get(mon_name)
        if mon:
            return f"{year:04d}-{mon:02d}-{day:02d}"
    return None


def parse_statement_period(full_text: str) -> Tuple[Optional[datetime], Optional[datetime]]:
    """
    Looks for:
      Statement Period : 30 July 2024 to 30 August 2024
    Used to handle year rollover (Dec -> Jan).
    """
    m = re.search(
        r"Statement Period\s*:\s*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})\s+to\s+(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})",
        full_text
    )
    if not m:
        return None, None

    d1, mon1, y1, d2, mon2, y2 = m.groups()
    mon1 = MONTHS.get(mon1[:3].title())
    mon2 = MONTHS.get(mon2[:3].title())
    if not mon1 or not mon2:
        return None, None

    start = datetime(int(y1), mon1, int(d1))
    end = datetime(int(y2), mon2, int(d2))
    return start, end


def infer_year_for_txn(day: int, mon: int, period_start: Optional[datetime], period_end: Optional[datetime], statement_year: int) -> int:
    """
    If statement spans across years (e.g., Dec -> Jan), decide which year a txn belongs to.
    Otherwise use statement_year.
    """
    if period_start and period_end:
        if period_start.year == period_end.year:
            return period_start.year

        # Cross-year: months >= start_month => start.year else end.year
        if mon >= period_start.month:
            return period_start.year
        return period_end.year

    return statement_year


# This regex matches lines like:
# 31 Jan SOME DESCRIPTION 1,234.56Cr 9,999.99Cr
# 01 Feb SOME DESCRIPTION 123.45 9,999.99Cr
TXN_LINE_RE = re.compile(
    r"""
    ^(?P<day>\d{2})\s+(?P<mon>[A-Za-z]{3})\s+
    (?P<desc>.+?)\s+
    (?P<amt>[\d,]+\.\d{2})(?P<cr>Cr)?\s+
    (?P<bal>[\d,]+\.\d{2})(?P<balcr>Cr|Dr)?
    (?:\s+.*)?$
    """,
    re.VERBOSE
)


def extract_transactions_from_text(full_text: str) -> List[str]:
    lines = [ln.strip() for ln in full_text.splitlines() if ln.strip()]
    txn_lines = []
    for ln in lines:
        # Skip common non-txn rows
        if ln.startswith("Transactions in RAND"):
            continue
        if ln.startswith("Date Description Amount"):
            continue
        if "Closing Balance" in ln or "Turnover for Statement Period" in ln:
            continue

        if TXN_LINE_RE.match(ln):
            txn_lines.append(ln)
    return txn_lines


def ocr_pdf_to_text(pdf_path: str) -> str:
    """
    OCR fallback for scanned PDFs.
    Needs:
      - Tesseract installed
      - Poppler installed (for pdf2image on Windows)
    """
    try:
        images = convert_from_path(pdf_path, dpi=300)
        texts = []
        for img in images:
            texts.append(pytesseract.image_to_string(img))
        return "\n".join(texts)
    except Exception as e:
        print(f"  ⚠️  OCR failed: {e}")
        return ""


def parse_pdf_statement(pdf_path: str) -> Tuple[str, List[Txn], str]:
    """
    Returns:
      statement_date (YYYY-MM-DD)
      txns
      sha256
    """
    file_hash = sha256_file(pdf_path)
    filename = os.path.basename(pdf_path)

    # 1) Extract text normally (best if PDF has real text)
    try:
        with pdfplumber.open(pdf_path) as pdf:
            all_text = "\n".join((page.extract_text() or "") for page in pdf.pages)
    except Exception as e:
        print(f"  ⚠️  PDF text extraction failed: {e}")
        all_text = ""

    statement_date = parse_statement_date(all_text)

    period_start, period_end = parse_statement_period(all_text)

    txn_lines = extract_transactions_from_text(all_text)

    # 2) OCR fallback if no txns found
    if len(txn_lines) == 0:
        print("  ℹ️  No transactions found in text, trying OCR...")
        ocr_text = ocr_pdf_to_text(pdf_path)

        if ocr_text:
            if not statement_date:
                statement_date = parse_statement_date(ocr_text)

            # period from OCR if needed
            if not period_start and not period_end:
                period_start, period_end = parse_statement_period(ocr_text)

            txn_lines = extract_transactions_from_text(ocr_text)

    if not statement_date:
        raise ValueError(f"Could not detect 'Statement Date' in {filename} (text or OCR).")

    statement_year = int(statement_date[:4])

    if len(txn_lines) == 0:
        raise ValueError(f"No transaction lines detected in {filename} (text or OCR).")

    txns: List[Txn] = []
    seen: Set[Tuple[str, str, Optional[str], Optional[str]]] = set()  # de-dup in output

    for ln in txn_lines:
        m = TXN_LINE_RE.match(ln)
        if not m:
            continue

        day = int(m.group("day"))
        mon_txt = m.group("mon")[:3].title()
        mon = MONTHS.get(mon_txt)
        if not mon:
            continue

        year = infer_year_for_txn(day, mon, period_start, period_end, statement_year)
        txn_date = f"{year:04d}-{mon:02d}-{day:02d}"

        desc = m.group("desc").strip()
        amt_raw = clean_amount(m.group("amt"))
        is_credit = bool(m.group("cr"))

        debit = None
        credit = None
        if is_credit:
            credit = amt_raw
        else:
            debit = amt_raw

        key = (txn_date, desc, debit, credit)
        if key in seen:
            continue
        seen.add(key)

        txns.append(Txn(
            txn_date=txn_date,
            description=desc,
            debit=debit,
            credit=credit,
            source_file=filename,
            file_hash=file_hash,
            statement_date=statement_date
        ))

    if not txns:
        raise ValueError(f"Transaction lines were found in {filename}, but none were parsed into transactions.")

    return statement_date, txns, file_hash


def create_database(db_path: str):
    """Create the SQLite database and tables if they don't exist"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fnb_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            txn_date TEXT NOT NULL,
            description TEXT NOT NULL,
            debit REAL,
            credit REAL,
            source_file TEXT NOT NULL,
            file_hash TEXT NOT NULL,
            statement_date TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create indexes for faster queries
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_txn_date ON fnb_transactions(txn_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_source_file ON fnb_transactions(source_file)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_hash ON fnb_transactions(file_hash)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_statement_date ON fnb_transactions(statement_date)')
    
    # Create a table to track processed files (to avoid duplicates)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_files (
            file_hash TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            statement_date TEXT NOT NULL,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            transaction_count INTEGER
        )
    ''')
    
    conn.commit()
    conn.close()


def is_file_processed(db_path: str, file_hash: str) -> bool:
    """Check if a file has already been processed"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM processed_files WHERE file_hash = ?', (file_hash,))
    result = cursor.fetchone() is not None
    conn.close()
    return result


def save_transactions_to_db(db_path: str, txns: List[Txn]):
    """Save transactions to SQLite database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    for txn in txns:
        cursor.execute('''
            INSERT INTO fnb_transactions 
            (txn_date, description, debit, credit, source_file, file_hash, statement_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            txn.txn_date,
            txn.description,
            float(txn.debit) if txn.debit else None,
            float(txn.credit) if txn.credit else None,
            txn.source_file,
            txn.file_hash,
            txn.statement_date
        ))
    
    conn.commit()
    conn.close()


def mark_file_processed(db_path: str, filename: str, file_hash: str, statement_date: str, txn_count: int):
    """Mark a file as processed in the database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO processed_files (file_hash, filename, statement_date, transaction_count)
        VALUES (?, ?, ?, ?)
    ''', (file_hash, filename, statement_date, txn_count))
    conn.commit()
    conn.close()


def process_folder(folder_path: str, db_path: str = "fnb_statements.db", 
                   skip_processed: bool = True, recursive: bool = False):
    """
    Process all PDF files in a folder and save to SQLite database
    
    Args:
        folder_path: Path to folder containing PDF statements
        db_path: Path to SQLite database file
        skip_processed: Skip files that have already been processed
        recursive: Search subfolders recursively
    """
    # Create database if it doesn't exist
    create_database(db_path)
    
    # Find all PDF files in the folder
    if recursive:
        pdf_files = list(Path(folder_path).rglob("*.pdf"))
    else:
        pdf_files = list(Path(folder_path).glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {folder_path}")
        return
    
    print(f"\n📂 Found {len(pdf_files)} PDF files")
    print(f"📁 Database: {db_path}")
    if recursive:
        print(f"🔍 Searching recursively in subfolders")
    print("-" * 60)
    
    stats = {
        "processed": 0,
        "skipped": 0,
        "failed": 0,
        "total_transactions": 0
    }
    
    for i, pdf_path in enumerate(pdf_files, 1):
        filename = pdf_path.name
        print(f"\n[{i}/{len(pdf_files)}] Processing: {filename}")
        
        try:
            # Check if file was already processed
            file_hash = sha256_file(str(pdf_path))
            
            if skip_processed and is_file_processed(db_path, file_hash):
                print(f"  ⏭️  Skipped (already processed)")
                stats["skipped"] += 1
                continue
            
            # Parse the PDF
            statement_date, txns, file_hash = parse_pdf_statement(str(pdf_path))
            
            # Save to database
            save_transactions_to_db(db_path, txns)
            mark_file_processed(db_path, filename, file_hash, statement_date, len(txns))
            
            print(f"  ✅ Processed {len(txns)} transactions")
            print(f"  📅 Statement date: {statement_date}")
            
            stats["processed"] += 1
            stats["total_transactions"] += len(txns)
            
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            stats["failed"] += 1
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 PROCESSING SUMMARY")
    print("=" * 60)
    print(f"✅ Files processed:   {stats['processed']}")
    print(f"⏭️  Files skipped:     {stats['skipped']}")
    print(f"❌ Files failed:      {stats['failed']}")
    print(f"💰 Total transactions: {stats['total_transactions']}")
    print(f"📁 Database: {os.path.abspath(db_path)}")
    print("=" * 60)


def show_database_stats(db_path: str):
    """Show statistics from the database"""
    if not os.path.exists(db_path):
        print(f"Database {db_path} does not exist.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n📊 DATABASE STATISTICS")
    print("-" * 60)
    
    # Total transactions
    cursor.execute('SELECT COUNT(*) FROM fnb_transactions')
    total_txns = cursor.fetchone()[0]
    print(f"💰 Total transactions: {total_txns}")
    
    # Total files processed
    cursor.execute('SELECT COUNT(*) FROM processed_files')
    total_files = cursor.fetchone()[0]
    print(f"📄 Files processed: {total_files}")
    
    # Date range
    cursor.execute('SELECT MIN(txn_date), MAX(txn_date) FROM fnb_transactions')
    min_date, max_date = cursor.fetchone()
    if min_date and max_date:
        print(f"📅 Date range: {min_date} to {max_date}")
    
    # Summary by year/month
    cursor.execute('''
        SELECT strftime('%Y-%m', txn_date) as month,
               COUNT(*) as txns,
               SUM(debit) as total_debits,
               SUM(credit) as total_credits
        FROM fnb_transactions
        GROUP BY month
        ORDER BY month DESC
        LIMIT 12
    ''')
    
    print("\n📈 Last 12 months summary:")
    print("  Month     | Transactions | Debits    | Credits")
    print("-" * 50)
    for row in cursor.fetchall():
        print(f"  {row[0]} | {row[1]:>11} | {row[2] or 0:>9.2f} | {row[3] or 0:>9.2f}")
    
    conn.close()


def query_database(db_path: str, sql_query: str = None, limit: int = 10):
    """
    Helper function to query the database
    
    If no query provided, shows sample queries
    """
    if not os.path.exists(db_path):
        print(f"Database {db_path} does not exist.")
        return
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if sql_query:
        try:
            cursor.execute(sql_query)
            rows = cursor.fetchall()
            
            if not rows:
                print("No results found.")
            else:
                # Get column names
                columns = [description[0] for description in cursor.description]
                print("\n" + " | ".join(columns))
                print("-" * 80)
                
                for row in rows[:limit]:
                    values = []
                    for col in columns:
                        val = row[col]
                        if val is None:
                            values.append("NULL")
                        elif isinstance(val, float):
                            values.append(f"{val:.2f}")
                        else:
                            values.append(str(val))
                    print(" | ".join(values))
                
                if len(rows) > limit:
                    print(f"... and {len(rows) - limit} more rows")
                    
        except sqlite3.Error as e:
            print(f"SQL Error: {e}")
    else:
        print("\n📝 SAMPLE QUERIES")
        print("=" * 60)
        print("1. View recent transactions:")
        print("   SELECT txn_date, description, debit, credit, source_file")
        print("   FROM fnb_transactions")
        f"   ORDER BY txn_date DESC LIMIT 10;\n"
        
        print("2. Summary by month:")
        print("   SELECT strftime('%Y-%m', txn_date) as month,")
        print("          COUNT(*) as transactions,")
        print("          SUM(debit) as total_spent,")
        print("          SUM(credit) as total_deposits")
        print("   FROM fnb_transactions")
        print("   GROUP BY month")
        print("   ORDER BY month DESC;\n")
        
        print("3. Search transactions:")
        print("   SELECT * FROM fnb_transactions")
        print("   WHERE description LIKE '%PAYMENT%'")
        print("   ORDER BY txn_date DESC;\n")
        
        print("4. Top spending categories:")
        print("   SELECT description, COUNT(*) as count, SUM(debit) as total")
        print("   FROM fnb_transactions")
        print("   WHERE debit IS NOT NULL")
        print("   GROUP BY description")
        print("   ORDER BY total DESC")
        print("   LIMIT 10;\n")
    
    conn.close()


def main():
    parser = argparse.ArgumentParser(
        description='Process FNB bank statement PDFs and store in SQLite database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /path/to/statements/
  %(prog)s /path/to/statements/ -d my_bank.db
  %(prog)s /path/to/statements/ --recursive --no-skip
  %(prog)s /path/to/statements/ --stats
  %(prog)s /path/to/statements/ --query "SELECT * FROM fnb_transactions LIMIT 5"
        """
    )
    
    parser.add_argument(
        'folder',
        help='Folder containing FNB statement PDFs'
    )
    
    parser.add_argument(
        '-d', '--database',
        default='fnb_statements.db',
        help='SQLite database file path (default: fnb_statements.db)'
    )
    
    parser.add_argument(
        '-r', '--recursive',
        action='store_true',
        help='Search for PDFs in subfolders recursively'
    )
    
    parser.add_argument(
        '--no-skip',
        action='store_true',
        help='Process all files even if they were processed before'
    )
    
    parser.add_argument(
        '-s', '--stats',
        action='store_true',
        help='Show database statistics after processing'
    )
    
    parser.add_argument(
        '-q', '--query',
        metavar='SQL',
        help='Run a SQL query on the database and exit'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=20,
        help='Limit results when using --query (default: 20)'
    )
    
    args = parser.parse_args()
    
    # Check if folder exists
    if not os.path.isdir(args.folder):
        print(f"Error: Folder '{args.folder}' does not exist.")
        return 1
    
    # If query is provided, just run the query and exit
    if args.query:
        query_database(args.database, args.query, args.limit)
        return 0
    
    # Process the folder
    try:
        process_folder(
            folder_path=args.folder,
            db_path=args.database,
            skip_processed=not args.no_skip,
            recursive=args.recursive
        )
        
        # Show stats if requested
        if args.stats:
            show_database_stats(args.database)
        
        # Ask if user wants to run a query
        while True:
            response = input("\n🔍 Do you want to run a query? (y/n/q): ").lower()
            if response == 'y':
                print("\nEnter SQL query (or 'exit' to stop):")
                while True:
                    sql = input("SQL> ").strip()
                    if sql.lower() in ('exit', 'quit'):
                        break
                    if sql:
                        query_database(args.database, sql, args.limit)
            elif response == 'n':
                break
            elif response == 'q':
                break
        
        print("\n✅ Done!")
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Processing interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())