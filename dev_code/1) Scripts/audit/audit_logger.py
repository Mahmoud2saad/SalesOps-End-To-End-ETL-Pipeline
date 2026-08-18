from sqlalchemy import text

class AuditLogger:
    def __init__(self, engine):
        """Initialize with a SQLAlchemy engine connected to postgres-control"""
        self.engine = engine
        self.schema = 'control'

    def log_start(self, pipeline_name, execution_id, task_name, table_name):
        """
        Logs the start of a batch extraction/load by calling the DB function.
        Returns the generated audit_id to be used when completing the log.
        """
        query = text(f"""
            SELECT {self.schema}.log_batch_start(
                :pipeline_name, :execution_id, :task_name, :table_name
            );
        """)
        
        with self.engine.begin() as conn:
            # scalar() fetches the first column of the first row (the returned audit_id)
            audit_id = conn.execute(query, {
                "pipeline_name": pipeline_name,
                "execution_id": str(execution_id),
                "task_name": task_name,
                "table_name": table_name
            }).scalar()
            
            print(f"📝 Audit log STARTED for {table_name} | Task: {task_name} | Audit ID: {audit_id}")
            return audit_id

    def log_complete(self, audit_id, status, rows_processed=0, error_message=None):
        """
        Logs the completion or failure of a batch by calling the DB function.
        Status should be one of: 'SUCCESS', 'FAILED', 'SKIPPED'
        """
        query = text(f"""
            SELECT {self.schema}.log_batch_complete(
                :audit_id, :status, :rows_processed, :error_message
            );
        """)
        
        with self.engine.begin() as conn:
            conn.execute(query, {
                "audit_id": audit_id,
                "status": status,
                "rows_processed": rows_processed,
                "error_message": error_message
            })
            
            symbol = "✅" if status == 'SUCCESS' else "❌" if status == 'FAILED' else "⏭️"
            print(f"{symbol} Audit log COMPLETED for Audit ID: {audit_id} | Status: {status} | Rows: {rows_processed}")