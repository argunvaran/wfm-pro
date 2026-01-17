import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.getenv('DB_NAME', 'wfm_db')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')

print(f"Connecting to {DB_HOST} as {DB_USER}...")

try:
    # Connect to 'postgres' db to drop/create the target db
    conn = psycopg2.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        dbname='postgres' 
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    # Terminate existing connections
    print(f"Terminating connections to {DB_NAME}...")
    cur.execute(f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{DB_NAME}';")
    
    print(f"Dropping database {DB_NAME}...")
    cur.execute(f"DROP DATABASE IF EXISTS {DB_NAME};")
    
    print(f"Creating database {DB_NAME}...")
    cur.execute(f"CREATE DATABASE {DB_NAME};")
    
    print(f"Database `{DB_NAME}` reset successfully.")
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error resetting database: {e}")
