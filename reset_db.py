import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

try:
    conn = psycopg2.connect(
        user="postgres",
        password="1q2w3e4r",
        host="localhost",
        port="5432"
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    # Terminate existing connections
    cur.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'wfm_db';")
    
    cur.execute("DROP DATABASE IF EXISTS wfm_db;")
    print("Database `wfm_db` dropped.")
    
    cur.execute("CREATE DATABASE wfm_db;")
    print("Database `wfm_db` created successfully.")
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error resetting database: {e}")
