"""
Processing Manager for handling case processing tasks
"""
import asyncio
import logging
import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import sys

logger = logging.getLogger(__name__)


class ProcessingManager:
    """
    Manages asynchronous processing of bank statement cases
    """
    
    def __init__(self, scripts_dir: Path):
        self.scripts_dir = Path(scripts_dir)
        self.active_processes: Dict[str, Dict[str, Any]] = {}
        self.processing_status: Dict[str, Dict[str, Any]] = {}
        
    async def start_processing(self, case_id: str, case):
        """
        Start processing a case asynchronously
        """
        if case_id in self.active_processes:
            raise ValueError(f"Case {case_id} is already being processed")
        
        # Initialize status
        self.processing_status[case_id] = {
            "case_id": case_id,
            "status": "processing",
            "progress": 0,
            "total": 0,
            "message": "Initializing processing..."
        }
        
        # Create async task for processing
        task = asyncio.create_task(self._process_case(case_id, case))
        self.active_processes[case_id] = {
            "task": task,
            "start_time": datetime.now()
        }
        
        logger.info(f"Started processing for case {case_id}")
    
    async def _process_case(self, case_id: str, case):
        """
        Internal method to process a case
        """
        try:
            # Import processing scripts
            sys.path.insert(0, str(self.scripts_dir))
            from fnb_statement_to_sqlite import process_statements
            
            input_folder = Path(case.input_folder)
            db_path = Path(case.db_path)
            
            # Get list of PDF files
            pdf_files = list(input_folder.glob("*.pdf"))
            total_files = len(pdf_files)
            
            self.processing_status[case_id].update({
                "total": total_files,
                "message": f"Found {total_files} PDF files to process"
            })
            
            # Process each file
            for idx, pdf_file in enumerate(pdf_files):
                # Check for cancellation
                if self.processing_status[case_id].get("cancelled"):
                    logger.info(f"Processing cancelled for case {case_id}")
                    break
                
                self.processing_status[case_id].update({
                    "progress": idx,
                    "message": f"Processing {pdf_file.name}..."
                })
                
                # Simulate processing (replace with actual processing)
                await asyncio.sleep(0.5)  # Simulate work
            
            # Mark as complete
            if not self.processing_status[case_id].get("cancelled"):
                self.processing_status[case_id].update({
                    "status": "completed",
                    "progress": total_files,
                    "message": "Processing completed successfully"
                })
                logger.info(f"Processing completed for case {case_id}")
            else:
                self.processing_status[case_id].update({
                    "status": "cancelled",
                    "message": "Processing was cancelled"
                })
        
        except Exception as e:
            logger.error(f"Processing error for case {case_id}: {e}")
            self.processing_status[case_id].update({
                "status": "error",
                "message": f"Error: {str(e)}"
            })
        
        finally:
            # Clean up
            if case_id in self.active_processes:
                del self.active_processes[case_id]
    
    async def cancel_processing(self, case_id: str):
        """
        Cancel processing for a case
        """
        if case_id in self.processing_status:
            self.processing_status[case_id]["cancelled"] = True
            logger.info(f"Cancellation requested for case {case_id}")
        
        if case_id in self.active_processes:
            task = self.active_processes[case_id]["task"]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    
    async def get_status(self, case_id: str) -> Optional[Dict[str, Any]]:
        """
        Get processing status for a case
        """
        return self.processing_status.get(case_id)
    
    async def chat_query(
        self,
        case_id: str,
        message: str,
        conversation_history: List[Dict[str, str]]
    ) -> str:
        """
        Process a chat query against case data
        """
        try:
            # Import chat assistant
            sys.path.insert(0, str(self.scripts_dir))
            
            # Simulate chat response (replace with actual AI chat)
            response = f"AI Response to: {message}"
            
            logger.info(f"Chat query processed for case {case_id}")
            return response
        
        except Exception as e:
            logger.error(f"Chat query error: {e}")
            raise
    
    async def get_insights(self, case_id: str, db_path: str) -> Dict[str, Any]:
        """
        Get insights and statistics for a case
        """
        try:
            # Connect to SQLite database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get statistics
            cursor.execute("SELECT COUNT(*) FROM transactions")
            total_transactions = cursor.fetchone()[0]
            
            cursor.execute("SELECT SUM(amount) FROM transactions WHERE amount > 0")
            total_credits = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT SUM(amount) FROM transactions WHERE amount < 0")
            total_debits = cursor.fetchone()[0] or 0
            
            conn.close()
            
            insights = {
                "insights": {
                    "total_transactions": total_transactions,
                    "total_credits": float(total_credits),
                    "total_debits": float(total_debits),
                    "net_flow": float(total_credits + total_debits)
                },
                "statistics": {
                    "transaction_count": total_transactions
                },
                "network_data": None
            }
            
            logger.info(f"Insights generated for case {case_id}")
            return insights
        
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return {
                "insights": {},
                "statistics": {},
                "network_data": None
            }
    
    async def cleanup(self):
        """
        Cleanup all active processes
        """
        for case_id in list(self.active_processes.keys()):
            await self.cancel_processing(case_id)
        logger.info("Processing manager cleanup complete")
