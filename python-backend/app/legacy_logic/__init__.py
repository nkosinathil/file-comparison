"""
Legacy Processing Logic

This package contains the core bank statement processing logic migrated from
the original Aurex Qt desktop application.

The logic has been preserved as-is to ensure compatibility and correctness.
These modules provide:

- fnb_statement_to_sqlite.py: PDF parsing and transaction extraction
- fnb_chat_assistant-v2.py: AI-powered chat interface for querying data
- account_analyzer.py: Account identification and analysis

These modules are imported and used by Celery tasks in app/tasks/
"""
