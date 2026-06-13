"""
Database Migration Runner
Executes SQL migration files in sequence
"""
import os
import sys
import psycopg2
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MigrationRunner:
    """Execute SQL migrations in order"""

    def __init__(self, database_url: str):
        """
        Initialize migration runner

        Args:
            database_url: PostgreSQL connection string
        """
        self.database_url = database_url
        self.migrations_dir = Path(__file__).parent
        self.migrations_table = 'schema_migrations'

    def connect(self):
        """Create database connection"""
        try:
            conn = psycopg2.connect(self.database_url)
            logger.info("✓ Connected to database")
            return conn
        except psycopg2.Error as e:
            logger.error(f"✗ Failed to connect to database: {e}")
            raise

    def ensure_migrations_table(self, cursor):
        """Create migrations tracking table if not exists"""
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.migrations_table} (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) UNIQUE NOT NULL,
            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        try:
            cursor.execute(create_table_sql)
            logger.info(f"✓ Ensured {self.migrations_table} table exists")
        except psycopg2.Error as e:
            logger.error(f"✗ Failed to create {self.migrations_table}: {e}")
            raise

    def get_executed_migrations(self, cursor) -> set:
        """Get list of already-executed migrations"""
        try:
            cursor.execute(f"SELECT name FROM {self.migrations_table}")
            return {row[0] for row in cursor.fetchall()}
        except psycopg2.Error as e:
            logger.error(f"✗ Failed to fetch migration history: {e}")
            return set()

    def get_migration_files(self) -> list:
        """Get migration files sorted by name (ensures order)"""
        migration_files = sorted([
            f for f in self.migrations_dir.glob('*.sql')
            if f.name != 'schema_migrations'
        ])
        return migration_files

    def record_migration(self, cursor, migration_name: str):
        """Record completed migration"""
        insert_sql = f"INSERT INTO {self.migrations_table} (name) VALUES (%s)"
        try:
            cursor.execute(insert_sql, (migration_name,))
        except psycopg2.Error as e:
            logger.error(f"✗ Failed to record migration: {e}")
            raise

    def execute_migration(self, cursor, migration_file: Path) -> bool:
        """
        Execute a single migration file

        Args:
            cursor: Database cursor
            migration_file: Path to .sql file

        Returns:
            True if successful, False otherwise
        """
        migration_name = migration_file.name
        logger.info(f"\n{'='*60}")
        logger.info(f"Executing: {migration_name}")
        logger.info(f"{'='*60}")

        try:
            with open(migration_file, 'r') as f:
                sql_content = f.read()

            # Execute the SQL
            cursor.execute(sql_content)

            # Record the migration
            self.record_migration(cursor, migration_name)

            logger.info(f"✓ Successfully executed {migration_name}")
            return True

        except psycopg2.Error as e:
            logger.error(f"✗ Failed to execute {migration_name}")
            logger.error(f"  Error: {e}")
            return False
        except Exception as e:
            logger.error(f"✗ Unexpected error in {migration_name}: {e}")
            return False

    def run(self):
        """Execute all pending migrations"""
        conn = None
        try:
            # Connect to database
            conn = self.connect()
            cursor = conn.cursor()

            # Ensure migrations table exists
            self.ensure_migrations_table(cursor)
            conn.commit()

            # Get executed migrations
            executed = self.get_executed_migrations(cursor)
            logger.info(f"Already executed: {len(executed)} migration(s)")

            # Get all migration files
            migration_files = self.get_migration_files()
            logger.info(f"Found: {len(migration_files)} migration file(s)")

            if not migration_files:
                logger.warning("No migration files found!")
                return True

            # Execute pending migrations
            pending = [f for f in migration_files if f.name not in executed]

            if not pending:
                logger.info("✓ All migrations already executed!")
                return True

            logger.info(f"\nExecuting {len(pending)} pending migration(s)...\n")

            failed = []
            for migration_file in pending:
                success = self.execute_migration(cursor, migration_file)
                if success:
                    conn.commit()
                else:
                    conn.rollback()
                    failed.append(migration_file.name)

            # Summary
            logger.info(f"\n{'='*60}")
            logger.info("MIGRATION SUMMARY")
            logger.info(f"{'='*60}")
            logger.info(f"Total migrations: {len(migration_files)}")
            logger.info(f"Executed this run: {len(pending) - len(failed)}")
            logger.info(f"Failed: {len(failed)}")

            if failed:
                logger.error(f"\nFailed migrations: {', '.join(failed)}")
                logger.error("Please review the errors above and fix the migrations.")
                return False
            else:
                logger.info("\n✓ All migrations completed successfully!")
                return True

        except Exception as e:
            logger.error(f"Fatal error: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()


def main():
    """Main entry point"""
    # Get database URL from environment
    database_url = os.getenv(
        'DATABASE_URL',
        'postgresql://postgres:postgres@localhost:5432/llm_obs'
    )

    logger.info("="*60)
    logger.info("LLM Observability Dashboard - Database Migration Runner")
    logger.info("="*60)
    logger.info(f"Database: {database_url.split('@')[-1]}")  # Show only host/db part
    logger.info("="*60)

    runner = MigrationRunner(database_url)
    success = runner.run()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
