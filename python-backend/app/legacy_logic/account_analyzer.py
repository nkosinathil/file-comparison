import sqlite3
import pandas as pd
import re
from pathlib import Path
from collections import defaultdict, Counter
import hashlib
import json
from datetime import datetime

def extract_account_from_filename(filename):
    """
    Extract account info from PDF filename using specific pattern:
    62275063536_20240420.pdf  (accountNumber_date.pdf)
    """
    filename = str(filename)
    
    # Your specific pattern: accountNumber_date.pdf
    # Example: 62275063536_20240420.pdf
    pattern = r'^(\d+)_(\d{8})\.pdf$'
    match = re.search(pattern, filename)
    
    if match:
        account_number = match.group(1)
        date_str = match.group(2)
        
        # Format date as YYYY-MM-DD
        try:
            formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        except:
            formatted_date = date_str
        
        return {
            'account_id': f"ACC_{account_number}",
            'account_number': account_number,
            'statement_date': formatted_date,
            'raw_date': date_str
        }
    
    # Fallback to other patterns if your specific pattern doesn't match
    filename_lower = filename.lower()
    
    # Pattern: accountNumber_date.pdf (more flexible)
    general_pattern = r'(\d{6,15})_(\d{8})'
    match = re.search(general_pattern, filename)
    if match:
        return {
            'account_id': f"ACC_{match.group(1)}",
            'account_number': match.group(1),
            'statement_date': f"{match.group(2)[:4]}-{match.group(2)[4:6]}-{match.group(2)[6:8]}",
            'raw_date': match.group(2)
        }
    
    # If no pattern matches, use fallback
    return {
        'account_id': f"ACC_{Path(filename).stem}",
        'account_number': 'unknown',
        'statement_date': 'unknown',
        'raw_date': 'unknown'
    }


class FNBAccountAnalyzer:
    def __init__(self, db_path="fnb_statements.db"):
        self.db_path = db_path
        try:
            self.conn = sqlite3.connect(db_path)
            print(f"✅ Connected to database: {db_path}")
        except Exception as e:
            print(f"❌ Error connecting to database: {e}")
            raise
    
    def analyze_files(self):
        """
        Identify accounts from PDF filenames using your specific pattern
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT source_file, COUNT(*) as txn_count,
                   SUM(debit) as total_out,
                   SUM(credit) as total_in,
                   MIN(txn_date) as earliest_txn,
                   MAX(txn_date) as latest_txn
            FROM fnb_transactions 
            GROUP BY source_file
            ORDER BY source_file
        """)
        
        file_accounts = []
        rows = cursor.fetchall()
        
        if not rows:
            print("⚠️ No files found in database")
            return file_accounts
        
        print("\n📁 Accounts Identified from Files:")
        print("-" * 80)
        
        # Track unique accounts
        unique_accounts = set()
        
        for row in rows:
            source_file, txn_count, total_out, total_in, earliest_txn, latest_txn = row
            
            # Extract account info from filename
            account_info = extract_account_from_filename(source_file)
            
            # Handle None values
            total_out = float(total_out) if total_out else 0.0
            total_in = float(total_in) if total_in else 0.0
            net_flow = total_in - total_out
            
            account_info.update({
                'source_file': source_file,
                'transactions': txn_count,
                'total_out': total_out,
                'total_in': total_in,
                'net_flow': net_flow,
                'earliest_txn': earliest_txn,
                'latest_txn': latest_txn
            })
            
            file_accounts.append(account_info)
            unique_accounts.add(account_info['account_id'])
            
            # Print detailed info
            print(f"\n📄 {source_file}")
            print(f"  → Account Number: {account_info['account_number']}")
            print(f"  → Account ID: {account_info['account_id']}")
            print(f"  → Statement Date: {account_info['statement_date']}")
            print(f"  → Transactions in this file: {txn_count}")
            print(f"  → Transaction period: {earliest_txn} to {latest_txn}")
            print(f"  → Money Out: R{total_out:,.2f}")
            print(f"  → Money In: R{total_in:,.2f}")
            print(f"  → Net Flow: R{net_flow:,.2f}")
        
        # Print summary
        print("\n" + "=" * 80)
        print(f"📊 SUMMARY: Found {len(unique_accounts)} Unique Bank Accounts across {len(file_accounts)} files")
        print("=" * 80)
        
        # Group by account number
        accounts_by_number = {}
        for acc in file_accounts:
            acc_num = acc['account_number']
            if acc_num not in accounts_by_number:
                accounts_by_number[acc_num] = {
                    'account_id': acc['account_id'],
                    'files': [],
                    'total_transactions': 0,
                    'total_out': 0,
                    'total_in': 0,
                    'first_statement': acc['statement_date'],
                    'last_statement': acc['statement_date']
                }
            
            accounts_by_number[acc_num]['files'].append(acc['source_file'])
            accounts_by_number[acc_num]['total_transactions'] += acc['transactions']
            accounts_by_number[acc_num]['total_out'] += acc['total_out']
            accounts_by_number[acc_num]['total_in'] += acc['total_in']
            
            # Update date range
            if acc['statement_date'] < accounts_by_number[acc_num]['first_statement']:
                accounts_by_number[acc_num]['first_statement'] = acc['statement_date']
            if acc['statement_date'] > accounts_by_number[acc_num]['last_statement']:
                accounts_by_number[acc_num]['last_statement'] = acc['statement_date']
        
        # Print account summary
        print("\n🏦 ACCOUNT SUMMARY:")
        for acc_num, data in accounts_by_number.items():
            print(f"\n  Account: {acc_num}")
            print(f"    Files: {len(data['files'])}")
            print(f"    Total Transactions: {data['total_transactions']}")
            print(f"    Date Range: {data['first_statement']} to {data['last_statement']}")
            print(f"    Total Out: R{data['total_out']:,.2f}")
            print(f"    Total In: R{data['total_in']:,.2f}")
            print(f"    Net Flow: R{data['total_in'] - data['total_out']:,.2f}")
        
        return file_accounts, accounts_by_number
    
    def analyze_descriptions(self):
        """
        Identify recurring payees/accounts from descriptions
        """
        df = pd.read_sql_query("""
            SELECT txn_date, description, debit, credit, source_file
            FROM fnb_transactions
        """, self.conn)
        
        if df.empty:
            print("⚠️ No transactions found in database")
            return {}
        
        # Get account mapping from files
        file_accounts, _ = self.analyze_files()
        file_to_account = {acc['source_file']: acc['account_number'] for acc in file_accounts}
        
        # Extract potential account names
        accounts = defaultdict(lambda: {
            'name': '',
            'transactions': [],
            'total_debits': 0.0,
            'total_credits': 0.0,
            'frequency': 0,
            'first_seen': None,
            'last_seen': None,
            'account_numbers': set()  # Track which bank accounts interacted with this payee
        })
        
        # Common keywords that precede account names
        keywords = [
            'payment to', 'transfer to', 'paid to', 'from',
            'purchase at', 'debit order', 'stop order',
            'salary from', 'wages from', 'internet transfer to',
            'online payment to', 'eft to', 'account transfer to'
        ]
        
        for _, row in df.iterrows():
            desc = str(row['description']).lower()
            
            # Skip if description is too short
            if len(desc) < 5:
                continue
                
            amount = float(row['debit']) if pd.notna(row['debit']) else float(row['credit'])
            txn_type = 'debit' if pd.notna(row['debit']) else 'credit'
            
            # Get which bank account this transaction belongs to
            bank_account = file_to_account.get(row['source_file'], 'unknown')
            
            # Try to extract account name
            account_found = False
            for keyword in keywords:
                if keyword in desc:
                    parts = desc.split(keyword)
                    if len(parts) > 1:
                        potential_name = parts[1].strip()
                        # Clean up
                        potential_name = re.sub(r'\s+ref\s*[\d\s]+', '', potential_name)
                        potential_name = re.sub(r'\s+\d{4}[-/]\d{2}[-/]\d{2}', '', potential_name)
                        potential_name = re.sub(r'\s+\d{2}[-/]\d{2}[-/]\d{4}', '', potential_name)
                        potential_name = re.sub(r'\s+\d+$', '', potential_name)
                        potential_name = re.sub(r'^\s+|\s+$', '', potential_name)
                        
                        if potential_name and len(potential_name) > 2:
                            acc_id = f"PAYEE_{hash(potential_name) % 10000:04d}"
                            
                            accounts[acc_id]['name'] = potential_name.title()
                            accounts[acc_id]['transactions'].append({
                                'date': row['txn_date'],
                                'amount': amount,
                                'type': txn_type,
                                'description': row['description'][:50]
                            })
                            accounts[acc_id]['frequency'] += 1
                            accounts[acc_id]['account_numbers'].add(bank_account)
                            
                            if accounts[acc_id]['first_seen'] is None or row['txn_date'] < accounts[acc_id]['first_seen']:
                                accounts[acc_id]['first_seen'] = row['txn_date']
                            if accounts[acc_id]['last_seen'] is None or row['txn_date'] > accounts[acc_id]['last_seen']:
                                accounts[acc_id]['last_seen'] = row['txn_date']
                            
                            if txn_type == 'debit':
                                accounts[acc_id]['total_debits'] += amount
                            else:
                                accounts[acc_id]['total_credits'] += amount
                            
                            account_found = True
                            break
        
        # Filter and sort
        significant_accounts = {
            acc_id: data for acc_id, data in accounts.items() 
            if data['frequency'] >= 2
        }
        
        # Convert sets to lists for JSON serialization
        for acc_id in significant_accounts:
            significant_accounts[acc_id]['account_numbers'] = list(significant_accounts[acc_id]['account_numbers'])
        
        sorted_accounts = sorted(
            significant_accounts.items(),
            key=lambda x: x[1]['frequency'],
            reverse=True
        )
        
        print(f"\n🏦 Detected {len(significant_accounts)} Regular Payees/Accounts:")
        print("-" * 80)
        
        for i, (acc_id, data) in enumerate(sorted_accounts[:15], 1):
            print(f"\n{i}. {data['name']}")
            print(f"   Transactions: {data['frequency']}")
            print(f"   Period: {data['first_seen']} to {data['last_seen']}")
            print(f"   Total Paid: R{data['total_debits']:,.2f}")
            if data['total_credits'] > 0:
                print(f"   Total Received: R{data['total_credits']:,.2f}")
            print(f"   Interacted with {len(data['account_numbers'])} of your bank accounts")
        
        return dict(significant_accounts)
    
    def analyze_inter_account_flow(self):
        """
        Analyze money flow between detected accounts
        """
        df = pd.read_sql_query("""
            SELECT txn_date, description, debit, credit, source_file
            FROM fnb_transactions
        """, self.conn)
        
        if df.empty:
            return {}
        
        # Get account mapping
        file_accounts, accounts_by_number = self.analyze_files()
        file_to_account = {acc['source_file']: acc['account_number'] for acc in file_accounts}
        
        # Build flow network
        flows = defaultdict(lambda: defaultdict(float))
        
        for _, row in df.iterrows():
            desc = str(row['description']).lower()
            amount = float(row['debit']) if pd.notna(row['debit']) else float(row['credit'])
            txn_type = 'debit' if pd.notna(row['debit']) else 'credit'
            
            source_account = file_to_account.get(row['source_file'], 'unknown')
            
            # Try to identify counterparty
            counterparty = None
            for keyword in ['payment to', 'transfer to', 'paid to', 'from', 'purchase at']:
                if keyword in desc:
                    parts = desc.split(keyword)
                    if len(parts) > 1:
                        counterparty = parts[1].strip()[:30]
                        counterparty = re.sub(r'\s+ref.*$', '', counterparty)
                        break
            
            if counterparty and amount > 0:
                if txn_type == 'debit':
                    # Money from my account to counterparty
                    flows[source_account][counterparty] += amount
                else:
                    # Money from counterparty to my account
                    flows[counterparty][source_account] += amount
        
        print("\n💰 Money Flow Analysis (by Account):")
        print("-" * 80)
        
        for account_num in accounts_by_number.keys():
            print(f"\nAccount {account_num}:")
            account_flows = {k: v for k, v in flows.items() if k == account_num}
            for source, destinations in account_flows.items():
                for dest, amt in sorted(destinations.items(), key=lambda x: x[1], reverse=True)[:5]:
                    if amt > 1000:
                        print(f"  → {dest[:40]}: R{amt:,.2f}")
        
        return flows
    
    def generate_account_report(self):
        """
        Generate comprehensive account report
        """
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE ACCOUNT ANALYSIS REPORT")
        print("=" * 80)
        
        file_accounts, accounts_by_number = self.analyze_files()
        description_accounts = self.analyze_descriptions()
        flows = self.analyze_inter_account_flow()
        
        print("\n" + "=" * 80)
        print("📊 FINAL SUMMARY")
        print("=" * 80)
        
        print(f"\n📁 Total PDF Statements: {len(file_accounts)}")
        print(f"🏦 Unique Bank Accounts: {len(accounts_by_number)}")
        print(f"💰 Unique Payees/Vendors: {len(description_accounts)}")
        
        print("\n📈 ACCOUNT PERFORMANCE:")
        for acc_num, data in accounts_by_number.items():
            net = data['total_in'] - data['total_out']
            print(f"\n  Account {acc_num}:")
            print(f"    Period: {data['first_statement']} to {data['last_statement']}")
            print(f"    Net Position: R{net:,.2f} ({'Positive' if net >= 0 else 'Negative'})")
            print(f"    Avg Monthly Spend: R{data['total_out'] / max(1, len(data['files'])):,.2f}")
        
        return {
            'file_accounts': file_accounts,
            'accounts_by_number': accounts_by_number,
            'description_accounts': description_accounts,
            'flows': flows
        }


def main():
    import sys
    
    db_path = "fnb_statements.db"
    if not Path(db_path).exists():
        print(f"❌ Database file '{db_path}' not found!")
        return
    
    try:
        analyzer = FNBAccountAnalyzer(db_path)
        results = analyzer.generate_account_report()
        
        # Save to JSON
        with open('account_analysis.json', 'w', encoding='utf-8') as f:
            # Convert for JSON serialization
            json_results = {
                'file_accounts': results['file_accounts'],
                'accounts_by_number': dict(results['accounts_by_number']),
                'description_accounts': results['description_accounts'],
            }
            json.dump(json_results, f, indent=2, default=str, ensure_ascii=False)
        
        print(f"\n💾 Analysis saved to 'account_analysis.json'")
        analyzer.conn.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()