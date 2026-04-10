# fnb_chat_assistant_final.py

import os
import sqlite3
import re
import sys
import threading
import time
import itertools
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
import argparse

print(f"Running with Python: {sys.executable}")

# ---------- THINKING ANIMATION ----------
class ThinkingAnimation:
    def __init__(self, message="Thinking"):
        self.message = message
        self.spinner = itertools.cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
        self.running = False
        self.thread = None

    def spin(self):
        while self.running:
            sys.stdout.write(f'\r{self.message} {next(self.spinner)} ')
            sys.stdout.flush()
            time.sleep(0.1)

    def __enter__(self):
        self.running = True
        self.thread = threading.Thread(target=self.spin)
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.running = False
        if self.thread:
            self.thread.join()
        sys.stdout.write('\r' + ' ' * 50 + '\r')
        sys.stdout.flush()


# ---------- MAIN ASSISTANT CLASS ----------
class FNBStatementChat:
    def __init__(self, db_path: str, model: str = "llama3", ollama_url: str = "http://localhost:11434"):
        self.db_path = db_path
        self.model = model
        self.ollama_url = ollama_url

        # Conversation memory
        self.conversation_history = []          # list of {'user':..., 'assistant':..., 'sql':...}
        self.last_context = {}                  # stores last question, SQL, results, and filter hint

        # Load database schema and stats
        self.table_info = self._get_table_info()
        self.stats = self._get_stats()
        self.full_schema = self._get_full_schema()

        print(f"\n✅ Loaded database: {db_path}")
        print(f"📊 Transactions: {self.stats['total']:,}")
        print(f"📅 Date range: {self.stats['min_date']} to {self.stats['max_date']}")
        print("🤖 Mode: factual & conversational with month ambiguity handling")

    def _get_full_schema(self) -> str:
        """Return the full CREATE TABLE statements."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            schema = "\n".join([t[0] for t in tables if t[0]])
            conn.close()
            return schema
        except Exception as e:
            return f"Error getting schema: {e}"

    def _get_table_info(self) -> str:
        """Return a human‑readable description of tables and columns."""
        info = []
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            for (table_name,) in tables:
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                col_desc = ", ".join([f"{col[1]} ({col[2]})" for col in columns])
                info.append(f"Table: {table_name}\n  Columns: {col_desc}")
                # Sample rows
                try:
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                    samples = cursor.fetchall()
                    if samples:
                        info.append("  Sample rows:")
                        for sample in samples:
                            info.append(f"    {sample}")
                except:
                    pass
            conn.close()
        except Exception as e:
            info.append(f"Error getting table info: {e}")
        return "\n".join(info)

    def _get_stats(self) -> Dict[str, Any]:
        """Return basic statistics about the database."""
        stats = {'total': 0, 'min_date': 'N/A', 'max_date': 'N/A',
                 'total_spent': 0.0, 'total_deposits': 0.0}
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM fnb_transactions")
            stats['total'] = cursor.fetchone()[0]
            cursor.execute("SELECT MIN(txn_date), MAX(txn_date) FROM fnb_transactions")
            stats['min_date'], stats['max_date'] = cursor.fetchone()
            cursor.execute("SELECT SUM(debit), SUM(credit) FROM fnb_transactions")
            stats['total_spent'], stats['total_deposits'] = cursor.fetchone()
            conn.close()
        except Exception as e:
            print(f"⚠️  Could not retrieve all stats: {e}")
        return stats

    def _execute_sql(self, query: str, max_display: int = 50) -> tuple[str, Optional[float]]:
        """
        Execute SQL and return:
        - formatted results string (up to max_display rows, with count)
        - total sum of debit amounts (if the result set contains debit values), else None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            if not rows:
                return "No results found.", None

            # Store for context
            self.last_context['last_results'] = rows[:5]
            self.last_context['last_query'] = query

            # Format output and compute total debit if column exists
            columns = [description[0] for description in cursor.description]
            result_lines = [f"📊 Found {len(rows)} result(s):\n"]
            total_debit = 0.0
            has_debit = 'debit' in columns

            for i, row in enumerate(rows[:max_display], 1):
                values = []
                for col in columns:
                    val = row[col]
                    if isinstance(val, float):
                        values.append(f"R{val:,.2f}")
                        if has_debit and col == 'debit':
                            total_debit += val
                    elif isinstance(val, str) and len(val) > 60:
                        values.append(val[:60] + "...")
                    else:
                        values.append(str(val))
                result_lines.append(f"{i}. {' | '.join(values)}")
            if len(rows) > max_display:
                result_lines.append(f"... and {len(rows) - max_display} more rows. To see all, use `/sql` with your query.")
            conn.close()

            total_debit = total_debit if has_debit else None
            return "\n".join(result_lines), total_debit
        except sqlite3.Error as e:
            return f"❌ SQL Error: {str(e)}", None

    def _call_ollama(self, prompt: str, system: Optional[str] = None) -> str:
        """Send a prompt to Ollama and return the response."""
        url = f"{self.ollama_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "temperature": 0.1,
        }
        if system:
            payload["system"] = system
        try:
            with ThinkingAnimation("🧠 Thinking"):
                response = requests.post(url, json=payload, timeout=60)
            if response.status_code == 200:
                return response.json().get('response', '')
            else:
                return f"Error: {response.status_code}"
        except Exception as e:
            return f"Error: {str(e)}"

    def _build_conversation_context(self, max_messages: int = 6) -> str:
        """Return a string of the most recent conversation turns."""
        if not self.conversation_history:
            return "No previous conversation."
        recent = self.conversation_history[-max_messages:]
        lines = []
        for msg in recent:
            lines.append(f"User: {msg['user']}")
            assist = msg['assistant'][:200] + "..." if len(msg['assistant']) > 200 else msg['assistant']
            lines.append(f"Assistant: {assist}")
            if 'sql' in msg:
                lines.append(f"  [SQL: {msg['sql'][:100]}...]")
        return "\n".join(lines)

    # ---------- MAIN QUESTION ANSWERING ----------
    def ask(self, question: str) -> str:
        """Process a user question and return the assistant's answer."""
        # Build conversation context
        context = self._build_conversation_context(6)

        # Include a hint about the last filter (date and transaction type)
        last_filter_hint = self.last_context.get('last_filter_hint', '')
        filter_hint_instruction = ""
        if last_filter_hint:
            filter_hint_instruction = (
                f"\nIMPORTANT CONTEXT: The previous query used this filter: {last_filter_hint}. "
                "If the user's question refers to 'that', 'it', 'this', or seems to ask for more details about the same transactions "
                "(e.g., 'where from', 'list them'), you MUST reuse the same date filter and transaction type (credit/debit) in your new SQL query, "
                "unless the user explicitly asks for a different period or type."
            )

        # Full schema reminder (exact column names)
        schema_reminder = f"""
EXACT DATABASE SCHEMA (use ONLY these column names):
{self.full_schema}

IMPORTANT: In the 'fnb_transactions' table, the column containing the source PDF filename is 'source_file' (NOT 'filename').
The column 'filename' exists only in the 'processed_files' table.
"""

        system_prompt = f"""You are a helpful banking assistant for FNB statements. You have access to a SQLite database.

{schema_reminder}

Current Statistics:
- Total transactions: {self.stats['total']:,}
- Date range: {self.stats['min_date']} to {self.stats['max_date']}
- Total spent: R{self.stats['total_spent']:,.2f}
- Total deposits: R{self.stats['total_deposits']:,.2f}

Recent conversation:
{context}
{filter_hint_instruction}

CRITICAL SQL SYNTAX RULES (SQLite ONLY):
- Use `strftime` for date operations. For example:
  * Filter by year: `strftime('%Y', txn_date) = '2024'`
  * Filter by month: `strftime('%m', txn_date) = '03'`
  * Filter by year‑month: `strftime('%Y-%m', txn_date) = '2024-03'`
- For date ranges, use `BETWEEN 'YYYY-MM-DD' AND 'YYYY-MM-DD'`.
- NEVER use `EXTRACT`, `DATE_PART`, or other functions not available in SQLite.
- Use ONLY the column names listed above. Do NOT invent column names like 'filename' when querying fnb_transactions.
- If the user asks about money received, use the `credit` column. If they ask about money spent, use the `debit` column.
- If the user asks for a total, use `SUM(credit)` or `SUM(debit)` as appropriate and return a single number.
- If the user asks for a breakdown (e.g., "where from", "list transactions"), return individual rows with relevant columns (e.g., description, source_file) and group if needed.
- **Important for month‑only questions:** If the user asks about a month without specifying a year (e.g., "month 1", "January"), and the data spans multiple years, you MUST include the year in the output. The best way is to select the date column (txn_date) and show the full date, so the user can see which year the transaction belongs to. Alternatively, group by year and month. Do NOT assume a year without evidence.
- Format currency as R123,456.78 in your final answer, but SQL should return raw numbers.
- Be concise and helpful.

To execute a SQL query, enclose it between [SQL] and [/SQL] tags.
Example: [SQL]SELECT txn_date, description, credit FROM fnb_transactions WHERE credit IS NOT NULL AND strftime('%Y', txn_date) = '2024' ORDER BY credit DESC LIMIT 5[/SQL]

Now answer this question: {question}"""

        try:
            response = self._call_ollama(question, system_prompt)
            sql_matches = re.findall(r'\[SQL\](.*?)\[/SQL\]', response, re.DOTALL)
            if sql_matches:
                sql = sql_matches[0].strip()
                print(f"\n🔍 Executing SQL: {sql[:150]}...")
                results_str, total_debit = self._execute_sql(sql)

                # Extract a rich filter hint from this SQL for future use
                filter_hint = ""
                # Look for year filter
                year_match = re.search(r"strftime\('%Y', txn_date\) = '(\d{4})'", sql)
                if year_match:
                    filter_hint += f"year {year_match.group(1)}"
                # Look for month filter
                month_match = re.search(r"strftime\('%Y-%m', txn_date\) = '(\d{4}-\d{2})'", sql)
                if month_match:
                    filter_hint += f"month {month_match.group(1)}"
                # Look for date range
                between_match = re.search(r"BETWEEN '(\d{4}-\d{2}-\d{2})' AND '(\d{4}-\d{2}-\d{2})'", sql)
                if between_match:
                    filter_hint += f"date range {between_match.group(1)} to {between_match.group(2)}"
                # Add transaction type if present
                if 'credit' in sql.lower() and 'debit' not in sql.lower():
                    filter_hint += ", transaction type: credit (money received)"
                elif 'debit' in sql.lower() and 'credit' not in sql.lower():
                    filter_hint += ", transaction type: debit (money spent)"
                self.last_context['last_filter_hint'] = filter_hint
                self.last_context['last_question'] = question
                self.last_context['last_sql'] = sql

                # Build total information (if any)
                total_info = ""
                total_instruction = ""
                if total_debit is not None:
                    total_info = f"\nTotal of debit amounts in these results: R{total_debit:,.2f}"
                    total_instruction = f"If you mention a total amount, use the exact total provided above (R{total_debit:,.2f})."
                else:
                    total_instruction = "If there is no total amount in the results, do not mention any total."

                final_prompt = f"""You are a helpful assistant that answers questions based strictly on the provided data.

Question: {question}
SQL results:{results_str}{total_info}

Instructions:
- Provide a natural, conversational answer using the data above.
- **If the user asked for a list, table, or detailed breakdown, you MUST present the data in a clear structured format (e.g., markdown table) with the relevant columns. Do not summarize by omitting rows – show as many as fit in the results (they are already truncated if necessary).**
- If the results show only a subset and there are more rows, mention the total number and suggest using `/sql` to see all.
- {total_instruction}
- Do not invent any numbers; only use the data shown.
- Keep your answer concise and friendly.

Now answer the question:"""
                final_answer = self._call_ollama(final_prompt)

                self.conversation_history.append({
                    'user': question,
                    'assistant': final_answer,
                    'sql': sql
                })
                return final_answer
            else:
                self.conversation_history.append({'user': question, 'assistant': response})
                return response
        except Exception as e:
            return f"❌ Error: {str(e)}"

    # ---------- INTERACTIVE CHAT ----------
    def chat(self):
        print("\n" + "="*70)
        print("💬 FNB Statement Chat Assistant (Final Edition with Month Ambiguity Handling)")
        print("="*70)
        print(f"🤖 Model: {self.model}")
        print(f"📁 Database: {self.db_path}")
        print(f"💰 Transactions: {self.stats['total']:,}")
        print(f"📅 Date range: {self.stats['min_date']} to {self.stats['max_date']}")
        print("-"*70)
        print("Commands:")
        print("  /stats    - Show database statistics")
        print("  /history  - Show recent conversation")
        print("  /clear    - Clear conversation history")
        print("  /sql      - Run raw SQL (e.g., /sql SELECT * FROM fnb_transactions LIMIT 5)")
        print("  /debug    - Show debug info")
        print("  /quit     - Exit")
        print("-"*70)

        while True:
            try:
                user_input = input("\n💭 You: ").strip()
                if user_input.lower() in ['/quit', '/exit', '/q']:
                    print("\n👋 Goodbye!")
                    break
                elif user_input.lower() == '/stats':
                    self._show_stats()
                elif user_input.lower() == '/history':
                    self._show_history()
                elif user_input.lower() == '/clear':
                    self.conversation_history = []
                    self.last_context = {}
                    print("🧹 History cleared!")
                elif user_input.lower().startswith('/sql'):
                    sql = user_input[4:].strip()
                    if sql:
                        results, _ = self._execute_sql(sql)
                        print(results)
                    else:
                        print("Please provide a SQL query after /sql")
                elif user_input.lower() == '/debug':
                    self._show_debug()
                elif user_input:
                    answer = self.ask(user_input)
                    print(f"\n🤖 Assistant: {answer}")
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break

    # ---------- UTILITY COMMANDS ----------
    def _show_stats(self):
        print("\n📊 DATABASE STATISTICS")
        print("-"*50)
        print(f"Total transactions: {self.stats['total']:,}")
        print(f"Date range: {self.stats['min_date']} to {self.stats['max_date']}")
        print(f"Total spent: R{self.stats['total_spent']:,.2f}")
        print(f"Total deposits: R{self.stats['total_deposits']:,.2f}")
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT description, COUNT(*) as cnt, SUM(debit) as total
                FROM fnb_transactions
                WHERE debit IS NOT NULL AND description NOT LIKE '%Transfer%'
                GROUP BY description
                ORDER BY total DESC
                LIMIT 10
            """)
            top = cursor.fetchall()
            if top:
                print("\nTop 10 merchants by spend:")
                for desc, cnt, total in top:
                    if total:
                        print(f"  • {desc[:40]}: R{total:,.2f} ({cnt} txns)")
            conn.close()
        except Exception:
            pass
        print("-"*50)

    def _show_history(self):
        print("\n📝 RECENT CONVERSATION")
        print("-"*50)
        if not self.conversation_history:
            print("No conversation history.")
        else:
            for i, msg in enumerate(self.conversation_history[-8:], 1):
                print(f"{i}. 👤 {msg['user'][:60]}...")
                print(f"   🤖 {msg['assistant'][:100]}...")
                if 'sql' in msg:
                    print(f"   🔍 SQL: {msg['sql'][:80]}...")
                print()
        print("-"*50)

    def _show_debug(self):
        print("\n🔍 DEBUG INFO")
        print("-"*50)
        print(f"Python executable: {sys.executable}")
        print(f"Database path: {self.db_path}")
        print(f"Model: {self.model}")
        print(f"Ollama URL: {self.ollama_url}")
        print(f"Last context keys: {list(self.last_context.keys())}")
        print(f"Last SQL: {self.last_context.get('last_sql', 'None')[:100]}")
        print(f"Last filter hint: {self.last_context.get('last_filter_hint', 'None')}")
        print("-"*50)


# ---------- MAIN ENTRY POINT ----------
def main():
    parser = argparse.ArgumentParser(description='Chat with your FNB statement database')
    parser.add_argument('database', nargs='?', default='fnb_statements.db',
                        help='SQLite database file (default: fnb_statements.db)')
    parser.add_argument('-m', '--model', default='llama3',
                        help='Ollama model to use (default: llama3)')
    parser.add_argument('-u', '--url', default='http://localhost:11434',
                        help='Ollama URL (default: http://localhost:11434)')
    args = parser.parse_args()

    if not os.path.exists(args.database):
        print(f"❌ Database '{args.database}' not found.")
        print("   Please run fnb_statement_to_sqlite.py first to create the database.")
        return 1

    chat = FNBStatementChat(args.database, args.model, args.url)
    chat.chat()
    return 0


if __name__ == "__main__":
    exit(main())