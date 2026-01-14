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
    cur.execute("CREATE DATABASE wfm_db;")
    print("Database `wfm_db` created successfully.")
    cur.close()
    conn.close()
except psycopg2.errors.DuplicateDatabase:
    print("Database `wfm_db` already exists.")
except Exception as e:
    print(f"Error creating database: {e}")
