# Aurex - Bank Statement Intelligence

A premium PySide6 desktop interface for FNB-style bank statement analysis.

## Features
- Welcome screen with finished-case reopening
- Case Information screen with case details and folder selection
- Progress screen with live processing logs, cancel, and finish workflow
- Analysis workspace with:
  - AI Chat powered by `fnb_chat_assistant-v2.py`
  - Network mapping tab using an HTML/SVG graph inside Qt WebView when available
  - Insights tab with a custom doughnut chart and textual breakdown
- Case persistence via `cases/<case_id>/case.json`

## Files expected in the project root
- `fnb_statement_to_sqlite.py`
- `fnb_chat_assistant-v2.py`
- `account_analyzer.py`

These are copied into `aurex_bank_analyzer/scripts/` automatically on first run.

## Run
```bash
python run_aurex.py
```

## Notes
- The AI chat expects Ollama to be running locally if you want model-backed answers.
- If `PySide6.QtWebEngineWidgets` is unavailable, the Network tab falls back to a text summary instead of the embedded visual graph.
- Processing is implemented directly against the parsing functions in `fnb_statement_to_sqlite.py` so the GUI can provide live progress updates.
