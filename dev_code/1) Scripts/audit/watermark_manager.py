import pandas as pd
from sqlalchemy import text
from datetime import datetime, timedelta

class WatermarkManager:
    def __init__(self, engine):
        """Initialize with a SQLAlchemy engine connected to postgres-control"""
        self.engine = engine
        self.schema = 'control'
        self.table_name = 'watermarks'

    def get_watermark(self, target_table):
        """
        Reads the watermark for a specific table and calculates the safety margin.
        Returns a dictionary with safe extraction bounds.
        """
        query = text(f"""
            SELECT incremental_column, last_processed_id, last_processed_timestamp, 
                   safety_margin_minutes, safety_margin_rows
            FROM {self.schema}.{self.table_name}
            WHERE table_name = :table_name
        """)
        
        with self.engine.connect() as conn:
            result = conn.execute(query, {"table_name": target_table}).mappings().fetchone()
            
            if result:
                # 1. Apply ID-based Safety Margin
                safe_id = max(0, result['last_processed_id'] - result['safety_margin_rows'])
                
                # 2. Apply Timestamp-based Safety Margin (if timestamp exists)
                safe_timestamp = None
                if result['last_processed_timestamp']:
                    safe_timestamp = result['last_processed_timestamp'] - timedelta(minutes=result['safety_margin_minutes'])
                    
                print(f"🔍 Watermark for {target_table}: Last ID = {result['last_processed_id']}, Safe ID to extract from = {safe_id}")
                
                return {
                    "incremental_column": result['incremental_column'],
                    "last_processed_id": result['last_processed_id'],
                    "safe_extraction_id": safe_id,
                    "last_processed_timestamp": result['last_processed_timestamp'],
                    "safe_extraction_timestamp": safe_timestamp
                }
            else:
                print(f"⚠️ No watermark found for {target_table}. Full load might be required.")
                return None

    def update_watermark(self, target_table, new_max_id, new_max_timestamp=None):
        """
        Updates the watermark in the control database after successful extraction/load.
        """
        query = text(f"""
            UPDATE {self.schema}.{self.table_name}
            SET last_processed_id = :new_id,
                last_processed_timestamp = COALESCE(:new_timestamp, last_processed_timestamp),
                updated_at = CURRENT_TIMESTAMP
            WHERE table_name = :table_name
        """)
        
        with self.engine.begin() as conn:
            conn.execute(query, {
                "new_id": new_max_id,
                "new_timestamp": new_max_timestamp,
                "table_name": target_table
            })
            print(f"✅ Watermark updated successfully for {target_table} -> New ID: {new_max_id}")