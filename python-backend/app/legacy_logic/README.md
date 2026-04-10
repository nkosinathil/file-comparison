# Legacy Processing Logic

## Purpose

This directory contains the core bank statement processing logic migrated from the original Aurex Qt desktop application. The code has been preserved with minimal changes to ensure reliability and correctness.

## Files

### fnb_statement_to_sqlite.py

**Original Purpose**: Parse FNB bank statement PDFs and extract transactions to SQLite.

**Key Functions**:
- `parse_pdf_statement(pdf_path)`: Extract transactions from a single PDF
- `create_database(db_path)`: Initialize SQLite database schema
- `save_transactions_to_db(db_path, transactions)`: Store extracted transactions
- `mark_file_processed(db_path, filename, file_hash, statement_date, txn_count)`: Track processed files

**How It's Used in Web App**:
- Called by Celery tasks for background PDF processing
- Transactions are saved to SQLite first (for compatibility)
- Then migrated to PostgreSQL for web access
- Or directly saved to PostgreSQL in future enhancement

**Technologies**:
- pdfplumber: PDF text extraction
- pdf2image + pytesseract: OCR fallback
- Regular expressions: Transaction pattern matching
- SQLite: Temporary storage

### fnb_chat_assistant-v2.py

**Original Purpose**: Provide AI-powered natural language querying of transaction data.

**Key Components**:
- `FNBStatementChat` class: Main chat interface
- Ollama integration for LLM-based responses
- SQL query generation from natural language
- Context-aware conversation handling

**How It's Used in Web App**:
- Integrated into "AI Chat" feature
- Users can ask questions like "What did I spend on fuel last month?"
- Backend generates SQL, queries PostgreSQL, returns natural language answer

**Technologies**:
- Ollama: Local LLM server
- SQLite queries (will be adapted for PostgreSQL)

### account_analyzer.py

**Original Purpose**: Identify accounts from filename patterns and analyze transaction patterns.

**Key Functions**:
- `extract_account_from_filename(filename)`: Parse account info from PDF filename
- `FNBAccountAnalyzer.analyze_files()`: Account-level analysis
- Account grouping and statistics

**How It's Used in Web App**:
- During upload: Extract account metadata from filenames
- During processing: Group transactions by account
- For insights: Account-level summaries and comparisons

## Migration Notes

### What Changed
- **Storage**: Originally used SQLite per case → Now uses PostgreSQL + MinIO
- **Execution**: Originally ran in Qt GUI thread → Now runs in Celery workers
- **File Paths**: Originally used local filesystem → Now uses MinIO object storage

### What Stayed the Same
- Core parsing algorithms
- Transaction extraction patterns
- Category classification rules
- Network graph generation logic

### Integration Pattern

```python
# Example: Using legacy logic in a Celery task

from app.legacy_logic import fnb_statement_to_sqlite as statement_parser

@celery_app.task
def process_pdf_file(minio_path: str, db_path: str):
    # Download from MinIO to temp location
    local_path = download_from_minio(minio_path)
    
    # Use legacy parser (unchanged)
    statement_date, txns, file_hash = statement_parser.parse_pdf_statement(local_path)
    
    # Save to PostgreSQL instead of SQLite
    save_to_postgres(txns)
    
    # Clean up temp file
    os.remove(local_path)
```

## Future Enhancements

1. **Direct PostgreSQL Support**: Modify parsers to write directly to PostgreSQL
2. **Streaming Processing**: Handle very large PDFs without loading entire file
3. **Enhanced Error Recovery**: Better handling of malformed PDFs
4. **Multi-Bank Support**: Extend beyond FNB to other banks
5. **Advanced AI**: More sophisticated chat with memory and context

## Testing

When making changes to this code:
1. Test with real FNB PDF statements
2. Verify transaction counts match original Qt app
3. Check date parsing handles year rollovers correctly
4. Ensure OCR fallback works for scanned PDFs
5. Validate category classification accuracy

## Maintenance

This code is production-critical. Changes should be:
- Minimal and well-tested
- Backward compatible
- Documented with examples
- Reviewed by someone familiar with FNB statement formats
